import sqlite3
import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory
)

from werkzeug.utils import secure_filename


app = Flask(__name__)

app.secret_key = "proje_yonetim_sistemi_gizli_anahtar"

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def veritabani_baglan():
    return sqlite3.connect("database.db")


def evrak_tablosu_olustur():

    baglanti = veritabani_baglan()
    cursor = baglanti.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evraklar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evrak_adi TEXT NOT NULL,
            fabrika_id INTEGER,
            aciklama TEXT,
            durum TEXT NOT NULL
        )
    """)

    baglanti.commit()
    baglanti.close()


def dosya_tablosu_olustur():

    baglanti = veritabani_baglan()
    cursor = baglanti.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dosyalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dosya_adi TEXT NOT NULL,
            fabrika_id INTEGER
        )
    """)

    baglanti.commit()
    baglanti.close()


evrak_tablosu_olustur()
dosya_tablosu_olustur()


@app.route("/", methods=["GET", "POST"])
def ana_sayfa():

    hata = None

    if request.method == "POST":

        kullanici_adi = request.form["kullanici_adi"]
        sifre = request.form["sifre"]

        baglanti = veritabani_baglan()
        cursor = baglanti.cursor()

        cursor.execute("""
            SELECT id, kullanici_adi, rol, fabrika_id
            FROM kullanicilar
            WHERE kullanici_adi = ? AND sifre = ?
        """, (kullanici_adi, sifre))

        kullanici = cursor.fetchone()

        baglanti.close()

        if kullanici:

            session["kullanici_id"] = kullanici[0]
            session["kullanici_adi"] = kullanici[1]
            session["rol"] = kullanici[2]
            session["fabrika_id"] = kullanici[3]

            return redirect(url_for("dashboard"))

        hata = "Kullanıcı adı veya şifre hatalı."

    return render_template(
        "login.html",
        hata=hata
    )


@app.route("/dashboard")
def dashboard():

    if "kullanici_id" not in session:
        return redirect(url_for("ana_sayfa"))

    baglanti = veritabani_baglan()
    cursor = baglanti.cursor()

    if session["rol"] == "yonetici":

        cursor.execute("""
            SELECT COUNT(*)
            FROM evraklar
            WHERE durum != 'Arşiv'
        """)

        bekleyen_isler = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM evraklar
        """)

        aktif_dosyalar = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM evraklar
            WHERE durum = 'Arşiv'
        """)

        arsivlenen_evraklar = cursor.fetchone()[0]

    else:

        fabrika_id = session["fabrika_id"]

        cursor.execute("""
            SELECT COUNT(*)
            FROM evraklar
            WHERE fabrika_id = ?
            AND durum != 'Arşiv'
        """, (fabrika_id,))

        bekleyen_isler = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM evraklar
            WHERE fabrika_id = ?
        """, (fabrika_id,))

        aktif_dosyalar = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM evraklar
            WHERE fabrika_id = ?
            AND durum = 'Arşiv'
        """, (fabrika_id,))

        arsivlenen_evraklar = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM fabrikalar
    """)

    fabrika_sayisi = cursor.fetchone()[0]

    baglanti.close()

    return render_template(
        "dashboard.html",
        bekleyen_isler=bekleyen_isler,
        aktif_dosyalar=aktif_dosyalar,
        arsivlenen_evraklar=arsivlenen_evraklar,
        fabrika_sayisi=fabrika_sayisi
    )


@app.route("/dosyalar", methods=["GET", "POST"])
def dosyalar():

    if "kullanici_id" not in session:
        return redirect(url_for("ana_sayfa"))

    if request.method == "POST":

        dosya = request.files.get("dosya")

        if dosya and dosya.filename != "":

            dosya_adi = secure_filename(dosya.filename)

            dosya_yolu = os.path.join(
                app.config["UPLOAD_FOLDER"],
                dosya_adi
            )

            dosya.save(dosya_yolu)

            baglanti = veritabani_baglan()
            cursor = baglanti.cursor()

            if session["rol"] == "yonetici":
                fabrika_id = request.form.get("fabrika_id")

                if not fabrika_id:
                    fabrika_id = None

            else:
                fabrika_id = session["fabrika_id"]

            cursor.execute("""
                INSERT INTO dosyalar
                (dosya_adi, fabrika_id)
                VALUES (?, ?)
            """, (
                dosya_adi,
                fabrika_id
            ))

            baglanti.commit()
            baglanti.close()

            session["mesaj"] = "Dosya başarıyla yüklendi."

    baglanti = veritabani_baglan()
    cursor = baglanti.cursor()

    if session["rol"] == "yonetici":

        cursor.execute("""
            SELECT
                dosyalar.id,
                dosyalar.dosya_adi,
                fabrikalar.fabrika_adi
            FROM dosyalar
            LEFT JOIN fabrikalar
            ON dosyalar.fabrika_id = fabrikalar.id
            ORDER BY dosyalar.id DESC
        """)

    else:

        cursor.execute("""
            SELECT
                dosyalar.id,
                dosyalar.dosya_adi,
                fabrikalar.fabrika_adi
            FROM dosyalar
            LEFT JOIN fabrikalar
            ON dosyalar.fabrika_id = fabrikalar.id
            WHERE dosyalar.fabrika_id = ?
            ORDER BY dosyalar.id DESC
        """, (session["fabrika_id"],))

    dosya_listesi = cursor.fetchall()

    cursor.execute("""
        SELECT id, fabrika_adi
        FROM fabrikalar
        ORDER BY id
    """)

    fabrika_listesi = cursor.fetchall()

    baglanti.close()

    mesaj = session.pop("mesaj", None)

    return render_template(
        "dosyalar.html",
        dosya_listesi=dosya_listesi,
        fabrika_listesi=fabrika_listesi,
        mesaj=mesaj
    )


@app.route("/dosya-indir/<dosya_adi>")
def dosya_indir(dosya_adi):

    if "kullanici_id" not in session:
        return redirect(url_for("ana_sayfa"))

    baglanti = veritabani_baglan()
    cursor = baglanti.cursor()

    if session["rol"] == "yonetici":

        cursor.execute("""
            SELECT id
            FROM dosyalar
            WHERE dosya_adi = ?
        """, (dosya_adi,))

    else:

        cursor.execute("""
            SELECT id
            FROM dosyalar
            WHERE dosya_adi = ?
            AND fabrika_id = ?
        """, (
            dosya_adi,
            session["fabrika_id"]
        ))

    dosya = cursor.fetchone()

    baglanti.close()

    if not dosya:
        return "Bu dosyaya erişim yetkiniz yok.", 403

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        dosya_adi,
        as_attachment=True
    )


@app.route("/dosya-sil/<dosya_adi>")
def dosya_sil(dosya_adi):

    if "kullanici_id" not in session:
        return redirect(url_for("ana_sayfa"))

    baglanti = veritabani_baglan()
    cursor = baglanti.cursor()

    if session["rol"] == "yonetici":

        cursor.execute("""
            SELECT id
            FROM dosyalar
            WHERE dosya_adi = ?
        """, (dosya_adi,))

    else:

        cursor.execute("""
            SELECT id
            FROM dosyalar
            WHERE dosya_adi = ?
            AND fabrika_id = ?
        """, (
            dosya_adi,
            session["fabrika_id"]
        ))

    dosya = cursor.fetchone()

    if not dosya:

        baglanti.close()

        return "Bu dosyayı silme yetkiniz yok.", 403

    dosya_yolu = os.path.join(
        app.config["UPLOAD_FOLDER"],
        dosya_adi
    )

    if os.path.exists(dosya_yolu):
        os.remove(dosya_yolu)

    cursor.execute(
        "DELETE FROM dosyalar WHERE id = ?",
        (dosya[0],)
    )

    baglanti.commit()
    baglanti.close()

    session["mesaj"] = "Dosya başarıyla silindi."

    return redirect(url_for("dosyalar"))


@app.route("/fabrikalar")
def fabrikalar():

    if "kullanici_id" not in session:
        return redirect(url_for("ana_sayfa"))

    baglanti = veritabani_baglan()
    cursor = baglanti.cursor()

    cursor.execute("""
        SELECT id, fabrika_adi
        FROM fabrikalar
        ORDER BY id
    """)

    fabrika_listesi = cursor.fetchall()

    baglanti.close()

    return render_template(
        "fabrikalar.html",
        fabrika_listesi=fabrika_listesi
    )


@app.route("/evraklar", methods=["GET", "POST"])
def evraklar():

    if "kullanici_id" not in session:
        return redirect(url_for("ana_sayfa"))

    if request.method == "POST":

        evrak_adi = request.form["evrak_adi"]
        fabrika_id = request.form["fabrika_id"]
        aciklama = request.form["aciklama"]
        durum = request.form["durum"]

        if session["rol"] == "fabrika":
            fabrika_id = session["fabrika_id"]

        baglanti = veritabani_baglan()
        cursor = baglanti.cursor()

        cursor.execute("""
            INSERT INTO evraklar
            (evrak_adi, fabrika_id, aciklama, durum)
            VALUES (?, ?, ?, ?)
        """, (
            evrak_adi,
            fabrika_id,
            aciklama,
            durum
        ))

        baglanti.commit()
        baglanti.close()

        session["mesaj"] = "Evrak başarıyla kaydedildi."

        return redirect(url_for("evraklar"))

    baglanti = veritabani_baglan()
    cursor = baglanti.cursor()

    if session["rol"] == "yonetici":

        cursor.execute("""
            SELECT
                evraklar.id,
                evraklar.evrak_adi,
                fabrikalar.fabrika_adi,
                evraklar.aciklama,
                evraklar.durum
            FROM evraklar
            LEFT JOIN fabrikalar
            ON evraklar.fabrika_id = fabrikalar.id
            ORDER BY evraklar.id DESC
        """)

    else:

        cursor.execute("""
            SELECT
                evraklar.id,
                evraklar.evrak_adi,
                fabrikalar.fabrika_adi,
                evraklar.aciklama,
                evraklar.durum
            FROM evraklar
            LEFT JOIN fabrikalar
            ON evraklar.fabrika_id = fabrikalar.id
            WHERE evraklar.fabrika_id = ?
            ORDER BY evraklar.id DESC
        """, (session["fabrika_id"],))

    evrak_listesi = cursor.fetchall()

    cursor.execute("""
        SELECT id, fabrika_adi
        FROM fabrikalar
        ORDER BY id
    """)

    fabrika_listesi = cursor.fetchall()

    baglanti.close()

    mesaj = session.pop("mesaj", None)

    return render_template(
        "evraklar.html",
        evrak_listesi=evrak_listesi,
        fabrika_listesi=fabrika_listesi,
        mesaj=mesaj
    )


@app.route("/evrak-sil/<int:evrak_id>")
def evrak_sil(evrak_id):

    if "kullanici_id" not in session:
        return redirect(url_for("ana_sayfa"))

    baglanti = veritabani_baglan()
    cursor = baglanti.cursor()

    if session["rol"] == "yonetici":

        cursor.execute(
            "DELETE FROM evraklar WHERE id = ?",
            (evrak_id,)
        )

    else:

        cursor.execute(
            """
            DELETE FROM evraklar
            WHERE id = ?
            AND fabrika_id = ?
            """,
            (
                evrak_id,
                session["fabrika_id"]
            )
        )

    baglanti.commit()
    baglanti.close()

    session["mesaj"] = "Evrak başarıyla silindi."

    return redirect(url_for("evraklar"))


@app.route("/arsiv")
def arsiv():

    if "kullanici_id" not in session:
        return redirect(url_for("ana_sayfa"))

    baglanti = veritabani_baglan()
    cursor = baglanti.cursor()

    if session["rol"] == "yonetici":

        cursor.execute("""
            SELECT
                evraklar.id,
                evraklar.evrak_adi,
                fabrikalar.fabrika_adi,
                evraklar.aciklama,
                evraklar.durum
            FROM evraklar
            LEFT JOIN fabrikalar
            ON evraklar.fabrika_id = fabrikalar.id
            WHERE evraklar.durum = 'Arşiv'
            ORDER BY evraklar.id DESC
        """)

    else:

        cursor.execute("""
            SELECT
                evraklar.id,
                evraklar.evrak_adi,
                fabrikalar.fabrika_adi,
                evraklar.aciklama,
                evraklar.durum
            FROM evraklar
            LEFT JOIN fabrikalar
            ON evraklar.fabrika_id = fabrikalar.id
            WHERE evraklar.durum = 'Arşiv'
            AND evraklar.fabrika_id = ?
            ORDER BY evraklar.id DESC
        """, (session["fabrika_id"],))

    arsiv_listesi = cursor.fetchall()

    baglanti.close()

    return render_template(
        "arsiv.html",
        arsiv_listesi=arsiv_listesi
    )


@app.route("/cikis")
def cikis():

    session.clear()

    return redirect(url_for("ana_sayfa"))


if __name__ == "__main__":
    app.run(debug=True)