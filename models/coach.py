# ORM models for coach-specific tables: Coach_Certifications, Coach_Session_Formats, Coach_Availability, Coach_Specialities, and Client_Coach.
# Captures a coach's credentials, schedule, and their active relationships with clients.

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Table, Time, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


def _now():
    return datetime.now(timezone.utc)


# Junction table: coaches ↔ session formats (no extra columns)
coach_session_formats = Table(
    'Coach_Session_Formats',
    Base.metadata,
    Column('coach_id',          Integer, ForeignKey('Coaches.coach_id',                  ondelete='CASCADE'), primary_key=True),
    Column('session_format_id', Integer, ForeignKey('Session_Formats.session_format_id', ondelete='CASCADE'), primary_key=True),
)

# Junction table: coaches ↔ goal types / specialities (no extra columns)
coach_specialities = Table(
    'Coach_Specialities',
    Base.metadata,
    Column('coach_id',     Integer, ForeignKey('Coaches.coach_id',         ondelete='CASCADE'), primary_key=True),
    Column('goal_type_id', Integer, ForeignKey('Goal_Types.goal_type_id',  ondelete='CASCADE'), primary_key=True),
)


class CoachCertification(Base):
    __tablename__ = 'Coach_Certifications'

    certification_id   = Column(Integer, primary_key=True, autoincrement=True)
    coach_id           = Column(Integer, ForeignKey('Coaches.coach_id', ondelete='CASCADE'), nullable=False)
    certification_name = Column(String(255), nullable=False)
    created_at         = Column(DateTime(timezone=True), nullable=False, default=_now)


class CoachAvailability(Base):
    __tablename__ = 'Coach_Availability'
    __table_args__ = (UniqueConstraint('coach_id', 'day_of_week', name='uq_coach_day'),)

    availability_id = Column(Integer, primary_key=True, autoincrement=True)
    coach_id        = Column(Integer, ForeignKey('Coaches.coach_id', ondelete='CASCADE'), nullable=False)
    day_of_week     = Column(Enum('MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'), nullable=False)
    start_time      = Column(Time, nullable=False)
    end_time        = Column(Time, nullable=False)
    created_at      = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated    = Column(DateTime(timezone=True), nullable=False, default=_now)


class ClientCoach(Base):
    __tablename__ = 'Client_Coach'

    client_id    = Column(Integer, ForeignKey('Clients.client_id', ondelete='CASCADE'), primary_key=True)
    coach_id     = Column(Integer, ForeignKey('Coaches.coach_id',  ondelete='CASCADE'), primary_key=True)
    created_at   = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=_now)
