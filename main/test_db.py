import psycopg2

DB_CONFIG = {
    "dbname": "lasersan", 
    "user": "postgres",
    "password": "1357913",
    "host": "localhost"
}

try:
    print("PostgreSQL'e bağlanmaya çalışıyorum...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("✅ HARİKA! psycopg2 kütüphanesi ve veritabanı kusursuz çalışıyor.")
    conn.close()
except Exception as e:
    print("❌ Bağlantı Hatası:", e)