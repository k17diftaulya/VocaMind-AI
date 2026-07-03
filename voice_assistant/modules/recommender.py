"""
recommender.py
Memberi rekomendasi:
1) Urutan pengerjaan tugas (berdasarkan priority_score dari todo_manager)
2) Slot waktu kosong (free time) di antara jadwal yang sudah ada, sebagai
   saran kapan sebaiknya tugas dikerjakan.
"""

from datetime import datetime, timedelta
from . import todo_manager, schedule_manager

WORK_DAY_START_HOUR = 8
WORK_DAY_END_HOUR = 22
MIN_FREE_SLOT_MINUTES = 30


def recommend_task_order(top_n=10):
    """
    Rekomendasi urutan pengerjaan tugas berdasarkan priority_score
    (yang sudah mempertimbangkan deadline & urgensi).
    """
    todo_manager.recompute_all_priorities()
    todos = todo_manager.get_all_todos(include_done=False, sort_by_priority=True)
    return todos[:top_n]


def find_free_slots(target_date=None, min_duration_minutes=MIN_FREE_SLOT_MINUTES):
    """
    Cari slot waktu kosong di hari target_date (default: hari ini) di antara
    jadwal WORK_DAY_START_HOUR - WORK_DAY_END_HOUR, dengan memperhitungkan
    jadwal yang sudah ada di schedule_manager.
    """
    if target_date is None:
        target_date = datetime.now().date()

    day_start = datetime_combine_helper(target_date, WORK_DAY_START_HOUR)
    day_end = datetime_combine_helper(target_date, WORK_DAY_END_HOUR)

    # Ambil semua jadwal di hari itu, urutkan berdasarkan waktu mulai
    schedules_today = []
    for s in schedule_manager.get_all_schedules():
        try:
            s_start = datetime.fromisoformat(s["start"])
            s_end = datetime.fromisoformat(s["end"])
        except (ValueError, KeyError):
            continue
        if s_start.date() == target_date:
            schedules_today.append((s_start, s_end))

    schedules_today.sort(key=lambda x: x[0])

    free_slots = []
    cursor = day_start

    for s_start, s_end in schedules_today:
        if s_start > cursor:
            gap_minutes = (s_start - cursor).total_seconds() / 60
            if gap_minutes >= min_duration_minutes:
                free_slots.append((cursor, s_start))
        if s_end > cursor:
            cursor = s_end

    if cursor < day_end:
        gap_minutes = (day_end - cursor).total_seconds() / 60
        if gap_minutes >= min_duration_minutes:
            free_slots.append((cursor, day_end))

    return free_slots


def datetime_combine_helper(date_obj, hour):
    return datetime.combine(date_obj, datetime.min.time()) + timedelta(hours=hour)


def recommend_schedule_for_task(todo_item, days_ahead=5, duration_minutes=60):
    """
    Cari rekomendasi slot waktu terbaik untuk mengerjakan sebuah tugas,
    dicari mulai hari ini sampai days_ahead hari ke depan, mengutamakan
    hari yang lebih dekat dan slot yang cukup panjang.
    """
    today = datetime.now().date()
    recommendations = []

    for offset in range(days_ahead):
        check_date = today + timedelta(days=offset)
        slots = find_free_slots(check_date, min_duration_minutes=duration_minutes)
        for start, end in slots:
            available_minutes = (end - start).total_seconds() / 60
            if available_minutes >= duration_minutes:
                recommendations.append({
                    "date": check_date.isoformat(),
                    "start": start.isoformat(timespec="minutes"),
                    "end": (start + timedelta(minutes=duration_minutes)).isoformat(timespec="minutes"),
                })
                break  # satu rekomendasi per hari sudah cukup
        if len(recommendations) >= 3:
            break

    return recommendations
