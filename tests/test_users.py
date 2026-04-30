import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from core.database import get_db
from dependencies.rbac import get_current_user
from main import app
from models.user import User, Client, Coach, CoachStatus


@pytest.fixture
def profile_user(db):
    user = User(auth0_sub="auth0|profile1", email="profile@test.com",
                first_name="Pro", last_name="File", role="client")
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def profile_client(db, profile_user):
    mock_user = profile_user

    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# GET /users/me: returns 200 with the current user's email and role.
def test_get_my_profile(profile_client, profile_user):
    resp = profile_client.get("/users/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "profile@test.com"
    assert data["role"] == "client"
    assert data["client_profile"] is None


# GET /users/me: a user with a Client record includes client_profile in the response.
def test_get_profile_with_client(db, profile_user):
    client = Client(user_id=profile_user.user_id, weekly_streak=2)
    db.add(client)
    db.flush()

    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: profile_user
    with TestClient(app) as c:
        resp = c.get("/users/me")
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["client_profile"] is not None
    assert data["client_profile"]["weekly_streak"] == 2


# PATCH /users/me: updating first_name returns the new name in the response.
def test_update_profile_first_name(profile_client):
    resp = profile_client.patch("/users/me", json={"first_name": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Updated"


# PATCH /users/me: updating last_name returns the new value.
def test_update_profile_last_name(profile_client):
    resp = profile_client.patch("/users/me", json={"last_name": "Newlast"})
    assert resp.status_code == 200
    assert resp.json()["last_name"] == "Newlast"


# PATCH /users/me: setting goal_weight_lb on a user with no Client profile returns 400.
def test_update_goal_weight_no_client(profile_client):
    resp = profile_client.patch("/users/me", json={"goal_weight_lb": 150.0})
    assert resp.status_code == 400


# PATCH /users/me: setting goal_weight_lb <= 0 returns 400.
def test_update_goal_weight_invalid(db, profile_user):
    client = Client(user_id=profile_user.user_id, weekly_streak=0)
    db.add(client)
    db.flush()

    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: profile_user
    with TestClient(app) as c:
        resp = c.patch("/users/me", json={"goal_weight_lb": 0})
    app.dependency_overrides.clear()

    assert resp.status_code == 400


# PATCH /users/me: setting bio on a user with no Coach profile returns 400.
def test_update_bio_no_coach(profile_client):
    resp = profile_client.patch("/users/me", json={"bio": "New bio"})
    assert resp.status_code == 400


# PATCH /users/me: empty payload (no fields) succeeds with 200 and makes no changes.
def test_update_profile_no_changes(profile_client, profile_user):
    resp = profile_client.patch("/users/me", json={})
    assert resp.status_code == 200
    assert resp.json()["first_name"] == profile_user.first_name
