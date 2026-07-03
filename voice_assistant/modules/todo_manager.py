"""
todo_manager.py
Smart To-Do List Generator:
- Menambahkan tugas baru dengan deadline (opsional)
- Menghitung skor prioritas berdasarkan:
    a) seberapa dekat deadline (semakin dekat = semakin prioritas)
    b) tingkat urgensi dari kata kunci ("penting", "urgent", dll)
    c) kategori (ujian/deadline dianggap lebih kritis daripada catatan biasa)
"""

from datetime import datetime
from . import data_store

# Bobot kategori: semakin tinggi, semakin dianggap kritis
CATEGORY_WEIGHT = {
    "ujian": 1.3,
    "deadline": 1.25,
    "tugas": 1.1,
    "organisasi": 1.0,
    "jadwal": 0.9,
    "catatan": 0.6,
}

URGENCY_WEIGHT = {
    "tinggi": 1.4,
    "normal": 1.0,
}


def compute_priority_score(deadline_dt, urgency="normal", category="tugas"):
    """
    Hitung skor prioritas (semakin tinggi = semakin prioritas).
    Basis skor dari kedekatan deadline (skala 0-100, memakai fungsi
    berkurang seiring jarak hari bertambah), lalu dikalikan bobot
    urgensi & kategori.
    """
    base_score = 30  # skor dasar kalau tidak ada deadline

    if deadline_dt:
        now = datetime.now()
        days_left = (deadline_dt - now).total_seconds() / 86400.0

        if days_left <= 0:
            base_score = 100  # sudah lewat / hari ini -> paling prioritas
        elif days_left <= 1:
            base_score = 95
        elif days_left <= 3:
            base_score = 85
        elif days_left <= 7:
            base_score = 65
        elif days_left <= 14:
            base_score = 45
        else:
            base_score = 25

    urgency_w = URGENCY_WEIGHT.get(urgency, 1.0)
    category_w = CATEGORY_WEIGHT.get(category, 1.0)

    score = base_score * urgency_w * category_w
    return round(min(score, 150), 1)  # cap supaya tidak liar


def add_todo(title, deadline_dt=None, urgency="normal", category="tugas", source_text=""):
    data = data_store.load_data()

    score = compute_priority_score(deadline_dt, urgency, category)

    new_item = {
        "id": data_store.next_id(data["todos"]),
        "title": title,
        "deadline": deadline_dt.isoformat(timespec="minutes") if deadline_dt else None,
        "urgency": urgency,
        "category": category,
        "priority_score": score,
        "done": False,
        "source_text": source_text,
        "created_at": data_store.now_iso(),
    }

    data["todos"].append(new_item)
    data_store.save_data(data)

    return new_item


def get_all_todos(include_done=False, sort_by_priority=True):
    data = data_store.load_data()
    todos = data["todos"]

    if not include_done:
        todos = [t for t in todos if not t.get("done")]

    if sort_by_priority:
        todos = sorted(todos, key=lambda t: t.get("priority_score", 0), reverse=True)

    return todos


def mark_done(todo_id, done=True):
    data = data_store.load_data()
    for t in data["todos"]:
        if t["id"] == todo_id:
            t["done"] = done
            break
    data_store.save_data(data)


def toggle_done(todo_id):
    """Balik status selesai/belum untuk satu todo (dipakai oleh checkbox di GUI)."""
    data = data_store.load_data()
    new_state = None
    for t in data["todos"]:
        if t["id"] == todo_id:
            t["done"] = not t.get("done", False)
            new_state = t["done"]
            break
    data_store.save_data(data)
    return new_state


def delete_todo(todo_id):
    data = data_store.load_data()
    data["todos"] = [t for t in data["todos"] if t["id"] != todo_id]
    data_store.save_data(data)


def recompute_all_priorities():
    """Panggil ini secara berkala (mis. saat GUI dibuka) supaya skor prioritas
    ter-update sesuai sisa waktu deadline yang terus berkurang."""
    data = data_store.load_data()
    for t in data["todos"]:
        deadline_dt = datetime.fromisoformat(t["deadline"]) if t.get("deadline") else None
        t["priority_score"] = compute_priority_score(
            deadline_dt, t.get("urgency", "normal"), t.get("category", "tugas")
        )
    data_store.save_data(data)
