import os
import cv2
import numpy as np
import base64
from collections import defaultdict, Counter
from ultralytics import YOLO

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from .models import AnalizGecmisi

YOLO_MODEL = YOLO(r"C:\piton\tomatotrain2\runs\segment\tomatonew4\weights\best.pt")

def dashboard(request):
    son_analiz = AnalizGecmisi.objects.first() 
    if son_analiz:
        total = son_analiz.ham_sayisi + son_analiz.yari_olgun_sayisi + son_analiz.olgun_sayisi
        context = {
            'total': total,
            'average': son_analiz.ortalama_olgunluk,
            'ham': son_analiz.ham_sayisi,
            'yari': son_analiz.yari_olgun_sayisi,
            'olgun': son_analiz.olgun_sayisi,
        }
    else:
        context = {'total': 0, 'average': 0, 'ham': 0, 'yari': 0, 'olgun': 0}
    return render(request, 'index.html', context)

def analiz_gecmisi(request):
    tum_analizler = AnalizGecmisi.objects.all().order_by('-id')
    paginator = Paginator(tum_analizler, 10)
    page_number = request.GET.get('page', 1)
    sayfa_objesi = paginator.get_page(page_number)
    return render(request, 'gecmis.html', {'analizler': sayfa_objesi})

def kameralar(request):
    return render(request, 'kameralar.html')

def ayarlar(request):
    return render(request, 'ayarlar.html')

@csrf_exempt
def yapay_zeka_analiz_api(request):
    if request.method == 'POST' and request.FILES.getlist('files'):
        yuklenen_dosyalar = request.FILES.getlist('files')
        
        toplam_ripe = 0
        toplam_half = 0
        toplam_unripe = 0
        tum_ripeness_degerleri = []
        islenen_gorseller_base64 = []

        ilk_dosya_adi = yuklenen_dosyalar[0].name
        if len(yuklenen_dosyalar) > 1:
            kamera_kayit_adi = f"{len(yuklenen_dosyalar)} Adet Fotoğraf (Toplu Analiz)"
        else:
            kamera_kayit_adi = ilk_dosya_adi

        fs = FileSystemStorage()

        for dosya in yuklenen_dosyalar:
            dosya_tipi = dosya.content_type
            dosya_adi = fs.save(dosya.name, dosya)
            dosya_yolu = fs.path(dosya_adi)

            if dosya_tipi.startswith('video'):
                cap = cv2.VideoCapture(dosya_yolu, cv2.CAP_FFMPEG)
                counted_ids = set()
                id_history = defaultdict(list)
                STABLE_FRAMES = 5
                frame_count = 0

                while True:
                    ret, frame = cap.read()
                    if not ret: break
                    
                    frame_count += 1
                    if frame_count % 2 != 0: continue
                        
                    frame = cv2.resize(frame, (1440, 960))
                    results = YOLO_MODEL.track(frame, conf=0.397, persist=True, imgsz=640, verbose=False)

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
                            h_values = h_values[s_values > 50]

                            if len(h_values) == 0: continue

                            h_mean = np.median(h_values)
                            g_mean, r_mean = np.mean(g[mask == 1]), np.mean(r[mask == 1])
                            gr_ratio = g_mean / (r_mean + 1e-6)

                            if (h_mean <= 18 or h_mean >= 150): label = "Olgun"
                            elif gr_ratio > 1.10 or (38 <= h_mean <= 75): label = "Ham"
                            else: label = "Yari Olgun"

                            id_history[track_id].append(label)
                            if len(id_history[track_id]) > 7: id_history[track_id].pop(0)
                            
                            stable_label = Counter(id_history[track_id]).most_common(1)[0][0]

                            if track_id not in counted_ids and len(id_history[track_id]) >= STABLE_FRAMES:
                                if stable_label == "Olgun":
                                    toplam_ripe += 1
                                    tum_ripeness_degerleri.append(100)
                                elif stable_label == "Ham":
                                    toplam_unripe += 1
                                    tum_ripeness_degerleri.append(20)
                                elif stable_label == "Yari Olgun":
                                    toplam_half += 1
                                    tum_ripeness_degerleri.append(60)
                                counted_ids.add(track_id)
                cap.release()

            elif dosya_tipi.startswith('image'):
                frame = cv2.imread(dosya_yolu)
                frame = cv2.resize(frame, (1440, 960))
                
                results = YOLO_MODEL.predict(frame, conf=0.397, imgsz=640, verbose=False)

                annotated_frame = frame.copy()

                if results[0].boxes is not None and results[0].masks is not None:
                    boxes = results[0].boxes.xyxy.cpu().numpy()
                    masks = results[0].masks.data.cpu().numpy()
                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    b, g, r = cv2.split(frame)

                    for box, mask in zip(boxes, masks):
                        mask_resized = cv2.resize(mask, (frame.shape[1], frame.shape[0]))
                        mask_bool = (mask_resized > 0.5).astype(np.uint8)
                        
                        h_values = hsv[:, :, 0][mask_bool == 1]
                        s_values = hsv[:, :, 1][mask_bool == 1]
                        h_values = h_values[s_values > 50]

                        if len(h_values) == 0: continue

                        h_mean = np.median(h_values)
                        g_mean = np.mean(g[mask_bool == 1])
                        r_mean = np.mean(r[mask_bool == 1])
                        gr_ratio = g_mean / (r_mean + 1e-6)

                        if (h_mean <= 18 or h_mean >= 150):
                            toplam_ripe += 1
                            tum_ripeness_degerleri.append(100)
                            label = "Olgun (%100)"
                            color = (0, 0, 255) 
                        elif gr_ratio > 1.10 or (38 <= h_mean <= 75):
                            toplam_unripe += 1
                            tum_ripeness_degerleri.append(20)
                            label = "Ham (%20)"
                            color = (0, 255, 0) 
                        else:
                            toplam_half += 1
                            tum_ripeness_degerleri.append(60)
                            label = "Yari Olgun (%60)"
                            color = (0, 165, 255) 

                        x1, y1, x2, y2 = map(int, box)
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                        colored_mask = np.zeros_like(annotated_frame)
                        colored_mask[mask_bool == 1] = color
                        cv2.addWeighted(annotated_frame, 1, colored_mask, 0.4, 0, annotated_frame)
                        cv2.putText(annotated_frame, label, (x1, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)

                _, buffer = cv2.imencode('.jpg', annotated_frame)
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                islenen_gorseller_base64.append(f"data:image/jpeg;base64,{img_base64}")

            if os.path.exists(dosya_yolu):
                os.remove(dosya_yolu)

        green_ripeness = int(np.mean(tum_ripeness_degerleri)) if len(tum_ripeness_degerleri) > 0 else 0
        
        AnalizGecmisi.objects.create(
            kamera_adi=kamera_kayit_adi,
            ham_sayisi=toplam_unripe,
            yari_olgun_sayisi=toplam_half,
            olgun_sayisi=toplam_ripe,
            ortalama_olgunluk=green_ripeness
        )

        return JsonResponse({
            'status': 'success',
            'mesaj': 'Tüm dosyalar başarıyla analiz edildi!',
            'sonuclar': {
                'ham': toplam_unripe,
                'yari': toplam_half,
                'olgun': toplam_ripe,
                'ortalama': green_ripeness,
                'gorseller': islenen_gorseller_base64
            }
        })
        
    return JsonResponse({'status': 'error', 'mesaj': 'Geçersiz istek veya dosya yok.'})