# ORM models for the Reviews and Reports tables.
# Reviews store client ratings of coaches; Reports track misconduct complaints submitted against coaches.

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import relationship
from core.database import Base


def _now():
    return datetime.now(timezone.utc)


class Review(Base):
    __tablename__ = 'Reviews'

    review_id    = Column(Integer, primary_key=True, autoincrement=True)
    client_id    = Column(Integer, ForeignKey('Clients.client_id', ondelete='CASCADE'), nullable=False)
    coach_id     = Column(Integer, ForeignKey('Coaches.coach_id',  ondelete='CASCADE'), nullable=False)
    description  = Column(Text)
    rating       = Column(SmallInteger, nullable=False)
    created_at   = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=_now)

    client = relationship('Client')
    coach  = relationship('Coach')


class Report(Base):
    __tablename__ = 'Reports'

    report_id    = Column(Integer, primary_key=True, autoincrement=True)
    reporter_id  = Column(Integer, ForeignKey('Users.user_id',   ondelete='CASCADE'), nullable=False)
    coach_id     = Column(Integer, ForeignKey('Coaches.coach_id', ondelete='CASCADE'), nullable=False)
    reason       = Column(Text)
    status       = Column(String(50), default='Pending')
    created_at   = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=_now)

    reporter = relationship('User')
    coach    = relationship('Coach')
