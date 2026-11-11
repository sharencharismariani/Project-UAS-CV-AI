"""ai_service.py - jembatan SI ke model AI. Mode: stub | local | remote."""
import os, json, time

MODE = os.environ.get("CVKU_AI_MODE", "stub")          # stub | local | remote
REMOTE_URL = os.environ.get("CVKU_AI_URL", "")           # dipakai mode remote
VERSI_MODEL = {"stub": "stub-v1", "local": "qwen-50data", "remote": "qwen-50data-remote"}

BAGIAN_VALID = ["Pendidikan", "Pengalaman Organisasi", "Magang", "Proyek",
                "Sertifikasi", "Penghargaan", "Lainnya"]


def _stub(data):
    """Hasil dummy dengan format sama seperti AI asli."""
    teks = f"{data.get('nama_kegiatan', '')} {data.get('uraian', '')}".lower()
    if any(k in teks for k in ("juara", "lomba", "beasiswa", "penghargaan")):
        bagian = "Penghargaan"
    elif any(k in teks for k in ("magang", "intern")):
        bagian = "Magang"
    elif any(k in teks for k in ("proyek", "project", "aplikasi")):
        bagian = "Proyek"
    elif any(k in teks for k in ("sertifikat", "kursus", "pelatihan")):
        bagian = "Sertifikasi"
    elif any(k in teks for k in ("organisasi", "himpunan", "ketua", "panitia")):
        bagian = "Pengalaman Organisasi"
    else:
        bagian = "Lainnya"
    uraian = (data.get("uraian") or "").strip()
    # pecah uraian user jadi kalimat; TIDAK ada kalimat template buatan sistem
    kalimat = [k.strip() for k in re.split(r"(?<=[.!?])\s+|\n+", uraian) if k.strip()]
    return {
        "bagian": bagian,
        "judul": data.get("nama_kegiatan", "Tanpa judul"),
        "poin": kalimat[:3] or [uraian or data.get("nama_kegiatan", "Tanpa judul")],
    }


def _local(data):
    """Panggil model_qwen.py di runtime yang sama (butuh GPU). Sesuaikan nama fungsinya."""
    import model_qwen                                    # <- sesuaikan
    return model_qwen.proses_pencapaian(data)                     # <- sesuaikan, harus return dict/JSON string


def _remote(data):
    """Panggil colab/server lain lewat HTTP."""
    import requests
    r = requests.post(REMOTE_URL, json=data, timeout=120)
    r.raise_for_status()
    return r.json()


def _normalisasi(hasil):
    """Pastikan output selalu {bagian, judul, poin[list str]} yang valid."""
    if isinstance(hasil, str):
        hasil = json.loads(hasil)
    bagian = hasil.get("bagian", "Lainnya")
    if bagian not in BAGIAN_VALID:
        bagian = "Lainnya"
    poin = [str(p).strip() for p in hasil.get("poin", []) if str(p).strip()]
    if not poin:
        raise ValueError("AI tidak menghasilkan poin")
    return {"bagian": bagian, "judul": str(hasil.get("judul", "")).strip() or "Tanpa judul", "poin": poin}


def proses_pencapaian(data, mode=None):
    """
    INPUT : dict {nama_kegiatan, uraian, penyelenggara, peran, periode, lokasi}
    OUTPUT: dict {bagian, judul, poin, versi_model, waktu_ms}
    """
    mode = mode or MODE
    t0 = time.time()
    fungsi = {"stub": _stub, "local": _local, "remote": _remote}[mode]
    hasil = _normalisasi(fungsi(data))
    hasil["versi_model"] = VERSI_MODEL[mode]
    hasil["waktu_ms"] = int((time.time() - t0) * 1000)
    return hasil
