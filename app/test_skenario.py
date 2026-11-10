"""Uji 5 skenario alur lengkap (tugas Reva, Rab 14 Okt). Jalankan: python test_skenario.py
Otomatis memakai model Sharen jika model_qwen.py ada; jika tidak, memakai stub."""
import os, tempfile
os.environ["CVKU_DIR"] = tempfile.mkdtemp()
import app
from skema import BAGIAN
from docx import Document

SKENARIO = {
 "1. Organisasi + angka": dict(nama_kegiatan="Seminar IT", penyelenggara="HIMA", peran="Ketua Pelaksana", periode="Okt 2024 - Nov 2024", lokasi="Malang", uraian="mimpin 30 panitia, peserta 200 orang"),
 "2. Magang": dict(nama_kegiatan="Magang Web", penyelenggara="PT Maju", peran="Web Developer Intern", periode="Jul 2024 - Sep 2024", lokasi="Jakarta", uraian="bikin halaman admin pakai Laravel"),
 "3. Penghargaan": dict(nama_kegiatan="Hackathon Kampus", penyelenggara="HMIF", peran="Juara 1", periode="Okt 2023", lokasi="Malang", uraian="juara 1 hackathon 24 jam"),
 "4. Sertifikasi tanpa peran": dict(nama_kegiatan="Dasar Python", penyelenggara="Dicoding", peran="", periode="Jan 2024", lokasi="Daring", uraian="selesai semua modul"),
 "5. Uraian tanpa angka (uji halusinasi)": dict(nama_kegiatan="Baksos Desa", penyelenggara="UKM Peduli", peran="Sekretaris", periode="Feb 2023 - Mei 2023", lokasi="Batu", uraian="bikin notulen dan laporan kegiatan"),
}
HARAP = ["Pengalaman Organisasi","Magang","Penghargaan","Sertifikasi","Pengalaman Organisasi"]
gagal = 0
for (nama, form), harap in zip(SKENARIO.items(), HARAP):
    h = app.proses_pencapaian(form)
    ok = h["bagian"] == harap and h["judul"] and h["poin"]
    import re
    angka_baru = set(re.findall(r"\d+", " ".join(h["poin"]))) - set(re.findall(r"\d+", form["uraian"]))
    app.simpan_entri(app.merge_ke_cv(form, h))
    print(("LULUS " if ok and not angka_baru else "PERIKSA"), nama, "|", h["bagian"], "|", h["judul"],
          "| harap:", harap, "| angka mengarang:", angka_baru or "-")
    gagal += 0 if ok and not angka_baru else 1
p = os.path.join(app.D_RIWAYAT, "uji.docx")
app.buat_docx(app.muat_profil(), app.muat_cv(), p)
d = Document(p); print("DOCX dibuat | tabel:", len(d.tables), "| gambar:", len(d.inline_shapes))
print("Mode:", app.MODE, "| skenario perlu diperiksa:", gagal)
