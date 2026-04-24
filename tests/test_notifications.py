import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from core.database import get_db
from dependencies.rbac import get_current_user, require_admin
from main import app
from models.notification import Notification
from models.user import User
from routers.notifications import notify


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def users(db):
    """Two plain users: one owner, one other."""
    owner = User(auth0_sub="user|owner1", email="owner@test.test",
                 first_name="Alice", last_name="Owner", role="client")
    other = User(auth0_sub="user|other1", email="other@test.test",
                 first_name="Bob", last_name="Other", role="client")
    db.add_all([owner, other])
    db.flush()
    return {"owner": owner, "other": other}


@pytest.fixture
def api(db):
    """Factory: api(user) → TestClient authenticated as that user."""
    def _make(current_user):
        def _override_get_db():
            yield db
        app.dependency_overrides[get_db] = _override_get_db
        app.dependency_overrides[get_current_user] = lambda: current_user
        return TestClient(app)

    yield _make
    app.dependency_overrides.clear()


@pytest.fixture
def admin_api(db):
    """TestClient authenticated as an admin (bypasses require_admin and get_current_user)."""
    mock_admin = MagicMock()
    mock_admin.role = "admin"
    mock_admin.user_id = 9999

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_admin] = lambda: mock_admin
    app.dependency_overrides[get_current_user] = lambda: mock_admin

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ── notify() helper ───────────────────────────────────────────────────────────

# notify() should create a Notification row and return it without committing.
def test_notify_helper_creates_notification(db, users):
    owner = users["owner"]
    n = notify(db, user_id=owner.user_id, message="Hello!")
    db.commit()
    db.refresh(n)

    assert n.notification_id is not None
    assert n.user_id == owner.user_id
    assert n.message == "Hello!"
    assert n.is_read is False


# ── POST /notifications/ ──────────────────────────────────────────────────────

# Admin can create a notification for an existing user.
def test_create_notification_ok(admin_api, db, users):
    owner = users["owner"]
    resp = admin_api.post("/notifications/", json={"user_id": owner.user_id, "message": "Welcome!"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["user_id"] == owner.user_id
    assert body["message"] == "Welcome!"
    assert body["is_read"] is False


# Admin gets 404 when targeting a user_id that does not exist.
def test_create_notification_user_not_found(admin_api):
    resp = admin_api.post("/notifications/", json={"user_id": 99999, "message": "Ghost"})
    assert resp.status_code == 404


# ── GET /notifications/{user_id}/count ───────────────────────────────────────

# Owner gets an unread count of 0 when they have no notifications.
def test_get_unread_count_empty(api, users):
    owner = users["owner"]
    resp = api(owner).get(f"/notifications/{owner.user_id}/count")
    assert resp.status_code == 200
    assert resp.json() == {"unread_count": 0}


# Unread count reflects only is_read=False notifications for that user.
def test_get_unread_count_nonzero(api, db, users):
    owner = users["owner"]
    db.add_all([
        Notification(user_id=owner.user_id, message="A", is_read=False),
        Notification(user_id=owner.user_id, message="B", is_read=True),
    ])
    db.flush()

    resp = api(owner).get(f"/notifications/{owner.user_id}/count")
    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 1


# A different (non-admin) user cannot view another user's unread count.
def test_get_unread_count_forbidden(api, users):
    owner = users["owner"]
    other = users["other"]
    resp = api(other).get(f"/notifications/{owner.user_id}/count")
    assert resp.status_code == 403


# ── GET /notifications/{user_id} ──────────────────────────────────────────────

# Owner with no notifications gets an empty list.
def test_get_notifications_empty(api, users):
    owner = users["owner"]
    resp = api(owner).get(f"/notifications/{owner.user_id}")
    assert resp.status_code == 200
    assert resp.json() == []


# Notifications are returned with unread ones first; after the call all are marked read.
def test_get_notifications_marks_as_read(api, db, users):
    owner = users["owner"]
    db.add_all([
        Notification(user_id=owner.user_id, message="Unread", is_read=False),
        Notification(user_id=owner.user_id, message="Already read", is_read=True),
    ])
    db.flush()

    resp = api(owner).get(f"/notifications/{owner.user_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    # unread notification is first in the response (is_read was False before the fetch)
    assert body[0]["is_read"] is False
    assert body[0]["message"] == "Unread"

    # after the GET, the previously-unread row is now marked read in the DB
    row = db.query(Notification).filter(Notification.message == "Unread").first()
    assert row.is_read is True


# A different (non-admin) user cannot view another user's notifications.
def test_get_notifications_forbidden(api, users):
    owner = users["owner"]
    other = users["other"]
    resp = api(other).get(f"/notifications/{owner.user_id}")
    assert resp.status_code == 403


# Admin can view any user's notifications.
def test_get_notifications_admin_can_view_others(admin_api, db, users):
    owner = users["owner"]
    db.add(Notification(user_id=owner.user_id, message="Admin visible"))
    db.flush()

    resp = admin_api.get(f"/notifications/{owner.user_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# ── DELETE /notifications/{notification_id} ───────────────────────────────────

# Owner can delete their own notification; response confirms deletion.
def test_delete_notification_ok(api, db, users):
    owner = users["owner"]
    n = Notification(user_id=owner.user_id, message="Delete me")
    db.add(n)
    db.flush()

    resp = api(owner).delete(f"/notifications/{n.notification_id}")
    assert resp.status_code == 200
    assert "deleted" in resp.json()["message"].lower()

    assert db.query(Notification).filter(Notification.notification_id == n.notification_id).first() is None


# Deleting a notification_id that does not exist returns 404.
def test_delete_notification_not_found(api, users):
    owner = users["owner"]
    resp = api(owner).delete("/notifications/99999")
    assert resp.status_code == 404


# A user cannot delete a notification that belongs to someone else.
def test_delete_notification_forbidden(api, db, users):
    owner = users["owner"]
    other = users["other"]
    n = Notification(user_id=owner.user_id, message="Not yours")
    db.add(n)
    db.flush()

    resp = api(other).delete(f"/notifications/{n.notification_id}")
    assert resp.status_code == 403
