"""Skema bersama Reva (aplikasi) dan Sharen (model). Prompt untuk fine-tuning dan inference HARUS sama."""
import json, re

BAGIAN = ["Pendidikan", "Pengalaman Organisasi", "Magang", "Proyek",
          "Sertifikasi", "Penghargaan", "Lainnya"]
FIELD_FORM = ["nama_kegiatan", "penyelenggara", "peran", "periode", "lokasi", "uraian"]

SYSTEM_PROMPT = (
    "Kamu asisten penyusun CV ATS-friendly untuk mahasiswa. Dari data kegiatan, "
    "keluarkan HANYA JSON dengan kunci: bagian, judul, poin. "
    "bagian salah satu dari: " + ", ".join(BAGIAN) + ". "
    "poin berisi 1-3 kalimat CV ringkas diawali kata kerja, berorientasi hasil. "
    "Jangan mengarang angka atau pencapaian yang tidak ada di uraian."
)


def susun_prompt(form: dict) -> str:
    """Isi form -> teks user untuk model (dipakai identik saat training & inference)."""
    return "\n".join(f"{k}: {str(form.get(k, '')).strip()}" for k in FIELD_FORM)


def pesan_chat(form: dict) -> list:
    return [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": susun_prompt(form)}]


def parse_hasil(teks: str):
    """Ambil JSON dari keluaran model. Return (dict_valid | None, bool_json_valid)."""
    m = re.search(r"\{.*\}", teks, re.S)
    if not m:
        return None, False
    try:
        d = json.loads(m.group(0))
        poin = d.get("poin", [])
        if isinstance(poin, str):
            poin = [poin]
        hasil = {"bagian": d.get("bagian", "Lainnya"),
                 "judul": str(d.get("judul", "")).strip(),
                 "poin": [str(p).strip() for p in poin if str(p).strip()]}
        if hasil["bagian"] not in BAGIAN:
            hasil["bagian"] = "Lainnya"
        return hasil, True
    except Exception:
        return None, False
