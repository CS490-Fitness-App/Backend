# Handles chat endpoints (UC 3.8): retrieving message history and sending messages between users.
# Real-time support via polling — GET /chats/{chat_id}/messages?since=<timestamp> returns only new messages.

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from dependencies.rbac import get_current_user
from models.chat import Conversation, Message
from models.coach import ClientCoach
from models.exercise import Exercise
from models.user import Client, Coach, User
from models.workout import Workout
from schemas.chat import ChatCreateIn, ConversationOut, MessageIn, MessageOut

router = APIRouter(prefix="/chats", tags=["chat"], redirect_slashes=False)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _assert_participant(chat: Conversation, user_id: int) -> None:
    """Raise 403 if the caller is not one of the two participants in the chat."""
    if user_id not in (chat.coach_user_id, chat.client_user_id):
        raise HTTPException(status_code=403, detail="You are not a participant in this chat.")


def _full_name(user) -> str:
    return f"{user.first_name or ''} {user.last_name or ''}".strip() or "Unknown"


def _message_out(msg: Message) -> MessageOut:
    """Build MessageOut from a Message ORM object (sender must be eagerly loaded)."""
    return MessageOut(
        message_id=msg.message_id,
        chat_id=msg.chat_id,
        sender_id=msg.sender_id,
        sender_name=_full_name(msg.sender),
        message_type=msg.message_type,
        body=msg.body,
        ref_id=msg.ref_id,
        snapshot=msg.snapshot,
        sent_at=msg.sent_at,
    )


def _conversation_out(chat: Conversation, caller_user_id: int) -> ConversationOut:
    """Build ConversationOut, resolving other_user_name relative to the caller."""
    if caller_user_id == chat.coach_user_id:
        other_user = chat.client_user
    else:
        other_user = chat.coach_user
    return ConversationOut(
        chat_id=chat.chat_id,
        coach_user_id=chat.coach_user_id,
        client_user_id=chat.client_user_id,
        other_user_name=_full_name(other_user),
        created_at=chat.created_at,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

# GET /chats — list all conversations the current user is part of
@router.get("/", response_model=list[ConversationOut])
def list_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = current_user.user_id

    # eager-load both participants to avoid N+1 per conversation
    chats = (
        db.query(Conversation)
        .options(
            joinedload(Conversation.coach_user),
            joinedload(Conversation.client_user),
        )
        .filter(
            or_(
                Conversation.coach_user_id == uid,
                Conversation.client_user_id == uid,
            )
        )
        .order_by(Conversation.last_updated.desc())
        .all()
    )

    return [_conversation_out(chat, uid) for chat in chats]


# POST /chats — create a new conversation between a coach and client (returns existing if already present)
@router.post("/", response_model=ConversationOut, status_code=200)
def create_chat(
    data: ChatCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # cannot chat with yourself
    if data.other_user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="You cannot create a chat with yourself.")

    # fetch the other user
    other_user = db.query(User).filter(User.user_id == data.other_user_id).first()
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found.")

    # admins cannot participate in coach-client chats
    if current_user.role == 'admin' or other_user.role == 'admin':
        raise HTTPException(status_code=400, detail="Admin users cannot participate in coach-client chats.")

    # both users must be different roles (one coach, one client)
    if current_user.role == other_user.role:
        raise HTTPException(status_code=400, detail="A chat must be between a coach and a client.")

    # determine which user is the coach and which is the client
    if current_user.role == 'coach':
        coach_user, client_user = current_user, other_user
    else:
        coach_user, client_user = other_user, current_user

    # validate that a coach-client relationship exists (ClientCoach uses coach_id/client_id, not user_ids)
    coach  = db.query(Coach).filter(Coach.user_id == coach_user.user_id).first()
    client = db.query(Client).filter(Client.user_id == client_user.user_id).first()

    if not coach or not client:
        raise HTTPException(status_code=400, detail="Could not find coach or client profile.")

    rel = db.query(ClientCoach).filter(
        ClientCoach.coach_id == coach.coach_id,
        ClientCoach.client_id == client.client_id,
        ClientCoach.status_name != 'Declined',
    ).first()
    if not rel:
        raise HTTPException(status_code=400, detail="No coach-client relationship exists between these users.")

    # return existing chat if the pair already has one (avoids unique constraint error)
    existing = (
        db.query(Conversation)
        .options(joinedload(Conversation.coach_user), joinedload(Conversation.client_user))
        .filter(
            Conversation.coach_user_id == coach_user.user_id,
            Conversation.client_user_id == client_user.user_id,
        )
        .first()
    )
    if existing:
        return _conversation_out(existing, current_user.user_id)

    # create the conversation
    chat = Conversation(
        coach_user_id=coach_user.user_id,
        client_user_id=client_user.user_id,
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)

    # reload with relationships for the response
    chat = (
        db.query(Conversation)
        .options(joinedload(Conversation.coach_user), joinedload(Conversation.client_user))
        .filter(Conversation.chat_id == chat.chat_id)
        .first()
    )
    return _conversation_out(chat, current_user.user_id)


# GET /chats/{chat_id}/messages — fetch messages; supports polling via ?since=
@router.get("/{chat_id}/messages", response_model=list[MessageOut])
def get_messages(
    chat_id: int,
    since: Optional[datetime] = Query(None, description="Return only messages sent after this UTC timestamp (ISO 8601). Use for polling."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # fetch the conversation
    chat = db.query(Conversation).filter(Conversation.chat_id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found.")

    _assert_participant(chat, current_user.user_id)

    # normalize `since` to UTC — FastAPI may parse naive datetimes from clients
    if since is not None and since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)

    # build query; eager-load sender to avoid N+1 per message
    query = (
        db.query(Message)
        .options(joinedload(Message.sender))
        .filter(Message.chat_id == chat_id)
    )
    if since is not None:
        query = query.filter(Message.sent_at > since)

    messages = query.order_by(Message.sent_at.asc()).all()
    return [_message_out(msg) for msg in messages]


# POST /chats/{chat_id}/messages — send a message
@router.post("/{chat_id}/messages", response_model=MessageOut, status_code=201)
def send_message(
    chat_id: int,
    data: MessageIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # fetch the conversation
    chat = db.query(Conversation).filter(Conversation.chat_id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found.")

    _assert_participant(chat, current_user.user_id)

    # validate ref_id for link message types
    if data.type == 'exercise_link':
        if not db.query(Exercise).filter(Exercise.exercise_id == data.ref_id).first():
            raise HTTPException(status_code=404, detail="Exercise not found.")
    elif data.type == 'workout_plan_link':
        if not db.query(Workout).filter(Workout.workout_id == data.ref_id).first():
            raise HTTPException(status_code=404, detail="Workout not found.")

    # create and persist the message; bump conversation.last_updated so GET /chats sorts correctly
    msg = Message(
        chat_id=chat_id,
        sender_id=current_user.user_id,
        message_type=data.type,
        body=data.body,
        ref_id=data.ref_id,
        snapshot=data.snapshot,
    )
    db.add(msg)
    chat.last_updated = datetime.now(timezone.utc)
    db.commit()
    db.refresh(msg)

    # reload with sender relationship for the response
    msg = (
        db.query(Message)
        .options(joinedload(Message.sender))
        .filter(Message.message_id == msg.message_id)
        .first()
    )
    return _message_out(msg)
