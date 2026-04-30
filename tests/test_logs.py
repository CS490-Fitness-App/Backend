from datetime import date

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from core.database import get_db
from dependencies.rbac import require_client
from main import app
from models.log import DailySurvey, MoodType
from models.user import User, Client
from models.workout import Workout, WorkoutLog


@pytest.fixture
def log_actors(db):
    user = User(auth0_sub="auth0|logclient", email="logclient@test.com",
                first_name="Log", last_name="Client", role="client")
    db.add(user)
    db.flush()
    client = Client(user_id=user.user_id, weekly_streak=0)
    db.add(client)
    db.flush()
    return user, client


@pytest.fixture
def log_client(db, log_actors):
    user, client = log_actors
    mock_user = MagicMock()
    mock_user.user_id = user.user_id
    mock_user.role = "client"
    mock_user.client = client

    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_client] = lambda: mock_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# GET /logs/daily-checkin/status: no survey exists for today → completed=False.
def test_daily_checkin_status_not_done(log_client):
    resp = log_client.get("/logs/daily-checkin/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["completed"] is False


# GET /logs/daily-checkin/status: after posting a check-in, status shows completed=True.
def test_daily_checkin_status_done(db, log_client, log_actors):
    user, _ = log_actors
    today = date.today()
    mood = MoodType(mood_type_name="Okay")
    db.add(mood)
    db.flush()
    db.add(DailySurvey(user_id=user.user_id, survey_date=today, mood_type_id=mood.mood_type_id))
    db.flush()
    resp = log_client.get("/logs/daily-checkin/status")
    assert resp.status_code == 200
    assert resp.json()["completed"] is True


# POST /logs/daily-checkin: first submission for today creates a survey and returns 201.
def test_create_daily_checkin(log_client):
    resp = log_client.post("/logs/daily-checkin", json={"date": str(date.today())})
    assert resp.status_code == 201
    data = resp.json()
    assert "daily_survey" in data


# POST /logs/daily-checkin: submitting twice for the same date returns 409.
def test_create_daily_checkin_duplicate(log_client):
    today = str(date.today())
    log_client.post("/logs/daily-checkin", json={"date": today})
    resp = log_client.post("/logs/daily-checkin", json={"date": today})
    assert resp.status_code == 409


# POST /logs/ with type=steps: upserts step count into the daily survey and returns 201.
def test_create_steps_log(log_client):
    resp = log_client.post("/logs/", json={"type": "steps", "date": str(date.today()), "step_count": 8000})
    assert resp.status_code == 201
    data = resp.json()
    assert data["step_count"] == 8000


# POST /logs/ with type=calories: upserts calorie data into the daily survey and returns 201.
def test_create_calories_log(log_client):
    resp = log_client.post("/logs/", json={
        "type": "calories", "date": str(date.today()),
        "calories_intake": 2000, "calories_burned": 500,
    })
    assert resp.status_code == 201


# GET /logs/: no logs for today returns empty workout_logs list.
def test_get_logs_empty(log_client, log_actors):
    user, _ = log_actors
    resp = log_client.get(f"/logs/?userId={user.user_id}&date={date.today()}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["workout_logs"] == []
    assert data["daily_survey"] is None


# GET /logs/: requesting another user's logs returns 403.
def test_get_logs_wrong_user(log_client):
    resp = log_client.get(f"/logs/?userId=9999&date={date.today()}")
    assert resp.status_code == 403


# DELETE /logs/{log_id}: non-existent log returns 404.
def test_delete_log_not_found(log_client):
    resp = log_client.delete("/logs/9999")
    assert resp.status_code == 404
