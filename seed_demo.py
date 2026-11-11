"""seed_demo.py - Mengisi data awal komprehensif untuk pengujian dan demo CVku Network.

Menciptakan:
1. Akun utama demo: demo / demo123 (lengkap headline, skill, ringkasan, dan 3 kegiatan beragam)
2. 9 Akun mahasiswa fiktif dengan headline, skill (tag), dan kegiatan beragam (organisasi, magang, proyek, lomba)
3. Koneksi awal (terhubung dengan demo, dan permintaan masuk)
4. 5 Postingan awal di feed untuk membuktikan filter koneksi
"""
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

os.environ.setdefault("CVKU_DB", os.path.join(DATA_DIR, "cvku.db"))
os.environ.setdefault("CVKU_DB_BACKUP", os.path.join(DATA_DIR, "cvku_backup.db"))
os.environ.setdefault("CVKU_AI_MODE", "stub")

import db
import jaringan

db.DB_PATH = os.environ["CVKU_DB"]
db.BACKUP_PATH = os.environ["CVKU_DB_BACKUP"]


def seed():
    print("Inisialisasi basis data dan tabel jejaring...")
    db.init_db()
    jaringan.init_jaringan()

    con = db.koneksi()
    try:
        # Bersihkan tabel jejaring agar seed selalu segar dan konsisten
        con.execute("DELETE FROM suka")
        con.execute("DELETE FROM posting")
        con.execute("DELETE FROM koneksi")
        con.execute("DELETE FROM pengguna WHERE peran = 'verifikator' OR username = 'dosen'")
        con.execute("UPDATE pengguna SET peran = 'pengguna'")
        con.commit()

        # Daftar 10 Pengguna Mahasiswa untuk Seed Demo
        daftar_mhs = [
            {
                "username": "demo",
                "password": "demo123",
                "nama": "Sharen Mahasiswa Demo",
                "email": "demo@student.filkom.ub.ac.id",
                "telepon": "081234567890",
                "kota": "Malang",
                "linkedin": "linkedin.com/in/demomahasiswa",
                "headline": "Mahasiswa Sistem Informasi | Aspiring Full-Stack & AI Engineer",
                "skill": "Python, Flask, React, System Analysis, ATS Optimization, SQL",
                "ringkasan": "Mahasiswa Sistem Informasi tingkat akhir dengan minat besar pada rekayasa perangkat lunak dan arsitektur data cerdas. Aktif memimpin kepanitiaan teknologi kampus dan menyelesaikan proyek web modern.",
                "kegiatan": [
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
                        ]
                    },
                    {
                        "nama_kegiatan": "Magang Frontend Engineer",
                        "penyelenggara": "PT Solusi Digital Nusantara",
                        "peran": "Frontend Intern",
                        "periode": "Jul 2024 - Sep 2024",
                        "lokasi": "Jakarta (Remote)",
                        "uraian": "Mengembangkan antarmuka dashboard analitik pengguna berbasis web dan mempercepat waktu muat komponen utama.",
                        "bagian": "Magang",
                        "judul": "Frontend Intern - PT Solusi Digital Nusantara",
                        "poin": [
                            "Mengembangkan komponen dashboard analitik pengguna yang responsif menggunakan HTML, CSS, dan JavaScript modern.",
                            "Mengoptimalkan waktu render halaman sehingga meningkatkan kecepatan akses hingga 25%.",
                            "Berkolaborasi aktif dengan tim desain UI/UX dan tim backend dalam integrasi REST API."
                        ]
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
                            "Mempresentasikan demo langsung produk dan model implementasi di hadapan dewan juri industri."
                        ]
                    }
                ]
            },
            {
                "username": "budi_pm",
                "password": "demo123",
                "nama": "Budi Pratama",
                "email": "budi.pratama@student.ub.ac.id",
                "telepon": "081298765432",
                "kota": "Jakarta",
                "linkedin": "linkedin.com/in/budipratama-pm",
                "headline": "Associate Product Manager Intern | Digital Product Strategy & Discovery",
                "skill": "Product Management, Agile Scrum, Wireframing, User Research, SQL, PRD Writing",
                "ringkasan": "Mahasiswa Ilmu Komputer berfokus pada product discovery, pemetaan alur pengguna, dan penyusunan spesifikasi produk berbasis riset metrik kualitatif serta kuantitatif.",
                "kegiatan": [
                    {
                        "nama_kegiatan": "Associate Product Manager Intern",
                        "penyelenggara": "PT Marketplace Digital Indonesia",
                        "peran": "APM Intern",
                        "periode": "Agu 2024 - Des 2024",
                        "lokasi": "Jakarta",
                        "uraian": "Menyusun PRD untuk alur checkout baru dan memimpin sprint grooming bersama tim engineering.",
                        "bagian": "Magang",
                        "judul": "APM Intern - PT Marketplace Digital Indonesia",
                        "poin": [
                            "Menyusun dokumen Product Requirement Document (PRD) fitur checkout terintegrasi yang diimplementasikan pada aplikasi mobile.",
                            "Melakukan interview kualitatif pada 20 calon pengguna untuk memetakan pain point transaksi pembayaran.",
                            "Memantau funnel konversi dan mencatat peningkatan funnel checkout sebesar 14% pasca perilisan fitur."
                        ]
                    },
                    {
                        "nama_kegiatan": "Divisi Inovasi & Produk Digital BEM",
                        "penyelenggara": "BEM Fakultas Ilmu Komputer",
                        "peran": "Ketua Divisi",
                        "periode": "Jan 2024 - Sekarang",
                        "lokasi": "Malang",
                        "uraian": "Mengelola portofolio produk layanan digital mahasiswa tingkat fakultas.",
                        "bagian": "Pengalaman Organisasi",
                        "judul": "Ketua Divisi Inovasi & Produk Digital - BEM FILKOM",
                        "poin": [
                            "Mengelola 4 kanal produk web aspirasi mahasiswa dengan total kunjungan aktif 1.200 per bulan.",
                            "Menerapkan metodologi Kanban untuk melacak siklus rilis dan penanganan laporan bug dari mahasiswa."
                        ]
                    },
                    {
                        "nama_kegiatan": "National Product Design Competition 2024",
                        "penyelenggara": "Universitas Indonesia",
                        "peran": "Team Lead & Product Strategist",
                        "periode": "Mei 2024",
                        "lokasi": "Depok",
                        "uraian": "Meraih Juara 2 dalam perancangan solusi produk FinTech untuk literasi keuangan generasi muda.",
                        "bagian": "Penghargaan",
                        "judul": "Juara 2 - National Product Design Competition 2024",
                        "poin": [
                            "Merancang konsep gamifikasi tabungan mikro untuk pelajar SMA dan mahasiswa tingkat awal.",
                            "Menyusun rencana go-to-market serta model proyeksi pendapatan produk selama 3 tahun ke depan."
                        ]
                    }
                ]
            },
            {
                "username": "siti_ai",
                "password": "demo123",
                "nama": "Siti Rahmawati",
                "email": "siti.rahma@student.itb.ac.id",
                "telepon": "081345678901",
                "kota": "Bandung",
                "linkedin": "linkedin.com/in/sitirahmawati-ai",
                "headline": "AI & Data Science Enthusiast | Natural Language Processing Researcher",
                "skill": "Machine Learning, Python, PyTorch, Natural Language Processing, Data Analysis",
                "ringkasan": "Peneliti muda di bidang NLP bahasa daerah dan pemrosesan teks medis. Berpengalaman melatih model transformator bahasa Indonesia.",
                "kegiatan": [
                    {
                        "nama_kegiatan": "Asisten Riset Laboratorium Kecerdasan Buatan",
                        "penyelenggara": "Lab AI & Data Engineering ITB",
                        "peran": "Research Assistant",
                        "periode": "Feb 2024 - Sekarang",
                        "lokasi": "Bandung",
                        "uraian": "Melakukan fine-tuning model IndoBERT untuk klasifikasi opini publik pada media sosial.",
                        "bagian": "Proyek",
                        "judul": "NLP Research Assistant - Lab AI & Data Engineering",
                        "poin": [
                            "Mengkurasi dan membersihkan dataset teks bahasa Indonesia beranotasi sejumlah 50.000 entri.",
                            "Mencapai skor F1-Score 92.4% dalam tugas analisis sentimen multi-kelas menggunakan transformer.",
                            "Mempresentasikan hasil riset pada seminar nasional pemrosesan bahasa alami."
                        ]
                    },
                    {
                        "nama_kegiatan": "Magang Data Scientist",
                        "penyelenggara": "Fintech Solusi Nusa",
                        "peran": "Data Science Intern",
                        "periode": "Jun 2024 - Agu 2024",
                        "lokasi": "Jakarta (Remote)",
                        "uraian": "Membangun model deteksi anomali transaksi mencurigakan secara otomatis.",
                        "bagian": "Magang",
                        "judul": "Data Science Intern - Fintech Solusi Nusa",
                        "poin": [
                            "Membangun pipeline ekstraksi fitur otomatis dari catatan log transaksi perbankan.",
                            "Mengurangi angka false positive deteksi anomali hingga 18% menggunakan algoritma Random Forest."
                        ]
                    }
                ]
            },
            {
                "username": "dimas_dev",
                "password": "demo123",
                "nama": "Dimas Anggara",
                "email": "dimas.dev@student.its.ac.id",
                "telepon": "081456789012",
                "kota": "Surabaya",
                "linkedin": "linkedin.com/in/dimas-backend",
                "headline": "Backend Engineer | Golang, PostgreSQL & Cloud Infrastructure",
                "skill": "Go, Docker, PostgreSQL, REST API, Microservices, Redis, Git",
                "ringkasan": "Spesialis rekayasa backend dengan fokus pada performa sistem tinggi, skalabilitas database, dan arsitektur microservices modern.",
                "kegiatan": [
                    {
                        "nama_kegiatan": "Backend Engineer Intern",
                        "penyelenggara": "PT Kode Kreasi Nusantara",
                        "peran": "Backend Intern",
                        "periode": "Jul 2024 - Okt 2024",
                        "lokasi": "Surabaya",
                        "uraian": "Mengembangkan microservice manajemen inventori menggunakan bahasa Go dan PostgreSQL.",
                        "bagian": "Magang",
                        "judul": "Backend Intern - PT Kode Kreasi Nusantara",
                        "poin": [
                            "Mengimplementasikan 15 endpoint REST API berkecepatan tinggi dengan response time rata-rata di bawah 45ms.",
                            "Mengintegrasikan caching Redis untuk mengurangi beban kueri database baca sebesar 40%."
                        ]
                    },
                    {
                        "nama_kegiatan": "Pengembangan API Gateway Kampus Terbuka",
                        "penyelenggara": "Komunitas Open Source Surabaya",
                        "peran": "Core Contributor",
                        "periode": "Mar 2024 - Jun 2024",
                        "lokasi": "Surabaya",
                        "uraian": "Merancang reverse proxy dan rate limiter berbasis worker pool konkurensi Go.",
                        "bagian": "Proyek",
                        "judul": "Core Developer - Open Source Gateway Engine",
                        "poin": [
                            "Merancang arsitektur rate-limiting berbasis token bucket untuk melindungi API dari request berlebih.",
                            "Menulis dokumentasi teknis dan panduan kontribusi yang telah digunakan oleh 100+ developer komunitas."
                        ]
                    }
                ]
            },
            {
                "username": "amanda_ui",
                "password": "demo123",
                "nama": "Amanda Putri",
                "email": "amanda.uiux@student.ugm.ac.id",
                "telepon": "081567890123",
                "kota": "Yogyakarta",
                "linkedin": "linkedin.com/in/amanda-uiux",
                "headline": "UI/UX Designer & Product Researcher | Human-Centered Design",
                "skill": "Figma, User Testing, Design System, Wireframing, Prototyping, Usability",
                "ringkasan": "Desainer produk digital yang menggabungkan estetika visual bersih dengan kenyamanan interaksi pengguna berbasis riset empati.",
                "kegiatan": [
                    {
                        "nama_kegiatan": "UI/UX Designer Intern",
                        "penyelenggara": "Creative Digital Studio Yogya",
                        "peran": "UI/UX Intern",
                        "periode": "Jul 2024 - Okt 2024",
                        "lokasi": "Yogyakarta",
                        "uraian": "Merancang sistem desain (design system) untuk 3 aplikasi mobile klien startup.",
                        "bagian": "Magang",
                        "judul": "UI/UX Designer Intern - Creative Digital Studio",
                        "poin": [
                            "Membangun perpustakaan komponen Figma komprehensif berisi lebih dari 80 komponen varian siap pakai.",
                            "Menyelenggarakan usability testing dengan 12 partisipan untuk menguji kemudahan navigasi aplikasi."
                        ]
                    },
                    {
                        "nama_kegiatan": "Koordinator Divisi Desain & Kreatif Kampus",
                        "penyelenggara": "Lembaga Pers Mahasiswa UGM",
                        "peran": "Koordinator Desain",
                        "periode": "Feb 2024 - Sekarang",
                        "lokasi": "Yogyakarta",
                        "uraian": "Memimpin tata letak publikasi majalah digital dan aset media sosial berkala.",
                        "bagian": "Pengalaman Organisasi",
                        "judul": "Koordinator Desain - Lembaga Pers Mahasiswa",
                        "poin": [
                            "Menerapkan standarisasi identitas visual baru yang meningkatkan engagement media sosial LPM sebesar 30%.",
                            "Mementori 8 staf desainer muda dalam penguasaan tool prototyping modern."
                        ]
                    }
                ]
            },
            {
                "username": "fajar_mobile",
                "password": "demo123",
                "nama": "Fajar Nugraha",
                "email": "fajar.mobile@student.ub.ac.id",
                "telepon": "081678901234",
                "kota": "Malang",
                "linkedin": "linkedin.com/in/fajarnugraha-mobile",
                "headline": "Flutter & Mobile App Developer | Cross-Platform Application Specialist",
                "skill": "Flutter, Dart, Firebase, Android, Mobile UI, State Management, REST API",
                "ringkasan": "Pengembang aplikasi seluler lintas platform yang antusias menghadirkan aplikasi cepat, responsif, dan mudah dipelihara.",
                "kegiatan": [
                    {
                        "nama_kegiatan": "Lead Mobile Developer Aplikasi Donasi",
                        "penyelenggara": "Komunitas Peduli Mahasiswa Malang",
                        "peran": "Lead Mobile Developer",
                        "periode": "Mei 2024 - Agu 2024",
                        "lokasi": "Malang",
                        "uraian": "Membangun aplikasi Android donasi sembako mahasiswa terdampak bencana.",
                        "bagian": "Proyek",
                        "judul": "Lead Mobile Developer - Aplikasi Donasi Peduli Kampus",
                        "poin": [
                            "Mengembangkan aplikasi Flutter dengan arsitektur BLoC pattern yang terstruktur rapi.",
                            "Mengintegrasikan notifikasi push real-time Firebase Cloud Messaging untuk pelacakan distribusi donasi."
                        ]
                    },
                    {
                        "nama_kegiatan": "Magang Mobile Engineer",
                        "penyelenggara": "EduTech Nusantara Bersama",
                        "peran": "Mobile Engineer Intern",
                        "periode": "Sep 2024 - Des 2024",
                        "lokasi": "Surabaya (Hybrid)",
                        "uraian": "Mengoptimalkan performa rendering layar video pembelajaran pada aplikasi mobile kursus.",
                        "bagian": "Magang",
                        "judul": "Mobile Engineer Intern - EduTech Nusantara Bersama",
                        "poin": [
                            "Meningkatkan skor frame-rate aplikasi dari 45 fps menjadi stabil 60 fps pada perangkat kelas menengah.",
                            "Memperbaiki 22 isu minor terkait kompatibilitas layar berbagai dimensi smartphone."
                        ]
                    }
                ]
            },
            {
                "username": "nadia_biz",
                "password": "demo123",
                "nama": "Nadia Safitri",
                "email": "nadia.biz@student.ui.ac.id",
                "telepon": "081789012345",
                "kota": "Jakarta",
                "linkedin": "linkedin.com/in/nadiasafitri-biz",
                "headline": "Business Development & Tech Partnership Enthusiast | Data-Driven Growth",
                "skill": "Business Analysis, Market Research, B2B Partnership, Public Speaking, Negotiation",
                "ringkasan": "Mahasiswa yang memiliki visi strategis dalam menghubungkan inovasi teknologi perangkat lunak dengan kebutuhan pasar dan kemitraan bisnis institusi.",
                "kegiatan": [
                    {
                        "nama_kegiatan": "VP Partnership & Sponsorship National Tech Summit",
                        "penyelenggara": "Fakultas Ekonomi & Bisnis UI",
                        "peran": "Vice President Partnership",
                        "periode": "Jun 2024 - Nov 2024",
                        "lokasi": "Jakarta",
                        "uraian": "Menggalang kemitraan strategis dengan perusahaan teknologi terkemuka untuk pendanaan acara.",
                        "bagian": "Pengalaman Organisasi",
                        "judul": "VP Partnership - National Tech Summit UI 2024",
                        "poin": [
                            "Berhasil mendapatkan sponsor senilai total Rp 75.000.000 dari 6 perusahaan teknologi nasional.",
                            "Menegosiasikan kontrak kerja sama mutualisme media partner dengan 15 kanal publikasi digital."
                        ]
                    },
                    {
                        "nama_kegiatan": "Juara 1 National Business Case Competition",
                        "penyelenggara": "Universitas Gadjah Mada",
                        "peran": "Team Leader",
                        "periode": "Okt 2024",
                        "lokasi": "Yogyakarta",
                        "uraian": "Merumuskan strategi ekspansi produk logistik berbasis AI di kawasan Indonesia Timur.",
                        "bagian": "Penghargaan",
                        "judul": "Juara 1 - National Business Case Competition 2024",
                        "poin": [
                            "Memimpin tim 3 orang dalam menyusun analisis kelayakan bisnis dan penetapan harga dinamis berbasis rute pengiriman.",
                            "Mempresentasikan pitch deck di hadapan eksekutif industri logistik nasional dan dewan juri."
                        ]
                    }
                ]
            },
            {
                "username": "reza_sec",
                "password": "demo123",
                "nama": "Reza Kurniawan",
                "email": "reza.sec@student.undip.ac.id",
                "telepon": "081890123456",
                "kota": "Semarang",
                "linkedin": "linkedin.com/in/rezakurniawan-sec",
                "headline": "Cybersecurity Analyst | Vulnerability Assessment & Network Security",
                "skill": "Network Security, Penetration Testing, Linux, Wireshark, Cryptography, OWASP",
                "ringkasan": "Peneliti keamanan siber muda yang fokus pada identifikasi kerentanan aplikasi web sesuai standar OWASP Top 10.",
                "kegiatan": [
                    {
                        "nama_kegiatan": "Ketua Komunitas Cyber Security Mahasiswa",
                        "penyelenggara": "Universitas Diponegoro",
                        "peran": "Ketua Komunitas",
                        "periode": "Jan 2024 - Sekarang",
                        "lokasi": "Semarang",
                        "uraian": "Menyelenggarakan pelatihan mingguan Capture The Flag (CTF) dan audit kode sumber.",
                        "bagian": "Pengalaman Organisasi",
                        "judul": "Ketua Komunitas - Cyber Security Research Group",
                        "poin": [
                            "Menyelenggarakan 12 sesi pelatihan hands-on mengenai teknik mitigasi SQL Injection dan XSS.",
                            "Membina 40 anggota aktif hingga berhasil menembus babak final kompetisi keamanan siber nasional."
                        ]
                    },
                    {
                        "nama_kegiatan": "Security Researcher Bug Bounty Kampus",
                        "penyelenggara": "Pusat Teknologi Informasi Kampus",
                        "peran": "Independent Security Researcher",
                        "periode": "Mei 2024 - Agu 2024",
                        "lokasi": "Semarang",
                        "uraian": "Melakukan uji penetrasi pada portal akademik dan melaporkan 4 kerentanan berisiko sedang.",
                        "bagian": "Proyek",
                        "judul": "Security Researcher - Audit Keamanan Portal Akademik",
                        "poin": [
                            "Menemukan dan mendokumentasikan bukti konsep (PoC) celah broken access control pada portal.",
                            "Membantu tim infrastruktur server dalam menerapkan patch keamanan sebelum masa pengisian KRS."
                        ]
                    }
                ]
            },
            {
                "username": "clara_qa",
                "password": "demo123",
                "nama": "Clara Stephanie",
                "email": "clara.qa@student.binus.ac.id",
                "telepon": "081901234567",
                "kota": "Jakarta",
                "linkedin": "linkedin.com/in/clarastephanie-qa",
                "headline": "QA Automation Engineer | Ensuring Software Quality & Reliability",
                "skill": "Selenium, Cypress, Automated Testing, Postman, CI/CD, Test Plan, Jira",
                "ringkasan": "QA Engineer dengan dedikasi tinggi pada pembuatan skrip uji otomatis end-to-end demi menjaga kualitas dan keandalan sistem.",
                "kegiatan": [
                    {
                        "nama_kegiatan": "QA Engineer Intern",
                        "penyelenggara": "Logistik Pintar Cemerlang",
                        "peran": "QA Automation Intern",
                        "periode": "Agu 2024 - Des 2024",
                        "lokasi": "Jakarta",
                        "uraian": "Membuat skrip automation testing menggunakan Cypress untuk modul pelacakan kurir.",
                        "bagian": "Magang",
                        "judul": "QA Automation Intern - Logistik Pintar Cemerlang",
                        "poin": [
                            "Menulis lebih dari 60 skenario uji otomatis regresi yang dijalankan pada pipeline CI/CD GitHub Actions.",
                            "Mempercepat waktu pengujian pra-rilis dari 4 jam manual menjadi hanya 12 menit secara otomatis."
                        ]
                    },
                    {
                        "nama_kegiatan": "Finalis Software Testing Competition 2024",
                        "penyelenggara": "Asosiasi Rekayasa Perangkat Lunak Indonesia",
                        "peran": "Peserta Individu",
                        "periode": "Sep 2024",
                        "lokasi": "Jakarta",
                        "uraian": "Menemukan bug kritis pada sistem perbankan simulasi dalam waktu 3 jam pengujian.",
                        "bagian": "Penghargaan",
                        "judul": "Finalis - Software Testing Hackathon Nasional 2024",
                        "poin": [
                            "Mendapatkan skor tertinggi dalam penyusunan laporan bug komprehensif berstandar internasional.",
                            "Mengidentifikasi 8 cacat logika bisnis pada alur transfer dana antarbank simulasi."
                        ]
                    }
                ]
            },
            {
                "username": "kevin_cloud",
                "password": "demo123",
                "nama": "Kevin Sanjaya",
                "email": "kevin.cloud@student.ub.ac.id",
                "telepon": "081234567000",
                "kota": "Malang",
                "linkedin": "linkedin.com/in/kevinsanjaya-cloud",
                "headline": "DevOps & Cloud Engineer | Kubernetes, Terraform & CI/CD Practitioner",
                "skill": "Kubernetes, AWS, Terraform, Docker, CI/CD Pipeline, Linux, Bash Scripting",
                "ringkasan": "Antusias dalam otomasi infrastruktur cloud, provisioning arsitektur microservices, dan implementasi observabilitas sistem.",
                "kegiatan": [
                    {
                        "nama_kegiatan": "Cloud DevOps Intern",
                        "penyelenggara": "Cloud Mandiri Solusindo",
                        "peran": "DevOps Intern",
                        "periode": "Jul 2024 - Nov 2024",
                        "lokasi": "Malang",
                        "uraian": "Mengotomasi pipeline deployment Kubernetes cluster menggunakan Helm chart dan GitLab CI.",
                        "bagian": "Magang",
                        "judul": "DevOps Intern - Cloud Mandiri Solusindo",
                        "poin": [
                            "Membuat template Terraform untuk provisioning resource AWS VPC dan database RDS secara otomatis.",
                            "Membantu proses zero-downtime deployment untuk 5 service produksi utama."
                        ]
                    },
                    {
                        "nama_kegiatan": "Modern Cloud Architecture Project",
                        "penyelenggara": "AWS Cloud Club Malang",
                        "peran": "Infrastructure Lead",
                        "periode": "Apr 2024 - Jun 2024",
                        "lokasi": "Malang",
                        "uraian": "Merancang arsitektur serverless berskala dinamis untuk aplikasi registrasi acara kampus.",
                        "bagian": "Proyek",
                        "judul": "Infrastructure Lead - Serverless Event Platform",
                        "poin": [
                            "Mengurangi estimasi biaya komputasi server hingga 60% dengan memanfaatkan AWS Lambda dan API Gateway.",
                            "Menerapkan sistem monitoring dan alerting berbasis Grafana dan Prometheus."
                        ]
                    }
                ]
            }
        ]

        # Simpan pengguna dan pencapaiannya
        user_ids = {}
        for m in daftar_mhs:
            u = con.execute("SELECT id FROM pengguna WHERE username = ?", (m["username"],)).fetchone()
            if not u:
                uid = db.simpan_pengguna(
                    username=m["username"],
                    password=m["password"],
                    peran="pengguna",
                    nama=m["nama"],
                    email=m["email"],
                    telepon=m["telepon"],
                    kota=m["kota"],
                    linkedin=m["linkedin"],
                    ringkasan=m["ringkasan"]
                )
            else:
                uid = u["id"]
                con.execute("UPDATE pengguna SET peran = 'pengguna' WHERE id = ?", (uid,))
                con.commit()
                db.perbarui_profil(
                    uid,
                    nama=m["nama"],
                    email=m["email"],
                    telepon=m["telepon"],
                    kota=m["kota"],
                    linkedin=m["linkedin"],
                    ringkasan=m["ringkasan"]
                )

            # Perbarui headline & skill
            jaringan.perbarui_headline_skill(uid, m["headline"], m["skill"])
            user_ids[m["username"]] = uid

            # Simpan kegiatan jika belum ada
            existing_act = con.execute("SELECT count(*) FROM pencapaian WHERE id_pengguna = ?", (uid,)).fetchone()[0]
            if existing_act == 0:
                for k in m["kegiatan"]:
                    id_p = db.simpan_pencapaian(
                        id_pengguna=uid,
                        nama_kegiatan=k["nama_kegiatan"],
                        uraian=k["uraian"],
                        penyelenggara=k["penyelenggara"],
                        peran=k["peran"],
                        periode=k["periode"],
                        lokasi=k["lokasi"]
                    )
                    db.simpan_hasil_ai(id_p, k["bagian"], k["judul"], k["poin"])
                    # Di CVku Network, semua pencapaian berstatus disetujui (tanpa verifikasi)
                    db.ubah_status_pencapaian(id_p, "disetujui")

            print(f"Mahasiswa '{m['nama']}' (@{m['username']}) siap (ID: {uid}).")

        # -------------------------------------------------------------
        # 2. Hubungan Koneksi Awal untuk Demo Skenario
        # -------------------------------------------------------------
        id_demo = user_ids["demo"]
        id_budi = user_ids["budi_pm"]
        id_siti = user_ids["siti_ai"]
        id_dimas = user_ids["dimas_dev"]
        id_amanda = user_ids["amanda_ui"]
        id_nadia = user_ids["nadia_biz"]
        id_reza = user_ids["reza_sec"]

        # Hubungan 1: Demo <-> Siti (Terhubung)
        con.execute(
            "INSERT INTO koneksi (id_pengirim, id_penerima, status) VALUES (?, ?, 'terhubung')",
            (id_demo, id_siti)
        )
        # Hubungan 2: Demo <-> Dimas (Terhubung)
        con.execute(
            "INSERT INTO koneksi (id_pengirim, id_penerima, status) VALUES (?, ?, 'terhubung')",
            (id_dimas, id_demo)
        )
        # Hubungan 3: Demo <-> Amanda (Permintaan Masuk: Amanda mengirim ke Demo, status 'menunggu')
        con.execute(
            "INSERT INTO koneksi (id_pengirim, id_penerima, status) VALUES (?, ?, 'menunggu')",
            (id_amanda, id_demo)
        )
        # Hubungan 4: Siti <-> Dimas (Terhubung)
        con.execute(
            "INSERT INTO koneksi (id_pengirim, id_penerima, status) VALUES (?, ?, 'terhubung')",
            (id_siti, id_dimas)
        )
        # Hubungan 5: Nadia <-> Reza (Terhubung)
        con.execute(
            "INSERT INTO koneksi (id_pengirim, id_penerima, status) VALUES (?, ?, 'terhubung')",
            (id_nadia, id_reza)
        )
        con.commit()
        print("Koneksi awal berhasil dibuat:")
        print("  ✓ Demo terhubung dengan Siti Rahmawati & Dimas Anggara")
        print("  ✓ Amanda Putri mengirim permintaan koneksi menunggu ke akun Demo")
        print("  ✓ Budi Pratama (Product Manager) belum terhubung dengan Demo (siap dicari dan dihubungkan!)")

        # -------------------------------------------------------------
        # 3. 5 Postingan Awal di Feed
        # -------------------------------------------------------------
        posts = [
            (
                id_siti,
                "Senang sekali paper riset NLP bahasa Indonesia tim kami resmi diterima untuk dipresentasikan di konferensi internasional IEEE bulan depan! Terima kasih untuk seluruh rekan lab AI dan dosen pembimbing. 🚀✨"
            ),
            (
                id_dimas,
                "Baru saja merilis pembaruan v2 untuk API gateway kampus. Response time turun hingga 35% setelah migrasi ke Golang worker pool. Semangat open-source bagi teman-teman developer! 💻🔥"
            ),
            (
                id_demo,
                "Baru saja memperbarui portofolio dan menyusun CV ATS otomatis lewat platform CVku Network. Cukup masukkan uraian kegiatan, langsung diproses AI jadi poin baku dan siap diunduh! 📄🎯"
            ),
            (
                id_budi,
                "Menyelesaikan sprint product discovery untuk fitur checkout baru. Belajar banyak tentang pentingnya user interview kualitatif dan validasi metrik sebelum merumuskan PRD final ke engineering. 💡📊"
            ),
            (
                id_amanda,
                "Baru menyelesaikan sesi workshop Design System untuk 50+ mahasiswa desain dan developer. Konsistensi UI dan reusable component benar-benar kunci efisiensi kolaborasi tim lintas fungsi. 🎨✨"
            )
        ]

        for p_uid, p_isi in posts:
            con.execute("INSERT INTO posting (id_pengguna, isi) VALUES (?, ?)", (p_uid, p_isi))
        con.commit()
        print("5 Postingan awal di feed berhasil ditambahkan.")

        # Tambahkan 1-2 suka awal untuk meramaikan
        p_demo = con.execute("SELECT id FROM posting WHERE id_pengguna = ?", (id_demo,)).fetchone()
        if p_demo:
            con.execute("INSERT OR IGNORE INTO suka (id_posting, id_pengguna) VALUES (?, ?)", (p_demo["id"], id_siti))
            con.execute("INSERT OR IGNORE INTO suka (id_posting, id_pengguna) VALUES (?, ?)", (p_demo["id"], id_dimas))
            con.commit()

        # Cadangkan database
        db.cadangkan()
        print("Pencadangan database berhasil.")
        print("\n" + "="*60)
        print("SEED DEMO CVKU NETWORK SELESAI DENGAN SUKSES!")
        print("="*60)
        print("Akun Demo Utama : demo / demo123 (Mahasiswa)")
        print("Akun PM         : budi_pm / demo123 (Siap dicari: 'product manager')")
        print("Total Mahasiswa : 10 akun profil lengkap")
        print("Feed & Koneksi  : Siap untuk demo 5 menit")
        print("="*60)
    finally:
        con.close()


if __name__ == "__main__":
    seed()
