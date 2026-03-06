# ORM model for the Notebook table.
# Stores personal notes and to-do entries created by individual users.

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from database import Base


def _now():
    return datetime.now(timezone.utc)


class Notebook(Base):
    __tablename__ = 'Notebook'

    note_id      = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'), nullable=False)
    content      = Column(Text)
    created_at   = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=_now)

    user = relationship('User')
