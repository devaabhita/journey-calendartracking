from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Journey, Task
from app.schemas import JourneyCreate, JourneyUpdate, JourneyResponse
from app.services.stats import calculate_progress

router = APIRouter(prefix="/journeys", tags=["Journeys"])


def enrich_journey_response(journey: Journey, db: Session) -> JourneyResponse:
    total_tasks = db.query(Task).filter(Task.journey_id == journey.id).count()
    completed_tasks = db.query(Task).filter(Task.journey_id == journey.id, Task.is_done == True).count()
    progress = calculate_progress(completed_tasks, total_tasks)

    return JourneyResponse(
        id=journey.id,
        title=journey.title,
        description=journey.description,
        start_date=journey.start_date,
        target_date=journey.target_date,
        created_at=journey.created_at,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        progress_percent=progress,
    )


@router.get("", response_model=List[JourneyResponse])
def get_journeys(db: Session = Depends(get_db)):
    journeys = db.query(Journey).order_by(Journey.created_at.desc()).all()
    return [enrich_journey_response(j, db) for j in journeys]


@router.post("", response_model=JourneyResponse, status_code=status.HTTP_201_CREATED)
def create_journey(journey_in: JourneyCreate, db: Session = Depends(get_db)):
    journey = Journey(
        title=journey_in.title,
        description=journey_in.description,
        start_date=journey_in.start_date,
        target_date=journey_in.target_date,
    )
    db.add(journey)
    db.commit()
    db.refresh(journey)
    return enrich_journey_response(journey, db)


@router.get("/{journey_id}", response_model=JourneyResponse)
def get_journey(journey_id: int, db: Session = Depends(get_db)):
    journey = db.query(Journey).filter(Journey.id == journey_id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")
    return enrich_journey_response(journey, db)


@router.put("/{journey_id}", response_model=JourneyResponse)
def update_journey(journey_id: int, journey_in: JourneyUpdate, db: Session = Depends(get_db)):
    journey = db.query(Journey).filter(Journey.id == journey_id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    if journey_in.title is not None:
        journey.title = journey_in.title
    if journey_in.description is not None:
        journey.description = journey_in.description
    if journey_in.start_date is not None:
        journey.start_date = journey_in.start_date
    if journey_in.target_date is not None:
        journey.target_date = journey_in.target_date

    db.commit()
    db.refresh(journey)
    return enrich_journey_response(journey, db)


@router.delete("/{journey_id}", status_code=status.HTTP_200_OK)
def delete_journey(journey_id: int, db: Session = Depends(get_db)):
    journey = db.query(Journey).filter(Journey.id == journey_id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    db.delete(journey)
    db.commit()
    return {"message": f"Journey '{journey.title}' deleted successfully"}
