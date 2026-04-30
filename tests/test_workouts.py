from datetime import date

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from core.database import get_db
from dependencies.rbac import get_current_user
from main import app
from models.user import User, Client
from models.workout import Workout, SavedWorkout, ScheduledWorkout


@pytest.fixture
def workout_user(db):
    user = User(auth0_sub="auth0|wuser", email="wuser@test.com",
                first_name="Work", last_name="Out", role="client")
    db.add(user)
    db.flush()
    client = Client(user_id=user.user_id, weekly_streak=0)
    db.add(client)
    db.flush()
    return user, client


@pytest.fixture
def workout_client(db, workout_user):
    user, client = workout_user
    mock_user = MagicMock()
    mock_user.user_id = user.user_id
    mock_user.role = "client"
    mock_user.client = client

    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# GET /workouts: no workouts in DB returns an empty list.
def test_list_workouts_empty(workout_client):
    resp = workout_client.get("/workouts")
    assert resp.status_code == 200
    assert resp.json() == []


# GET /workouts/saved: no saved workouts returns an empty list.
def test_list_saved_workouts_empty(workout_client):
    resp = workout_client.get("/workouts/saved")
    assert resp.status_code == 200
    assert resp.json() == []


# GET /workouts/scheduled: no scheduled workouts returns an empty list.
def test_list_scheduled_workouts_empty(workout_client):
    resp = workout_client.get("/workouts/scheduled")
    assert resp.status_code == 200
    assert resp.json() == []


# GET /workouts/{workout_id}: non-existent ID returns 404.
def test_get_workout_not_found(workout_client):
    resp = workout_client.get("/workouts/9999")
    assert resp.status_code == 404


# POST /workouts: minimal payload creates a workout and returns 201 with the new ID.
def test_create_workout(workout_client):
    resp = workout_client.post("/workouts", json={"name": "Morning Run"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Morning Run"
    assert "workout_id" in data
    assert data["exercises"] == []


# POST /workouts with duplicate exercise IDs returns 400.
def test_create_workout_duplicate_exercises(workout_client):
    resp = workout_client.post("/workouts", json={
        "name": "Bad Plan",
        "exercises": [
            {"exercise_id": 1, "unit_id": 1},
            {"exercise_id": 1, "unit_id": 1},
        ],
    })
    assert resp.status_code == 400


# GET /workouts/{id}: created workout is accessible by its creator.
def test_get_workout_by_creator(workout_client, db, workout_user):
    user, _ = workout_user
    resp = workout_client.post("/workouts", json={"name": "Pull Day"})
    workout_id = resp.json()["workout_id"]
    resp = workout_client.get(f"/workouts/{workout_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Pull Day"


# DELETE /workouts/{id}: creator can delete their own workout and get 204.
def test_delete_workout(workout_client):
    create_resp = workout_client.post("/workouts", json={"name": "Temp Workout"})
    workout_id = create_resp.json()["workout_id"]
    resp = workout_client.delete(f"/workouts/{workout_id}")
    assert resp.status_code == 204
    assert workout_client.get(f"/workouts/{workout_id}").status_code == 404


# DELETE /workouts/{id}: deleting a non-existent workout returns 404.
def test_delete_workout_not_found(workout_client):
    resp = workout_client.delete("/workouts/9999")
    assert resp.status_code == 404


# POST /workouts/{id}/save: saves a workout for the user, returns 201.
def test_save_workout(workout_client):
    create_resp = workout_client.post("/workouts", json={"name": "Save Me"})
    workout_id = create_resp.json()["workout_id"]
    resp = workout_client.post(f"/workouts/{workout_id}/save")
    assert resp.status_code == 201


# POST /workouts/{id}/save twice returns 409.
def test_save_workout_duplicate(workout_client):
    create_resp = workout_client.post("/workouts", json={"name": "Save Twice"})
    workout_id = create_resp.json()["workout_id"]
    workout_client.post(f"/workouts/{workout_id}/save")
    resp = workout_client.post(f"/workouts/{workout_id}/save")
    assert resp.status_code == 409


# DELETE /workouts/{id}/save: unsaving a workout returns 204.
def test_unsave_workout(workout_client):
    create_resp = workout_client.post("/workouts", json={"name": "Unsave Me"})
    workout_id = create_resp.json()["workout_id"]
    workout_client.post(f"/workouts/{workout_id}/save")
    resp = workout_client.delete(f"/workouts/{workout_id}/save")
    assert resp.status_code == 204


# POST /workouts/{id}/schedule: scheduling a workout returns 201.
def test_schedule_workout(workout_client):
    create_resp = workout_client.post("/workouts", json={"name": "Schedule Me"})
    workout_id = create_resp.json()["workout_id"]
    resp = workout_client.post(f"/workouts/{workout_id}/schedule",
                               json={"scheduled_date": str(date.today())})
    assert resp.status_code == 201
    assert resp.json()["status"] == "Scheduled"


# DELETE /workouts/{id}/schedule/{date}: unscheduling a workout returns 204.
def test_unschedule_workout(workout_client):
    create_resp = workout_client.post("/workouts", json={"name": "Unschedule Me"})
    workout_id = create_resp.json()["workout_id"]
    today = str(date.today())
    workout_client.post(f"/workouts/{workout_id}/schedule", json={"scheduled_date": today})
    resp = workout_client.delete(f"/workouts/{workout_id}/schedule/{today}")
    assert resp.status_code == 204
