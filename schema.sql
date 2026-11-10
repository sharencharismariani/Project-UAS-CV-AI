PRAGMA foreign_keys = ON;

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

-- Data awal bagian CV
INSERT OR IGNORE INTO bagian_cv (nama) VALUES ('Pendidikan');
INSERT OR IGNORE INTO bagian_cv (nama) VALUES ('Pengalaman Organisasi');
INSERT OR IGNORE INTO bagian_cv (nama) VALUES ('Magang');
INSERT OR IGNORE INTO bagian_cv (nama) VALUES ('Proyek');
INSERT OR IGNORE INTO bagian_cv (nama) VALUES ('Sertifikasi');
INSERT OR IGNORE INTO bagian_cv (nama) VALUES ('Penghargaan');
INSERT OR IGNORE INTO bagian_cv (nama) VALUES ('Lainnya');
