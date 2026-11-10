"""seed_demo.py - Mengisi data awal untuk pengujian aplikasi CVku.

Akun yang dibuat:
1. Mahasiswa: demo / demo123 (lengkap dengan profil dan 3 pencapaian contoh)
2. Verifikator: dosen / dosen123
"""
import os
import shutil

# Konfigurasi environment variable default
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

os.environ.setdefault("CVKU_DB", os.path.join(DATA_DIR, "cvku.db"))
os.environ.setdefault("CVKU_DB_BACKUP", os.path.join(DATA_DIR, "cvku_backup.db"))
os.environ.setdefault("CVKU_AI_MODE", "stub")

# Pulihkan cadangan jika ada di root namun belum ada di data/
root_backup = os.path.join(BASE_DIR, "cvku_backup.db")
target_backup = os.environ["CVKU_DB_BACKUP"]
if os.path.exists(root_backup) and not os.path.exists(target_backup):
    shutil.copy(root_backup, target_backup)

import db

# Pastikan path pada db sesuai konfigurasi
db.DB_PATH = os.environ["CVKU_DB"]
db.BACKUP_PATH = os.environ["CVKU_DB_BACKUP"]

def seed():
    print("Inisialisasi database...")
    db.init_db()

    con = db.koneksi()
    try:
        # 1. Akun Mahasiswa
        u_mhs = con.execute("SELECT id FROM pengguna WHERE username = 'demo'").fetchone()
        if not u_mhs:
            id_mhs = db.simpan_pengguna(
                username="demo",
                password="demo123",
                peran="mahasiswa",
                nama="Sharen Mahasiswa Demo",
                email="demo@student.filkom.ub.ac.id",
                telepon="081234567890",
                kota="Malang",
                linkedin="linkedin.com/in/demomahasiswa",
                ringkasan="Mahasiswa Sistem Informasi yang aktif dalam kegiatan organisasi teknologi dan memiliki minat besar pada rekayasa perangkat lunak serta penerapan kecerdasan buatan."
            )
            print(f"Akun mahasiswa 'demo' berhasil dibuat (ID: {id_mhs}).")
        else:
            id_mhs = u_mhs["id"]
            db.perbarui_profil(
                id_mhs,
                nama="Sharen Mahasiswa Demo",
                email="demo@student.filkom.ub.ac.id",
                telepon="081234567890",
                kota="Malang",
                linkedin="linkedin.com/in/demomahasiswa",
                ringkasan="Mahasiswa Sistem Informasi yang aktif dalam kegiatan organisasi teknologi dan memiliki minat besar pada rekayasa perangkat lunak serta penerapan kecerdasan buatan."
            )
            print(f"Akun mahasiswa 'demo' sudah ada (ID: {id_mhs}), profil diperbarui.")

        # 2. Akun Verifikator
        u_dosen = con.execute("SELECT id FROM pengguna WHERE username = 'dosen'").fetchone()
        if not u_dosen:
            id_dosen = db.simpan_pengguna(
                username="dosen",
                password="dosen123",
                peran="verifikator",
                nama="Dr. Dosen Verifikator, M.Kom.",
                email="dosen@filkom.ub.ac.id"
            )
            print(f"Akun verifikator 'dosen' berhasil dibuat (ID: {id_dosen}).")
        else:
            id_dosen = u_dosen["id"]
            print(f"Akun verifikator 'dosen' sudah ada (ID: {id_dosen}).")

        # 3. Pencapaian Contoh untuk Akun Mahasiswa
        contoh_pencapaian = [
            {
                "nama_kegiatan": "Seminar Nasional Teknologi Informasi",
                "penyelenggara": "Himpunan Mahasiswa Sistem Informasi",
                "peran": "Ketua Pelaksana",
                "periode": "Sep 2024 - Okt 2024",
                "lokasi": "Malang",
                "uraian": "Memimpin 35 panitia dalam menyelenggarakan seminar nasional teknologi yang dihadiri lebih dari 300 peserta mahasiswa dan praktisi industri.",
                "bagian": "Pengalaman Organisasi",
                "judul": "Ketua Pelaksana - Seminar Nasional Teknologi Informasi",
                "poin": [
                    "Memimpin tim kepanitiaan beranggotakan 35 mahasiswa dalam merancang dan menyelenggarakan seminar nasional teknologi.",
                    "Mengkoordinasikan divisi logistik, acara, dan sponsorship hingga berhasil mendatangkan 300+ peserta.",
                    "Mengelola anggaran kegiatan sebesar Rp 15.000.000 secara akuntabel dan transparan."
                ],
                "status": "disetujui"
            },
            {
                "nama_kegiatan": "Magang Frontend Engineer",
                "penyelenggara": "PT Solusi Digital Nusantara",
                "peran": "Frontend Intern",
                "periode": "Jul 2024 - Sep 2024",
                "lokasi": "Jakarta (Remote)",
                "uraian": "Mengembangkan antarmuka dashboard pengguna berbasis web dan mempercepat waktu muat komponen utama.",
                "bagian": "Magang",
                "judul": "Frontend Intern - PT Solusi Digital Nusantara",
                "poin": [
                    "Mengembangkan komponen dashboard analitik pengguna yang responsif menggunakan HTML, CSS, dan JavaScript.",
                    "Mengoptimalkan waktu render halaman sehingga meningkatkan kecepatan akses hingga 25%.",
                    "Berkolaborasi aktif dengan tim desain UI/UX dan tim backend dalam integrasi API."
                ],
                "status": "disetujui"
            },
            {
                "nama_kegiatan": "Hackathon Inovasi Solusi Digital 2024",
                "penyelenggara": "Fakultas Ilmu Komputer",
                "peran": "Ketua Tim & Developer",
                "periode": "Nov 2024",
                "lokasi": "Malang",
                "uraian": "Meraih Juara 1 dalam lomba hackathon 24 jam dengan merancang prototipe aplikasi cerdas pemilahan sampah.",
                "bagian": "Penghargaan",
                "judul": "Juara 1 - Hackathon Inovasi Solusi Digital 2024",
                "poin": [
                    "Meraih peringkat pertama dalam kompetisi hackathon pengembangan solusi inovasi digital kampus tingkat universitas.",
                    "Memimpin tim 3 orang dalam membangun MVP aplikasi pemilahan sampah cerdas dalam kurun waktu 24 jam.",
                    "Mempresentasikan demo langsung produk dan model implementasi di hadapan dewan juri."
                ],
                "status": "menunggu"  # Dibiarkan menunggu untuk pengujian verifikator
            }
        ]

        # Periksa apakah mahasiswa demo sudah memiliki pencapaian
        existing = con.execute("SELECT count(*) FROM pencapaian WHERE id_pengguna = ?", (id_mhs,)).fetchone()[0]
        if existing == 0:
            for p in contoh_pencapaian:
                id_p = db.simpan_pencapaian(
                    id_pengguna=id_mhs,
                    nama_kegiatan=p["nama_kegiatan"],
                    uraian=p["uraian"],
                    penyelenggara=p["penyelenggara"],
                    peran=p["peran"],
                    periode=p["periode"],
                    lokasi=p["lokasi"]
                )
                db.simpan_hasil_ai(id_p, p["bagian"], p["judul"], p["poin"])
                db.ubah_status_pencapaian(id_p, p["status"])
                print(f"Pencapaian '{p['nama_kegiatan']}' ditambahkan (Status: {p['status']}).")
        else:
            print(f"Pencapaian untuk akun 'demo' sudah ada ({existing} kegiatan).")
            # Pastikan pencapaian ke-3 kembali berstatus 'menunggu' untuk demo verifikator
            con.execute("UPDATE pencapaian SET status = 'menunggu' WHERE nama_kegiatan LIKE 'Hackathon%'")
            con.execute("DELETE FROM verifikasi WHERE id_pencapaian IN (SELECT id FROM pencapaian WHERE nama_kegiatan LIKE 'Hackathon%')")
            con.commit()
            print("Status pencapaian Hackathon direset ke 'menunggu' untuk pengujian verifikator.")

        # Cadangkan database
        db.cadangkan()
        print("Pencadangan database berhasil.")
        print("\nSeed data selesai!")
        print("Silakan masuk menggunakan:")
        print("1. Akun Mahasiswa   : demo / demo123")
        print("2. Akun Verifikator : dosen / dosen123")
    finally:
        con.close()

if __name__ == "__main__":
    seed()
