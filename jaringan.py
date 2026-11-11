"""jaringan.py - Modul Jejaring Profesional Mahasiswa (CVku Network).

Modul ini mengelola tabel tambahan untuk fitur sosial dan jejaring:
- Kolom 'headline' dan 'skill' pada tabel 'pengguna'
- Tabel 'koneksi' (permintaan dan hubungan pertemanan antar mahasiswa)
- Tabel 'posting' (kabar singkat maksimal 500 karakter)
- Tabel 'suka' (reaksi suka per posting)

Semua operasi menggunakan koneksi SQLite melalui db.koneksi() tanpa mengubah db.py.
"""
import os
import shutil
import sqlite3
import db


def cadangkan_semua():
    """Sinkronkan cadangan basis data ke seluruh lokasi cadangan."""
    try:
        db.cadangkan()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        root_backup = os.path.join(base_dir, "cvku_backup.db")
        app_backup = os.path.join(base_dir, "app", "cvku_backup.db")
        if os.path.exists(db.DB_PATH):
            shutil.copy(db.DB_PATH, root_backup)
            if os.path.exists(os.path.join(base_dir, "app")):
                shutil.copy(db.DB_PATH, app_backup)
    except Exception:
        pass


def init_jaringan():
    """Inisialisasi tabel jejaring dan migrasi kolom baru pada tabel pengguna."""
    con = db.koneksi()
    try:
        # 1. Tambah kolom headline dan skill pada pengguna secara aman jika belum ada
        info_kolom = [row["name"] for row in con.execute("PRAGMA table_info(pengguna)").fetchall()]
        if "headline" not in info_kolom:
            con.execute("ALTER TABLE pengguna ADD COLUMN headline TEXT")
        if "skill" not in info_kolom:
            con.execute("ALTER TABLE pengguna ADD COLUMN skill TEXT")

        # 2. Buat tabel koneksi
        con.execute("""
        CREATE TABLE IF NOT EXISTS koneksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pengirim INTEGER NOT NULL REFERENCES pengguna(id),
            id_penerima INTEGER NOT NULL REFERENCES pengguna(id),
            status TEXT NOT NULL DEFAULT 'menunggu' CHECK (status IN ('menunggu', 'terhubung', 'ditolak')),
            dibuat_pada TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(id_pengirim, id_penerima)
        )
        """)

        # 3. Buat tabel posting
        con.execute("""
        CREATE TABLE IF NOT EXISTS posting (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pengguna INTEGER NOT NULL REFERENCES pengguna(id),
            isi TEXT NOT NULL,
            dibuat_pada TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 4. Buat tabel suka (F8)
        con.execute("""
        CREATE TABLE IF NOT EXISTS suka (
            id_posting INTEGER NOT NULL REFERENCES posting(id) ON DELETE CASCADE,
            id_pengguna INTEGER NOT NULL REFERENCES pengguna(id),
            dibuat_pada TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_posting, id_pengguna)
        )
        """)

        con.commit()
    finally:
        con.close()
    cadangkan_semua()


def perbarui_headline_skill(id_pengguna: int, headline: str = None, skill: str = None):
    """Memperbarui kolom headline dan skill untuk pengguna tertentu."""
    con = db.koneksi()
    try:
        h = headline.strip() if headline else ""
        s = skill.strip() if skill else ""
        con.execute(
            "UPDATE pengguna SET headline = ?, skill = ? WHERE id = ?",
            (h, s, id_pengguna)
        )
        con.commit()
    finally:
        con.close()
    cadangkan_semua()


def _parse_skill(skill_str):
    """Helper untuk memecah string skill koma menjadi list tag bersih."""
    if not skill_str:
        return []
    return [s.strip() for s in skill_str.split(",") if s.strip()]


def cari_mahasiswa(q: str = "", id_saat_ini: int = None):
    """Mencari mahasiswa berdasarkan nama, headline, skill, atau judul/uraian kegiatan.
    
    Mengembalikan daftar profil mahasiswa lengkap dengan cuplikan skill dan status koneksi.
    """
    con = db.koneksi()
    try:
        q_clean = (q or "").strip()
        sql = (
            "SELECT u.id, u.username, u.nama, u.kota, u.headline, u.skill, u.linkedin, u.ringkasan "
            "FROM pengguna u "
            "WHERE u.peran = 'mahasiswa'"
        )
        params = []

        if q_clean:
            wildcard = f"%{q_clean}%"
            sql += (
                " AND ("
                "   u.nama LIKE ? OR "
                "   u.headline LIKE ? OR "
                "   u.skill LIKE ? OR "
                "   u.kota LIKE ? OR "
                "   u.id IN (SELECT p.id_pengguna FROM pencapaian p WHERE p.nama_kegiatan LIKE ? OR p.uraian LIKE ?) OR "
                "   u.id IN (SELECT p2.id_pengguna FROM entri_cv e JOIN pencapaian p2 ON p2.id = e.id_pencapaian WHERE e.judul LIKE ?)"
                " )"
            )
            params.extend([wildcard, wildcard, wildcard, wildcard, wildcard, wildcard, wildcard])

        sql += " ORDER BY u.id ASC"
        rows = [dict(r) for r in con.execute(sql, params).fetchall()]

        hasil = []
        for r in rows:
            all_skills = _parse_skill(r.get("skill"))
            r["skill_list"] = all_skills
            r["tiga_skill"] = all_skills[:3]
            if id_saat_ini:
                r["status_koneksi"] = status_koneksi(id_saat_ini, r["id"])
            else:
                r["status_koneksi"] = "tidak_terhubung"
            hasil.append(r)

        return hasil
    finally:
        con.close()


def status_koneksi(id_user1: int, id_user2: int) -> str:
    """Mengecek status hubungan koneksi antara user1 dan user2.
    
    Nilai balik:
    - 'self' : diri sendiri
    - 'terhubung' : sudah terhubung
    - 'menunggu_keluar' : user1 sudah mengirim permintaan, menunggu persetujuan user2
    - 'menunggu_masuk' : user2 mengirim permintaan, menunggu disetujui user1
    - 'ditolak' : permintaan ditolak
    - 'tidak_terhubung' : belum ada hubungan
    """
    if id_user1 == id_user2:
        return "self"

    con = db.koneksi()
    try:
        # Cek permintaan yang dikirim oleh user1 ke user2
        k1 = con.execute(
            "SELECT id, status FROM koneksi WHERE id_pengirim = ? AND id_penerima = ?",
            (id_user1, id_user2)
        ).fetchone()
        if k1:
            if k1["status"] == "terhubung":
                return "terhubung"
            elif k1["status"] == "menunggu":
                return "menunggu_keluar"
            elif k1["status"] == "ditolak":
                return "ditolak"

        # Cek permintaan yang dikirim oleh user2 ke user1
        k2 = con.execute(
            "SELECT id, status FROM koneksi WHERE id_pengirim = ? AND id_penerima = ?",
            (id_user2, id_user1)
        ).fetchone()
        if k2:
            if k2["status"] == "terhubung":
                return "terhubung"
            elif k2["status"] == "menunggu":
                return "menunggu_masuk"
            elif k2["status"] == "ditolak":
                return "ditolak"

        return "tidak_terhubung"
    finally:
        con.close()


def kirim_koneksi(id_pengirim: int, id_penerima: int):
    """Mengirim permintaan koneksi dari id_pengirim ke id_penerima.
    
    Mengembalikan tuple (berhasil: bool, pesan: str).
    """
    if id_pengirim == id_penerima:
        return False, "Tidak dapat menghubungkan akun dengan diri sendiri."

    con = db.koneksi()
    try:
        # Cek apakah sudah pernah kirim dari pengirim ke penerima
        ada = con.execute(
            "SELECT id, status FROM koneksi WHERE id_pengirim = ? AND id_penerima = ?",
            (id_pengirim, id_penerima)
        ).fetchone()
        if ada:
            if ada["status"] == "terhubung":
                return False, "Anda sudah terhubung dengan mahasiswa ini."
            elif ada["status"] == "menunggu":
                return False, "Permintaan koneksi sudah dikirim sebelumnya dan sedang menunggu."
            elif ada["status"] == "ditolak":
                # Izinkan kirim ulang jika sebelumnya ditolak
                con.execute(
                    "UPDATE koneksi SET status = 'menunggu', dibuat_pada = CURRENT_TIMESTAMP WHERE id = ?",
                    (ada["id"],)
                )
                con.commit()
                cadangkan_semua()
                return True, "Permintaan koneksi berhasil dikirim kembali."

        # Cek jika ternyata penerima sebelumnya sudah mengirim permintaan ke pengirim
        sebaliknya = con.execute(
            "SELECT id, status FROM koneksi WHERE id_pengirim = ? AND id_penerima = ?",
            (id_penerima, id_pengirim)
        ).fetchone()
        if sebaliknya:
            if sebaliknya["status"] == "terhubung":
                return False, "Anda sudah terhubung dengan mahasiswa ini."
            elif sebaliknya["status"] == "menunggu":
                # Otomatis langsung jadikan terhubung karena kedua pihak saling ingin terhubung
                con.execute(
                    "UPDATE koneksi SET status = 'terhubung' WHERE id = ?",
                    (sebaliknya["id"],)
                )
                con.commit()
                cadangkan_semua()
                return True, "Kalian berdua saling ingin terhubung! Status kini resmi terhubung."

        # Insert baru
        con.execute(
            "INSERT INTO koneksi (id_pengirim, id_penerima, status) VALUES (?, ?, 'menunggu')",
            (id_pengirim, id_penerima)
        )
        con.commit()
        cadangkan_semua()
        return True, "Permintaan koneksi berhasil dikirim."
    except Exception as e:
        return False, f"Gagal mengirim permintaan koneksi: {e}"
    finally:
        con.close()


def balas_koneksi(id_koneksi: int, status: str, id_penerima: int = None):
    """Menyetujui ('terhubung') atau menolak ('ditolak') permintaan koneksi masuk.
    
    Mengembalikan tuple (berhasil: bool, pesan: str).
    """
    if status not in ("terhubung", "ditolak"):
        return False, "Status respon koneksi tidak valid."

    con = db.koneksi()
    try:
        k = con.execute("SELECT * FROM koneksi WHERE id = ?", (id_koneksi,)).fetchone()
        if not k:
            return False, "Permintaan koneksi tidak ditemukan."

        if id_penerima and k["id_penerima"] != id_penerima:
            return False, "Anda tidak berhak merespons permintaan koneksi ini."

        con.execute("UPDATE koneksi SET status = ? WHERE id = ?", (status, id_koneksi))
        con.commit()
        cadangkan_semua()
        aksi = "diterima" if status == "terhubung" else "ditolak"
        return True, f"Permintaan koneksi berhasil {aksi}."
    except Exception as e:
        return False, f"Kendala saat memproses koneksi: {e}"
    finally:
        con.close()


def daftar_koneksi(id_pengguna: int):
    """Mengambil daftar seluruh mahasiswa yang telah berstatus 'terhubung' dengan id_pengguna."""
    con = db.koneksi()
    try:
        sql = """
        SELECT 
            u.id, u.username, u.nama, u.kota, u.headline, u.skill, u.linkedin,
            k.id AS id_koneksi, k.dibuat_pada
        FROM koneksi k
        JOIN pengguna u ON u.id = (
            CASE WHEN k.id_pengirim = ? THEN k.id_penerima ELSE k.id_pengirim END
        )
        WHERE (k.id_pengirim = ? OR k.id_penerima = ?) AND k.status = 'terhubung'
        ORDER BY k.id DESC
        """
        rows = [dict(r) for r in con.execute(sql, (id_pengguna, id_pengguna, id_pengguna)).fetchall()]
        for r in rows:
            all_skills = _parse_skill(r.get("skill"))
            r["skill_list"] = all_skills
            r["tiga_skill"] = all_skills[:3]
        return rows
    finally:
        con.close()


def permintaan_masuk(id_pengguna: int):
    """Mengambil daftar permintaan koneksi masuk yang berstatus 'menunggu' untuk id_pengguna."""
    con = db.koneksi()
    try:
        sql = """
        SELECT 
            k.id AS id_koneksi, k.dibuat_pada,
            u.id AS id_pengirim, u.username, u.nama, u.kota, u.headline, u.skill, u.linkedin
        FROM koneksi k
        JOIN pengguna u ON u.id = k.id_pengirim
        WHERE k.id_penerima = ? AND k.status = 'menunggu'
        ORDER BY k.id DESC
        """
        rows = [dict(r) for r in con.execute(sql, (id_pengguna,)).fetchall()]
        for r in rows:
            all_skills = _parse_skill(r.get("skill"))
            r["skill_list"] = all_skills
            r["tiga_skill"] = all_skills[:3]
        return rows
    finally:
        con.close()


def buat_posting(id_pengguna: int, isi: str):
    """Membuat postingan baru di feed dengan batas maksimal 500 karakter.
    
    Mengembalikan tuple (berhasil: bool, pesan: str).
    """
    teks = (isi or "").strip()
    if not teks:
        return False, "Isi postingan tidak boleh kosong."
    if len(teks) > 500:
        return False, f"Postingan melebihi batas 500 karakter (saat ini {len(teks)} karakter)."

    con = db.koneksi()
    try:
        con.execute(
            "INSERT INTO posting (id_pengguna, isi) VALUES (?, ?)",
            (id_pengguna, teks)
        )
        con.commit()
        cadangkan_semua()
        return True, "Kabar berhasil dibagikan ke feed."
    except Exception as e:
        return False, f"Gagal membuat postingan: {e}"
    finally:
        con.close()


def feed(id_pengguna: int, limit: int = 50):
    """Mengambil feed postingan dari diri sendiri dan teman yang sudah terhubung (status 'terhubung').
    
    Urutan terbaru di atas.
    """
    con = db.koneksi()
    try:
        sql = """
        SELECT 
            p.id, p.id_pengguna, p.isi, p.dibuat_pada,
            u.nama, u.username, u.headline, u.kota,
            (SELECT COUNT(*) FROM suka s WHERE s.id_posting = p.id) AS jumlah_suka,
            (SELECT COUNT(*) FROM suka s WHERE s.id_posting = p.id AND s.id_pengguna = ?) AS disukai_saya
        FROM posting p
        JOIN pengguna u ON u.id = p.id_pengguna
        WHERE p.id_pengguna = ?
           OR p.id_pengguna IN (
               SELECT id_penerima FROM koneksi WHERE id_pengirim = ? AND status = 'terhubung'
               UNION
               SELECT id_pengirim FROM koneksi WHERE id_penerima = ? AND status = 'terhubung'
           )
        ORDER BY p.id DESC
        LIMIT ?
        """
        rows = [dict(r) for r in con.execute(sql, (id_pengguna, id_pengguna, id_pengguna, id_pengguna, limit)).fetchall()]
        return rows
    finally:
        con.close()


def toggle_suka(id_posting: int, id_pengguna: int):
    """Menyukai atau membatalkan suka pada postingan (F8).
    
    Mengembalikan tuple (disukai: bool, jumlah_suka: int).
    """
    con = db.koneksi()
    try:
        ada = con.execute(
            "SELECT 1 FROM suka WHERE id_posting = ? AND id_pengguna = ?",
            (id_posting, id_pengguna)
        ).fetchone()
        if ada:
            con.execute("DELETE FROM suka WHERE id_posting = ? AND id_pengguna = ?", (id_posting, id_pengguna))
            disukai = False
        else:
            con.execute("INSERT OR IGNORE INTO suka (id_posting, id_pengguna) VALUES (?, ?)", (id_posting, id_pengguna))
            disukai = True
        con.commit()
        cadangkan_semua()
        total = con.execute("SELECT COUNT(*) FROM suka WHERE id_posting = ?", (id_posting,)).fetchone()[0]
        return disukai, total
    finally:
        con.close()
