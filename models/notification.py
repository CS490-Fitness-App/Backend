# ORM model for the Notifications table.
# Represents in-app notifications sent to users for events like coach requests and contract updates.

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from core.database import Base


def _now():
    return datetime.now(timezone.utc)


class Notification(Base):
    __tablename__ = 'notifications'

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    message         = Column(Text, nullable=False)
    is_read         = Column(Boolean, nullable=False, default=False)
    created_at      = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated    = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    user = relationship('User')
