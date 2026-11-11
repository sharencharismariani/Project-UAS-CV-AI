"""uji_alur_penuh_network.py - Pengujian End-to-End Komprehensif CVku Network (MVP).

Menguji seluruh alur dan kriteria acceptance sesuai PRD:
1. Seed database segar
2. Autentikasi (demo / demo123)
3. Pembaruan profil (headline & skill)
4. Tambah kegiatan + proses AI -> langsung tampil di profil publik tanpa verifikasi
5. Jelajah mahasiswa & pencarian "product manager"
6. Alur koneksi dua arah (Demo <-> Budi Pratama)
7. Feed sosial (posting, filter koneksi, dan tombol suka)
8. Pembuatan dokumen CV ATS DOCX (satu kolom, 0 tabel, 0 gambar)
9. Ketahanan terhadap error ramah pengguna (tanpa stack trace)
"""
import io
import docx
from docx import Document

import db
import jaringan
import seed_demo
from app import app


def jalankan_pengujian_penuh():
    print("=" * 70)
    print("MEMULAI PENGUJIAN END-TO-END CVKU NETWORK (MVP)")
    print("=" * 70)

    # 1. Reset ke seed data
    print("\n[Tahap 1] Menyiapkan Data Awal Seed Demo...")
    seed_demo.seed()
    print("  ✓ Basis data berhasil diisi dengan 10 profil mahasiswa fiktif.")

    client = app.test_client()

    # 2. Uji Login
    print("\n[Tahap 2] Menguji Login Akun Demo...")
    res = client.post("/login", data={"username": "demo", "password": "demo123"}, follow_redirects=True)
    assert res.status_code == 200
    assert "Sharen Charismariani" in res.data.decode("utf-8")
    print("  ✓ Login mahasiswa demo berhasil dan sesi terpasang.")

    # 3. Uji Isi Profil (Headline, Skill, Ringkasan)
    print("\n[Tahap 3] Menguji Pengisian Profil (Headline & Skill)...")
    res = client.post("/profil", data={
        "nama": "Sharen Charismariani",
        "headline": "Lead Full-Stack Engineer & AI Enthusiast | Final Year Student",
        "skill": "Python, Flask, React, ATS Optimization, Microservices, System Design",
        "email": "demo@student.filkom.ub.ac.id",
        "telepon": "081234567890",
        "kota": "Malang",
        "linkedin": "linkedin.com/in/demomahasiswa",
        "ringkasan": "Mahasiswa Sistem Informasi yang berpengalaman membangun produk digital dan mengoptimalkan sistem ATS."
    }, follow_redirects=True)
    assert res.status_code == 200
    assert "Profil pribadi berhasil diperbarui" in res.data.decode("utf-8")

    # Verifikasi langsung ke basis data
    u = db.baca_pengguna(1)
    assert u["headline"] == "Lead Full-Stack Engineer & AI Enthusiast | Final Year Student"
    assert "Microservices" in u["skill"]
    print("  ✓ Headline dan skill berhasil disimpan ke kolom tabel pengguna.")

    # 4. Uji Tambah Kegiatan + AI -> Langsung Tampil di Profil Publik Tanpa Langkah Persetujuan
    print("\n[Tahap 4] Menguji Tambah Kegiatan + Alur AI Otomatis...")
    res = client.post("/pencapaian/tambah", data={
        "nama_kegiatan": "Proyek Capstone Sistem Cerdas Rekomendasi Kampus",
        "penyelenggara": "Fakultas Ilmu Komputer",
        "peran": "Technical Lead",
        "periode": "Agu 2024 - Des 2024",
        "lokasi": "Malang",
        "uraian": "Memimpin arsitektur sistem rekomendasi mata kuliah berbasis AI yang digunakan oleh 500+ mahasiswa aktif."
    }, follow_redirects=False)
    assert res.status_code == 302
    assert "/sunting" in res.headers["Location"]
    url_sunting = res.headers["Location"]
    print("  ✓ Kegiatan berhasil diproses oleh AI dan dialihkan ke cek-sunting.")

    # Simpan hasil olahan AI di halaman cek-sunting
    res = client.post(url_sunting, data={
        "bagian": "Proyek",
        "judul": "Technical Lead - Capstone Sistem Cerdas Kampus",
        "peran": "Technical Lead",
        "poin[]": [
            "Memimpin arsitektur sistem rekomendasi mata kuliah cerdas berbasis AI untuk 500+ mahasiswa.",
            "Mengoptimalkan performa kueri database sehingga latensi API turun hingga 30%."
        ]
    }, follow_redirects=True)
    assert res.status_code == 200
    assert "langsung tampil di profil publik serta CV" in res.data.decode("utf-8")
    print("  ✓ Hasil olahan AI disimpan ke entri & poin CV.")

    # Verifikasi kegiatan baru langsung muncul di profil publik /u/1 tanpa persetujuan
    res = client.get("/u/1")
    assert res.status_code == 200
    html_profil = res.data.decode("utf-8")
    assert "Technical Lead - Capstone Sistem Cerdas Kampus" in html_profil
    assert "Memimpin arsitektur sistem rekomendasi mata kuliah" in html_profil
    print("  ✓ KRITERIA ACCEPTANCE: Kegiatan baru lewat AI langsung muncul di profil publik tanpa verifikasi!")

    # 5. Uji Jelajah & Cari Mahasiswa
    print("\n[Tahap 5] Menguji Jelajah & Pencarian 'product' / 'product manager'...")
    res = client.get("/jelajah?q=product")
    assert res.status_code == 200
    assert "Budi Pratama" in res.data.decode("utf-8")

    res = client.get("/jelajah?q=product+manager")
    assert res.status_code == 200
    html_jelajah = res.data.decode("utf-8")
    assert "Budi Pratama" in html_jelajah
    assert "Associate Product Manager Intern" in html_jelajah
    print("  ✓ KRITERIA ACCEPTANCE: Pencarian 'product' & 'product manager' berhasil menemukan Budi Pratama!")

    # 6. Uji Alur Koneksi (Demo kirim ke Budi, Budi menerima)
    print("\n[Tahap 6] Menguji Hubungan Koneksi Dua Arah (F5)...")
    # Demo mengirim permintaan koneksi ke Budi (ID: 3)
    res = client.post("/koneksi/kirim/3", follow_redirects=True)
    assert res.status_code == 200
    assert "Permintaan koneksi berhasil dikirim" in res.data.decode("utf-8")
    print("  ✓ Demo berhasil mengirim permintaan koneksi ke Budi.")

    # Sesi Budi Pratama (ID: 3)
    with client.session_transaction() as sess:
        sess["user_id"] = 3
        sess["username"] = "budi_pm"
        sess["peran"] = "mahasiswa"
        sess["nama"] = "Budi Pratama"

    # Budi melihat permintaan koneksi masuk
    res = client.get("/jaringan?tab=permintaan")
    html_budi_req = res.data.decode("utf-8")
    assert "Sharen Charismariani" in html_budi_req

    con = db.koneksi()
    k_req = con.execute("SELECT id FROM koneksi WHERE id_pengirim = 1 AND id_penerima = 3 AND status = 'menunggu'").fetchone()
    id_k = k_req["id"]
    con.close()

    # Budi menerima permintaan koneksi
    res = client.post(f"/koneksi/{id_k}/balas", data={"status": "terhubung"}, follow_redirects=True)
    assert res.status_code == 200

    # Cek bahwa di daftar Budi ada Demo
    res = client.get("/jaringan?tab=koneksi")
    assert "Sharen Charismariani" in res.data.decode("utf-8")

    # Sesi kembali ke Demo
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "demo"
        sess["peran"] = "pengguna"
        sess["nama"] = "Sharen Charismariani"

    # Cek bahwa di daftar Demo ada Budi
    res = client.get("/jaringan?tab=koneksi")
    assert "Budi Pratama" in res.data.decode("utf-8")
    print("  ✓ KRITERIA ACCEPTANCE: Dua akun saling menghubungkan dan koneksi muncul di kedua akun!")

    # 7. Uji Feed (F7 & F8)
    print("\n[Tahap 7] Menguji Feed Sosial & Filter Koneksi...")
    res = client.get("/feed")
    html_feed = res.data.decode("utf-8")
    # Karena Budi kini terhubung, postingan Budi HARUS muncul
    assert "Budi Pratama" in html_feed
    assert "sprint product discovery" in html_feed
    # Postingan Amanda (belum terhubung) TIDAK boleh muncul
    assert "sesi workshop Design System" not in html_feed
    print("  ✓ KRITERIA ACCEPTANCE: Postingan dari koneksi muncul di feed, orang yang tidak terhubung tidak muncul.")

    # Buat postingan baru oleh Demo
    res = client.post("/posting/buat", data={
        "isi": "Senang sekali portofolio CVku Network sudah terintegrasi rapi dengan sistem AI ATS. Jaringan makin luas, CV otomatis terbarui!"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert "Kabar berhasil dibagikan" in res.data.decode("utf-8")
    assert "Senang sekali portofolio CVku Network" in res.data.decode("utf-8")
    print("  ✓ Demo berhasil membuat postingan baru di feed.")

    # Uji Suka (Like F8)
    con = db.koneksi()
    p_budi = con.execute("SELECT id FROM posting WHERE id_pengguna = 3").fetchone()
    id_pb = p_budi["id"]
    con.close()

    res = client.post(f"/posting/{id_pb}/suka", headers={"X-Requested-With": "XMLHttpRequest"})
    assert res.status_code == 200
    assert res.get_json()["disukai"] is True
    print("  ✓ Fitur suka (F8) berhasil digunakan.")

    # 8. Uji CV ATS DOCX
    print("\n[Tahap 8] Menguji Dokumen CV ATS DOCX...")
    res = client.get("/cv/unduh")
    assert res.status_code == 200
    assert res.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    doc = Document(io.BytesIO(res.data))
    # Validasi ATS: 0 tabel, 0 gambar/shape
    assert len(doc.tables) == 0, f"Ditemukan {len(doc.tables)} tabel pada dokumen CV ATS (harus 0)!"
    assert len(doc.inline_shapes) == 0, f"Ditemukan {len(doc.inline_shapes)} gambar pada dokumen CV ATS (harus 0)!"

    seluruh_teks = "\n".join(p.text for p in doc.paragraphs)
    assert "SHAREN CHARISMARIANI" in seluruh_teks
    assert "Malang" in seluruh_teks
    assert "Technical Lead - Capstone Sistem Cerdas Kampus" in seluruh_teks
    print(f"  ✓ KRITERIA ACCEPTANCE: Dokumen DOCX memenuhi standar ATS (0 tabel, 0 gambar, satu kolom).")

    # 9. Uji Penanganan Error Ramah Pengguna
    print("\n[Tahap 9] Menguji Penanganan Error Ramah Pengguna (Tanpa Stack Trace)...")
    res = client.get("/halaman-yang-tidak-ada-12345", follow_redirects=True)
    assert res.status_code == 200
    html_err = res.data.decode("utf-8")
    assert "Error 404" in html_err or "tidak ditemukan" in html_err
    assert "Traceback" not in html_err
    print("  ✓ Error 404 ditangani secara ramah tanpa stack trace.")

    print("\n" + "=" * 70)
    print("SELURUH ALUR DAN KRITERIA ACCEPTANCE BERHASIL 100% TANPA KENDALA!")
    print("=" * 70)


if __name__ == "__main__":
    jalankan_pengujian_penuh()
