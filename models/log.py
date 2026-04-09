# ORM models for tracking and survey tables: Daily_Surveys, Weight_Logs, Goals, Goal_Types, Mood_Types, and Audit_Log.
# Stores daily wellness check-ins, weight history, user goals, and a full database audit trail.

from datetime import datetime, timezone
from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, JSON, Numeric, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from core.database import Base


def _now():
    return datetime.now(timezone.utc)


class GoalType(Base):
    __tablename__ = 'goal_types'

    goal_type_id   = Column(Integer, primary_key=True, autoincrement=True)
    goal_type_name = Column(String(50), nullable=False, unique=True)


class Goal(Base):
    __tablename__ = 'goals'

    goal_id      = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey('users.user_id',          ondelete='CASCADE'), nullable=False)
    goal_type_id = Column(Integer, ForeignKey('goal_types.goal_type_id'), nullable=False)
    created_at   = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=_now)

    goal_type = relationship('GoalType')


class MoodType(Base):
    __tablename__ = 'mood_types'

    mood_type_id   = Column(Integer, primary_key=True, autoincrement=True)
    mood_type_name = Column(String(20), nullable=False, unique=True)


class DailySurvey(Base):
    __tablename__ = 'daily_surveys'
    __table_args__ = (UniqueConstraint('user_id', 'survey_date', name='uq_survey_user_date'),)

    survey_id       = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    survey_date     = Column(Date, nullable=False)
    mood_type_id    = Column(Integer, ForeignKey('mood_types.mood_type_id'), nullable=False)
    energy_level    = Column(SmallInteger)      # 1-10
    sleep_hours     = Column(Numeric(4, 1))     # e.g. 7.5
    step_count      = Column(Integer)
    calories_intake = Column(Integer)           # kcal
    calories_burned = Column(Integer)           # kcal
    water_intake    = Column(SmallInteger)      # glasses per day
    notes           = Column(Text)
    created_at      = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated    = Column(DateTime(timezone=True), nullable=False, default=_now)

    mood_type = relationship('MoodType')


class WeightLog(Base):
    __tablename__ = 'weight_logs'

    weight_log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    weight        = Column(Integer, nullable=False)     # grams
    created_at    = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated  = Column(DateTime(timezone=True), nullable=False, default=_now)


class AuditLog(Base):
    __tablename__ = 'audit_log'

    audit_id   = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(64), nullable=False)
    record_id  = Column(Integer, nullable=False)
    action     = Column(Enum('INSERT', 'UPDATE', 'DELETE'), nullable=False)
    changed_by = Column(Integer, ForeignKey('users.user_id', ondelete='SET NULL'))
    old_values = Column(JSON)
    new_values = Column(JSON)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=_now)
