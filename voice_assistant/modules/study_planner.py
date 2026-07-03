"""
study_planner.py
Study Planner otomatis:
Mengambil tugas/ujian yang punya deadline, lalu membagi sesi belajar/
pengerjaan dari sekarang sampai H-1 deadline.

Strategi sederhana:
- Semakin dekat deadline & semakin tinggi prioritas, semakin sering sesi belajar dibuat.
- Sesi dijadwalkan tiap hari (jika waktu tersisa <=3 hari), tiap 2 hari
  (jika waktu tersisa <=7 hari), atau tiap 3 hari (lebih dari 7 hari).
- Durasi default per sesi 60 menit, bisa disesuaikan.
"""

from datetime import datetime, timedelta
from . import data_store, todo_manager


def generate_study_plan(todo_item, session_duration_minutes=60, preferred_hour=19):
    """
    Buat sesi-sesi belajar untuk satu todo (biasanya kategori 'ujian' atau 'tugas'
    dengan deadline). preferred_hour = jam yang disukai untuk belajar (default 19:00).
    Mengembalikan list sesi yang sudah disimpan ke data store.
    """
    if not todo_item.get("deadline"):
        return []

    deadline_dt = datetime.fromisoformat(todo_item["deadline"])
    now = datetime.now()
    days_left = (deadline_dt - now).days

    if days_left <= 0:
        return []  # tidak cukup waktu untuk bikin rencana belajar

    if days_left <= 3:
        interval_days = 1
    elif days_left <= 7:
        interval_days = 2
    else:
        interval_days = 3

    data = data_store.load_data()
    sessions_created = []

    current = now.replace(hour=preferred_hour, minute=0, second=0, microsecond=0)
    if current <= now:
        current += timedelta(days=1)

    while current.date() < deadline_dt.date():
        session = {
            "id": data_store.next_id(data["study_plan"]),
            "related_task_id": todo_item["id"],
            "related_task_title": todo_item["title"],
            "session_date": current.isoformat(timespec="minutes"),
            "duration_minutes": session_duration_minutes,
            "note": f"Sesi belajar/persiapan untuk: {todo_item['title']}",
        }
        data["study_plan"].append(session)
        sessions_created.append(session)
        current += timedelta(days=interval_days)

    data_store.save_data(data)
    return sessions_created


def generate_plan_for_all_upcoming(max_days_ahead=14):
    """
    Otomatis buat study plan untuk semua todo kategori ujian/tugas yang
    punya deadline dalam rentang max_days_ahead hari ke depan, dan yang
    belum punya study plan.
    """
    data = data_store.load_data()
    existing_task_ids = {sp["related_task_id"] for sp in data["study_plan"]}

    now = datetime.now()
    limit = now + timedelta(days=max_days_ahead)

    all_new_sessions = []
    for todo in todo_manager.get_all_todos(include_done=False):
        if todo["id"] in existing_task_ids:
            continue
        if todo.get("category") not in ("ujian", "tugas", "deadline"):
            continue
        if not todo.get("deadline"):
            continue

        deadline_dt = datetime.fromisoformat(todo["deadline"])
        if now <= deadline_dt <= limit:
            sessions = generate_study_plan(todo)
            all_new_sessions.extend(sessions)

    return all_new_sessions


def get_all_study_sessions(sort=True):
    data = data_store.load_data()
    sessions = data["study_plan"]
    if sort:
        sessions = sorted(sessions, key=lambda s: s.get("session_date", ""))
    return sessions


def delete_session(session_id):
    data = data_store.load_data()
    data["study_plan"] = [s for s in data["study_plan"] if s["id"] != session_id]
    data_store.save_data(data)
