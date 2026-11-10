---
title: "CVKu: Generator CV ATS-Friendly Berbasis Qwen dengan Fine-Tuning LoRA"
subtitle: "Dokumentasi Bagian Aplikasi (Tahap 1–3, 10, dan 12) — Reva"
---

# Tahap 1. Permasalahan dan Domain Aplikasi

**Domain:** pendidikan dan pengembangan karier mahasiswa.

**Permasalahan.** Mahasiswa sering kesulitan menulis CV yang rapi dan dapat dibaca oleh sistem ATS (*Applicant Tracking System*). Uraian kegiatan biasanya ditulis seadanya, tanpa kata kerja aktif dan tanpa fokus pada hasil. CV juga jarang diperbarui setiap ada pengalaman, lomba, atau sertifikat baru, sehingga saat dibutuhkan harus disusun ulang dari nol.

**Solusi.** CVKu adalah aplikasi yang membantu mahasiswa mencatat pencapaian lewat satu form sederhana. Model Qwen2.5 yang telah di-*fine-tuning* dengan LoRA menentukan bagian CV yang sesuai, menyusun judul entri yang baku, dan menulis ulang uraian menjadi poin CV yang ringkas dan berorientasi hasil.

**Tujuan.** Mempercepat penyusunan dan pembaruan CV tanpa pengguna perlu memahami aturan penulisan CV ATS.

**Pembagian peran AI dan kode.** AI hanya mengerjakan bagian bahasa (klasifikasi bagian, judul, poin CV). Penyimpanan data, penggabungan ke CV, dan pembuatan DOCX dikerjakan kode biasa. Data faktual (periode, penyelenggara, lokasi) diambil langsung dari form, bukan dari keluaran AI, agar tidak ada fakta yang diubah model.

# Tahap 2. Jenis Input

**Pilihan 1 — Text AI** dengan alur *Text → Qwen → Text*. Input berupa teks terstruktur dari form Tambah Pencapaian:

| Kolom form | Contoh |
|---|---|
| Nama kegiatan | FILKOM Mengajar |
| Penyelenggara | BEM FILKOM |
| Peran | Project Officer |
| Periode | Maret 2024 - Juni 2024 |
| Lokasi | Malang |
| Uraian singkat | jadi PO program mengajar anak SD, ngatur 20 panitia, bikin rundown |

Isi form disusun menjadi satu prompt terstruktur (fungsi `susun_prompt` pada `skema.py`). Prompt yang sama dipakai saat fine-tuning dan saat inference agar perilaku model konsisten.

# Tahap 3. Output yang Diharapkan

Keluaran model berupa JSON dengan tiga kunci:

```json
{
  "bagian": "Pengalaman Organisasi",
  "judul": "Project Officer - FILKOM Mengajar",
  "poin": [
    "Memimpin pelaksanaan program mengajar untuk siswa SD sebagai Project Officer",
    "Mengoordinasikan 20 panitia serta menyusun rundown dan komunikasi dengan pihak sekolah"
  ]
}
```

`bagian` dibatasi pada tujuh nilai: Pendidikan, Pengalaman Organisasi, Magang, Proyek, Sertifikasi, Penghargaan, dan Lainnya. Fungsi `parse_hasil` memeriksa JSON, mengganti bagian yang tidak dikenal menjadi "Lainnya", dan menjadikan keluaran tidak valid sebagai kegagalan yang terdeteksi.

Output akhir bagi pengguna adalah berkas **CV format DOCX ATS-friendly**: satu kolom, heading standar, tanpa tabel, gambar, atau kotak teks, dengan font Calibri.

# Tahap 10. Prototype Antarmuka (Gradio)

Antarmuka dibangun dengan Gradio (`app/app.py`) dan memiliki lima menu:

| Menu | Fungsi |
|---|---|
| Beranda | Ringkasan: status profil, jumlah entri CV per bagian, jumlah versi CV, dan mode AI yang aktif |
| Profil Saya | Mengisi dan menyimpan identitas serta kontak ke `profil.json` |
| Tambah Pencapaian | Mengisi form → **Proses dengan AI** → hasil ditampilkan untuk dicek dan disunting → **Konfirmasi & Simpan ke CV** |
| CV Saya & Unduh | Melihat daftar entri, menghapus entri, dan membuat serta mengunduh CV (DOCX) |
| Riwayat CV | Daftar semua versi CV yang pernah diunduh |

**Alur pengguna.** (1) Isi profil; (2) isi form pencapaian; (3) AI menentukan bagian, judul, dan poin; (4) pengguna memeriksa dan menyunting hasil; (5) setelah konfirmasi, entri masuk ke `cv_user.json`; (6) pengguna mengunduh DOCX dan versinya tersimpan di Riwayat CV.

**Alur teknis.** Form → prompt terstruktur → Qwen + LoRA (JSON) → kode *merge* (menambahkan periode, penyelenggara, dan lokasi dari form) → `cv_user.json` → template `python-docx` → berkas DOCX → Riwayat CV.

**Keputusan rancangan.**

- *Pengguna tetap mengendalikan:* hasil AI tidak langsung masuk CV, melainkan ditampilkan dulu agar dapat disunting.
- *Fakta dijaga:* periode, penyelenggara, dan lokasi selalu berasal dari form.
- *Tahan gangguan:* bila model gagal atau belum tersambung, aplikasi memakai *stub* sehingga antarmuka tetap dapat diuji.

**Pengujian aplikasi.** Skrip `test_skenario.py` menguji lima skenario: organisasi dengan angka, magang, penghargaan, sertifikasi tanpa peran, dan uraian tanpa angka. Skenario terakhir menguji bahwa model tidak mengarang angka. Setiap skenario diperiksa pada tiga hal: bagian CV sesuai harapan, judul dan poin terisi, serta tidak ada angka yang tidak ada di uraian.

*[Sisipkan screenshot: Beranda, Profil Saya, Tambah Pencapaian (sebelum dan sesudah AI), CV Saya & Unduh, Riwayat CV, dan hasil DOCX.]*

# Tahap 12. Kesimpulan

*(Bagian ini dilengkapi setelah evaluasi dari Sharen selesai. Angka di bawah wajib diisi dari tabel evaluasi, jangan diperkirakan.)*

**Apakah model setelah fine-tuning lebih baik daripada sebelum adaptasi?**

| Metrik (20 data uji) | Qwen mentah | Qwen + LoRA |
|---|---|---|
| Kualitas poin CV (skala 1–5) | … | … |
| JSON valid (%) | … | … |
| Akurasi bagian CV (%) | … | … |

Kesimpulan ditulis berdasarkan tabel di atas: metrik mana yang naik, seberapa besar, dan apakah model masih mengarang angka. Pastikan juga menyebut keterbatasan, yaitu jumlah data kecil (120 pasang) dan data dibuat sendiri oleh dua penyusun.

**Kesimpulan aplikasi.** Prototype CVKu menunjukkan bahwa alur Text → Qwen → Text dapat dikemas menjadi aplikasi yang bermanfaat: pengguna cukup menulis uraian apa adanya, dan hasil akhirnya adalah CV ATS-friendly yang dapat langsung diunduh. Pembagian tugas yang jelas antara AI (bahasa) dan kode biasa (data dan format) menjaga keandalan hasil.

**Saran pengembangan.** Penambahan data latih yang lebih beragam, dukungan bahasa Inggris, beberapa pilihan template CV, dan pencocokan CV dengan deskripsi lowongan.
