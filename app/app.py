"""CVKu - Generator CV ATS-Friendly (Qwen + LoRA + Gradio). Sisi aplikasi: Reva.

Jalankan (Colab): !pip -q install gradio python-docx  ->  !python app.py
Mode model:
  - Jika ada model_qwen.py (dari Sharen) yang punya proses_pencapaian(form)->dict, dipakai otomatis.
  - Jika tidak ada, dipakai STUB (hasil contoh) agar aplikasi tetap bisa diuji.
"""
import json, os, datetime
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from skema import BAGIAN, FIELD_FORM

BASE = os.environ.get("CVKU_DIR", os.path.dirname(os.path.abspath(__file__)))
F_PROFIL = os.path.join(BASE, "profil.json")
F_CV = os.path.join(BASE, "cv_user.json")
D_RIWAYAT = os.path.join(BASE, "riwayat_cv")
os.makedirs(D_RIWAYAT, exist_ok=True)

PROFIL_KOSONG = {"nama": "", "email": "", "telepon": "", "kota": "", "linkedin": "", "ringkasan": ""}


# ---------------------------------------------------------------- penyimpanan
def _baca(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _tulis(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def muat_profil():
    return {**PROFIL_KOSONG, **_baca(F_PROFIL, {})}


def muat_cv():
    return _baca(F_CV, [])


# ---------------------------------------------------------------- model / stub
def proses_stub(form: dict) -> dict:
    """Pengganti sementara model. Mengikuti skema keluaran yang disepakati."""
    peran, nama = form.get("peran", "").strip(), form.get("nama_kegiatan", "").strip()
    return {"bagian": "Pengalaman Organisasi",
            "judul": f"{peran} - {nama}" if peran else nama,
            "poin": [f"[STUB] Melaksanakan peran {peran or 'peserta'} pada kegiatan {nama}",
                     "[STUB] " + form.get("uraian", "").strip()[:120]]}


try:
    from model_qwen import proses_pencapaian as _proses_model  # dari Sharen
    MODE = "MODEL QWEN + LoRA"
except Exception:
    _proses_model, MODE = None, "STUB (model belum tersambung)"


def proses_pencapaian(form: dict) -> dict:
    if _proses_model is not None:
        try:
            return _proses_model(form)
        except Exception as e:  # model gagal -> jangan matikan aplikasi
            print("Model error, pakai stub:", e)
    return proses_stub(form)


# ---------------------------------------------------------------- merge ke CV
def merge_ke_cv(form: dict, hasil: dict) -> dict:
    """Fakta (periode, penyelenggara, lokasi) selalu dari FORM, bukan dari AI."""
    return {"bagian": hasil["bagian"] if hasil["bagian"] in BAGIAN else "Lainnya",
            "judul": hasil["judul"].strip(),
            "poin": [p.strip() for p in hasil["poin"] if p.strip()],
            "periode": form.get("periode", "").strip(),
            "penyelenggara": form.get("penyelenggara", "").strip(),
            "lokasi": form.get("lokasi", "").strip()}


def simpan_entri(entri: dict):
    cv = muat_cv()
    cv.append(entri)
    _tulis(F_CV, cv)
    return cv


# ---------------------------------------------------------------- DOCX (ATS)
def buat_docx(profil: dict, cv: list, path: str):
    """Satu kolom, heading standar, tanpa tabel/gambar/kotak teks, font Calibri."""
    doc = Document()
    sec = doc.sections[0]
    sec.left_margin = sec.right_margin = Cm(2)
    sec.top_margin = sec.bottom_margin = Cm(1.8)
    st = doc.styles["Normal"]
    st.font.name, st.font.size = "Calibri", Pt(11)
    st.paragraph_format.space_after = Pt(2)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(profil.get("nama") or "Nama Lengkap"); r.bold = True; r.font.size = Pt(18)
    kontak = " | ".join(x for x in [profil.get("email"), profil.get("telepon"),
                                    profil.get("kota"), profil.get("linkedin")] if x)
    if kontak:
        p = doc.add_paragraph(kontak); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if profil.get("ringkasan"):
        doc.add_heading("Ringkasan Profil", level=1)
        doc.add_paragraph(profil["ringkasan"])

    for bag in BAGIAN:
        items = [e for e in cv if e["bagian"] == bag]
        if not items:
            continue
        doc.add_heading(bag, level=1)
        for e in items:
            p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(6)
            p.add_run(e["judul"]).bold = True
            info = ", ".join(x for x in [e.get("penyelenggara"), e.get("lokasi")] if x)
            if e.get("periode"):
                info = (info + " | " if info else "") + e["periode"]
            if info:
                doc.add_paragraph(info).runs[0].italic = True
            for pt in e["poin"]:
                doc.add_paragraph(pt, style="List Bullet")
    doc.save(path)


def daftar_riwayat():
    fs = sorted([f for f in os.listdir(D_RIWAYAT) if f.endswith(".docx")], reverse=True)
    return [os.path.join(D_RIWAYAT, f) for f in fs]


# ---------------------------------------------------------------- UI
def ringkasan_beranda():
    profil, cv = muat_profil(), muat_cv()
    baris = [f"## Halo, {profil['nama'] or 'Mahasiswa'}!",
             f"Mode AI: **{MODE}**", "",
             f"- Profil terisi: **{'Ya' if profil['nama'] else 'Belum'}**",
             f"- Total entri CV: **{len(cv)}**",
             f"- Versi CV tersimpan: **{len(daftar_riwayat())}**", ""]
    for b in BAGIAN:
        n = sum(1 for e in cv if e["bagian"] == b)
        if n:
            baris.append(f"- {b}: {n}")
    baris += ["", "**Langkah:** isi *Profil Saya* → tambah di *Tambah Pencapaian* → "
              "cek hasil AI → unduh CV."]
    return "\n".join(baris)


def buat_ui():
    import gradio as gr

    def simpan_profil(nama, email, telepon, kota, linkedin, ringkasan):
        if not nama.strip():
            return "Nama wajib diisi."
        _tulis(F_PROFIL, dict(nama=nama.strip(), email=email.strip(), telepon=telepon.strip(),
                              kota=kota.strip(), linkedin=linkedin.strip(), ringkasan=ringkasan.strip()))
        return "Profil tersimpan."

    def jalankan_ai(*nilai):
        form = dict(zip(FIELD_FORM, nilai))
        if not form["nama_kegiatan"].strip() or not form["uraian"].strip():
            return (gr.update(),) * 3 + ({}, "Nama kegiatan dan uraian wajib diisi.")
        h = merge_ke_cv(form, proses_pencapaian(form))
        return (gr.update(value=h["bagian"]), h["judul"], "\n".join(h["poin"]), form,
                "Hasil AI siap. Silakan cek dan sunting, lalu klik **Konfirmasi & Simpan ke CV**.")

    def konfirmasi(bagian, judul, poin_teks, form):
        if not form:
            return "Jalankan AI dulu."
        if not judul.strip() or not poin_teks.strip():
            return "Judul dan poin tidak boleh kosong."
        entri = merge_ke_cv(form, {"bagian": bagian, "judul": judul,
                                   "poin": poin_teks.splitlines()})
        n = len(simpan_entri(entri))
        return f"Tersimpan ke CV. Total entri: {n}."

    def unduh():
        cv = muat_cv()
        if not cv:
            return None, "CV masih kosong. Tambahkan pencapaian dulu."
        nama = datetime.datetime.now().strftime("CV_%Y%m%d_%H%M%S.docx")
        path = os.path.join(D_RIWAYAT, nama)
        buat_docx(muat_profil(), cv, path)
        return path, f"CV dibuat: {nama} (tersimpan di Riwayat CV)."

    def hapus_entri(nomor):
        cv = muat_cv()
        i = int(nomor) - 1
        if 0 <= i < len(cv):
            cv.pop(i); _tulis(F_CV, cv)
            return daftar_entri(), "Entri dihapus."
        return daftar_entri(), "Nomor tidak valid."

    def daftar_entri():
        cv = muat_cv()
        return "\n".join(f"{i+1}. [{e['bagian']}] {e['judul']}" for i, e in enumerate(cv)) or "(kosong)"

    p0 = muat_profil()
    with gr.Blocks(title="CVKu - Generator CV ATS") as demo:
        gr.Markdown("# CVKu — Generator CV ATS-Friendly\nQwen + LoRA untuk menulis poin CV.")
        with gr.Tab("Beranda") as t_home:
            beranda = gr.Markdown(ringkasan_beranda())
            gr.Button("Segarkan").click(ringkasan_beranda, outputs=beranda)
        with gr.Tab("Profil Saya"):
            pf = [gr.Textbox(label=l, value=p0[k], lines=3 if k == "ringkasan" else 1)
                  for k, l in [("nama", "Nama lengkap *"), ("email", "Email"), ("telepon", "Telepon"),
                               ("kota", "Kota"), ("linkedin", "LinkedIn / Portofolio"),
                               ("ringkasan", "Ringkasan profil (opsional)")]]
            st_p = gr.Markdown()
            gr.Button("Simpan Profil", variant="primary").click(simpan_profil, pf, st_p)
        with gr.Tab("Tambah Pencapaian"):
            gr.Markdown("**1. Isi form**")
            f_in = [gr.Textbox(label="Nama kegiatan *"), gr.Textbox(label="Penyelenggara"),
                    gr.Textbox(label="Peran"), gr.Textbox(label="Periode (mis. Maret 2024 - Juni 2024)"),
                    gr.Textbox(label="Lokasi"),
                    gr.Textbox(label="Uraian singkat *", lines=4,
                               placeholder="Tulis apa adanya, boleh bahasa santai. Jangan lupa angka yang benar-benar ada.")]
            btn_ai = gr.Button("Proses dengan AI", variant="primary")
            gr.Markdown("**2. Cek dan sunting hasil AI** (periode, penyelenggara, lokasi diambil dari form)")
            o_bag = gr.Dropdown(BAGIAN, label="Bagian CV")
            o_jud = gr.Textbox(label="Judul entri")
            o_poin = gr.Textbox(label="Poin CV (satu poin per baris)", lines=5)
            st_form = gr.State({})
            st_a = gr.Markdown()
            btn_ok = gr.Button("Konfirmasi & Simpan ke CV", variant="primary")
            btn_ai.click(jalankan_ai, f_in, [o_bag, o_jud, o_poin, st_form, st_a])
            btn_ok.click(konfirmasi, [o_bag, o_jud, o_poin, st_form], st_a)
        with gr.Tab("CV Saya & Unduh"):
            daft = gr.Textbox(label="Entri CV saat ini", value=daftar_entri(), lines=8, interactive=False)
            gr.Button("Segarkan daftar").click(daftar_entri, outputs=daft)
            no = gr.Number(label="Nomor entri yang ingin dihapus", precision=0)
            st_h = gr.Markdown()
            gr.Button("Hapus entri").click(hapus_entri, no, [daft, st_h])
            file_cv = gr.File(label="Unduh CV (DOCX)")
            gr.Button("Buat & Unduh CV (DOCX)", variant="primary").click(unduh, outputs=[file_cv, st_h])
        with gr.Tab("Riwayat CV") as t_riw:
            riw = gr.File(label="Versi CV tersimpan", file_count="multiple", value=daftar_riwayat())
            gr.Button("Segarkan").click(daftar_riwayat, outputs=riw)
        t_home.select(ringkasan_beranda, outputs=beranda)
        t_riw.select(daftar_riwayat, outputs=riw)
    return demo


if __name__ == "__main__":
    buat_ui().launch(share=True)
