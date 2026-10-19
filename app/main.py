import os
import logging
from datetime import date, time, timedelta, datetime, timezone
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app import models
from app.routers import journeys, tasks, stats, notes, recurring
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("journey_tracker")

# Create tables & migrate columns if needed
try:
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN recurring_schedule_id INT NULL"))
            conn.commit()
        except Exception:
            pass
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")

app = FastAPI(
    title="🧭 Journey Tracker API",
    description="Aplikasi to-do list berbasis perjalanan (journey) dengan checklist, waktu, streak, dan rekap otomatis.",
    version="1.0.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(journeys.router)
app.include_router(tasks.router)
app.include_router(recurring.router)
app.include_router(stats.router)
app.include_router(notes.router)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": "Journey Tracker",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def seed_demo_data_if_empty():
    db: Session = SessionLocal()
    try:
        count = db.query(models.Journey).count()
        if count == 0:
            logger.info("Seeding initial sample journey and tasks...")
            today = date.today()
            now_utc = datetime.now(timezone.utc)

            # Create sample journey
            j1 = models.Journey(
                title="🐍 Master Python & FastAPI (3 Bulan)",
                description="Membangun pemahaman mendalam tentang Python, FastAPI, relational database, dan deployment arsitektur modern.",
                start_date=today - timedelta(days=14),
                target_date=today + timedelta(days=76),
            )
            j2 = models.Journey(
                title="🏃 Kebugaran & Olahraga Konsisten",
                description="Menjaga kesehatan fisik dengan jogging pagi, workout teratur, dan hidrasi cukup.",
                start_date=today - timedelta(days=7),
                target_date=today + timedelta(days=53),
            )
            db.add_all([j1, j2])
            db.commit()
            db.refresh(j1)
            db.refresh(j2)

            # Sample tasks over previous days to establish streak and heatmap
            sample_tasks = [
                # 2 days ago
                models.Task(
                    journey_id=j1.id,
                    title="Setup struktur arsitektur modular FastAPI",
                    category="Belajar",
                    priority=1,
                    task_date=today - timedelta(days=2),
                    start_time=time(9, 0),
                    end_time=time(11, 0),
                    is_done=True,
                    done_at=now_utc - timedelta(days=2),
                ),
                models.Task(
                    journey_id=j2.id,
                    title="Jogging santai 3 km di taman",
                    category="Kesehatan",
                    priority=2,
                    task_date=today - timedelta(days=2),
                    start_time=time(6, 30),
                    end_time=time(7, 15),
                    is_done=True,
                    done_at=now_utc - timedelta(days=2),
                ),
                # Yesterday
                models.Task(
                    journey_id=j1.id,
                    title="Eksplorasi SQLAlchemy ORM & Foreign Keys",
                    category="Belajar",
                    priority=1,
                    task_date=today - timedelta(days=1),
                    start_time=time(19, 0),
                    end_time=time(21, 0),
                    is_done=True,
                    done_at=now_utc - timedelta(days=1),
                ),
                # Today
                models.Task(
                    journey_id=j1.id,
                    title="Implementasi endpoint stats, streak & heatmap",
                    category="Coding",
                    priority=1,
                    task_date=today,
                    start_time=time(10, 0),
                    end_time=time(12, 0),
                    is_done=True,
                    done_at=now_utc,
                    repeat_rule="daily",
                ),
                models.Task(
                    journey_id=j1.id,
                    title="Latihan soal algoritma & struktur data",
                    category="Latihan",
                    priority=2,
                    task_date=today,
                    start_time=time(14, 0),
                    end_time=time(15, 30),
                    is_done=False,
                ),
                models.Task(
                    journey_id=j2.id,
                    title="Workout 20 menit (Push-up & Plank)",
                    category="Kesehatan",
                    priority=2,
                    task_date=today,
                    start_time=time(17, 0),
                    end_time=time(17, 30),
                    is_done=False,
                    repeat_rule="daily",
                ),
                # Tomorrow
                models.Task(
                    journey_id=j1.id,
                    title="Desain antarmuka UI Dashboard yang memukau",
                    category="Desain",
                    priority=2,
                    task_date=today + timedelta(days=1),
                    start_time=time(19, 0),
                    end_time=time(20, 30),
                    is_done=False,
                ),
            ]
            db.add_all(sample_tasks)

            # Sample daily note
            note = models.DailyNote(
                note_date=today,
                mood=5,
                content="Hari ini produktif banget! Berhasil menyelesaikan modul analitik dan streak tetap terjaga.",
            )
            db.add(note)

            db.commit()
            logger.info("Demo data seeded successfully.")
    except Exception as e:
        logger.warning(f"Could not seed sample data: {e}")
        db.rollback()
    finally:
        db.close()


seed_demo_data_if_empty()

# Mount frontend static directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
