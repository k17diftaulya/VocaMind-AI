"""
schedule_manager.py
Smart Schedule Generator:
- Menambahkan jadwal baru dari hasil ekstraksi suara
- Mendeteksi bentrok (overlap) dengan jadwal lain
- Estimasi durasi default jika tidak disebutkan (60 menit)
"""

from datetime import datetime, timedelta
from . import data_store

DEFAULT_DURATION_MINUTES = 60


def add_schedule(title, start_dt, duration_minutes=None, category="jadwal", source_text=""):
    """
    Tambahkan jadwal baru. Mengembalikan tuple (schedule_item, conflicts)
    conflicts = list jadwal lain yang bentrok waktu dengan jadwal baru ini.
    """
    data = data_store.load_data()

    if duration_minutes is None:
        duration_minutes = DEFAULT_DURATION_MINUTES

    end_dt = start_dt + timedelta(minutes=duration_minutes)

    new_item = {
        "id": data_store.next_id(data["schedules"]),
        "title": title,
        "start": start_dt.isoformat(timespec="minutes"),
        "end": end_dt.isoformat(timespec="minutes"),
        "category": category,
        "source_text": source_text,
        "created_at": data_store.now_iso(),
    }

    conflicts = find_conflicts(data["schedules"], start_dt, end_dt)

    data["schedules"].append(new_item)
    data_store.save_data(data)

    return new_item, conflicts


def find_conflicts(existing_schedules, start_dt, end_dt):
    """Cari jadwal yang overlap dengan rentang waktu (start_dt, end_dt)."""
    conflicts = []
    for sched in existing_schedules:
        try:
            s_start = datetime.fromisoformat(sched["start"])
            s_end = datetime.fromisoformat(sched["end"])
        except (ValueError, KeyError):
            continue

        # Dua rentang waktu overlap jika: start1 < end2 AND start2 < end1
        if start_dt < s_end and s_start < end_dt:
            conflicts.append(sched)

    return conflicts


def get_all_schedules(sort=True):
    data = data_store.load_data()
    schedules = data["schedules"]
    if sort:
        schedules = sorted(schedules, key=lambda s: s.get("start", ""))
    return schedules


def delete_schedule(schedule_id):
    data = data_store.load_data()
    data["schedules"] = [s for s in data["schedules"] if s["id"] != schedule_id]
    data_store.save_data(data)


def get_upcoming_schedules(within_days=7):
    now = datetime.now()
    limit = now + timedelta(days=within_days)
    result = []
    for s in get_all_schedules():
        try:
            s_start = datetime.fromisoformat(s["start"])
        except (ValueError, KeyError):
            continue
        if now <= s_start <= limit:
            result.append(s)
    return result
