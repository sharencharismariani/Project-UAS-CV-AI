"""model_qwen.py - sisi AI (Sharen). Versi 2 + perbaikan pencocokan angka (himpunan angka utuh)."""
import os, re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

from skema import pesan_chat, parse_hasil, BAGIAN

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER_DIR = os.environ.get("CVKU_ADAPTER", "/content/drive/MyDrive/UTS_AI_CV/model/adapter_run1")

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_DTYPE = torch.float16 if _DEVICE == "cuda" else torch.float32

print(f"[model_qwen] memuat {MODEL_NAME} + adapter di {_DEVICE} ...")
_tok = AutoTokenizer.from_pretrained(MODEL_NAME)
_base = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=_DTYPE)
_model = PeftModel.from_pretrained(_base, ADAPTER_DIR).to(_DEVICE).eval()
print("[model_qwen] siap")

_STOP = {"yang", "dan", "dengan", "untuk", "pada", "dalam", "dari", "atau", "agar", "serta", "oleh",
         "kepada", "sebagai", "hingga", "tersebut", "secara", "dapat", "akan", "telah", "adalah", "ini", "itu"}


def _kata(teks):
    return {w for w in re.findall(r"[a-z0-9]+", teks.lower()) if len(w) > 3 and w not in _STOP}


def _cocok(w, sumber):
    return any(w == s or (len(w) >= 6 and len(s) >= 6 and w[:6] == s[:6]) for s in sumber)


def _berdasar(poin, sumber_kata, sumber_teks):
    """Poin berdasar jika semua angkanya ada di form (sebagai angka utuh) dan minimal separuh kata isinya muncul di form."""
    angka_form = set(re.findall(r"\d+", sumber_teks))
    if any(a not in angka_form for a in re.findall(r"\d+", poin)):
        return False
    kata = _kata(poin)
    return True if not kata else sum(_cocok(w, sumber_kata) for w in kata) / len(kata) >= 0.5


def _generate(form):
    teks = _tok.apply_chat_template(pesan_chat(form), tokenize=False, add_generation_prompt=True)
    inputs = _tok(teks, return_tensors="pt").to(_model.device)
    with torch.no_grad():
        out = _model.generate(**inputs, max_new_tokens=250, do_sample=False)
    return _tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)


def proses_pencapaian(form: dict) -> dict:
    mentah = _generate(form)
    hasil, valid = parse_hasil(mentah)
    if not (valid and isinstance(hasil, dict)):
        raise ValueError("Keluaran model bukan JSON valid: " + mentah[:200])

    poin = hasil.get("poin", [])
    if isinstance(poin, str):
        poin = [poin]
    poin = [str(p).strip() for p in poin if str(p).strip()]

    sumber_teks = " ".join(str(v) for v in form.values()).lower()
    sumber_kata = _kata(sumber_teks)
    uraian = form.get("uraian", "").strip()
    n_kata = len(uraian.split())
    batas = 1 if n_kata < 8 else 2 if n_kata < 20 else 3

    terpakai = [p for p in poin if _berdasar(p, sumber_kata, sumber_teks)]
    poin = (terpakai or [uraian])[:batas]

    bagian = hasil.get("bagian")
    return {
        "bagian": bagian if bagian in BAGIAN else "Lainnya",
        "judul": str(hasil.get("judul", "")).strip() or form.get("nama_kegiatan", "").strip(),
        "poin": poin,
    }
