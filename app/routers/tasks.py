from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models import Task, Journey
from app.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskRecurringCreate

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def enrich_task_response(task: Task) -> TaskResponse:
    journey_title = task.journey.title if task.journey else None
    return TaskResponse(
        id=task.id,
        journey_id=task.journey_id,
        journey_title=journey_title,
        title=task.title,
        category=task.category or "General",
        priority=task.priority or 2,
        task_date=task.task_date,
        start_time=task.start_time,
        end_time=task.end_time,
        is_done=task.is_done,
        done_at=task.done_at,
        repeat_rule=task.repeat_rule or "none",
    )


@router.get("", response_model=List[TaskResponse])
def get_tasks(
    date_val: Optional[date] = Query(None, alias="date", description="Filter by exact task date (YYYY-MM-DD)"),
    journey_id: Optional[int] = Query(None, description="Filter by journey ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_done: Optional[bool] = Query(None, description="Filter by status (done/not done)"),
    start_date: Optional[date] = Query(None, description="Start date range"),
    end_date: Optional[date] = Query(None, description="End date range"),
    search: Optional[str] = Query(None, description="Search task title"),
    db: Session = Depends(get_db),
):
    query = db.query(Task).join(Journey)

    if date_val is not None:
        query = query.filter(Task.task_date == date_val)
    if journey_id is not None:
        query = query.filter(Task.journey_id == journey_id)
    if category is not None and category != "":
        query = query.filter(Task.category.ilike(f"%{category}%"))
    if is_done is not None:
        query = query.filter(Task.is_done == is_done)
    if start_date is not None:
        query = query.filter(Task.task_date >= start_date)
    if end_date is not None:
        query = query.filter(Task.task_date <= end_date)
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    # Order by task_date asc, priority asc (1 high first), start_time asc
    tasks = query.order_by(Task.task_date.asc(), Task.priority.asc(), Task.start_time.asc()).all()
    return [enrich_task_response(t) for t in tasks]


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    journey = db.query(Journey).filter(Journey.id == task_in.journey_id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    task = Task(
        journey_id=task_in.journey_id,
        title=task_in.title,
        category=task_in.category or "General",
        priority=task_in.priority or 2,
        task_date=task_in.task_date,
        start_time=task_in.start_time,
        end_time=task_in.end_time,
        repeat_rule=task_in.repeat_rule or "none",
        is_done=False,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return enrich_task_response(task)


@router.post("/recurring", response_model=List[TaskResponse], status_code=status.HTTP_201_CREATED)
def create_recurring_tasks(rec_in: TaskRecurringCreate, db: Session = Depends(get_db)):
    journey = db.query(Journey).filter(Journey.id == rec_in.journey_id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    if rec_in.start_date > rec_in.end_date:
        raise HTTPException(status_code=400, detail="Tanggal mulai tidak boleh lebih dari tanggal selesai")

    created_tasks = []
    current_d = rec_in.start_date
    while current_d <= rec_in.end_date:
        if current_d.weekday() in rec_in.days_of_week:
            existing = db.query(Task).filter(
                Task.journey_id == rec_in.journey_id,
                Task.title == rec_in.title,
                Task.task_date == current_d
            ).first()

            if not existing:
                task = Task(
                    journey_id=rec_in.journey_id,
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
                created_tasks.append(task)
        current_d += timedelta(days=1)

    db.commit()
    for t in created_tasks:
        db.refresh(t)

    return [enrich_task_response(t) for t in created_tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return enrich_task_response(task)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_in: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_in.journey_id is not None:
        journey = db.query(Journey).filter(Journey.id == task_in.journey_id).first()
        if not journey:
            raise HTTPException(status_code=404, detail="Target journey not found")
        task.journey_id = task_in.journey_id

    if task_in.title is not None:
        task.title = task_in.title
    if task_in.category is not None:
        task.category = task_in.category
    if task_in.priority is not None:
        task.priority = task_in.priority
    if task_in.task_date is not None:
        task.task_date = task_in.task_date
    if task_in.start_time is not None:
        task.start_time = task_in.start_time
    if task_in.end_time is not None:
        task.end_time = task_in.end_time
    if task_in.repeat_rule is not None:
        task.repeat_rule = task_in.repeat_rule
    if task_in.is_done is not None:
        task.is_done = task_in.is_done
        task.done_at = datetime.now(timezone.utc) if task_in.is_done else None

    db.commit()
    db.refresh(task)
    return enrich_task_response(task)


@router.patch("/{task_id}/toggle", response_model=TaskResponse)
def toggle_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    new_status = not task.is_done
    task.is_done = new_status
    task.done_at = datetime.now(timezone.utc) if new_status else None

    # Handle repeat rule if newly marked as completed
    if new_status and task.repeat_rule in ("daily", "weekly"):
        delta_days = 1 if task.repeat_rule == "daily" else 7
        next_date = task.task_date + timedelta(days=delta_days)

        # Check if next occurrence already exists
        existing = db.query(Task).filter(
            Task.journey_id == task.journey_id,
            Task.title == task.title,
            Task.task_date == next_date
        ).first()

        if not existing:
            next_task = Task(
                journey_id=task.journey_id,
                title=task.title,
                category=task.category,
                priority=task.priority,
                task_date=next_date,
                start_time=task.start_time,
                end_time=task.end_time,
                repeat_rule=task.repeat_rule,
                is_done=False,
            )
            db.add(next_task)

    db.commit()
    db.refresh(task)
    return enrich_task_response(task)


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"message": f"Task '{task.title}' deleted successfully"}
