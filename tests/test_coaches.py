import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from core.database import get_db
from dependencies.rbac import require_client, require_coach
from main import app
from models.coach import ClientCoach
from models.payment import Card, CardType
from models.user import User, Coach, CoachStatus, Client


@pytest.fixture
def coach_setup(db):
    active_status = CoachStatus(status_name="Active")
    pending_status = CoachStatus(status_name="Pending")
    db.add_all([active_status, pending_status])
    db.flush()

    coach_user = User(auth0_sub="auth0|coachA", email="coachA@test.com",
                      first_name="Alex", last_name="Coach", role="coach")
    db.add(coach_user)
    db.flush()

    coach = Coach(user_id=coach_user.user_id, status_id=active_status.status_id,
                  accepting_clients=True, hourly_rate=75.0, gender="Male")
    db.add(coach)
    db.flush()

    client_user = User(auth0_sub="auth0|clientA", email="clientA@test.com",
                       first_name="Amy", last_name="Client", role="client")
    db.add(client_user)
    db.flush()

    client = Client(user_id=client_user.user_id, weekly_streak=0)
    db.add(client)

    card_type = CardType(card_type_name="Visa")
    db.add(card_type)
    db.flush()

    card = Card(user_id=client_user.user_id, card_type_id=card_type.card_type_id,
                card_number="************1234", expiry_month=12, expiry_year=2030, is_default=True)
    db.add(card)
    db.flush()

    return {"coach": coach, "coach_user": coach_user, "client": client, "client_user": client_user,
            "active_status": active_status}


@pytest.fixture
def browse_client(db):
    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client_request_client(db, coach_setup):
    mock_user = MagicMock()
    mock_user.user_id = coach_setup["client_user"].user_id
    mock_user.role = "client"
    mock_user.client = coach_setup["client"]
    mock_user.first_name = "Amy"
    mock_user.last_name = "Client"

    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_client] = lambda: mock_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def coach_auth_client(db, coach_setup):
    mock_user = MagicMock()
    mock_user.user_id = coach_setup["coach_user"].user_id
    mock_user.role = "coach"
    mock_user.coach = coach_setup["coach"]
    mock_user.first_name = "Alex"
    mock_user.last_name = "Coach"

    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_coach] = lambda: mock_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# GET /coaches/: no coaches in DB returns an empty list.
def test_browse_coaches_empty(browse_client):
    resp = browse_client.get("/coaches/")
    assert resp.status_code == 200
    assert resp.json() == []


# GET /coaches/: a seeded Active coach who accepts clients appears in results.
def test_browse_coaches_returns_active_coach(db, coach_setup):
    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        resp = c.get("/coaches/")
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["first_name"] == "Alex"


# POST /coaches/request: requesting a non-existent coach_id returns 404.
def test_send_request_coach_not_found(client_request_client):
    resp = client_request_client.post("/coaches/request?coach_id=9999")
    assert resp.status_code == 404


# POST /coaches/request: valid coach → request is created and returns success message.
def test_send_request_success(db, client_request_client, coach_setup):
    coach_id = coach_setup["coach"].coach_id
    resp = client_request_client.post(f"/coaches/request?coach_id={coach_id}")
    assert resp.status_code == 200
    assert "message" in resp.json()


# POST /coaches/request: duplicate pending request returns 409.
def test_send_request_duplicate(db, client_request_client, coach_setup):
    coach_id = coach_setup["coach"].coach_id
    client_request_client.post(f"/coaches/request?coach_id={coach_id}")
    resp = client_request_client.post(f"/coaches/request?coach_id={coach_id}")
    assert resp.status_code == 409


# POST /coaches/request/accept: no pending request found returns 404.
def test_accept_request_not_found(coach_auth_client):
    resp = coach_auth_client.post("/coaches/request/accept?client_id=9999")
    assert resp.status_code == 404


# POST /coaches/request/decline: no pending request found returns 404.
def test_decline_request_not_found(coach_auth_client):
    resp = coach_auth_client.post("/coaches/request/decline?client_id=9999")
    assert resp.status_code == 404


# POST /coaches/request/accept: existing pending request is accepted and returns success.
def test_accept_request_success(db, coach_auth_client, coach_setup):
    client_id = coach_setup["client"].client_id
    coach_id = coach_setup["coach"].coach_id
    db.add(ClientCoach(client_id=client_id, coach_id=coach_id, status_name="Pending"))
    db.flush()
    resp = coach_auth_client.post(f"/coaches/request/accept?client_id={client_id}")
    assert resp.status_code == 200


# GET /coaches/me: coach with a DB profile returns 200 with their coach_id.
def test_get_my_coach_profile(db, coach_setup):
    mock_user = MagicMock()
    mock_user.user_id = coach_setup["coach_user"].user_id

    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_coach] = lambda: mock_user
    with TestClient(app) as c:
        resp = c.get("/coaches/me")
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["coach_id"] == coach_setup["coach"].coach_id
