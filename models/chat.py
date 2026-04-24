# ORM model for the legacy flat Chat table
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from core.database import Base


def _now():
    return datetime.now(timezone.utc)


class Chat(Base):
    __tablename__ = 'chat'

    message_id   = Column(Integer, primary_key=True, autoincrement=True)
    sender_id    = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    receiver_id  = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    message      = Column(Text, nullable=False)
    sent_at      = Column(DateTime(timezone=True), nullable=False, default=_now)
    created_at   = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=_now)

    # Relationships exist for convenience, but the DB is a flat message table
    sender   = relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = relationship('User', foreign_keys=[receiver_id], backref='received_messages')
