from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    Time,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Journey(Base):
    __tablename__ = "journeys"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    tasks = relationship("Task", back_populates="journey", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    journey_id = Column(Integer, ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=True, default="General")
    priority = Column(Integer, default=2)  # 1: Tinggi, 2: Sedang, 3: Rendah
    task_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    is_done = Column(Boolean, default=False)
    done_at = Column(DateTime, nullable=True)
    repeat_rule = Column(String(10), default="none")  # 'none' | 'daily' | 'weekly'

    journey = relationship("Journey", back_populates="tasks")
    recurring_schedule_id = Column(Integer, ForeignKey("recurring_schedules.id", ondelete="CASCADE"), nullable=True)
    recurring_schedule = relationship("RecurringSchedule", back_populates="tasks")

    __table_args__ = (
        Index("idx_task_date", "task_date"),
    )


class RecurringSchedule(Base):
    __tablename__ = "recurring_schedules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    journey_id = Column(Integer, ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=True, default="General")
    priority = Column(Integer, default=2)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    days_of_week = Column(String(50), nullable=False)  # e.g. "0,1,2" (0=Senin ... 6=Minggu)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    journey = relationship("Journey")
    tasks = relationship("Task", back_populates="recurring_schedule", cascade="all, delete-orphan")


class DailyNote(Base):
    __tablename__ = "daily_notes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    note_date = Column(Date, nullable=False, unique=True, index=True)
    mood = Column(Integer, nullable=True)  # 1 (buruk) s.d. 5 (bagus)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
