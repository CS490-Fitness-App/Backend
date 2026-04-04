# ORM models for the Chat table (legacy) and the new Conversation/Message models.
# Chat is the original flat message table kept for backwards compatibility.
# Conversation represents a persistent chat session between a coach and client.
# Message represents an individual message within a conversation.

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import relationship
from core.database import Base


def _now():
    return datetime.now(timezone.utc)


# Legacy flat message table — kept for backwards compatibility
class Chat(Base):
    __tablename__ = 'chat'

    message_id   = Column(Integer, primary_key=True, autoincrement=True)
    sender_id    = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    receiver_id  = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    message      = Column(Text, nullable=False)
    sent_at      = Column(DateTime(timezone=True), nullable=False, default=_now)
    created_at   = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=_now)

    sender   = relationship('User', foreign_keys=[sender_id])
    receiver = relationship('User', foreign_keys=[receiver_id])


# A conversation thread between exactly one coach and one client
class Conversation(Base):
    __tablename__ = 'chats'

    chat_id        = Column(Integer, primary_key=True, autoincrement=True)
    coach_user_id  = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    client_user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    created_at     = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated   = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    coach_user  = relationship('User', foreign_keys=[coach_user_id])
    client_user = relationship('User', foreign_keys=[client_user_id])
    messages    = relationship('Message', back_populates='conversation')


# A single message within a conversation
class Message(Base):
    __tablename__ = 'messages'

    message_id   = Column(Integer, primary_key=True, autoincrement=True)
    chat_id      = Column(Integer, ForeignKey('chats.chat_id', ondelete='CASCADE'), nullable=False)
    sender_id    = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    message_type = Column(
        SAEnum('text', 'exercise_link', 'workout_plan_link', 'survey_snapshot'),
        nullable=False,
        default='text',
    )
    body         = Column(Text, nullable=True)       # text content for 'text' type
    ref_id       = Column(Integer, nullable=True)    # exercise_id or workout_id for link types
    snapshot     = Column(JSON, nullable=True)       # survey answer data for 'survey_snapshot'
    sent_at      = Column(DateTime(timezone=True), nullable=False, default=_now)
    created_at   = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    sender       = relationship('User', foreign_keys=[sender_id])
    conversation = relationship('Conversation', back_populates='messages')
