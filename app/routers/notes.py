from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import DailyNote
from app.schemas import DailyNoteCreate, DailyNoteResponse

router = APIRouter(prefix="/notes", tags=["Daily Notes & Mood"])


@router.get("", response_model=Optional[DailyNoteResponse])
def get_note_by_date(
    date_val: date = Query(..., alias="date", description="Date of the note (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    note = db.query(DailyNote).filter(DailyNote.note_date == date_val).first()
    return note


@router.post("", response_model=DailyNoteResponse)
def save_daily_note(note_in: DailyNoteCreate, db: Session = Depends(get_db)):
    note = db.query(DailyNote).filter(DailyNote.note_date == note_in.note_date).first()
    if note:
        note.mood = note_in.mood
        note.content = note_in.content
    else:
        note = DailyNote(
            note_date=note_in.note_date,
            mood=note_in.mood,
            content=note_in.content,
        )
        db.add(note)

    db.commit()
    db.refresh(note)
    return note


@router.get("/history", response_model=List[DailyNoteResponse])
def get_notes_history(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db)
):
    notes = db.query(DailyNote).order_by(DailyNote.note_date.desc()).limit(limit).all()
    return notes
