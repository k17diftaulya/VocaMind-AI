"""
entity_extractor.py
Mengekstrak entitas dari teks hasil speech-to-text:
- tanggal & waktu (pakai library dateparser, mendukung ID & EN)
- kata kunci urgensi (penting, mendesak, urgent, asap, dll)
- judul/topik (teks setelah keyword konteks dibuang)
"""

import re
import dateparser
from dateparser.search import search_dates

URGENCY_KEYWORDS = [
    "penting", "mendesak", "segera", "urgent", "asap", "darurat",
    "prioritas tinggi", "high priority", "critical", "kritis",
]

# Kata-kata yang sering muncul tapi bukan bagian dari judul tugas
STOPWORD_TRIM = [
    "tolong", "please", "bisa", "bisakah", "saya", "aku", "gue", "i", "am",
    "want", "to", "mau", "ingin", "buatkan", "buat", "catat", "catatkan",
    "tambahkan", "tambah", "add", "create", "remind", "ingatkan", "note",
]


def extract_datetime(text):
    """
    Cari tanggal/waktu di dalam teks. Mengembalikan objek datetime atau None.
    Menggunakan dateparser dengan setting PREFER_DATES_FROM_FUTURE karena
    konteks kita adalah jadwal/deadline yang biasanya di masa depan.
    """
    settings = {
        "PREFER_DATES_FROM": "future",
        "RETURN_AS_TIMEZONE_AWARE": False,
    }
    results = search_dates(
        text, languages=["id", "en"], settings=settings
    )
    if not results:
        return None, None
    # Ambil hasil pertama yang valid (biasanya yang paling relevan)
    matched_text, dt = results[0]
    return dt, matched_text


def extract_urgency(text):
    """Deteksi apakah teks mengandung kata-kata urgensi tinggi."""
    lower = text.lower()
    for kw in URGENCY_KEYWORDS:
        if kw in lower:
            return "tinggi"
    return "normal"


def extract_duration_minutes(text):
    """
    Coba deteksi estimasi durasi kegiatan, misal: '2 jam', '30 menit', '1 hour'.
    Mengembalikan menit (int) atau None jika tidak ditemukan.
    """
    lower = text.lower()

    match_jam = re.search(r"(\d+(?:[.,]\d+)?)\s*(jam|hour|hours|hr)", lower)
    if match_jam:
        val = float(match_jam.group(1).replace(",", "."))
        return int(val * 60)

    match_menit = re.search(r"(\d+)\s*(menit|minute|minutes|min)", lower)
    if match_menit:
        return int(match_menit.group(1))

    return None


def clean_title(text, matched_date_text=None, category_keywords=None):
    """
    Bersihkan teks mentah menjadi judul tugas/jadwal yang lebih ringkas:
    - hapus bagian teks yang cocok dengan tanggal (matched_date_text)
    - hapus keyword kategori yang men-trigger klasifikasi (mis. 'tugas', 'deadline')
    - hapus stopword umum
    """
    cleaned = text

    if matched_date_text:
        cleaned = cleaned.replace(matched_date_text, " ")

    if category_keywords:
        for kw in category_keywords:
            cleaned = re.sub(re.escape(kw), " ", cleaned, flags=re.IGNORECASE)

    words = cleaned.split()
    words = [w for w in words if w.lower().strip(",.!?") not in STOPWORD_TRIM]
    cleaned = " ".join(words).strip(" ,.-")

    # Kapitalisasi awal kalimat
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]

    return cleaned if cleaned else text.strip()
