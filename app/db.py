"""db.py - lapisan database SI (SQLite)."""
import os, shutil, sqlite3, hashlib, secrets

DB_PATH = os.environ.get("CVKU_DB", "/content/cvku.db")
BACKUP_PATH = os.environ.get("CVKU_DB_BACKUP", "/content/drive/MyDrive/UTS_AI_CV/app/cvku_backup.db")

SKEMA = """
CREATE TABLE IF NOT EXISTS pengguna (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
  peran TEXT NOT NULL CHECK (peran IN ('mahasiswa','verifikator')),
  nama TEXT, email TEXT, telepon TEXT, kota TEXT, linkedin TEXT, ringkasan TEXT);
CREATE TABLE IF NOT EXISTS bagian_cv (
  id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS pencapaian (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  id_pengguna INTEGER NOT NULL REFERENCES pengguna(id),
  nama_kegiatan TEXT NOT NULL, penyelenggara TEXT, peran TEXT, periode TEXT, lokasi TEXT,
  uraian TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'menunggu' CHECK (status IN ('menunggu','disetujui','ditolak')),
  dibuat_pada TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS entri_cv (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  id_pencapaian INTEGER UNIQUE NOT NULL REFERENCES pencapaian(id) ON DELETE CASCADE,
  id_bagian INTEGER NOT NULL REFERENCES bagian_cv(id), judul TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS poin_cv (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  id_entri INTEGER NOT NULL REFERENCES entri_cv(id) ON DELETE CASCADE,
  urutan INTEGER NOT NULL, teks TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS versi_cv (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  id_pengguna INTEGER NOT NULL REFERENCES pengguna(id),
  nama_file TEXT NOT NULL, dibuat_pada TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS verifikasi (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  id_pencapaian INTEGER NOT NULL REFERENCES pencapaian(id) ON DELETE CASCADE,
  id_verifikator INTEGER NOT NULL REFERENCES pengguna(id),
  status TEXT NOT NULL, catatan TEXT, tanggal TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS log_ai (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  id_pengguna INTEGER REFERENCES pengguna(id),
  masukan TEXT, keluaran TEXT, waktu_respons_ms INTEGER, versi_model TEXT,
  dibuat_pada TEXT DEFAULT CURRENT_TIMESTAMP);
"""


def koneksi():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    """Buat tabel dan isi bagian_cv. Jika file belum ada tapi cadangan ada, pulihkan dari cadangan."""
    if not os.path.exists(DB_PATH) and os.path.exists(BACKUP_PATH):
        shutil.copy(BACKUP_PATH, DB_PATH)
    from skema import BAGIAN
    con = koneksi()
    con.executescript(SKEMA)
    for nama in BAGIAN:
        con.execute("INSERT OR IGNORE INTO bagian_cv (nama) VALUES (?)", (nama,))
    con.commit()
    con.close()


def cadangkan():
    shutil.copy(DB_PATH, BACKUP_PATH)

import hashlib, secrets


# ---------- util ----------
def _hash(password, salt=None):
    salt = salt or secrets.token_hex(8)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${h}"

def _cocok(password, tersimpan):
    salt = tersimpan.split("$")[0]
    return secrets.compare_digest(_hash(password, salt), tersimpan)

def _satu(sql, args=()):
    con = koneksi()
    try:
        r = con.execute(sql, args).fetchone()
        return dict(r) if r else None
    finally:
        con.close()

def _semua(sql, args=()):
    con = koneksi()
    try:
        return [dict(r) for r in con.execute(sql, args).fetchall()]
    finally:
        con.close()

def _tulis(sql, args=()):
    con = koneksi()
    try:
        cur = con.execute(sql, args)
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


# ---------- pengguna ----------
def simpan_pengguna(username, password, peran, nama=None, email=None,
                    telepon=None, kota=None, linkedin=None, ringkasan=None):
    return _tulis(
        "INSERT INTO pengguna (username, password_hash, peran, nama, email, telepon, kota, linkedin, ringkasan) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (username, _hash(password), peran, nama, email, telepon, kota, linkedin, ringkasan))

def cek_login(username, password):
    """Return dict pengguna (tanpa password_hash) jika benar, None jika salah."""
    u = _satu("SELECT * FROM pengguna WHERE username=?", (username,))
    if u and _cocok(password, u["password_hash"]):
        u.pop("password_hash")
        return u
    return None

def baca_pengguna(id_pengguna):
    u = _satu("SELECT * FROM pengguna WHERE id=?", (id_pengguna,))
    if u:
        u.pop("password_hash")
    return u

def perbarui_profil(id_pengguna, **data):
    boleh = {"nama", "email", "telepon", "kota", "linkedin", "ringkasan"}
    data = {k: v for k, v in data.items() if k in boleh}
    if not data:
        return
    kolom = ", ".join(f"{k}=?" for k in data)
    _tulis(f"UPDATE pengguna SET {kolom} WHERE id=?", (*data.values(), id_pengguna))


# ---------- pencapaian ----------
def simpan_pencapaian(id_pengguna, nama_kegiatan, uraian, penyelenggara=None,
                      peran=None, periode=None, lokasi=None):
    return _tulis(
        "INSERT INTO pencapaian (id_pengguna, nama_kegiatan, penyelenggara, peran, periode, lokasi, uraian) "
        "VALUES (?,?,?,?,?,?,?)",
        (id_pengguna, nama_kegiatan, penyelenggara, peran, periode, lokasi, uraian))

def baca_pencapaian(id_pencapaian):
    return _satu("SELECT * FROM pencapaian WHERE id=?", (id_pencapaian,))

def daftar_pencapaian(id_pengguna, status=None):
    sql = ("SELECT p.*, e.judul, b.nama AS bagian FROM pencapaian p "
           "LEFT JOIN entri_cv e ON e.id_pencapaian=p.id "
           "LEFT JOIN bagian_cv b ON b.id=e.id_bagian WHERE p.id_pengguna=?")
    args = [id_pengguna]
    if status:
        sql += " AND p.status=?"
        args.append(status)
    return _semua(sql + " ORDER BY p.id DESC", args)

def ubah_status_pencapaian(id_pencapaian, status):
    _tulis("UPDATE pencapaian SET status=? WHERE id=?", (status, id_pencapaian))

def hapus_pencapaian(id_pencapaian):
    _tulis("DELETE FROM pencapaian WHERE id=?", (id_pencapaian,))  # entri dan poin ikut terhapus


# ---------- entri dan poin (hasil AI) ----------
def simpan_hasil_ai(id_pencapaian, nama_bagian, judul, daftar_poin):
    """Simpan (atau timpa) entri CV + poin untuk satu pencapaian. Return id_entri."""
    con = koneksi()
    try:
        b = con.execute("SELECT id FROM bagian_cv WHERE nama=?", (nama_bagian,)).fetchone()
        id_bagian = b["id"] if b else con.execute("SELECT id FROM bagian_cv WHERE nama='Lainnya'").fetchone()["id"]
        con.execute("DELETE FROM entri_cv WHERE id_pencapaian=?", (id_pencapaian,))
        id_entri = con.execute(
            "INSERT INTO entri_cv (id_pencapaian, id_bagian, judul) VALUES (?,?,?)",
            (id_pencapaian, id_bagian, judul)).lastrowid
        for i, teks in enumerate(daftar_poin, start=1):
            con.execute("INSERT INTO poin_cv (id_entri, urutan, teks) VALUES (?,?,?)", (id_entri, i, teks))
        con.commit()
        return id_entri
    finally:
        con.close()

def baca_entri(id_pencapaian):
    e = _satu("SELECT e.*, b.nama AS bagian FROM entri_cv e JOIN bagian_cv b ON b.id=e.id_bagian "
              "WHERE e.id_pencapaian=?", (id_pencapaian,))
    if e:
        e["poin"] = [r["teks"] for r in _semua(
            "SELECT teks FROM poin_cv WHERE id_entri=? ORDER BY urutan", (e["id"],))]
    return e

def baca_cv_pengguna(id_pengguna, hanya_disetujui=True):
    """Semua entri CV pengguna, dikelompokkan per bagian (urutan sesuai bagian_cv). Untuk pembuat DOCX."""
    sql = ("SELECT e.id, e.judul, b.nama AS bagian, p.periode, p.penyelenggara, p.peran, p.lokasi "
           "FROM entri_cv e JOIN pencapaian p ON p.id=e.id_pencapaian "
           "JOIN bagian_cv b ON b.id=e.id_bagian WHERE p.id_pengguna=?")
    if hanya_disetujui:
        sql += " AND p.status='disetujui'"
    hasil = {}
    for e in _semua(sql + " ORDER BY b.id, p.id", (id_pengguna,)):
        e["poin"] = [r["teks"] for r in _semua(
            "SELECT teks FROM poin_cv WHERE id_entri=? ORDER BY urutan", (e["id"],))]
        hasil.setdefault(e["bagian"], []).append(e)
    return hasil


# ---------- versi CV ----------
def simpan_versi_cv(id_pengguna, nama_file):
    return _tulis("INSERT INTO versi_cv (id_pengguna, nama_file) VALUES (?,?)", (id_pengguna, nama_file))

def daftar_versi_cv(id_pengguna):
    return _semua("SELECT * FROM versi_cv WHERE id_pengguna=? ORDER BY id DESC", (id_pengguna,))


# ---------- verifikasi dan log AI ----------
def simpan_verifikasi(id_pencapaian, id_verifikator, status, catatan=None):
    id_v = _tulis("INSERT INTO verifikasi (id_pencapaian, id_verifikator, status, catatan) VALUES (?,?,?,?)",
                  (id_pencapaian, id_verifikator, status, catatan))
    ubah_status_pencapaian(id_pencapaian, status)
    return id_v

def catat_log_ai(id_pengguna, masukan, keluaran, waktu_respons_ms=None, versi_model=None):
    return _tulis("INSERT INTO log_ai (id_pengguna, masukan, keluaran, waktu_respons_ms, versi_model) "
                  "VALUES (?,?,?,?,?)", (id_pengguna, masukan, keluaran, waktu_respons_ms, versi_model))
