from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RecurringSchedule, Task, Journey
from app.schemas import (
    RecurringScheduleCreate,
    RecurringScheduleUpdate,
    RecurringScheduleResponse,
)

router = APIRouter(prefix="/recurring-schedules", tags=["Recurring Schedules"])


def enrich_recurring_response(schedule: RecurringSchedule, db: Session) -> RecurringScheduleResponse:
    journey_title = schedule.journey.title if schedule.journey else None
    total_tasks = db.query(Task).filter(Task.recurring_schedule_id == schedule.id).count()
    completed_tasks = db.query(Task).filter(Task.recurring_schedule_id == schedule.id, Task.is_done == True).count()

    days_list = [int(x.strip()) for x in schedule.days_of_week.split(",") if x.strip().isdigit()]

    return RecurringScheduleResponse(
        id=schedule.id,
        journey_id=schedule.journey_id,
        journey_title=journey_title,
        title=schedule.title,
        category=schedule.category or "General",
        priority=schedule.priority or 2,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        days_of_week=days_list,
        start_date=schedule.start_date,
        end_date=schedule.end_date,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        created_at=schedule.created_at,
    )


@router.get("", response_model=List[RecurringScheduleResponse])
def get_recurring_schedules(db: Session = Depends(get_db)):
    schedules = db.query(RecurringSchedule).order_by(RecurringSchedule.created_at.desc()).all()
    return [enrich_recurring_response(s, db) for s in schedules]


@router.post("", response_model=RecurringScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_recurring_schedule(rec_in: RecurringScheduleCreate, db: Session = Depends(get_db)):
    journey = db.query(Journey).filter(Journey.id == rec_in.journey_id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    if rec_in.start_date > rec_in.end_date:
        raise HTTPException(status_code=400, detail="Tanggal mulai tidak boleh lebih dari tanggal selesai")

    days_str = ",".join(str(d) for d in sorted(rec_in.days_of_week))

    schedule = RecurringSchedule(
        journey_id=rec_in.journey_id,
        title=rec_in.title,
        category=rec_in.category or "General",
        priority=rec_in.priority or 2,
        start_time=rec_in.start_time,
        end_time=rec_in.end_time,
        days_of_week=days_str,
        start_date=rec_in.start_date,
        end_date=rec_in.end_date,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    # Generate tasks across the date range
    current_d = rec_in.start_date
    while current_d <= rec_in.end_date:
        if current_d.weekday() in rec_in.days_of_week:
            task = Task(
                journey_id=rec_in.journey_id,
                recurring_schedule_id=schedule.id,
                title=rec_in.title,
                category=rec_in.category or "General",
                priority=rec_in.priority or 2,
                task_date=current_d,
                start_time=rec_in.start_time,
                end_time=rec_in.end_time,
                repeat_rule="custom",
                is_done=False,
            )
            db.add(task)
        current_d += timedelta(days=1)

    db.commit()
    return enrich_recurring_response(schedule, db)


@router.get("/{schedule_id}", response_model=RecurringScheduleResponse)
def get_recurring_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(RecurringSchedule).filter(RecurringSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Jadwal berulang tidak ditemukan")
    return enrich_recurring_response(schedule, db)


@router.put("/{schedule_id}", response_model=RecurringScheduleResponse)
def update_recurring_schedule(
    schedule_id: int,
    rec_in: RecurringScheduleUpdate,
    db: Session = Depends(get_db)
):
    schedule = db.query(RecurringSchedule).filter(RecurringSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Jadwal berulang tidak ditemukan")

    if rec_in.journey_id is not None:
        journey = db.query(Journey).filter(Journey.id == rec_in.journey_id).first()
        if not journey:
            raise HTTPException(status_code=404, detail="Journey not found")
        schedule.journey_id = rec_in.journey_id

    if rec_in.title is not None:
        schedule.title = rec_in.title
    if rec_in.category is not None:
        schedule.category = rec_in.category
    if rec_in.priority is not None:
        schedule.priority = rec_in.priority
    if rec_in.start_time is not None:
        schedule.start_time = rec_in.start_time
    if rec_in.end_time is not None:
        schedule.end_time = rec_in.end_time
    if rec_in.days_of_week is not None:
        schedule.days_of_week = ",".join(str(d) for d in sorted(rec_in.days_of_week))
    if rec_in.start_date is not None:
        schedule.start_date = rec_in.start_date
    if rec_in.end_date is not None:
        schedule.end_date = rec_in.end_date

    if schedule.start_date > schedule.end_date:
        raise HTTPException(status_code=400, detail="Tanggal mulai tidak boleh lebih dari tanggal selesai")

    # Parse current active days
    active_days = [int(x.strip()) for x in schedule.days_of_week.split(",") if x.strip().isdigit()]

    # Sync all existing tasks under this schedule:
    existing_tasks = db.query(Task).filter(Task.recurring_schedule_id == schedule.id).all()
    existing_task_dates = set()

    for task in existing_tasks:
        existing_task_dates.add(task.task_date)
        # Check if task is still in valid range and on an active weekday
        in_range = (schedule.start_date <= task.task_date <= schedule.end_date)
        on_active_day = (task.task_date.weekday() in active_days)

        if not in_range or not on_active_day:
            # If not yet done, remove task
            if not task.is_done:
                db.delete(task)
        else:
            # Update attributes
            task.title = schedule.title
            task.category = schedule.category
            task.priority = schedule.priority
            task.start_time = schedule.start_time
            task.end_time = schedule.end_time
            task.journey_id = schedule.journey_id

    # Create missing tasks for any newly included dates
    current_d = schedule.start_date
    while current_d <= schedule.end_date:
        if current_d.weekday() in active_days:
            if current_d not in existing_task_dates:
                new_task = Task(
                    journey_id=schedule.journey_id,
                    recurring_schedule_id=schedule.id,
                    title=schedule.title,
                    category=schedule.category or "General",
                    priority=schedule.priority or 2,
                    task_date=current_d,
                    start_time=schedule.start_time,
                    end_time=schedule.end_time,
                    repeat_rule="custom",
                    is_done=False,
                )
                db.add(new_task)
        current_d += timedelta(days=1)

    db.commit()
    db.refresh(schedule)
    return enrich_recurring_response(schedule, db)


@router.delete("/{schedule_id}")
def delete_recurring_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(RecurringSchedule).filter(RecurringSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Jadwal berulang tidak ditemukan")

    db.delete(schedule)
    db.commit()
    return {"message": f"Jadwal berulang '{schedule.title}' berhasil dihapus beserta seluruh task-nya."}
