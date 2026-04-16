# Handles chat endpoints (UC 3.8): retrieving message history and sending messages.
# The DB has a single flat `chat` table (message_id, sender_id, receiver_id, message, sent_at).
# A "conversation" is derived from a unique (sender_id, receiver_id) pair.
# chat_id is synthetic: min(uid_a, uid_b) * 1_000_000 + max(uid_a, uid_b).

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from dependencies.rbac import get_current_user
from models.chat import Chat
from models.user import Client, Coach, User
from models.coach import ClientCoach
from schemas.chat import ChatCreateIn, ConversationOut, MessageIn, MessageOut

router = APIRouter(prefix="/chats", tags=["chat"], redirect_slashes=False)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_chat_id(uid_a: int, uid_b: int) -> int:
    """Stable, order-independent synthetic chat_id for a pair of users."""
    return min(uid_a, uid_b) * 1_000_000 + max(uid_a, uid_b)


def _decode_chat_id(chat_id: int):
    """Return (uid_small, uid_large) from a synthetic chat_id."""
    return chat_id // 1_000_000, chat_id % 1_000_000


def _full_name(user: User) -> str:
    return f"{user.first_name or ''} {user.last_name or ''}".strip() or "Unknown"


def _assert_participant(chat_id: int, user_id: int):
    """Raise 403 if the caller is not one of the two participants. Returns (uid_a, uid_b)."""
    uid_a, uid_b = _decode_chat_id(chat_id)
    if user_id not in (uid_a, uid_b):
        raise HTTPException(status_code=403, detail="You are not a participant in this chat.")
    return uid_a, uid_b


def _message_out(msg: Chat) -> MessageOut:
    """Build MessageOut from a Chat row (sender must be eagerly loaded)."""
    return MessageOut(
        message_id=msg.message_id,
        chat_id=_make_chat_id(msg.sender_id, msg.receiver_id),
        sender_id=msg.sender_id,
        sender_name=_full_name(msg.sender),
        message_type='text',
        body=msg.message,
        ref_id=None,
        snapshot=None,
        sent_at=msg.sent_at,
    )


# ── Endpoints ────────────────────────────────────────────────────────────────

# POST /chats — resolve a chat_id for the current user and another user (no DB write; conversation is implicit)
@router.post("/", response_model=ConversationOut, status_code=200)
def create_or_get_chat(
    data: ChatCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # resolve other_user_id from either field
    other_user_id = data.other_user_id
    if other_user_id is None and data.other_coach_id is not None:
        coach_row = db.query(Coach).filter(Coach.coach_id == data.other_coach_id).first()
        if not coach_row:
            raise HTTPException(status_code=404, detail="Coach not found.")
        other_user_id = coach_row.user_id

    if other_user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="You cannot create a chat with yourself.")

    other_user = db.query(User).filter(User.user_id == other_user_id).first()
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Admins cannot participate in coach-client chats
    if current_user.role == 'admin' or other_user.role == 'admin':
        raise HTTPException(status_code=400, detail="Admin users cannot participate in coach-client chats.")

    # Both users must be different roles (one coach, one client)
    if current_user.role == other_user.role:
        raise HTTPException(status_code=400, detail="A chat must be between a coach and a client.")

    # Determine coach/client sides
    if current_user.role == 'coach':
        coach_user, client_user = current_user, other_user
    else:
        coach_user, client_user = other_user, current_user

    # Validate that a coach-client relationship exists (must not be Declined)
    coach_profile = db.query(Coach).filter(Coach.user_id == coach_user.user_id).first()
    client_profile = db.query(Client).filter(Client.user_id == client_user.user_id).first()

    if not coach_profile or not client_profile:
        raise HTTPException(status_code=400, detail="Could not find coach or client profile.")

    rel_exists = db.query(ClientCoach.client_id).filter(
        ClientCoach.coach_id == coach_profile.coach_id,
        ClientCoach.client_id == client_profile.client_id,
        ClientCoach.status_name != 'Declined',
    ).first()
    if not rel_exists:
        raise HTTPException(status_code=400, detail="No coach-client relationship exists between these users.")

    uid = current_user.user_id
    coach_uid = coach_user.user_id
    client_uid = client_user.user_id

    return ConversationOut(
        chat_id=_make_chat_id(uid, other_user_id),
        coach_user_id=coach_uid,
        client_user_id=client_uid,
        other_user_name=_full_name(other_user),
        created_at=datetime.now(timezone.utc),
    )


# GET /chats — list unique conversations the current user is part of
@router.get("/", response_model=list[ConversationOut])
def list_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = current_user.user_id

    # fetch all messages involving this user, most recent first
    rows = (
        db.query(Chat)
        .options(joinedload(Chat.sender), joinedload(Chat.receiver))
        .filter(or_(Chat.sender_id == uid, Chat.receiver_id == uid))
        .order_by(Chat.sent_at.desc())
        .all()
    )

    # one ConversationOut per unique conversation partner
    seen: dict[int, ConversationOut] = {}
    for msg in rows:
        other_id = msg.receiver_id if msg.sender_id == uid else msg.sender_id
        if other_id in seen:
            continue
        other_user: User = msg.receiver if msg.sender_id == uid else msg.sender

        # determine coach/client sides from user roles
        if current_user.role == 'coach':
            coach_uid, client_uid = uid, other_id
        elif other_user.role == 'coach':
            coach_uid, client_uid = other_id, uid
        else:
            # both same role (e.g. two clients) — assign arbitrarily
            coach_uid, client_uid = uid, other_id

        seen[other_id] = ConversationOut(
            chat_id=_make_chat_id(uid, other_id),
            coach_user_id=coach_uid,
            client_user_id=client_uid,
            other_user_name=_full_name(other_user),
            created_at=msg.sent_at,
        )

    return list(seen.values())


# GET /chats/{chat_id}/messages — fetch messages; supports polling via ?since=
@router.get("/{chat_id}/messages", response_model=list[MessageOut])
def get_messages(
    chat_id: int,
    since: Optional[datetime] = Query(None, description="Return only messages sent after this UTC timestamp (ISO 8601)."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid_a, uid_b = _assert_participant(chat_id, current_user.user_id)

    if since is not None and since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)

    query = (
        db.query(Chat)
        .options(joinedload(Chat.sender))
        .filter(
            or_(
                (Chat.sender_id == uid_a) & (Chat.receiver_id == uid_b),
                (Chat.sender_id == uid_b) & (Chat.receiver_id == uid_a),
            )
        )
    )
    if since is not None:
        query = query.filter(Chat.sent_at > since)

    messages = query.order_by(Chat.sent_at.asc()).all()
    return [_message_out(msg) for msg in messages]


# POST /chats/{chat_id}/messages — send a message
@router.post("/{chat_id}/messages", response_model=MessageOut, status_code=201)
def send_message(
    chat_id: int,
    data: MessageIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid_a, uid_b = _assert_participant(chat_id, current_user.user_id)
    receiver_id = uid_b if current_user.user_id == uid_a else uid_a

    # verify receiver exists
    if not db.query(User.user_id).filter(User.user_id == receiver_id).first():
        raise HTTPException(status_code=404, detail="Recipient user not found.")

    msg = Chat(
        sender_id=current_user.user_id,
        receiver_id=receiver_id,
        message=data.body,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # reload with sender relationship for the response
    msg = (
        db.query(Chat)
        .options(joinedload(Chat.sender))
        .filter(Chat.message_id == msg.message_id)
        .first()
    )
    return _message_out(msg)
