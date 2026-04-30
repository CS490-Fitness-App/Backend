from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from dependencies.rbac import get_current_user
from main import app
from models.chat import Chat
from models.coach import ClientCoach
from models.user import Client, Coach, User


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def chat_users(db):
    """Coach user, client user, their profiles, and an Active ClientCoach relationship."""
    coach_user = User(auth0_sub="coach|chat1", email="coach@chat.test",
                      first_name="Alice", last_name="Coach", role="coach")
    client_user = User(auth0_sub="client|chat1", email="client@chat.test",
                       first_name="Bob", last_name="Client", role="client")
    db.add_all([coach_user, client_user])
    db.flush()

    coach = Coach(user_id=coach_user.user_id, status_id=1)
    client = Client(user_id=client_user.user_id)
    db.add_all([coach, client])
    db.flush()

    db.add(ClientCoach(client_id=client.client_id, coach_id=coach.coach_id, status_name="Active"))
    db.flush()

    return {"coach_user": coach_user, "client_user": client_user,
            "coach": coach, "client": client}


@pytest.fixture
def api(db):
    """Factory: api(user) returns a TestClient with that user as the authenticated caller."""
    def _make(current_user):
        def _override_get_db():
            yield db
        app.dependency_overrides[get_db] = _override_get_db
        app.dependency_overrides[get_current_user] = lambda: current_user
        return TestClient(app)

    yield _make
    app.dependency_overrides.clear()


def _chat_id(u1: User, u2: User) -> int:
    """Replicates the router's synthetic chat_id formula."""
    return min(u1.user_id, u2.user_id) * 1_000_000 + max(u1.user_id, u2.user_id)


# ── list_chats ────────────────────────────────────────────────────────────────

# GET /chats/: a user who has sent or received no messages should get an empty list.
def test_list_chats_empty(api, chat_users):
    resp = api(chat_users["coach_user"]).get("/chats/")
    assert resp.status_code == 200
    assert resp.json() == []


# GET /chats/: after a message exists, the sender should see one conversation
# entry whose other_user_name resolves to the recipient's full name.
def test_list_chats_with_messages(api, db, chat_users):
    coach = chat_users["coach_user"]
    client = chat_users["client_user"]

    db.add(Chat(sender_id=coach.user_id, receiver_id=client.user_id, message="Hello!"))
    db.flush()

    resp = api(coach).get("/chats/")
    assert resp.status_code == 200
    convos = resp.json()
    assert len(convos) == 1
    assert convos[0]["other_user_name"] == "Bob Client"


# ── get_messages ──────────────────────────────────────────────────────────────

# GET /chats/{chat_id}/messages: a valid participant with no messages yet should
# receive an empty list, not an error.
def test_get_messages_empty(api, chat_users):
    coach = chat_users["coach_user"]
    client = chat_users["client_user"]
    cid = _chat_id(coach, client)

    resp = api(coach).get(f"/chats/{cid}/messages")
    assert resp.status_code == 200
    assert resp.json() == []


# GET /chats/{chat_id}/messages: messages should come back in chronological order
# (oldest first) with sender_name resolved from the User table, not stored as text.
def test_get_messages_history(api, db, chat_users):
    coach = chat_users["coach_user"]
    client = chat_users["client_user"]

    t1 = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc)
    db.add(Chat(sender_id=coach.user_id, receiver_id=client.user_id,
                message="First", sent_at=t1, created_at=t1, last_updated=t1))
    db.add(Chat(sender_id=client.user_id, receiver_id=coach.user_id,
                message="Second", sent_at=t2, created_at=t2, last_updated=t2))
    db.flush()
    cid = _chat_id(coach, client)

    resp = api(coach).get(f"/chats/{cid}/messages")
    assert resp.status_code == 200
    msgs = resp.json()
    assert [m["body"] for m in msgs] == ["First", "Second"]
    assert msgs[0]["sender_name"] == "Alice Coach"
    assert msgs[1]["sender_name"] == "Bob Client"


# GET /chats/{chat_id}/messages: a user whose user_id is not encoded in the chat_id
# should be rejected with 403, not allowed to read the conversation.
def test_get_messages_not_a_participant(api, db, chat_users):
    coach = chat_users["coach_user"]
    client = chat_users["client_user"]
    outsider = User(auth0_sub="other|1", email="outsider@chat.test",
                    first_name="Eve", last_name="Other", role="client")
    db.add(outsider)
    db.flush()

    cid = _chat_id(coach, client)
    resp = api(outsider).get(f"/chats/{cid}/messages")
    assert resp.status_code == 403


# GET /chats/{chat_id}/messages?since=: only messages whose sent_at is strictly after
# the cutoff should be returned; older messages must be excluded.
def test_get_messages_since_filter(api, db, chat_users):
    coach = chat_users["coach_user"]
    client = chat_users["client_user"]

    old = datetime(2025, 12, 30, tzinfo=timezone.utc)
    new = datetime(2026, 3, 12, tzinfo=timezone.utc)
    db.add(Chat(sender_id=coach.user_id, receiver_id=client.user_id,
                message="Old message", sent_at=old, created_at=old, last_updated=old))
    db.add(Chat(sender_id=client.user_id, receiver_id=coach.user_id,
                message="New message", sent_at=new, created_at=new, last_updated=new))
    db.flush()
    cid = _chat_id(coach, client)

    resp = api(coach).get(f"/chats/{cid}/messages?since=2026-01-01T00:00:00Z")
    assert resp.status_code == 200
    bodies = [m["body"] for m in resp.json()]
    assert "New message" in bodies
    assert "Old message" not in bodies


# ── send_message ──────────────────────────────────────────────────────────────

# POST /chats/{chat_id}/messages: a valid participant should receive the sent message
# back with the correct body, sender name, and chat_id in the response.
def test_send_message(api, db, chat_users):
    coach = chat_users["coach_user"]
    client = chat_users["client_user"]
    cid = _chat_id(coach, client)

    resp = api(coach).post(f"/chats/{cid}/messages", json={"body": "Hey there!"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["body"] == "Hey there!"
    assert data["sender_name"] == "Alice Coach"
    assert data["chat_id"] == cid


# POST /chats/{chat_id}/messages: a user whose user_id is not encoded in the chat_id
# should be rejected with 403 before any message is written.
def test_send_message_not_a_participant(api, db, chat_users):
    coach = chat_users["coach_user"]
    client = chat_users["client_user"]
    outsider = User(auth0_sub="other|2", email="outsider2@chat.test",
                    first_name="Eve", last_name="Other", role="client")
    db.add(outsider)
    db.flush()

    cid = _chat_id(coach, client)
    resp = api(outsider).post(f"/chats/{cid}/messages", json={"body": "Sneaky!"})
    assert resp.status_code == 403


# POST /chats/{chat_id}/messages: when the chat_id encodes a receiver user_id that no
# longer exists in the DB, the route should return 404 rather than crash.
def test_send_message_recipient_not_found(api, db, chat_users):
    coach = chat_users["coach_user"]
    ghost_uid = 99999
    fake_cid = min(coach.user_id, ghost_uid) * 1_000_000 + max(coach.user_id, ghost_uid)
    resp = api(coach).post(f"/chats/{fake_cid}/messages", json={"body": "Hello?"})
    assert resp.status_code == 404


# ── list_chats edge cases ─────────────────────────────────────────────────────

# GET /chats/: multiple messages with the same partner should collapse into a single
# conversation entry — the second message triggers the deduplication continue branch.
def test_list_chats_deduplicates_partner(api, db, chat_users):
    coach = chat_users["coach_user"]
    client = chat_users["client_user"]

    db.add(Chat(sender_id=coach.user_id, receiver_id=client.user_id, message="First"))
    db.add(Chat(sender_id=coach.user_id, receiver_id=client.user_id, message="Second"))
    db.flush()

    resp = api(coach).get("/chats/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# GET /chats/: when the current user is a client and the other user is a coach,
# the conversation should correctly assign coach_user_id and client_user_id.
def test_list_chats_as_client(api, db, chat_users):
    coach = chat_users["coach_user"]
    client = chat_users["client_user"]

    db.add(Chat(sender_id=client.user_id, receiver_id=coach.user_id, message="Hi coach"))
    db.flush()

    resp = api(client).get("/chats/")
    assert resp.status_code == 200
    convos = resp.json()
    assert len(convos) == 1
    assert convos[0]["coach_user_id"] == coach.user_id
    assert convos[0]["client_user_id"] == client.user_id


# GET /chats/: messages between two users of the same role fall into the else branch
# that assigns coach/client sides arbitrarily; the response should still be well-formed.
def test_list_chats_same_role_users(api, db):
    client_a = User(auth0_sub="c|same1", email="same1@chat.test",
                    first_name="Alice", last_name="A", role="client")
    client_b = User(auth0_sub="c|same2", email="same2@chat.test",
                    first_name="Bob", last_name="B", role="client")
    db.add_all([client_a, client_b])
    db.flush()

    db.add(Chat(sender_id=client_a.user_id, receiver_id=client_b.user_id, message="Hey"))
    db.flush()

    resp = api(client_a).get("/chats/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# ── get_messages ?since= without timezone ────────────────────────────────────

# GET /chats/{chat_id}/messages?since= with a timezone-naive timestamp: the router
# attaches UTC automatically so the filter still works without crashing.
def test_get_messages_since_naive_timezone(api, db, chat_users):
    coach = chat_users["coach_user"]
    client = chat_users["client_user"]

    new = datetime(2024, 6, 1, tzinfo=timezone.utc)
    db.add(Chat(sender_id=coach.user_id, receiver_id=client.user_id,
                message="Recent", sent_at=new, created_at=new, last_updated=new))
    db.flush()
    cid = _chat_id(coach, client)

    # No trailing Z or +00:00 — naive datetime string
    resp = api(coach).get(f"/chats/{cid}/messages?since=2021-01-01T00:00:00")
    assert resp.status_code == 200
    assert any(m["body"] == "Recent" for m in resp.json())


# ── create_or_get_chat (POST /chats/) ────────────────────────────────────────

# POST /chats/: happy path where a coach initiates a chat with their client using
# other_user_id — should return a ConversationOut with correct user IDs.
def test_create_chat_happy_path_as_coach(api, chat_users):
    coach = chat_users["coach_user"]
    client = chat_users["client_user"]

    resp = api(coach).post("/chats/", json={"other_user_id": client.user_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["coach_user_id"] == coach.user_id
    assert data["client_user_id"] == client.user_id


# POST /chats/: happy path where a client initiates the chat — the router must flip
# coach/client sides correctly when current_user is the client.
def test_create_chat_happy_path_as_client(api, chat_users):
    coach = chat_users["coach_user"]
    client = chat_users["client_user"]

    resp = api(client).post("/chats/", json={"other_user_id": coach.user_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["coach_user_id"] == coach.user_id
    assert data["client_user_id"] == client.user_id


# POST /chats/: passing other_coach_id instead of other_user_id — the route must
# resolve the Coach row to its user_id before proceeding.
def test_create_chat_via_coach_id(api, chat_users):
    client = chat_users["client_user"]
    coach_profile = chat_users["coach"]

    resp = api(client).post("/chats/", json={"other_coach_id": coach_profile.coach_id})
    assert resp.status_code == 200


# POST /chats/: other_coach_id that doesn't exist in the coaches table should
# return 404 before any further validation.
def test_create_chat_coach_not_found(api, chat_users):
    client = chat_users["client_user"]
    resp = api(client).post("/chats/", json={"other_coach_id": 99999})
    assert resp.status_code == 404


# POST /chats/: attempting to create a chat with your own user_id should return 400.
def test_create_chat_with_self(api, chat_users):
    coach = chat_users["coach_user"]
    resp = api(coach).post("/chats/", json={"other_user_id": coach.user_id})
    assert resp.status_code == 400


# POST /chats/: other_user_id that doesn't exist in the users table should return 404.
def test_create_chat_user_not_found(api, chat_users):
    coach = chat_users["coach_user"]
    resp = api(coach).post("/chats/", json={"other_user_id": 99999})
    assert resp.status_code == 404


# POST /chats/: admin users cannot participate in chats — should return 400 whether
# the admin is the caller or the target.
def test_create_chat_admin_involved(api, db, chat_users):
    admin_user = User(auth0_sub="admin|1", email="admin@chat.test",
                      first_name="Admin", last_name="User", role="admin")
    db.add(admin_user)
    db.flush()

    coach = chat_users["coach_user"]
    resp = api(coach).post("/chats/", json={"other_user_id": admin_user.user_id})
    assert resp.status_code == 400



# POST /chats/: valid coach and client users but no ClientCoach row between them
# should return 400 — the relationship must exist before chatting is allowed.
def test_create_chat_no_relationship(api, db, chat_users):
    new_client_user = User(auth0_sub="client|2", email="client2@chat.test",
                           first_name="Carol", last_name="New", role="client")
    db.add(new_client_user)
    db.flush()
    db.add(Client(user_id=new_client_user.user_id))
    db.flush()

    coach = chat_users["coach_user"]
    resp = api(coach).post("/chats/", json={"other_user_id": new_client_user.user_id})
    assert resp.status_code == 400


# POST /chats/: a user with role='coach' but no row in the coaches table should
# return 400 — the route validates the profile exists before allowing the chat.
def test_create_chat_missing_coach_profile(api, db, chat_users):
    ghost_coach = User(auth0_sub="coach|ghost", email="ghost@chat.test",
                       first_name="Ghost", last_name="Coach", role="coach")
    db.add(ghost_coach)
    db.flush()

    client = chat_users["client_user"]
    resp = api(client).post("/chats/", json={"other_user_id": ghost_coach.user_id})
    assert resp.status_code == 400
