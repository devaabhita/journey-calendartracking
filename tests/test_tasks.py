from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# Use in-memory SQLite with StaticPool so all connections share the same memory instance
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_journey_crud():
    # 1. Create Journey
    create_resp = client.post(
        "/journeys",
        json={
            "title": "Belajar FastAPI 1 Bulan",
            "description": "Target menguasai backend API modern",
            "start_date": "2026-10-01",
            "target_date": "2026-10-31",
        },
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    journey_id = data["id"]
    assert data["title"] == "Belajar FastAPI 1 Bulan"
    assert data["progress_percent"] == 0.0

    # 2. Get All Journeys
    list_resp = client.get("/journeys")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 3. Update Journey
    update_resp = client.put(
        f"/journeys/{journey_id}",
        json={"title": "Belajar FastAPI & Docker 1 Bulan"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Belajar FastAPI & Docker 1 Bulan"


def test_task_creation_and_toggle():
    # 1. Create parent journey
    j_resp = client.post(
        "/journeys",
        json={
            "title": "Road to Data Scientist",
            "description": "Belajar matematika dan machine learning",
            "start_date": "2026-10-15",
            "target_date": "2026-12-31",
        },
    )
    journey_id = j_resp.json()["id"]

    # 2. Create Task with daily repeat rule
    t_resp = client.post(
        "/tasks",
        json={
            "journey_id": journey_id,
            "title": "Belajar Aljabar Linear",
            "category": "Matematika",
            "priority": 1,
            "task_date": "2026-10-19",
            "start_time": "08:00:00",
            "end_time": "09:30:00",
            "repeat_rule": "daily",
        },
    )
    assert t_resp.status_code == 201
    task = t_resp.json()
    assert task["is_done"] is False
    task_id = task["id"]

    # 3. Toggle task checklist to True
    toggle_resp = client.patch(f"/tasks/{task_id}/toggle")
    assert toggle_resp.status_code == 200
    toggled = toggle_resp.json()
    assert toggled["is_done"] is True
    assert toggled["done_at"] is not None

    # Verify that repeat_rule daily created the next task for tomorrow (2026-10-20)
    all_tasks = client.get(f"/tasks?journey_id={journey_id}").json()
    assert len(all_tasks) == 2
    dates = [t["task_date"] for t in all_tasks]
    assert "2026-10-19" in dates
    assert "2026-10-20" in dates

    # Check journey progress (1 done out of 2 = 50.0%)
    j_check = client.get(f"/journeys/{journey_id}").json()
    assert j_check["total_tasks"] == 2
    assert j_check["completed_tasks"] == 1
    assert j_check["progress_percent"] == 50.0


def test_stats_summary_endpoint():
    # Create journey and completed task to test summary
    j_resp = client.post(
        "/journeys",
        json={
            "title": "Summary Test Journey",
            "description": "Testing stats",
            "start_date": "2026-10-19",
            "target_date": "2026-10-25",
        },
    )
    j_id = j_resp.json()["id"]

    client.post(
        "/tasks",
        json={
            "journey_id": j_id,
            "title": "Task 1",
            "category": "Dev",
            "priority": 1,
            "task_date": "2026-10-19",
            "start_time": "09:00:00",
            "end_time": "11:00:00",
        },
    )

    resp = client.get("/stats/summary?period=week")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tasks"] == 1
    assert data["completed_tasks"] == 0


def test_recurring_tasks_and_calendar():
    # 1. Create Journey
    j_resp = client.post(
        "/journeys",
        json={
            "title": "Semester Journey",
            "description": "Kuliah dan belajar",
            "start_date": "2026-10-01",
            "target_date": "2026-10-31",
        },
    )
    j_id = j_resp.json()["id"]

    # 2. Create recurring task for Senin (0), Selasa (1), Rabu (2) between 2026-10-19 and 2026-10-25
    rec_resp = client.post(
        "/tasks/recurring",
        json={
            "journey_id": j_id,
            "title": "Belajar Python Rutin",
            "category": "Belajar",
            "priority": 1,
            "start_time": "19:00:00",
            "end_time": "20:30:00",
            "days_of_week": [0, 1, 2],  # Senin, Selasa, Rabu
            "start_date": "2026-10-19",
            "end_date": "2026-10-25",
        },
    )
    assert rec_resp.status_code == 201
    tasks = rec_resp.json()
    assert len(tasks) == 3  # Oct 19 (Mon), Oct 20 (Tue), Oct 21 (Wed)

    # 3. Test calendar month progress
    cal_resp = client.get("/stats/calendar?year=2026&month=10")
    assert cal_resp.status_code == 200
    cal_data = cal_resp.json()
    assert cal_data["year"] == 2026
    assert cal_data["month"] == 10
    assert "2026-10-19" in cal_data["days"]
    assert cal_data["days"]["2026-10-19"]["total"] == 1

