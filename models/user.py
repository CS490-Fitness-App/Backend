# ORM models for the core user tables: Users, Clients, Coaches, Admins, Coach_Statuses, and Session_Formats.
# Defines the structure of every user-related row in the MySQL database.

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from database import Base


def _now():
    return datetime.now(timezone.utc)


class CoachStatus(Base):
    __tablename__ = 'Coach_Statuses'

    status_id   = Column(Integer, primary_key=True, autoincrement=True)
    status_name = Column(String(50), nullable=False, unique=True)


class SessionFormat(Base):
    __tablename__ = 'Session_Formats'

    session_format_id   = Column(Integer, primary_key=True, autoincrement=True)
    session_format_name = Column(String(50), nullable=False, unique=True)


class User(Base):
    __tablename__ = 'Users'

    user_id         = Column(Integer, primary_key=True, autoincrement=True)
    auth0_sub       = Column(String(128), nullable=False, unique=True)
    email           = Column(String(255), nullable=False, unique=True)
    first_name      = Column(String(100))
    last_name       = Column(String(100))
    profile_picture = Column(Text)
    role            = Column(String(50), nullable=False, default='client')
    created_at      = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated    = Column(DateTime(timezone=True), nullable=False, default=_now)

    client = relationship('Client', back_populates='user', uselist=False)
    coach  = relationship('Coach',  back_populates='user', uselist=False)
    admin  = relationship('Admin',  back_populates='user', uselist=False)


class Client(Base):
    __tablename__ = 'Clients'

    client_id     = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    DOB           = Column(Date)
    height        = Column(Integer)         # centimetres
    weight        = Column(Integer)         # grams
    goal_weight   = Column(Integer)         # grams
    sex           = Column(String(20))
    weekly_streak = Column(Integer, nullable=False, default=0)
    created_at    = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated  = Column(DateTime(timezone=True), nullable=False, default=_now)

    user = relationship('User', back_populates='client')


class Coach(Base):
    __tablename__ = 'Coaches'

    coach_id            = Column(Integer, primary_key=True, autoincrement=True)
    user_id             = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    gender              = Column(String(20))
    hourly_rate         = Column(Numeric(10, 2))
    accepting_clients   = Column(Boolean, nullable=False, default=True)
    bio                 = Column(Text)
    status_id           = Column(Integer, ForeignKey('Coach_Statuses.status_id'), nullable=False, default=1)
    is_trainer          = Column(Boolean, nullable=False, default=True)
    is_nutritionist     = Column(Boolean, nullable=False, default=False)
    years_of_experience = Column(Integer)
    max_clients         = Column(Integer)
    created_at          = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated        = Column(DateTime(timezone=True), nullable=False, default=_now)

    user   = relationship('User',        back_populates='coach')
    status = relationship('CoachStatus')


class Admin(Base):
    __tablename__ = 'Admins'

    admin_id     = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    created_at   = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=_now)

    user = relationship('User', back_populates='admin')
