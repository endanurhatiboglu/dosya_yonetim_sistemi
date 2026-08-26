import sqlite3

baglanti = sqlite3.connect("database.db")
cursor = baglanti.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS fabrikalar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fabrika_adi TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS kullanicilar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kullanici_adi TEXT NOT NULL UNIQUE,
    sifre TEXT NOT NULL,
    rol TEXT NOT NULL,
    fabrika_id INTEGER,
    FOREIGN KEY (fabrika_id) REFERENCES fabrikalar(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS evraklar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evrak_adi TEXT NOT NULL,
    fabrika_id INTEGER,
    aciklama TEXT,
    durum TEXT NOT NULL,
    tarih TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fabrika_id) REFERENCES fabrikalar(id)
)
""")

cursor.execute("SELECT COUNT(*) FROM fabrikalar")
fabrika_sayisi = cursor.fetchone()[0]

if fabrika_sayisi == 0:

    fabrikalar = [
        ("Fabrika A",),
        ("Fabrika B",),
        ("Fabrika C",),
        ("Fabrika D",)
    ]

    cursor.executemany(
        "INSERT INTO fabrikalar (fabrika_adi) VALUES (?)",
        fabrikalar
    )


cursor.execute("SELECT COUNT(*) FROM kullanicilar")
kullanici_sayisi = cursor.fetchone()[0]

if kullanici_sayisi == 0:

    kullanicilar = [
        ("admin", "1234", "yonetici", None),
        ("fabrika_a", "1234", "fabrika", 1),
        ("fabrika_b", "1234", "fabrika", 2),
        ("fabrika_c", "1234", "fabrika", 3),
        ("fabrika_d", "1234", "fabrika", 4)
    ]

    cursor.executemany(
        """
        INSERT INTO kullanicilar
        (kullanici_adi, sifre, rol, fabrika_id)
        VALUES (?, ?, ?, ?)
        """,
        kullanicilar
    )

baglanti.commit()
baglanti.close()

print("Veritabanı hazır.")