import sqlite3

baglanti = sqlite3.connect("database.db")
cursor = baglanti.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS dosyalar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dosya_adi TEXT NOT NULL,
    dosya_yolu TEXT NOT NULL,
    aciklama TEXT,
    fabrika_id INTEGER,
    yukleyen_id INTEGER,
    durum TEXT DEFAULT 'Bekliyor',
    yuklenme_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fabrika_id) REFERENCES fabrikalar(id),
    FOREIGN KEY (yukleyen_id) REFERENCES kullanicilar(id)
)
""")

baglanti.commit()
baglanti.close()

print("Dosyalar tablosu hazır.")