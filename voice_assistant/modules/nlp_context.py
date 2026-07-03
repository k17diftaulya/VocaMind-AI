"""
nlp_context.py
Modul klasifikasi konteks berbasis keyword matching (rule-based).
Mendeteksi apakah ucapan pengguna berkaitan dengan:
- jadwal (schedule)
- deadline
- tugas (task)
- ujian (exam)
- catatan (note)
- organisasi (organization/event)

Mendukung campuran kata Bahasa Indonesia & Inggris.
"""

# Setiap kategori punya daftar keyword ID + EN.
# Urutan CATEGORY_KEYWORDS penting -> dipakai sebagai prioritas jika
# beberapa kategori match sekaligus (mis. "deadline tugas" -> deadline menang
# karena deadline lebih spesifik untuk penentuan prioritas).
CATEGORY_KEYWORDS = {
    "deadline": [
        "deadline", "batas waktu", "tenggat", "jatuh tempo", "due date", "due",
    ],
    "ujian": [
        "ujian", "exam", "tes", "test", "quiz", "kuis", "uas", "uts", "ulangan",
    ],
    "tugas": [
        "tugas", "task", "pr", "pekerjaan rumah", "assignment", "homework",
        "kerjakan", "mengerjakan",
    ],
    "jadwal": [
        "jadwal", "schedule", "agenda", "meeting", "rapat", "kelas", "class",
        "kuliah", "pertemuan", "appointment", "janji",
    ],
    "organisasi": [
        "organisasi", "organization", "acara", "event", "kepanitiaan",
        "rapat organisasi", "himpunan", "ukm", "komunitas",
    ],
    "catatan": [
        "catatan", "note", "catat", "notes", "ingatkan aku", "reminder",
        "ingat", "remember",
    ],
}

# Kategori yang dianggap "actionable" untuk to-do / schedule generator
TASK_LIKE_CATEGORIES = {"tugas", "deadline", "ujian", "jadwal", "organisasi"}


def detect_context(text):
    """
    Deteksi kategori dari teks.
    Mengembalikan tuple (kategori, matched_keywords)
    Jika tidak ada yang cocok, kategori = 'catatan' (fallback default),
    karena kalau tidak jelas maksudnya, paling aman disimpan sebagai catatan.
    """
    lower = text.lower()
    matches = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        found = [kw for kw in keywords if kw in lower]
        if found:
            matches[category] = found

    if not matches:
        return "catatan", []

    # Prioritas berdasarkan urutan dict CATEGORY_KEYWORDS di atas
    for category in CATEGORY_KEYWORDS:
        if category in matches:
            return category, matches[category]

    # fallback (seharusnya tidak pernah sampai sini)
    first_cat = next(iter(matches))
    return first_cat, matches[first_cat]


def is_task_like(category):
    return category in TASK_LIKE_CATEGORIES
