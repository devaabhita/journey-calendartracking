from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ==========================================
# Journey Schemas
# ==========================================

class JourneyBase(BaseModel):
    title: str = Field(..., max_length=150, description="Title of the journey")
    description: Optional[str] = Field(None, description="Detailed description")
    start_date: date = Field(..., description="Start date of the journey")
    target_date: Optional[date] = Field(None, description="Target completion date")


class JourneyCreate(JourneyBase):
    pass


class JourneyUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None


class JourneyResponse(JourneyBase):
    id: int
    created_at: Optional[datetime] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    progress_percent: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Task Schemas
# ==========================================

class TaskBase(BaseModel):
    journey_id: int = Field(..., description="Associated journey ID")
    title: str = Field(..., max_length=200, description="Task title")
    category: Optional[str] = Field("General", max_length=50)
    priority: Optional[int] = Field(2, ge=1, le=3, description="1: High, 2: Medium, 3: Low")
    task_date: date = Field(..., description="Date of the task")
    start_time: Optional[time] = Field(None, description="Start time (HH:MM)")
    end_time: Optional[time] = Field(None, description="End time (HH:MM)")
    repeat_rule: Optional[str] = Field("none", description="'none' | 'daily' | 'weekly'")


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    journey_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=3)
    task_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    repeat_rule: Optional[str] = None
    is_done: Optional[bool] = None


class TaskResponse(BaseModel):
    id: int
    journey_id: int
    journey_title: Optional[str] = None
    title: str
    category: Optional[str] = "General"
    priority: int = 2
    task_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_done: bool = False
    done_at: Optional[datetime] = None
    repeat_rule: Optional[str] = "none"

    model_config = ConfigDict(from_attributes=True)


class TaskRecurringCreate(BaseModel):
    journey_id: int
    title: str
    category: Optional[str] = "General"
    priority: Optional[int] = Field(2, ge=1, le=3)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    days_of_week: List[int] = Field(..., description="0=Senin, 1=Selasa, 2=Rabu, 3=Kamis, 4=Jumat, 5=Sabtu, 6=Minggu")
    start_date: date
    end_date: date


# ==========================================
# Daily Note Schemas
# ==========================================

class DailyNoteBase(BaseModel):
    note_date: date
    mood: Optional[int] = Field(None, ge=1, le=5, description="Mood 1-5")
    content: Optional[str] = None


class DailyNoteCreate(DailyNoteBase):
    pass


class DailyNoteResponse(DailyNoteBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Stats Schemas
# ==========================================

class SummaryResponse(BaseModel):
    period: str
    start_date: date
    end_date: date
    total_tasks: int
    completed_tasks: int
    progress_percent: float
    total_focus_hours: float
    active_days: int
    weekly_consistency: float


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    last_active_date: Optional[date] = None


class HeatmapItem(BaseModel):
    date: str
    total: int
    completed: int


class HeatmapResponse(BaseModel):
    days: List[HeatmapItem]


class CalendarDayItem(BaseModel):
    date: str
    total: int
    completed: int
    progress_percent: float
    tasks: List[TaskResponse] = []


class CalendarMonthResponse(BaseModel):
    year: int
    month: int
    days: dict[str, CalendarDayItem]
