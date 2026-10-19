from datetime import date, timedelta, datetime, time
from typing import List, Set, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Task, Journey


def calculate_progress(completed: int, total: int) -> float:
    """Progres journey = task selesai ÷ total task × 100%"""
    if total <= 0:
        return 0.0
    return round((completed / total) * 100.0, 1)


def calculate_focus_hours(tasks: List[Task]) -> float:
    """
    Total jam fokus = jumlah (end_time - start_time) pada task yang selesai.
    """
    total_minutes = 0.0
    for task in tasks:
        if task.is_done and task.start_time and task.end_time:
            # Calculate duration in minutes
            start_dt = datetime.combine(date.min, task.start_time)
            end_dt = datetime.combine(date.min, task.end_time)
            if end_dt >= start_dt:
                duration_mins = (end_dt - start_dt).total_seconds() / 60.0
            else:
                # Spans midnight
                duration_mins = ((end_dt + timedelta(days=1)) - start_dt).total_seconds() / 60.0
            total_minutes += duration_mins
    return round(total_minutes / 60.0, 2)


def calculate_streaks(
    active_dates: Set[date],
    reference_date: Optional[date] = None
) -> Tuple[int, int, Optional[date]]:
    """
    Menghitung current streak dan longest streak.
    active_dates: kumpulan tanggal yang memiliki minimal 1 task selesai.
    reference_date: tanggal referensi (biasanya hari ini).
    """
    if not active_dates:
        return 0, 0, None

    sorted_dates = sorted(list(active_dates))
    last_active = sorted_dates[-1]

    ref = reference_date or date.today()

    # Hitung current streak
    # Streak tetap hidup jika ada aktivitas hari ini ATAU kemarin
    current_streak = 0
    check_date = ref

    if check_date in active_dates:
        while check_date in active_dates:
            current_streak += 1
            check_date -= timedelta(days=1)
    elif (check_date - timedelta(days=1)) in active_dates:
        check_date -= timedelta(days=1)
        while check_date in active_dates:
            current_streak += 1
            check_date -= timedelta(days=1)
    else:
        current_streak = 0

    # Hitung longest streak
    longest_streak = 0
    curr_run = 0
    prev_d = None

    for d in sorted_dates:
        if prev_d is None:
            curr_run = 1
        elif d == prev_d + timedelta(days=1):
            curr_run += 1
        else:
            curr_run = 1
        if curr_run > longest_streak:
            longest_streak = curr_run
        prev_d = d

    return current_streak, longest_streak, last_active


def get_summary_stats(db: Session, period: str = "week", ref_date: Optional[date] = None):
    ref = ref_date or date.today()

    if period == "month":
        start_date = ref.replace(day=1)
        # Next month first day minus 1
        if start_date.month == 12:
            next_month = start_date.replace(year=start_date.year + 1, month=1, day=1)
        else:
            next_month = start_date.replace(month=start_date.month + 1, day=1)
        end_date = next_month - timedelta(days=1)
    else:  # week
        # Monday to Sunday of the current week
        start_date = ref - timedelta(days=ref.weekday())
        end_date = start_date + timedelta(days=6)

    tasks = db.query(Task).filter(Task.task_date >= start_date, Task.task_date <= end_date).all()

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.is_done)
    progress_percent = calculate_progress(completed_tasks, total_tasks)
    total_focus_hours = calculate_focus_hours(tasks)

    # Active days in period
    active_days_set = {t.task_date for t in tasks if t.is_done}
    active_days = len(active_days_set)

    # Konsistensi mingguan = hari aktif / 7 * 100%
    days_in_period = (end_date - start_date).days + 1
    weekly_consistency = round((active_days / 7.0) * 100.0, 1) if period == "week" else round((active_days / days_in_period) * 100.0, 1)

    return {
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "progress_percent": progress_percent,
        "total_focus_hours": total_focus_hours,
        "active_days": active_days,
        "weekly_consistency": weekly_consistency,
    }


def get_heatmap_stats(db: Session, days_count: int = 60, ref_date: Optional[date] = None):
    ref = ref_date or date.today()
    start_date = ref - timedelta(days=days_count - 1)

    tasks = db.query(Task).filter(Task.task_date >= start_date, Task.task_date <= ref).all()

    # Aggregate by date
    daily_map = {}
    for i in range(days_count):
        d_str = (start_date + timedelta(days=i)).isoformat()
        daily_map[d_str] = {"date": d_str, "total": 0, "completed": 0}

    for t in tasks:
        d_str = t.task_date.isoformat()
        if d_str in daily_map:
            daily_map[d_str]["total"] += 1
            if t.is_done:
                daily_map[d_str]["completed"] += 1

    return list(daily_map.values())
