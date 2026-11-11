"""app.py - Aplikasi Web CVku (Flask + Jinja2 + CSS Tanpa Framework JS Berat).

Aplikasi penyusun CV ATS-friendly untuk mahasiswa dengan bantuan AI.
Fitur:
- Autentikasi sesi & batasan hak akses (Mahasiswa & Verifikator)
- Kelola profil identitas dan ringkasan profesional
- Tambah kegiatan & pencapaian dengan proses AI (fallback otomatis ke stub jika gagal/timeout)
- Cek dan sunting hasil AI (dropdown 7 bagian CV, judul, dan poin-poin bullet)
- Daftar dan kurasi pencapaian (sunting dan hapus dengan konfirmasi)
- Pratinjau CV ATS dan unduh dokumen .docx resmi (satu kolom, tanpa tabel, tanpa gambar)
- Riwayat versi berkas CV tersimpan
- Panel Verifikator untuk meninjau dan menyetujui/menolak kegiatan mahasiswa
"""
import os
import shutil
import json
import datetime
import re
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_file, abort
)
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

# -----------------------------------------------------------------------------
# Konfigurasi Direktori & Environment Variable Default
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RIWAYAT_DIR = os.path.join(BASE_DIR, "riwayat_cv")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RIWAYAT_DIR, exist_ok=True)

# Default environment variable sesuai ATURAN WAJIB
os.environ.setdefault("CVKU_DB", os.path.join(DATA_DIR, "cvku.db"))
os.environ.setdefault("CVKU_DB_BACKUP", os.path.join(DATA_DIR, "cvku_backup.db"))

# Pulihkan cadangan jika ada di root namun belum ada di data/
root_backup = os.path.join(BASE_DIR, "cvku_backup.db")
target_backup = os.environ["CVKU_DB_BACKUP"]
if os.path.exists(root_backup) and not os.path.exists(target_backup):
    try:
        shutil.copy(root_backup, target_backup)
    except Exception:
        pass

# Import modul yang sudah ada (TIDAK BOLEH DIUBAH)
import db
import ai_service
import skema

# Pastikan modul re tersedia untuk ai_service._stub
ai_service.re = re

# Sinkronkan mode AI dan URL dari environment variable jika diset (tidak memaksa stub)
if "CVKU_AI_MODE" in os.environ:
    ai_service.MODE = os.environ["CVKU_AI_MODE"]
if "CVKU_AI_URL" in os.environ:
    ai_service.REMOTE_URL = os.environ["CVKU_AI_URL"]

# Pastikan path pada db.py sinkron
db.DB_PATH = os.environ["CVKU_DB"]
db.BACKUP_PATH = os.environ["CVKU_DB_BACKUP"]

# Panggil db.init_db() saat aplikasi mulai
db.init_db()

# Konfigurasi AUTO_APPROVE:
# Default True: setiap pencapaian yang disimpan langsung otomatis disetujui untuk CV
AUTO_APPROVE_ENV = os.environ.get("CVKU_AUTO_APPROVE", os.environ.get("AUTO_APPROVE", "True"))
AUTO_APPROVE = AUTO_APPROVE_ENV.lower() in ("true", "1", "yes")

# -----------------------------------------------------------------------------
# Inisialisasi Flask
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cvku-secret-key-2026-uts-ai-cv")


# -----------------------------------------------------------------------------
# Middleware & Decorators Hak Akses
# -----------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Silakan masuk terlebih dahulu untuk mengakses halaman ini.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def mahasiswa_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Silakan masuk terlebih dahulu.", "warning")
            return redirect(url_for("login", next=request.path))
        if session.get("peran") != "mahasiswa":
            flash("Halaman ini khusus untuk pengguna dengan peran Mahasiswa.", "danger")
            return redirect(url_for("beranda"))
        return f(*args, **kwargs)
    return decorated_function


def verifikator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Silakan masuk terlebih dahulu.", "warning")
            return redirect(url_for("login", next=request.path))
        if session.get("peran") != "verifikator":
            flash("Halaman ini khusus untuk verifikator kampus.", "danger")
            return redirect(url_for("beranda"))
        return f(*args, **kwargs)
    return decorated_function


# -----------------------------------------------------------------------------
# Helper DOCX ATS-Friendly
# -----------------------------------------------------------------------------
def buat_file_docx(profil: dict, cv_data: dict, filepath: str):
    """
    Menghasilkan berkas DOCX ATS-friendly:
    - Satu kolom, TANPA tabel, TANPA gambar atau bingkai
    - Margin 2cm kiri/kanan, 1.8cm atas/bawah
    - Font Calibri standar 11pt, judul 18pt bold
    - Urutan: Nama & Kontak -> Ringkasan Profil -> Tiap Bagian dengan poin bullet
    """
    doc = Document()
    sec = doc.sections[0]
    sec.left_margin = sec.right_margin = Cm(2)
    sec.top_margin = sec.bottom_margin = Cm(1.8)

    # Gaya normal dokumen
    st = doc.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(11)
    st.paragraph_format.space_after = Pt(2)
    st.paragraph_format.line_spacing = 1.15

    # 1. Header: Nama Lengkap (Besar, Bold, Center)
    nama = (profil.get("nama") or "").strip() or "NAMA LENGKAP"
    p_nama = doc.add_paragraph()
    p_nama.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_nama.paragraph_format.space_after = Pt(2)
    r_nama = p_nama.add_run(nama.upper())
    r_nama.bold = True
    r_nama.font.size = Pt(18)

    # 2. Kontak: Email | Telepon | Kota | LinkedIn (Center)
    kontak_parts = [
        profil.get("email", "").strip(),
        profil.get("telepon", "").strip(),
        profil.get("kota", "").strip(),
        profil.get("linkedin", "").strip(),
    ]
    kontak_text = " | ".join(k for k in kontak_parts if k)
    if kontak_text:
        p_kontak = doc.add_paragraph()
        p_kontak.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_kontak.paragraph_format.space_after = Pt(10)
        r_kontak = p_kontak.add_run(kontak_text)
        r_kontak.font.size = Pt(10)

    # 3. Ringkasan Profil (jika ada)
    ringkasan = (profil.get("ringkasan") or "").strip()
    if ringkasan:
        h_ringkasan = doc.add_heading("RINGKASAN PROFIL", level=1)
        h_ringkasan.paragraph_format.space_before = Pt(8)
        h_ringkasan.paragraph_format.space_after = Pt(3)
        p_ringkasan = doc.add_paragraph(ringkasan)
        p_ringkasan.paragraph_format.space_after = Pt(6)

    # 4. Setiap Bagian sesuai urutan skema.BAGIAN
    for bag in skema.BAGIAN:
        items = cv_data.get(bag, [])
        if not items:
            continue

        h_bag = doc.add_heading(bag.upper(), level=1)
        h_bag.paragraph_format.space_before = Pt(10)
        h_bag.paragraph_format.space_after = Pt(3)

        for item in items:
            # Judul entri
            p_item = doc.add_paragraph()
            p_item.paragraph_format.space_before = Pt(4)
            p_item.paragraph_format.space_after = Pt(1)
            r_judul = p_item.add_run(item.get("judul", "").strip())
            r_judul.bold = True
            r_judul.font.size = Pt(11)

            # Metadata entri: Juara/Peran | Penyelenggara | Lokasi | Periode (mendatar)
            meta_parts = []
            if item.get("peran") and item["peran"].strip():
                meta_parts.append(item["peran"].strip())
            if item.get("penyelenggara"):
                meta_parts.append(item["penyelenggara"].strip())
            if item.get("lokasi"):
                meta_parts.append(item["lokasi"].strip())
            if item.get("periode"):
                meta_parts.append(item["periode"].strip())

            if meta_parts:
                p_meta = doc.add_paragraph()
                p_meta.paragraph_format.space_before = Pt(0)
                p_meta.paragraph_format.space_after = Pt(2)
                r_meta = p_meta.add_run(" | ".join(meta_parts))
                r_meta.italic = True
                r_meta.font.size = Pt(10)

            # Poin-poin berbentuk bullet
            for pt in item.get("poin", []):
                pt_text = str(pt).strip()
                if pt_text:
                    p_pt = doc.add_paragraph(pt_text, style="List Bullet")
                    p_pt.paragraph_format.space_after = Pt(2)
                    p_pt.paragraph_format.line_spacing = 1.15

    doc.save(filepath)


# -----------------------------------------------------------------------------
# Rute 1: Beranda
# -----------------------------------------------------------------------------
@app.route("/")
def beranda():
    user_id = session.get("user_id")
    peran = session.get("peran")

    profil = {}
    stats = {"total": 0, "disetujui": 0, "menunggu": 0, "ditolak": 0, "versi_cv": 0}
    pencapaian_terbaru = []
    ai_mode = os.environ.get("CVKU_AI_MODE", "stub")

    if user_id:
        profil = db.baca_pengguna(user_id) or {}
        if peran == "mahasiswa":
            semua = db.daftar_pencapaian(user_id)
            stats["total"] = len(semua)
            stats["disetujui"] = sum(1 for p in semua if p["status"] == "disetujui")
            stats["menunggu"] = sum(1 for p in semua if p["status"] == "menunggu")
            stats["ditolak"] = sum(1 for p in semua if p["status"] == "ditolak")
            stats["versi_cv"] = len(db.daftar_versi_cv(user_id))
            pencapaian_terbaru = semua[:5]
        elif peran == "verifikator":
            con = db.koneksi()
            try:
                stats["menunggu"] = con.execute("SELECT count(*) FROM pencapaian WHERE status='menunggu'").fetchone()[0]
                stats["disetujui"] = con.execute("SELECT count(*) FROM pencapaian WHERE status='disetujui'").fetchone()[0]
                stats["ditolak"] = con.execute("SELECT count(*) FROM pencapaian WHERE status='ditolak'").fetchone()[0]
            finally:
                con.close()

    return render_template(
        "beranda.html",
        profil=profil,
        stats=stats,
        pencapaian_terbaru=pencapaian_terbaru,
        ai_mode=ai_mode
    )


# -----------------------------------------------------------------------------
# Rute 2: Autentikasi (Login, Register, Logout)
# -----------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("beranda"))

    username_input = ""
    if request.method == "POST":
        username_input = request.form.get("username", "").strip()
        password_input = request.form.get("password", "")

        user = db.cek_login(username_input, password_input)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["peran"] = user["peran"]
            session["nama"] = user.get("nama") or user["username"]
            flash(f"Selamat datang kembali, {session['nama']}!", "success")

            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("beranda"))
        else:
            flash("Username atau password salah. Silakan coba lagi.", "error")

    return render_template("login.html", username=username_input)


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("beranda"))

    form_data = {}
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        username = request.form.get("username", "").strip()
        peran = request.form.get("peran", "").strip()
        password = request.form.get("password", "")
        konfirmasi = request.form.get("konfirmasi_password", "")

        form_data = {"nama": nama, "username": username, "peran": peran}

        if not nama or not username or not password:
            flash("Nama lengkap, username, dan password wajib diisi.", "error")
            return render_template("register.html", form_data=form_data)

        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            flash("Username hanya boleh terdiri dari huruf, angka, dan garis bawah (_).", "error")
            return render_template("register.html", form_data=form_data)

        if peran not in ("mahasiswa", "verifikator"):
            flash("Peran yang dipilih tidak valid.", "error")
            return render_template("register.html", form_data=form_data)

        if len(password) < 6:
            flash("Password minimal terdiri dari 6 karakter.", "error")
            return render_template("register.html", form_data=form_data)

        if password != konfirmasi:
            flash("Password dan konfirmasi password tidak cocok.", "error")
            return render_template("register.html", form_data=form_data)

        try:
            db.simpan_pengguna(username=username, password=password, peran=peran, nama=nama)
            db.cadangkan()
            flash("Pendaftaran akun berhasil! Silakan masuk dengan akun Anda.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            msg = str(e).lower()
            if "unique" in msg or "pengguna.username" in msg:
                flash(f"Username '{username}' sudah terdaftar. Silakan pilih username lain.", "error")
            else:
                flash("Terjadi kendala saat mendaftarkan akun. Silakan coba lagi.", "error")

    return render_template("register.html", form_data=form_data)


@app.route("/logout")
def logout():
    session.clear()
    flash("Anda telah berhasil keluar dari sistem.", "info")
    return redirect(url_for("login"))


# -----------------------------------------------------------------------------
# Rute 3: Profil Saya (Mahasiswa)
# -----------------------------------------------------------------------------
@app.route("/profil", methods=["GET", "POST"])
@mahasiswa_required
def profil():
    user_id = session["user_id"]

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        email = request.form.get("email", "").strip()
        telepon = request.form.get("telepon", "").strip()
        kota = request.form.get("kota", "").strip()
        linkedin = request.form.get("linkedin", "").strip()
        ringkasan = request.form.get("ringkasan", "").strip()

        if not nama:
            flash("Nama lengkap wajib diisi.", "error")
        else:
            db.perbarui_profil(
                user_id,
                nama=nama,
                email=email,
                telepon=telepon,
                kota=kota,
                linkedin=linkedin,
                ringkasan=ringkasan
            )
            db.cadangkan()
            session["nama"] = nama
            flash("Profil pribadi berhasil diperbarui.", "success")
            return redirect(url_for("profil"))

    pengguna = db.baca_pengguna(user_id) or {}
    return render_template("profil.html", pengguna=pengguna)


# -----------------------------------------------------------------------------
# Rute 4: Form Tambah Pencapaian & AI Fallback
# -----------------------------------------------------------------------------
@app.route("/pencapaian/tambah", methods=["GET", "POST"])
@mahasiswa_required
def tambah_pencapaian_page():
    form_data = {}
    if request.method == "POST":
        nama_kegiatan = request.form.get("nama_kegiatan", "").strip()
        penyelenggara = request.form.get("penyelenggara", "").strip()
        juara_input = request.form.get("juara", "").strip()
        peran_input = request.form.get("peran", "").strip()
        periode = request.form.get("periode", "").strip()
        lokasi = request.form.get("lokasi", "").strip()
        uraian = request.form.get("uraian", "").strip()

        # Gabungkan juara dan peran jika diisi (misal: "Juara 3 (Project Leader)")
        if juara_input and peran_input:
            peran = f"{juara_input} ({peran_input})"
        elif juara_input:
            peran = juara_input
        else:
            peran = peran_input

        form_data = {
            "nama_kegiatan": nama_kegiatan,
            "penyelenggara": penyelenggara,
            "juara": juara_input,
            "peran": peran,
            "periode": periode,
            "lokasi": lokasi,
            "uraian": uraian
        }

        # Validasi wajib: uraian tidak boleh kosong
        if not uraian:
            flash("Uraian kegiatan wajib diisi.", "error")
            return render_template("pencapaian_tambah.html", form_data=form_data)

        if not nama_kegiatan:
            flash("Nama kegiatan wajib diisi.", "error")
            return render_template("pencapaian_tambah.html", form_data=form_data)

        # 1. Simpan pencapaian faktual ke database
        user_id = session["user_id"]
        id_pencapaian = db.simpan_pencapaian(
            id_pengguna=user_id,
            nama_kegiatan=nama_kegiatan,
            uraian=uraian,
            penyelenggara=penyelenggara,
            peran=peran,
            periode=periode,
            lokasi=lokasi
        )

        # 2. Proses dengan AI (Fallback otomatis jika error/timeout)
        pakai_fallback = False
        hasil_ai = None
        try:
            if "CVKU_AI_MODE" in os.environ:
                ai_service.MODE = os.environ["CVKU_AI_MODE"]
            if "CVKU_AI_URL" in os.environ:
                ai_service.REMOTE_URL = os.environ["CVKU_AI_URL"]
            hasil_ai = ai_service.proses_pencapaian(form_data)
        except Exception as err:
            # Cetak penyebab error aslinya ke terminal untuk diagnosis
            print(f"[AI SERVICE ERROR] Gagal memanggil AI ({getattr(ai_service, 'MODE', 'unknown')}): {err}", flush=True)
            # Fallback otomatis ke stub tanpa menambah poin buatan sendiri
            hasil_ai = ai_service.proses_pencapaian(form_data, mode="stub")
            pakai_fallback = True

        # 3. Simpan hasil AI & catat log AI
        db.simpan_hasil_ai(
            id_pencapaian=id_pencapaian,
            nama_bagian=hasil_ai["bagian"],
            judul=hasil_ai["judul"],
            daftar_poin=hasil_ai["poin"]
        )
        db.catat_log_ai(
            id_pengguna=user_id,
            masukan=json.dumps(form_data, ensure_ascii=False),
            keluaran=json.dumps(hasil_ai, ensure_ascii=False),
            waktu_respons_ms=hasil_ai.get("waktu_ms", 0),
            versi_model=hasil_ai.get("versi_model", "stub")
        )
        db.cadangkan()

        # 4. Peringatan fallback dan arahkan ke halaman cek-sunting
        if pakai_fallback:
            flash("AI sedang tidak tersedia, memakai uraian Anda.", "warning")
        else:
            flash("Kegiatan berhasil diproses oleh AI. Silakan periksa dan sunting sebelum disimpan.", "info")

        return redirect(url_for("sunting_pencapaian_page", id=id_pencapaian, versi_model=hasil_ai.get("versi_model")))

    return render_template("pencapaian_tambah.html", form_data=form_data)


# -----------------------------------------------------------------------------
# Rute 5: Halaman Cek-Sunting Hasil AI
# -----------------------------------------------------------------------------
@app.route("/pencapaian/<int:id>/sunting", methods=["GET", "POST"])
@mahasiswa_required
def sunting_pencapaian_page(id):
    user_id = session["user_id"]
    pencapaian = db.baca_pencapaian(id)

    # Validasi kepemilikan
    if not pencapaian or pencapaian["id_pengguna"] != user_id:
        flash("Pencapaian tidak ditemukan atau Anda tidak memiliki akses.", "error")
        return redirect(url_for("daftar_pencapaian_page"))

    if request.method == "POST":
        bagian = request.form.get("bagian", "").strip()
        judul = request.form.get("judul", "").strip()
        poin_list = request.form.getlist("poin[]")

        # Bersihkan poin kosong
        daftar_poin = [p.strip() for p in poin_list if p.strip()]

        if not judul:
            flash("Judul entri CV wajib diisi.", "error")
            return redirect(url_for("sunting_pencapaian_page", id=id))

        if not daftar_poin:
            flash("Minimal harus ada satu poin pencapaian pada CV.", "error")
            return redirect(url_for("sunting_pencapaian_page", id=id))

        if bagian not in skema.BAGIAN:
            bagian = "Lainnya"

        # Simpan kembali hasil sunting
        db.simpan_hasil_ai(id, bagian, judul, daftar_poin)

        # Perbarui juara / peran pada pencapaian jika diedit
        peran_baru = request.form.get("peran", "").strip()
        con = db.koneksi()
        try:
            con.execute("UPDATE pencapaian SET peran = ? WHERE id = ?", (peran_baru, id))
            con.commit()
        finally:
            con.close()

        # Ubah status sesuai konfigurasi AUTO_APPROVE
        if AUTO_APPROVE:
            db.ubah_status_pencapaian(id, "disetujui")
            flash("Pencapaian berhasil disimpan dan langsung disetujui untuk masuk ke CV!", "success")
        else:
            db.ubah_status_pencapaian(id, "menunggu")
            flash("Pencapaian berhasil disimpan dan menunggu verifikasi verifikator kampus.", "success")

        db.cadangkan()
        return redirect(url_for("daftar_pencapaian_page"))

    entri = db.baca_entri(id)
    versi_model = request.args.get("versi_model")
    if not versi_model:
        con = db.koneksi()
        try:
            r = con.execute(
                "SELECT versi_model FROM log_ai WHERE id_pengguna=? ORDER BY id DESC LIMIT 1",
                (user_id,)
            ).fetchone()
            if r and r["versi_model"]:
                versi_model = r["versi_model"]
        finally:
            con.close()
    if not versi_model:
        mode_saat_ini = os.environ.get("CVKU_AI_MODE", getattr(ai_service, "MODE", "stub"))
        versi_model = getattr(ai_service, "VERSI_MODEL", {}).get(mode_saat_ini, "stub-v1")

    return render_template(
        "pencapaian_sunting.html",
        pencapaian=pencapaian,
        entri=entri,
        bagian_pilihan=skema.BAGIAN,
        versi_model=versi_model
    )


# -----------------------------------------------------------------------------
# Rute 6: Daftar Pencapaian & Hapus
# -----------------------------------------------------------------------------
@app.route("/pencapaian")
@mahasiswa_required
def daftar_pencapaian_page():
    user_id = session["user_id"]
    daftar = db.daftar_pencapaian(user_id)
    return render_template("pencapaian_daftar.html", daftar=daftar)


@app.route("/pencapaian/<int:id>/hapus", methods=["POST"])
@mahasiswa_required
def hapus_pencapaian_action(id):
    user_id = session["user_id"]
    pencapaian = db.baca_pencapaian(id)

    if not pencapaian or pencapaian["id_pengguna"] != user_id:
        flash("Pencapaian tidak ditemukan atau Anda tidak memiliki akses.", "error")
    else:
        db.hapus_pencapaian(id)
        db.cadangkan()
        flash(f"Pencapaian '{pencapaian['nama_kegiatan']}' berhasil dihapus.", "success")

    return redirect(url_for("daftar_pencapaian_page"))


# -----------------------------------------------------------------------------
# Rute 7: Buat CV, Pratinjau, & Unduh DOCX ATS-Friendly
# -----------------------------------------------------------------------------
@app.route("/cv")
@mahasiswa_required
def cv_preview_page():
    user_id = session["user_id"]
    profil = db.baca_pengguna(user_id) or {}
    cv = db.baca_cv_pengguna(user_id, hanya_disetujui=True)

    cv_ada = any(len(items) > 0 for items in cv.values())
    return render_template(
        "cv_preview.html",
        profil=profil,
        cv=cv,
        urutan_bagian=skema.BAGIAN,
        cv_ada=cv_ada
    )


@app.route("/cv/unduh")
@mahasiswa_required
def unduh_cv_action():
    user_id = session["user_id"]
    profil = db.baca_pengguna(user_id) or {}
    cv = db.baca_cv_pengguna(user_id, hanya_disetujui=True)

    # Buat nama berkas timestamp unik
    nama_mentah = profil.get("nama") or session.get("username") or "Mahasiswa"
    nama_bersih = re.sub(r"[^a-zA-Z0-9_]", "_", nama_mentah)
    waktu_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nama_file = f"CV_{nama_bersih}_{waktu_str}.docx"
    filepath = os.path.join(RIWAYAT_DIR, nama_file)

    # Buat berkas DOCX ATS-friendly
    buat_file_docx(profil, cv, filepath)

    # Catat versi CV ke database
    db.simpan_versi_cv(user_id, nama_file)
    db.cadangkan()

    return send_file(
        filepath,
        as_attachment=True,
        download_name=nama_file,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


# -----------------------------------------------------------------------------
# Rute 8: Riwayat CV & Unduh Ulang
# -----------------------------------------------------------------------------
@app.route("/cv/riwayat")
@mahasiswa_required
def cv_riwayat_page():
    user_id = session["user_id"]
    versi_list = db.daftar_versi_cv(user_id)
    return render_template("cv_riwayat.html", versi_list=versi_list)


@app.route("/cv/riwayat/<int:id>/unduh")
@mahasiswa_required
def unduh_ulang_cv_action(id):
    user_id = session["user_id"]
    con = db.koneksi()
    try:
        versi = con.execute("SELECT * FROM versi_cv WHERE id=? AND id_pengguna=?", (id, user_id)).fetchone()
    finally:
        con.close()

    if not versi:
        flash("Versi dokumen CV tidak ditemukan.", "error")
        return redirect(url_for("cv_riwayat_page"))

    filepath = os.path.join(RIWAYAT_DIR, versi["nama_file"])
    if not os.path.exists(filepath):
        flash("Berkas fisik dokumen tidak ditemukan di server.", "error")
        return redirect(url_for("cv_riwayat_page"))

    return send_file(
        filepath,
        as_attachment=True,
        download_name=versi["nama_file"],
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


# -----------------------------------------------------------------------------
# Rute 9 (Prioritas 2): Halaman Verifikator
# -----------------------------------------------------------------------------
@app.route("/verifikator")
@verifikator_required
def verifikator_page():
    con = db.koneksi()
    try:
        # Ambil pencapaian berstatus 'menunggu' dari semua mahasiswa
        sql = (
            "SELECT p.*, u.nama AS nama_mahasiswa, u.username, b.nama AS bagian "
            "FROM pencapaian p "
            "JOIN pengguna u ON u.id = p.id_pengguna "
            "LEFT JOIN entri_cv e ON e.id_pencapaian = p.id "
            "LEFT JOIN bagian_cv b ON b.id = e.id_bagian "
            "WHERE p.status = 'menunggu' ORDER BY p.id DESC"
        )
        antrean = [dict(r) for r in con.execute(sql).fetchall()]
        for a in antrean:
            a["entri"] = db.baca_entri(a["id"])

        # Riwayat verifikasi terbaru oleh verifikator ini
        sql_riwayat = (
            "SELECT v.*, p.nama_kegiatan, u.nama AS nama_mahasiswa, u.username "
            "FROM verifikasi v "
            "JOIN pencapaian p ON p.id = v.id_pencapaian "
            "JOIN pengguna u ON u.id = p.id_pengguna "
            "WHERE v.id_verifikator = ? ORDER BY v.id DESC LIMIT 15"
        )
        riwayat_terverifikasi = [dict(r) for r in con.execute(sql_riwayat, (session["user_id"],)).fetchall()]
    finally:
        con.close()

    return render_template(
        "verifikator.html",
        antrean=antrean,
        riwayat_terverifikasi=riwayat_terverifikasi
    )


@app.route("/verifikator/<int:id>/verifikasi", methods=["POST"])
@verifikator_required
def verifikasi_action(id):
    status = request.form.get("status", "").strip()
    catatan = request.form.get("catatan", "").strip() or None

    if status not in ("disetujui", "ditolak"):
        flash("Keputusan status verifikasi tidak valid.", "error")
        return redirect(url_for("verifikator_page"))

    id_verifikator = session["user_id"]
    db.simpan_verifikasi(id, id_verifikator, status, catatan=catatan)
    db.cadangkan()

    status_teks = "disetujui untuk masuk ke CV" if status == "disetujui" else "ditolak"
    flash(f"Pencapaian berhasil diverifikasi dan {status_teks}.", "success")
    return redirect(url_for("verifikator_page"))


# -----------------------------------------------------------------------------
# Penanganan Error Ramah Pengguna (Bukan Stack Trace)
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    flash("Halaman yang Anda tuju tidak ditemukan (Error 404).", "error")
    return redirect(url_for("beranda"))


@app.errorhandler(500)
def internal_server_error(error):
    flash("Terjadi kendala pada sistem server (Error 500). Silakan coba lagi.", "error")
    return redirect(url_for("beranda"))


# -----------------------------------------------------------------------------
# Titik Masuk Aplikasi
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"Menjalankan server web CVku pada http://127.0.0.1:{port}")
    print(f"Mode AI: {os.environ.get('CVKU_AI_MODE', 'stub')}")
    print(f"AUTO_APPROVE: {AUTO_APPROVE}")
    app.run(host="127.0.0.1", port=port, debug=False)
