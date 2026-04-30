import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from core.auth0 import auth
from core.database import get_db
from dependencies.rbac import require_client, require_coach, require_admin
from main import app
from models.user import User


# ── fixtures ──────────────────────────────────────────────────────────────────

FAKE_CLAIMS = {"sub": "auth0|testuser", "email": "test@auth.test"}


@pytest.fixture
def auth_client(db):
    """TestClient with auth and get_db both overridden — no real Auth0 or MySQL needed."""
    def _override_get_db():
        yield db

    app.dependency_overrides[auth] = lambda: FAKE_CLAIMS
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def seeded_user(db):
    """A User row whose auth0_sub matches FAKE_CLAIMS, for returning-user tests."""
    user = User(
        auth0_sub=FAKE_CLAIMS["sub"],
        email="test@auth.test",
        first_name="Jane",
        last_name="Doe",
        role="client",
    )
    db.add(user)
    db.flush()
    return user


# ── logout ────────────────────────────────────────────────────────────────────

# POST /auth/logout: requires no authentication and no DB — returns a static message
# telling the frontend to clear its token and call the Auth0 logout endpoint.
def test_logout():
    resp = TestClient(app).post("/auth/logout")
    assert resp.status_code == 200
    assert "message" in resp.json()


# ── GET /auth/me ──────────────────────────────────────────────────────────────

# GET /auth/me: when the auth0_sub in the token matches a local user, the endpoint
# should return that user's profile with is_new_user=False.
def test_get_me_found(auth_client, seeded_user):
    resp = auth_client.get("/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@auth.test"
    assert data["is_new_user"] is False


# GET /auth/me: if no local user matches the token's sub, the endpoint should return
# 404 rather than crash, so the frontend knows to redirect to signup.
def test_get_me_not_found(auth_client):
    resp = auth_client.get("/auth/me")
    assert resp.status_code == 404


# ── POST /auth/signup ─────────────────────────────────────────────────────────

# POST /auth/signup: a brand-new auth0_sub with a valid email should create a user
# row and return is_new_user=True.
def test_signup_new_user(auth_client):
    resp = auth_client.post("/auth/signup", json={"email": "newuser@auth.test", "role": "client"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@auth.test"
    assert data["is_new_user"] is True


# POST /auth/signup: if a user with the same auth0_sub already exists, signup should
# return 409 to tell the frontend to call /login instead.
def test_signup_already_exists(auth_client, seeded_user):
    resp = auth_client.post("/auth/signup", json={"email": "other@auth.test", "role": "client"})
    assert resp.status_code == 409


# POST /auth/signup: when neither the payload nor the JWT claims contain an email,
# signup must return 400 rather than create a user without an email address.
def test_signup_no_email(auth_client):
    app.dependency_overrides[auth] = lambda: {"sub": "auth0|noemail"}
    resp = auth_client.post("/auth/signup", json={})
    assert resp.status_code == 400


# ── POST /auth/login ──────────────────────────────────────────────────────────

# POST /auth/login: first-ever login for a new sub with no matching email in the DB
# should create a new user and return is_new_user=True.
def test_login_new_user(auth_client):
    resp = auth_client.post("/auth/login", json={"email": "brand@new.test", "role": "client"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "brand@new.test"
    assert data["is_new_user"] is True


# POST /auth/login: when the auth0_sub already exists, login should return the existing
# user with is_new_user=False — this is the normal returning-user path.
def test_login_returning_user(auth_client, seeded_user):
    resp = auth_client.post("/auth/login", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["auth0_sub"] == FAKE_CLAIMS["sub"]
    assert data["is_new_user"] is False


# POST /auth/login: when there is no auth0_sub match but the email already exists,
# the route should merge by updating the existing user's sub rather than creating a duplicate.
def test_login_email_merge(auth_client, db):
    existing = User(auth0_sub="old|sub", email="test@auth.test", role="client")
    db.add(existing)
    db.flush()

    resp = auth_client.post("/auth/login", json={"email": "test@auth.test"})
    assert resp.status_code == 200
    assert resp.json()["is_new_user"] is False


# POST /auth/login: if no user matches the sub and neither the payload nor claims
# carry an email, login must return 400 — an email is required to create the account.
def test_login_no_email(auth_client):
    app.dependency_overrides[auth] = lambda: {"sub": "auth0|noemail2"}
    resp = auth_client.post("/auth/login", json={})
    assert resp.status_code == 400


# POST /auth/login: optional fields (first_name, last_name) that are missing on an
# existing user should be filled in from the payload on subsequent logins.
def test_login_fills_optional_fields(auth_client, db):
    user = User(auth0_sub=FAKE_CLAIMS["sub"], email="test@auth.test", role="client")
    db.add(user)
    db.flush()

    resp = auth_client.post("/auth/login", json={"first_name": "Jane", "last_name": "Doe"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"


# ── GET /auth/rbac/* ──────────────────────────────────────────────────────────

# GET /auth/rbac/client: a valid client token should receive a 200 with ok=True,
# confirming the RBAC dependency correctly passes client-role users through.
def test_rbac_client(db):
    mock_user = MagicMock()
    mock_user.role = "client"
    mock_user.user_id = 1

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_client] = lambda: mock_user

    resp = TestClient(app).get("/auth/rbac/client")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    app.dependency_overrides.clear()


# GET /auth/rbac/coach: same check for the coach RBAC guard.
def test_rbac_coach(db):
    mock_user = MagicMock()
    mock_user.role = "coach"
    mock_user.user_id = 2

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_coach] = lambda: mock_user

    resp = TestClient(app).get("/auth/rbac/coach")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    app.dependency_overrides.clear()


# GET /auth/rbac/admin: same check for the admin RBAC guard.
def test_rbac_admin(db):
    mock_user = MagicMock()
    mock_user.role = "admin"
    mock_user.user_id = 3

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_admin] = lambda: mock_user

    resp = TestClient(app).get("/auth/rbac/admin")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    app.dependency_overrides.clear()
