import calendar
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.database import get_db
from app.models import Task
from app.schemas import (
    SummaryResponse,
    StreakResponse,
    HeatmapResponse,
    HeatmapItem,
    CalendarMonthResponse,
    CalendarDayItem,
    TaskResponse,
)
from app.routers.tasks import enrich_task_response
from app.services.stats import (
    get_summary_stats,
    calculate_streaks,
    get_heatmap_stats,
)

router = APIRouter(prefix="/stats", tags=["Stats & Analytics"])


@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    period: str = Query("week", pattern="^(week|month)$", description="'week' or 'month'"),
    ref_date: Optional[date] = Query(None, description="Reference date (defaults to today)"),
    db: Session = Depends(get_db),
):
    stats = get_summary_stats(db, period=period, ref_date=ref_date)
    return stats


@router.get("/streak", response_model=StreakResponse)
def get_streak(
    ref_date: Optional[date] = Query(None, description="Reference date (defaults to today)"),
    db: Session = Depends(get_db),
):
    # Query all distinct dates where is_done is True
    rows = (
        db.query(Task.task_date)
        .filter(Task.is_done == True)
        .distinct()
        .all()
    )
    active_dates = {row[0] for row in rows}

    current, longest, last_active = calculate_streaks(active_dates, ref_date)
    return {
        "current_streak": current,
        "longest_streak": longest,
        "last_active_date": last_active,
    }


@router.get("/heatmap", response_model=HeatmapResponse)
def get_heatmap(
    days: int = Query(60, ge=7, le=365, description="Number of days to look back"),
    ref_date: Optional[date] = Query(None, description="Reference date (defaults to today)"),
    db: Session = Depends(get_db),
):
    heatmap_list = get_heatmap_stats(db, days_count=days, ref_date=ref_date)
    return {"days": [HeatmapItem(**item) for item in heatmap_list]}


@router.get("/calendar", response_model=CalendarMonthResponse)
def get_calendar_month(
    year: int = Query(..., description="Year (e.g. 2026)"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    db: Session = Depends(get_db),
):
    days_in_month = calendar.monthrange(year, month)[1]
    start_date = date(year, month, 1)
    end_date = date(year, month, days_in_month)

    tasks = (
        db.query(Task)
        .filter(Task.task_date >= start_date, Task.task_date <= end_date)
        .order_by(Task.task_date.asc(), Task.priority.asc(), Task.start_time.asc())
        .all()
    )

    # Group by date
    days_map = {}
    for d in range(1, days_in_month + 1):
        d_str = date(year, month, d).isoformat()
        days_map[d_str] = {
            "date": d_str,
            "total": 0,
            "completed": 0,
            "progress_percent": 0.0,
            "tasks": [],
        }

    for t in tasks:
        d_str = t.task_date.isoformat()
        if d_str in days_map:
            days_map[d_str]["total"] += 1
            if t.is_done:
                days_map[d_str]["completed"] += 1
            days_map[d_str]["tasks"].append(enrich_task_response(t))

    for d_str, item in days_map.items():
        total = item["total"]
        comp = item["completed"]
        item["progress_percent"] = round((comp / total) * 100.0, 1) if total > 0 else 0.0

    return CalendarMonthResponse(
        year=year,
        month=month,
        days={k: CalendarDayItem(**v) for k, v in days_map.items()},
    )


@router.get("/categories")
def get_category_distribution(db: Session = Depends(get_db)):
    results = (
        db.query(
            Task.category,
            func.count(Task.id).label("total"),
            func.sum(case((Task.is_done == True, 1), else_=0)).label("completed"),
        )
        .group_by(Task.category)
        .all()
    )
    return [
        {
            "category": row[0] or "General",
            "total": row[1],
            "completed": int(row[2] or 0),
        }
        for row in results
    ]
