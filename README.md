# CVku — Aplikasi Penyusun CV ATS-Friendly Mahasiswa Berbasis AI

Aplikasi web **CVku** dibangun menggunakan **Python Flask** (template Jinja2 dan CSS khusus yang bersih, modern, dan responsif tanpa framework JavaScript berat). Aplikasi ini membantu mahasiswa menyusun Curriculum Vitae (CV) berstandar ATS (*Applicant Tracking System*) secara cepat dan terarah menggunakan bantuan kecerdasan buatan.

Seluruh antarmuka dirancang dalam **Bahasa Indonesia**, dengan validasi formulir yang ketat dan pesan galat yang ramah pengguna.

---

## Daftar Isi
1. [Fitur Utama](#fitur-utama)
2. [Struktur Folder Proyek](#struktur-folder-proyek)
3. [Prasyarat & Instalasi](#prasyarat--instalasi)
4. [Konfigurasi Environment Variable](#konfigurasi-environment-variable)
5. [Inisialisasi & Data Demo](#inisialisasi--data-demo)
6. [Menjalankan Aplikasi](#menjalankan-aplikasi)
7. [Akun Demo Pengujian](#akun-demo-pengujian)
8. [Panduan Pengujian Alur Lengkap](#panduan-pengujian-alur-lengkap)
9. [Uji Otomatis](#uji-otomatis)

---

## Fitur Utama

### Prioritas 1 (Wajib & Selesai)
1. **Autentikasi & Pembatasan Peran (Session Flask)**
   - Registrasi dan login aman menggunakan hashing PBKDF2.
   - Dua peran: **Mahasiswa** (penyusun CV) dan **Verifikator** (dosen/kurator kampus).
   - Akses halaman dibatasi ketat berdasarkan peran dengan pesan peringatan ramah jika tidak berhak.

2. **Profil Identitas CV**
   - Melihat dan menyunting: Nama Lengkap, Email, Nomor Telepon, Kota Domisili, Tautan LinkedIn, dan Ringkasan Profil (*Executive Summary*).

3. **Form Tambah Pencapaian & AI Fallback**
   - Kolom isian: Nama Kegiatan, Penyelenggara, Peran, Periode, Lokasi, dan Uraian Singkat.
   - Validasi ketat: uraian kegiatan wajib diisi.
   - Terintegrasi dengan modul AI: jika model AI mengalami *timeout* atau gagal jaringan, aplikasi otomatis melakukan **fallback** ke mode *stub* dengan peringatan *"AI sedang tidak tersedia, memakai hasil contoh"* tanpa membuat web mogok (*crash*).
   - Aktivitas dicatat pada `log_ai`.

4. **Halaman Cek-Sunting Hasil AI**
   - Menampilkan data asli kegiatan sebagai referensi faktual.
   - Dropdown 7 Bagian CV baku: *Pendidikan, Pengalaman Organisasi, Magang, Proyek, Sertifikasi, Penghargaan, Lainnya*.
   - Judul entri yang dapat disunting.
   - Editor poin pencapaian dinamis: dapat mengedit teks, menambah butir baru, atau menghapus butir poin.
   - Tombol **Simpan ke CV** memperbarui entri CV.

5. **Daftar Pencapaian**
   - Tabel responsif berisi nama kegiatan, bagian CV, periode/lokasi, dan badge status (*disetujui, menunggu, ditolak*).
   - Tombol **Sunting** dan **Hapus** (dilengkapi konfirmasi keamanan).

6. **Pratinjau CV & Unduh Berkas DOCX ATS-Friendly**
   - Pratinjau simulasi kertas CV di peramban.
   - Pembuat dokumen Word (`.docx`) menggunakan `python-docx` dengan kriteria ketat ATS:
     - **Satu kolom**.
     - **TANPA tabel** dan **TANPA gambar/bentuk**.
     - Font standar *Calibri* (11pt teks normal, 18pt nama bold, 12pt heading).
     - Urutan: Nama & Kontak di bagian atas, Ringkasan Profil, lalu tiap Bagian dengan butir *bullet points*.
   - Berkas fisik otomatis disimpan di folder `riwayat_cv/` dengan penamaan berbasis waktu (*timestamp*), serta dicatat ke basis data.

7. **Riwayat Versi CV**
   - Menampilkan seluruh versi berkas CV yang pernah diunduh beserta waktu pembuatan.
   - Tombol **Unduh Ulang** untuk mengunduh kembali dokumen yang tersimpan di server.

### Prioritas 2 (Fitur Verifikator Kampus)
- **Panel Verifikator (`/verifikator`)**:
  - Menampilkan antrean kegiatan mahasiswa yang berstatus `menunggu`.
  - Verifikator dapat membaca detail kegiatan, uraian asli, dan hasil rumusan AI.
  - Verifikator dapat memberikan keputusan **Setuju** atau **Tolak** beserta catatan opsional.
  - Riwayat verifikasi yang telah disahkan tersimpan rapi.

---

## Struktur Folder Proyek

```
UTS_AI_CV/
├── app.py                  # Aplikasi utama Flask (routing, auth, kontroler, DOCX)
├── db.py                   # Modul database SQLite (asli, tidak diubah)
├── ai_service.py           # Jembatan AI (stub/local/remote) (asli, tidak diubah)
├── skema.py                # Skema 7 bagian CV dan prompt (asli, tidak diubah)
├── schema.sql              # Skema SQL pendukung
├── seed_demo.py            # Skrip pengisi data awal (demo akun & 3 pencapaian)
├── uji_alur_lengkap.py     # Skrip pengujian otomatis menyeluruh
├── requirements.txt        # Daftar pustaka (Flask, python-docx, requests)
├── README.md               # Dokumentasi cara menjalankan aplikasi
├── data/                   # Folder database lokal (dibuat otomatis)
│   ├── cvku.db             # Basis data SQLite aktif
│   └── cvku_backup.db      # Cadangan basis data SQLite
├── riwayat_cv/             # Folder penyimpanan berkas DOCX yang diunduh
├── static/
│   └── css/
│       └── style.css       # Gaya CSS khusus, modern, dan responsif
└── templates/              # Template HTML Jinja2
    ├── base.html           # Layout dasar & navigasi responsif
    ├── beranda.html        # Halaman muka / dashboard pengguna
    ├── login.html          # Form masuk & tombol isi cepat demo
    ├── register.html       # Form pendaftaran akun baru
    ├── profil.html         # Form pengelolaan profil & identitas
    ├── pencapaian_tambah.html   # Form tambah kegiatan & pemicu AI
    ├── pencapaian_sunting.html  # Cek & sunting hasil AI (dropdown 7 bagian & poin)
    ├── pencapaian_daftar.html   # Tabel kurasi pencapaian mahasiswa
    ├── cv_preview.html     # Pratinjau CV ATS & tombol unduh DOCX
    ├── cv_riwayat.html     # Daftar riwayat versi CV untuk unduh ulang
    └── verifikator.html    # Panel kurasi kegiatan oleh dosen/verifikator
```

---

## Prasyarat & Instalasi

### 1. Kebutuhan Sistem
- Python 3.9 atau lebih baru.
- Peramban web modern (Chrome, Firefox, Safari, Edge).

### 2. Pemasangan Pustaka Dependencies
Buat *virtual environment* dan pasang pustaka yang tercantum pada `requirements.txt`:

```bash
# Buat virtual environment
python3 -m venv venv

# Aktifkan virtual environment
# Pada macOS / Linux:
source venv/bin/activate
# Pada Windows:
# venv\Scripts\activate

# Pasang dependensi
pip install -r requirements.txt
```

Isi `requirements.txt`:
```
flask>=3.0.0
python-docx>=1.0.0
requests>=2.31.0
```

---

## Konfigurasi Environment Variable

Aplikasi mendukung konfigurasi fleksibel melalui variabel lingkungan dengan nilai bawaan (*default*) berikut:

| Variabel | Nilai Default | Penjelasan |
|---|---|---|
| `CVKU_DB` | `./data/cvku.db` | Lokasi berkas basis data SQLite aktif |
| `CVKU_DB_BACKUP` | `./data/cvku_backup.db` | Lokasi berkas cadangan basis data |
| `CVKU_AI_MODE` | `stub` | Mode AI: `stub` (bawaan lokal), `local`, atau `remote` |
| `CVKU_AUTO_APPROVE` | `False` | Jika `False`, pencapaian baru berstatus `menunggu` untuk diverifikasi dosen. Jika `True`, pencapaian langsung disetujui |
| `PORT` | `5001` | Port web server Flask (menghindari konflik AirPlay macOS pada port 5000) |
| `SECRET_KEY` | `cvku-secret-key-2026-uts-ai-cv` | Kunci sesi Flask |

Folder `data/` dan `riwayat_cv/` akan otomatis dibuat oleh aplikasi jika belum ada. Saat pertama kali berjalan, fungsi `db.init_db()` akan dipanggil secara otomatis.

---

## Inisialisasi & Data Demo

Jalankan skrip `seed_demo.py` untuk menginisialisasi basis data dan membuat akun uji coba beserta contoh pencapaian:

```bash
python seed_demo.py
```

Skrip ini akan membuat:
- 1 Akun Mahasiswa (`demo` / `demo123`) lengkap dengan data profil.
- 1 Akun Verifikator (`dosen` / `dosen123`).
- 3 Pencapaian contoh:
  1. *Seminar Nasional Teknologi Informasi* (Pengalaman Organisasi, status: disetujui).
  2. *Magang Frontend Engineer* (Magang, status: disetujui).
  3. *Hackathon Inovasi Solusi Digital 2024* (Penghargaan, status: menunggu verifikasi).

---

## Menjalankan Aplikasi

Jalankan perintah berikut pada terminal:

```bash
python app.py
```

Buka peramban dan akses alamat:
```
http://127.0.0.1:5001
```

*(Catatan: Anda juga dapat menentukan port secara bebas, misalnya `PORT=8080 python app.py`)*.

---

## Akun Demo Pengujian

Pada halaman login, tersedia tombol pintas (**Klik Cepat Akun Uji Coba**) untuk mengisi kredensial dengan satu klik:

| Peran | Username | Password | Keterangan |
|---|---|---|---|
| **Mahasiswa** | `demo` | `demo123` | Akses penuh profil, kegiatan, sunting AI, dan unduh CV |
| **Verifikator** | `dosen` | `dosen123` | Akses panel kurasi & validasi kegiatan mahasiswa |

---

## Panduan Pengujian Alur Lengkap

### Alur 1: Mahasiswa — Login, Tambah Pencapaian, Cek-Sunting, & Unduh CV
1. Buka `http://127.0.0.1:5001/login`.
2. Klik tombol **Mahasiswa (demo)** atau ketik `demo` / `demo123`, lalu klik **Masuk**.
3. Buka menu **Profil Saya**: periksa identitas (Nama, Email, Telepon, Domisili, LinkedIn, dan Ringkasan Profil). Ubah salah satu data lalu klik **Simpan Perubahan Profil**.
4. Buka menu **+ Tambah Kegiatan**:
   - Isi form:
     - Nama Kegiatan: `Proyek Sistem AI CVku`
     - Peran: `Backend & AI Developer`
     - Penyelenggara: `Fakultas Ilmu Komputer`
     - Periode: `Okt 2024 - Nov 2024`
     - Lokasi: `Malang`
     - Uraian: `Membangun arsitektur backend Python Flask serta mengintegrasikan model AI dan generator dokumen DOCX ATS.`
   - Klik **Proses dengan AI & Lanjut**.
5. Sistem akan otomatis memanggil `ai_service.proses_pencapaian` dan mengarahkan ke halaman **Cek & Sunting Entri CV**:
   - Periksa dropdown **Bagian CV** (7 pilihan: Pendidikan, Pengalaman Organisasi, Magang, Proyek, Sertifikasi, Penghargaan, Lainnya).
   - Sunting judul bila diperlukan.
   - Tambahkan butir poin baru dengan tombol **+ Tambah Poin** atau hapus poin yang tidak relevan dengan tombol **✕**.
   - Klik **Simpan Entri ke CV**.
6. Masuk ke halaman **CV Saya**:
   - Pratinjau dokumen CV akan menampilkan identitas dan kegiatan yang disetujui.
   - Klik tombol **Unduh CV (.docx)**. Berkas Word akan terunduh ke komputer Anda.
   - Berkas fisik tersimpan pada folder `riwayat_cv/` dan tercatat pada menu **Riwayat CV**.
7. Buka berkas `.docx` yang diunduh menggunakan Microsoft Word / LibreOffice. Periksa bahwa dokumen berformat satu kolom rapi, tanpa tabel, dan tanpa gambar sesuai standar ATS.

### Alur 2: Verifikator — Kurasi Pencapaian Mahasiswa
1. Klik tombol **Keluar** di pojok kanan atas.
2. Masuk sebagai verifikator menggunakan akun `dosen` / `dosen123`.
3. Anda akan diarahkan ke dasbor verifikator. Klik **Verifikasi Pencapaian** pada navigasi atas.
4. Anda akan melihat daftar kegiatan mahasiswa yang berstatus `menunggu` (misalnya *Hackathon Inovasi Solusi Digital 2024*).
5. Masukkan catatan pada kolom *Catatan Verifikator* (misalnya: `"Sertifikat juara telah divalidasi bagian kemahasiswaan"`).
6. Klik **✓ Setujui Masuk ke CV** atau **✗ Tolak Pencapaian**.
7. Status pencapaian berhasil diperbarui dan riwayat verifikasi akan tercatat pada tabel di bawahnya.
8. Masuk kembali sebagai mahasiswa `demo`: pencapaian yang telah disetujui akan langsung muncul pada pratinjau dan dokumen CV yang diunduh.

---

## Uji Otomatis

Untuk memastikan seluruh rute, proteksi hak akses, generator DOCX, dan logika fallback berjalan tanpa cacat, jalankan uji otomatis menyeluruh:

```bash
python uji_alur_lengkap.py
```

Skrip ini akan memverifikasi:
- Rute login dan penolakan kredensial salah secara ramah.
- Penyimpanan dan pembaruan profil pengguna.
- Validasi form (uraian wajib diisi, tidak boleh kosong).
- Integrasi proses AI dan pencatatan log.
- Fallback otomatis saat AI mengalami kendala tanpa *crash*.
- Penyuntingan dropdown bagian CV dan poin-poin *bullet*.
- Kepatuhan ATS pada dokumen DOCX (memverifikasi jumlah tabel = 0 dan jumlah gambar = 0).
- Pencatatan riwayat versi berkas CV.
- Mekanisme verifikasi dosen/verifikator.
