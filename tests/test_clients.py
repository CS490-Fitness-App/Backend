import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from core.database import get_db
from dependencies.rbac import require_client
from main import app
from models.log import Goal, GoalType
from models.user import User, Client


@pytest.fixture
def client_actor(db):
    user = User(auth0_sub="auth0|survey1", email="survey@test.com",
                first_name="Sur", last_name="Vey", role="client")
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def survey_client(db, client_actor):
    mock_user = MagicMock()
    mock_user.user_id = client_actor.user_id
    mock_user.role = "client"
    mock_user.client = None

    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_client] = lambda: mock_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# POST /users/register: new client with no existing profile is created and returns 201.
def test_register_client_new(survey_client):
    resp = survey_client.post("/users/register", json={"goal_type_ids": []})
    assert resp.status_code == 200
    data = resp.json()
    assert data["weekly_streak"] == 0


# POST /users/register: registering twice for the same user returns 409.
def test_register_client_duplicate(db, client_actor):
    existing_client = Client(user_id=client_actor.user_id, weekly_streak=0)
    db.add(existing_client)
    db.flush()

    mock_user = MagicMock()
    mock_user.user_id = client_actor.user_id
    mock_user.role = "client"
    mock_user.client = existing_client

    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_client] = lambda: mock_user
    with TestClient(app) as c:
        resp = c.post("/users/register", json={"goal_type_ids": []})
    app.dependency_overrides.clear()

    assert resp.status_code == 409


# POST /users/register: invalid goal_type_id returns 404.
def test_register_client_invalid_goal(survey_client):
    resp = survey_client.post("/users/register", json={"goal_type_ids": [9999]})
    assert resp.status_code == 404


# POST /users/register: valid goal_type_ids are persisted as Goal rows.
def test_register_client_with_goals(db, survey_client):
    goal_type = GoalType(goal_type_name="Weight Loss")
    db.add(goal_type)
    db.flush()
    resp = survey_client.post("/users/register", json={"goal_type_ids": [goal_type.goal_type_id]})
    assert resp.status_code == 200


# GET /users/goals: client with no goals returns an empty list.
def test_get_goals_empty(survey_client):
    resp = survey_client.get("/users/goals")
    assert resp.status_code == 200
    assert resp.json() == []


# GET /users/goals: after registration with goals, returns those goals.
def test_get_goals_after_register(db, client_actor, survey_client):
    goal_type = GoalType(goal_type_name="Muscle Gain")
    db.add(goal_type)
    db.flush()
    survey_client.post("/users/register", json={"goal_type_ids": [goal_type.goal_type_id]})
    resp = survey_client.get("/users/goals")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# GET /users/goal-types: no goal types seeded returns an empty list.
def test_get_goal_types_empty(client):
    resp = client.get("/users/goal-types")
    assert resp.status_code == 200
    assert resp.json() == []


# GET /users/goal-types: seeded goal types are returned with their IDs and names.
def test_get_goal_types_seeded(db, client):
    db.add_all([GoalType(goal_type_name="Endurance"), GoalType(goal_type_name="Flexibility")])
    db.flush()
    resp = client.get("/users/goal-types")
    assert resp.status_code == 200
    names = [g["goal_type_name"] for g in resp.json()]
    assert "Endurance" in names
    assert "Flexibility" in names


# PUT /users/goals: replaces existing goals with a new list.
def test_update_goals(db, client_actor, survey_client):
    goal1 = GoalType(goal_type_name="Strength")
    goal2 = GoalType(goal_type_name="Cardio")
    db.add_all([goal1, goal2])
    db.flush()

    survey_client.post("/users/register", json={"goal_type_ids": [goal1.goal_type_id]})
    resp = survey_client.put("/users/goals", json=[goal2.goal_type_id])
    assert resp.status_code == 200
    ids = [g["goal_type"]["goal_type_id"] for g in resp.json()]
    assert goal2.goal_type_id in ids
    assert goal1.goal_type_id not in ids


# PUT /users/goals: invalid goal_type_id returns 404.
def test_update_goals_invalid(survey_client):
    resp = survey_client.put("/users/goals", json=[9999])
    assert resp.status_code == 404
