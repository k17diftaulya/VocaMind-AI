"""
data_store.py
Modul penyimpanan data sederhana berbasis JSON.
Menyimpan: schedules, todos, notes, study_plan
"""

import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "assistant_data.json")

DEFAULT_DATA = {
    "schedules": [],   # {id, title, start, end, category, source_text}
    "todos": [],        # {id, title, deadline, priority_score, urgency, done, category, source_text}
    "notes": [],         # {id, text, created_at}
    "study_plan": []      # {id, related_task_id, session_date, duration_minutes, note}
}


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_data():
    """Load seluruh data dari file JSON. Jika belum ada, buat default."""
    _ensure_data_dir()
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return json.loads(json.dumps(DEFAULT_DATA))

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        save_data(DEFAULT_DATA)
        return json.loads(json.dumps(DEFAULT_DATA))


def save_data(data):
    """Simpan seluruh data ke file JSON."""
    _ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def next_id(items):
    """Ambil ID berikutnya (auto increment sederhana)."""
    if not items:
        return 1
    return max(item.get("id", 0) for item in items) + 1


def now_iso():
    return datetime.now().isoformat(timespec="seconds")
