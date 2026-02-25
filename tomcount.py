import cv2
import numpy as np
import torch
import psycopg2
from ultralytics import YOLO
from collections import defaultdict, Counter
DB_CONFIG = {
    "dbname": "lasersan", 
    "user": "postgres",
    "password": "1357913",
    "host": "localhost"
}
model = YOLO(r"C:\piton\tomatotrain2\runs\segment\tomatonew4\weights\best.pt")

videopath = r"C:\piton\tomatotrain\img\tomvideo.mp4"
cap = cv2.VideoCapture(videopath, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

counted_ids = set()
id_history = defaultdict(list)
STABLE_FRAMES = 5

ripe_count = 0
half_ripe_count = 0
unripe_count = 0

all_ripeness_values = []

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    if frame_count % 2 != 0:
        continue

    frame = cv2.resize(frame, (1440, 960))

    results = model.track(
        frame,
        conf=0.397,
        persist=True,
        imgsz=640,
        verbose=False
    )

    if results[0].boxes.id is not None and results[0].masks is not None:

        ids = results[0].boxes.id.cpu().numpy().astype(int)
        boxes = results[0].boxes.xyxy.cpu().numpy()
        masks = results[0].masks.data.cpu().numpy()

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        b, g, r = cv2.split(frame)

        for box, mask, track_id in zip(boxes, masks, ids):

            mask = cv2.resize(mask, (frame.shape[1], frame.shape[0]))
            mask = (mask > 0.5).astype(np.uint8)

            h_values = hsv[:, :, 0][mask == 1]
            s_values = hsv[:, :, 1][mask == 1]

            valid = s_values > 50
            h_values = h_values[valid]

            if len(h_values) == 0:
                continue

            h_mean = np.median(h_values)

            g_mean = np.mean(g[mask == 1])
            r_mean = np.mean(r[mask == 1])
            gr_ratio = g_mean / (r_mean + 1e-6)

            if (h_mean <= 18 or h_mean >= 150):
                label = "Olgun"
                color = (0,0,255)
                ripeness_percent = 100

            elif gr_ratio > 1.10 or (38 <= h_mean <= 75):
                label = "Ham"
                color = (0,255,0)
                ripeness_percent = 20

            elif 22 < h_mean < 38:
                label = "Yari Olgun"
                color = (0,165,255)
                ripeness_percent = 60

            else:
                label = "Yari Olgun"
                color = (0,165,255)
                ripeness_percent = 60

            id_history[track_id].append(label)

            if len(id_history[track_id]) > 7:
                id_history[track_id].pop(0)

            label_counter = Counter(id_history[track_id])
            stable_label = label_counter.most_common(1)[0][0]

            if track_id not in counted_ids and len(id_history[track_id]) >= STABLE_FRAMES:

                if stable_label == "Olgun":
                    ripe_count += 1
                    all_ripeness_values.append(100)

                elif stable_label == "Ham":
                    unripe_count += 1
                    all_ripeness_values.append(20)

                elif stable_label == "Yari Olgun":
                    half_ripe_count += 1
                    all_ripeness_values.append(60)

                counted_ids.add(track_id)

            x1, y1, x2, y2 = box.astype(int)
            cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
            cv2.putText(frame,
                        f"{stable_label} %{ripeness_percent}",
                        (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        color,
                        2)

    if len(all_ripeness_values) > 0:
        green_ripeness = int(np.mean(all_ripeness_values))
    else:
        green_ripeness = 0

    cv2.putText(frame, f"Olgun: {ripe_count}", (10,30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

    cv2.putText(frame, f"Yari: {half_ripe_count}", (10,60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,165,255), 2)

    cv2.putText(frame, f"Ham: {unripe_count}", (10,90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    cv2.putText(frame,
                f"Sera Olgunluk: %{green_ripeness}",
                (10,120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255,255,255),
                2)

    cv2.imshow("Tom", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()


print("tamamlandı")

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    insert_query = """
    INSERT INTO analiz_gecmisi 
    (kamera_adi, ham_sayisi, yari_olgun_sayisi, olgun_sayisi, ortalama_olgunluk)
    VALUES (%s, %s, %s, %s, %s)
    """
    
    veri = ("tomvideo.mp4", unripe_count, half_ripe_count, ripe_count, green_ripeness)
    
    cur.execute(insert_query, veri)
    conn.commit()
    
    cur.close()
    conn.close()
    print(" PostgreSQL'e  kaydedildi!")
    
except Exception as e:
    print(" hata ", e)