# ORM model for the Notifications table.
# Represents in-app notifications sent to users for events like coach requests and contract updates.

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from database import Base


def _now():
    return datetime.now(timezone.utc)


class Notification(Base):
    __tablename__ = 'Notifications'

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'), nullable=False)
    message         = Column(Text, nullable=False)
    created_at      = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated    = Column(DateTime(timezone=True), nullable=False, default=_now)

    user = relationship('User')
