import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from core.database import get_db
from dependencies.rbac import require_client, get_current_user
from main import app
from models.user import User, Client


@pytest.fixture
def dash_actors(db):
    user = User(auth0_sub="auth0|dash1", email="dash@test.com",
                first_name="Dash", last_name="Client", role="client")
    db.add(user)
    db.flush()
    client = Client(user_id=user.user_id, weekly_streak=3)
    db.add(client)
    db.flush()
    return user, client


@pytest.fixture
def dash_client(db, dash_actors):
    user, client = dash_actors
    mock_user = MagicMock()
    mock_user.user_id = user.user_id
    mock_user.role = "client"
    mock_user.client = client

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_client] = lambda: mock_user
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# GET /dashboard/client: with a seeded user and client, returns 200 with the user's full name.
def test_client_dashboard_basic(dash_client):
    resp = dash_client.get("/dashboard/client")
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Dash Client"
    assert data["weekly_streak"] == 0


# GET /dashboard/client: with no workouts or logs in DB, all fields fall back to safe defaults.
def test_client_dashboard_defaults(dash_client):
    resp = dash_client.get("/dashboard/client")
    assert resp.status_code == 200
    data = resp.json()
    assert data["today_workout"] == "No workout available."
    assert data["current_plan_name"] == "No active workout plan"
    assert data["coach_name"] == "No coach assigned"
    assert data["today_workouts"] == []


# GET /dashboard/client: with no client profile in DB, all numeric fields default to None/0.
def test_client_dashboard_no_client_profile(db):
    user = User(auth0_sub="auth0|dash2", email="dash2@test.com",
                first_name="Bare", last_name="User", role="client")
    db.add(user)
    db.flush()

    mock_user = MagicMock()
    mock_user.user_id = user.user_id
    mock_user.role = "client"
    mock_user.client = None

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_client] = lambda: mock_user
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with TestClient(app) as c:
        resp = c.get("/dashboard/client")

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["weekly_streak"] == 0
    assert data["current_weight_lb"] is None
