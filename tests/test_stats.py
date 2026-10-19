from datetime import date, time, timedelta
from app.services.stats import (
    calculate_progress,
    calculate_focus_hours,
    calculate_streaks,
)
from app.models import Task


def test_calculate_progress():
    assert calculate_progress(0, 0) == 0.0
    assert calculate_progress(1, 4) == 25.0
    assert calculate_progress(2, 3) == 66.7
    assert calculate_progress(5, 5) == 100.0


def test_calculate_focus_hours():
    class MockTask:
        def __init__(self, is_done, start_time, end_time):
            self.is_done = is_done
            self.start_time = start_time
            self.end_time = end_time

    # Task 1: 10:00 - 11:30 (1.5 hours), completed
    # Task 2: 14:00 - 15:00 (1.0 hour), NOT completed -> shouldn't count
    # Task 3: 16:00 - 16:45 (0.75 hour), completed
    tasks = [
        MockTask(True, time(10, 0), time(11, 30)),
        MockTask(False, time(14, 0), time(15, 0)),
        MockTask(True, time(16, 0), time(16, 45)),
    ]

    focus_hours = calculate_focus_hours(tasks)
    assert focus_hours == 2.25  # 1.5 + 0.75


def test_calculate_streaks():
    today = date(2026, 10, 19)

    # Scenario 1: Active today, yesterday, and 2 days ago
    active = {
        today - timedelta(days=2),
        today - timedelta(days=1),
        today,
    }
    current, longest, last_active = calculate_streaks(active, today)
    assert current == 3
    assert longest == 3
    assert last_active == today

    # Scenario 2: Active yesterday and day before, but not yet today
    # Streak should still be 2 (grace period for current day)
    active_yesterday = {
        today - timedelta(days=2),
        today - timedelta(days=1),
    }
    current, longest, last_active = calculate_streaks(active_yesterday, today)
    assert current == 2
    assert longest == 2

    # Scenario 3: Broken streak (active 3 days ago, but missed 2 days ago and yesterday)
    active_gap = {
        today - timedelta(days=3),
    }
    current, longest, last_active = calculate_streaks(active_gap, today)
    assert current == 0
    assert longest == 1

    # Scenario 4: Longest streak in past was longer than current streak
    active_complex = {
        # Past 4-day streak:
        date(2026, 9, 1),
        date(2026, 9, 2),
        date(2026, 9, 3),
        date(2026, 9, 4),
        # Current 2-day streak:
        today - timedelta(days=1),
        today,
    }
    current, longest, _ = calculate_streaks(active_complex, today)
    assert current == 2
    assert longest == 4
