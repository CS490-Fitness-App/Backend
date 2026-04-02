# ORM models for workout-related tables: Workouts, Workout_Plans, Workout_Logs, Set_Results, Saved_Workouts, and Scheduled_Workout.
# Covers workout creation, exercise-to-workout assignment, session logging, and calendar scheduling.

from datetime import datetime, timezone
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from core.database import Base


def _now():
    return datetime.now(timezone.utc)


class Workout(Base):
    __tablename__ = 'workouts'

    workout_id              = Column(Integer, primary_key=True, autoincrement=True)
    creator_id              = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    assigned_to             = Column(Integer, ForeignKey('users.user_id'))
    name                    = Column(String(255), nullable=False)
    status                  = Column(String(20), default='Not Scheduled')
    goal_type_id            = Column(Integer, ForeignKey('goal_types.goal_type_id'))
    experience_level_id     = Column(Integer, ForeignKey('experience_levels.experience_level_id'))
    equipment_required      = Column(String(255))
    workout_time_mins       = Column(Integer)
    intended_duration_weeks = Column(Integer)
    image_url               = Column(Text)
    created_at              = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated            = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    creator          = relationship('User', foreign_keys=[creator_id])
    assigned_user    = relationship('User', foreign_keys=[assigned_to])
    goal_type        = relationship('GoalType')
    experience_level = relationship('ExperienceLevel')


class WorkoutPlan(Base):
    __tablename__ = 'workout_plans'

    workout_id       = Column(Integer, ForeignKey('workouts.workout_id',   ondelete='CASCADE'), primary_key=True)
    exercise_id      = Column(Integer, ForeignKey('exercises.exercise_id', ondelete='CASCADE'), primary_key=True)
    sets             = Column(Integer)
    target_value     = Column(Numeric(8, 2))
    unit_id          = Column(Integer, ForeignKey('units.unit_id'), nullable=False)
    order_in_workout = Column(Integer)
    rest             = Column(Integer)      # seconds
    weeks_completed  = Column(Integer, nullable=False, default=0)
    created_at       = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated     = Column(DateTime(timezone=True), nullable=False, default=_now)

    workout  = relationship('Workout')
    exercise = relationship('Exercise')
    unit     = relationship('Unit')


class WorkoutLog(Base):
    __tablename__ = 'workout_logs'

    workout_log_id = Column(Integer, primary_key=True, autoincrement=True)
    workout_id     = Column(Integer, ForeignKey('workouts.workout_id', ondelete='CASCADE'), nullable=False)
    client_id      = Column(Integer, ForeignKey('clients.client_id',   ondelete='CASCADE'), nullable=False)
    logged_at      = Column(DateTime(timezone=True), nullable=False, default=_now)
    created_at     = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated   = Column(DateTime(timezone=True), nullable=False, default=_now)

    workout     = relationship('Workout')
    client      = relationship('Client')
    set_results = relationship('SetResult', back_populates='workout_log', foreign_keys='SetResult.workout_log_id')


class SetResult(Base):
    __tablename__ = 'set_results'

    set_results_id = Column(Integer, primary_key=True, autoincrement=True)
    workout_log_id = Column(Integer, ForeignKey('workout_logs.workout_log_id', ondelete='CASCADE'), nullable=False)
    actual_weight  = Column(Numeric(8, 2))
    actual_value   = Column(Numeric(8, 2))
    created_at     = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated   = Column(DateTime(timezone=True), nullable=False, default=_now)

    workout_log = relationship('WorkoutLog', back_populates='set_results', foreign_keys=[workout_log_id])


class SavedWorkout(Base):
    __tablename__ = 'saved_workouts'

    user_id    = Column(Integer, ForeignKey('users.user_id',       ondelete='CASCADE'), primary_key=True)
    workout_id = Column(Integer, ForeignKey('workouts.workout_id', ondelete='CASCADE'), primary_key=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)


class ScheduledWorkout(Base):
    __tablename__ = 'scheduled_workout'

    user_id        = Column(Integer, ForeignKey('users.user_id',       ondelete='CASCADE'), primary_key=True)
    workout_id     = Column(Integer, ForeignKey('workouts.workout_id', ondelete='CASCADE'), primary_key=True)
    scheduled_date = Column(Date, primary_key=True)
    status         = Column(String(50))
    created_at     = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated   = Column(DateTime(timezone=True), nullable=False, default=_now)
