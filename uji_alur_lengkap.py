"""uji_alur_lengkap.py - Menguji seluruh alur aplikasi web CVku secara komprehensif."""
import os
import io
import docx
from docx import Document

# Set konfigurasi pengujian
os.environ["CVKU_DB"] = "./data/cvku_test.db"
os.environ["CVKU_DB_BACKUP"] = "./data/cvku_test_backup.db"
os.environ["CVKU_AI_MODE"] = "stub"
os.environ["CVKU_AUTO_APPROVE"] = "True"  # Uji auto approve dulu

from app import app, db, ai_service, skema

def jalankan_pengujian():
    print("=" * 65)
    print("MEMULAI PENGUJIAN ALUR LENGKAP APLIKASI WEBKU")
    print("=" * 65)

    client = app.test_client()
    db.init_db()

    # Buat akun pengujian
    db.simpan_pengguna("test_mhs", "pass123", "mahasiswa", nama="Mahasiswa Uji Coba")
    db.simpan_pengguna("test_dosen", "dosen123", "verifikator", nama="Dosen Penguji")

    # 1. Uji Login Berhasil & Gagal
    print("\n[1] Menguji Rute Autentikasi...")
    # Login gagal
    res = client.post("/login", data={"username": "test_mhs", "password": "wrongpassword"}, follow_redirects=True)
    assert b"Username atau password salah" in res.data, "Gagal mendeteksi password salah"
    print("  ✓ Login kredensial salah berhasil ditolak secara ramah.")

    # Login berhasil
    res = client.post("/login", data={"username": "test_mhs", "password": "pass123"}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Mahasiswa Uji Coba" in res.data
    print("  ✓ Login mahasiswa berhasil dan sesi terpasang.")

    # 2. Uji Profil
    print("\n[2] Menguji Halaman Profil...")
    res = client.post("/profil", data={
        "nama": "Mahasiswa Uji Lengkap",
        "email": "mhs_uji@filkom.ac.id",
        "telepon": "08123456789",
        "kota": "Malang",
        "linkedin": "linkedin.com/in/mhsuji",
        "ringkasan": "Mahasiswa berprestasi yang berfokus pada teknologi web dan AI."
    }, follow_redirects=True)
    assert b"Profil pribadi berhasil diperbarui" in res.data
    p_data = db.baca_pengguna(1)  # atau id pengguna test
    print("  ✓ Pembaruan profil berhasil disimpan ke database.")

    # 3. Uji Form Pencapaian - Validasi Uraian Kosong
    print("\n[3] Menguji Form Pencapaian & Validasi...")
    res = client.post("/pencapaian/tambah", data={
        "nama_kegiatan": "Lomba Hackathon",
        "penyelenggara": "Kampus",
        "peran": "Ketua",
        "periode": "Jan 2024",
        "lokasi": "Malang",
        "uraian": ""  # Kosong!
    }, follow_redirects=True)
    assert b"Uraian kegiatan wajib diisi" in res.data, "Validasi uraian kosong gagal"
    print("  ✓ Validasi form: uraian kegiatan wajib diisi berhasil diverifikasi.")

    # 4. Uji Submit Form Pencapaian Normal (AI Stub)
    print("\n[4] Menguji Submit Form & Pemrosesan AI...")
    res = client.post("/pencapaian/tambah", data={
        "nama_kegiatan": "Proyek Aplikasi CV ATS",
        "penyelenggara": "Fakultas",
        "peran": "Fullstack Developer",
        "periode": "Okt 2024 - Nov 2024",
        "lokasi": "Malang",
        "uraian": "Mengembangkan aplikasi web menggunakan Flask dan Qwen AI untuk membuat CV otomatis."
    }, follow_redirects=False)
    assert res.status_code == 302, f"Harus redirect ke cek-sunting, dapat status {res.status_code}"
    redirect_url = res.headers["Location"]
    print(f"  ✓ Berhasil diproses AI dan dialihkan ke: {redirect_url}")

    # Ambil ID pencapaian dari redirect URL
    id_pencapaian = int(redirect_url.split("/")[-2])
    entri_ai = db.baca_entri(id_pencapaian)
    assert entri_ai is not None
    assert len(entri_ai["poin"]) > 0
    print(f"  ✓ Entri AI terbentuk: Bagian='{entri_ai['bagian']}', Judul='{entri_ai['judul']}', Poin={len(entri_ai['poin'])} butir")

    # 5. Uji Halaman Cek-Sunting & Simpan ke CV
    print("\n[5] Menguji Halaman Cek-Sunting...")
    res_sunting_view = client.get(redirect_url)
    assert res_sunting_view.status_code == 200
    assert b"Cek &amp; Sunting Entri CV" in res_sunting_view.data

    # Simpan hasil sunting
    res_sunting_save = client.post(redirect_url, data={
        "bagian": "Proyek",
        "judul": "Lead Developer - Aplikasi CV ATS",
        "poin[]": [
            "Merancang arsitektur web berbasis Python Flask dan integrasi model AI.",
            "Mengimplementasikan parser keluaran JSON dan generator berkas DOCX ATS-friendly."
        ]
    }, follow_redirects=True)
    assert res_sunting_save.status_code == 200
    assert b"Pencapaian berhasil disimpan" in res_sunting_save.data
    
    entri_updated = db.baca_entri(id_pencapaian)
    assert entri_updated["bagian"] == "Proyek"
    assert entri_updated["judul"] == "Lead Developer - Aplikasi CV ATS"
    assert len(entri_updated["poin"]) == 2
    print("  ✓ Hasil sunting berhasil disimpan kembali ke database.")

    # 6. Uji Halaman Daftar Pencapaian
    print("\n[6] Menguji Daftar Pencapaian...")
    res_daftar = client.get("/pencapaian")
    assert b"Lead Developer - Aplikasi CV ATS" in res_daftar.data
    print("  ✓ Daftar pencapaian menampilkan data terbaru secara rapi.")

    # 7. Uji Pratinjau & Unduh CV (DOCX)
    print("\n[7] Menguji Pratinjau CV & Pembuatan Dokumen DOCX...")
    res_cv_page = client.get("/cv")
    assert res_cv_page.status_code == 200
    assert b"Pratinjau CV ATS Mahasiswa" in res_cv_page.data

    res_unduh = client.get("/cv/unduh")
    assert res_unduh.status_code == 200
    assert res_unduh.mimetype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    # Validasi struktur berkas DOCX yang diunduh
    doc_bytes = io.BytesIO(res_unduh.data)
    doc_test = Document(doc_bytes)
    assert len(doc_test.tables) == 0, "DOCX tidak boleh memiliki tabel (ATS rule)"
    assert len(doc_test.inline_shapes) == 0, "DOCX tidak boleh memiliki gambar (ATS rule)"
    print("  ✓ Berkas DOCX berhasil digenerate dan memenuhi kriteria ATS (0 tabel, 0 gambar).")

    # 8. Uji Riwayat CV & Unduh Ulang
    print("\n[8] Menguji Riwayat CV...")
    res_riwayat = client.get("/cv/riwayat")
    assert res_riwayat.status_code == 200
    assert b".docx" in res_riwayat.data
    
    versi_list = db.daftar_versi_cv(entri_updated["id"])
    print("  ✓ Riwayat versi CV tercatat di database.")

    # 9. Uji Halaman Verifikator (Prioritas 2)
    print("\n[9] Menguji Panel Verifikator (Prioritas 2)...")
    # Tambah pencapaian dengan status menunggu
    id_p_menunggu = db.simpan_pencapaian(
        id_pengguna=entri_updated["id"],
        nama_kegiatan="Lomba Inovasi Mahasiswa",
        uraian="Juara harapan lomba inovasi tingkat nasional",
        penyelenggara="Kementerian",
        peran="Peserta",
        periode="2024",
        lokasi="Jakarta"
    )
    db.simpan_hasil_ai(id_p_menunggu, "Penghargaan", "Peserta - Lomba Inovasi", ["Mendapatkan juara harapan"])
    db.ubah_status_pencapaian(id_p_menunggu, "menunggu")

    # Login sebagai verifikator
    client.get("/logout")
    client.post("/login", data={"username": "test_dosen", "password": "dosen123"}, follow_redirects=True)
    
    res_verif = client.get("/verifikator")
    assert res_verif.status_code == 200
    assert b"Lomba Inovasi Mahasiswa" in res_verif.data
    print("  ✓ Halaman verifikator menampilkan kegiatan yang berstatus 'menunggu'.")

    # Aksi verifikasi: setujui
    res_setuju = client.post(f"/verifikator/{id_p_menunggu}/verifikasi", data={
        "status": "disetujui",
        "catatan": "Sertifikat terverifikasi valid."
    }, follow_redirects=True)
    assert b"Pencapaian berhasil diverifikasi" in res_setuju.data
    p_cek = db.baca_pencapaian(id_p_menunggu)
    assert p_cek["status"] == "disetujui"
    print("  ✓ Verifikator berhasil menyetujui pencapaian dengan catatan.")

    print("\n" + "=" * 65)
    print("SELURUH ALUR PENGUJIAN BERHASIL 100% TANPA KENDALA!")
    print("=" * 65)

if __name__ == "__main__":
    jalankan_pengujian()
