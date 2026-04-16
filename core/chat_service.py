"""
Helper functions for working with the legacy flat `chat` table.
This module provides conversation-like helpers on top of the flat schema.
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, case
from models.chat import Chat
from datetime import datetime


def list_conversations(user_id: int, db: Session, limit: int = 50) -> List[Dict]:
    """Return recent conversation summaries for user_id.
    Each item: {counterpart_id, last_sent, message_count, last_message}
    """
    counterpart = case([(Chat.sender_id == user_id, Chat.receiver_id)], else_=Chat.sender_id).label('counterpart')

    q = (
        db.query(counterpart, func.max(Chat.sent_at).label('last_sent'), func.count(Chat.message_id).label('message_count'))
        .filter(or_(Chat.sender_id == user_id, Chat.receiver_id == user_id))
        .group_by(counterpart)
        .order_by(func.max(Chat.sent_at).desc())
        .limit(limit)
    )

    results = []
    for row in q:
        cp = row.counterpart
        last_sent = row.last_sent
        count = row.message_count
        # fetch last message text
        last_msg = (
            db.query(Chat)
            .filter(or_((Chat.sender_id == user_id) & (Chat.receiver_id == cp), (Chat.sender_id == cp) & (Chat.receiver_id == user_id)))
            .order_by(Chat.sent_at.desc())
            .limit(1)
            .one_or_none()
        )
        last_text = last_msg.message if last_msg is not None else None
        results.append({"counterpart_id": cp, "last_sent": last_sent, "message_count": count, "last_message": last_text})

    return results


def get_messages(user_a: int, user_b: int, db: Session, limit: int = 100, since: Optional[datetime] = None, before: Optional[datetime] = None, asc: bool = True) -> List[Chat]:
    """Return messages exchanged between user_a and user_b. Order ascending by default."""
    q = db.query(Chat).filter(
        or_((Chat.sender_id == user_a) & (Chat.receiver_id == user_b), (Chat.sender_id == user_b) & (Chat.receiver_id == user_a))
    )
    if since:
        q = q.filter(Chat.sent_at >= since)
    if before:
        q = q.filter(Chat.sent_at <= before)

    q = q.order_by(Chat.sent_at.asc() if asc else Chat.sent_at.desc()).limit(limit)
    return q.all()


def send_message(sender_id: int, receiver_id: int, message_text: str, db: Session) -> Chat:
    """Insert a new chat message and return it (committed)."""
    new = Chat(sender_id=sender_id, receiver_id=receiver_id, message=message_text)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new
