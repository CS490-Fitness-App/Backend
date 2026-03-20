# ORM models for workout-related tables: Workouts, Workout_Plans, Workout_Logs, Set_Results, Saved_Workouts, and Scheduled_Workout.
# Covers workout creation, exercise-to-workout assignment, session logging, and calendar scheduling.

from datetime import datetime, timezone
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from database import Base


def _now():
    return datetime.now(timezone.utc)


class Workout(Base):
    __tablename__ = 'Workouts'

    workout_id              = Column(Integer, primary_key=True, autoincrement=True)
    creator_id              = Column(Integer, ForeignKey('Users.user_id'), nullable=False)
    assigned_to             = Column(Integer, ForeignKey('Users.user_id'))
    name                    = Column(String(255), nullable=False)
    status                  = Column(String(20), default='Not Scheduled')
    goal_type_id            = Column(Integer, ForeignKey('Goal_Types.goal_type_id'))
    experience_level_id     = Column(Integer, ForeignKey('Experience_Levels.experience_level_id'))
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
    __tablename__ = 'Workout_Plans'

    workout_id       = Column(Integer, ForeignKey('Workouts.workout_id',   ondelete='CASCADE'), primary_key=True)
    exercise_id      = Column(Integer, ForeignKey('Exercises.exercise_id', ondelete='CASCADE'), primary_key=True)
    sets             = Column(Integer)
    target_value     = Column(Numeric(8, 2))
    unit_id          = Column(Integer, ForeignKey('Units.unit_id'), nullable=False)
    order_in_workout = Column(Integer)
    rest             = Column(Integer)      # seconds
    weeks_completed  = Column(Integer, nullable=False, default=0)
    created_at       = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated     = Column(DateTime(timezone=True), nullable=False, default=_now)

    workout  = relationship('Workout')
    exercise = relationship('Exercise')
    unit     = relationship('Unit')


class WorkoutLog(Base):
    __tablename__ = 'Workout_Logs'

    workout_log_id = Column(Integer, primary_key=True, autoincrement=True)
    workout_id     = Column(Integer, ForeignKey('Workouts.workout_id', ondelete='CASCADE'), nullable=False)
    client_id      = Column(Integer, ForeignKey('Clients.client_id',   ondelete='CASCADE'), nullable=False)
    logged_at      = Column(DateTime(timezone=True), nullable=False, default=_now)
    created_at     = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated   = Column(DateTime(timezone=True), nullable=False, default=_now)

    workout     = relationship('Workout')
    client      = relationship('Client')
    set_results = relationship('SetResult', back_populates='workout_log')


class SetResult(Base):
    __tablename__ = 'Set_Results'

    set_results_id = Column(Integer, primary_key=True, autoincrement=True)
    workout_log_id = Column(Integer, ForeignKey('Workout_Logs.workout_log_id', ondelete='CASCADE'), nullable=False)
    actual_weight  = Column(Numeric(8, 2))
    actual_value   = Column(Numeric(8, 2))
    created_at     = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated   = Column(DateTime(timezone=True), nullable=False, default=_now)

    workout_log = relationship('WorkoutLog', back_populates='set_results')


class SavedWorkout(Base):
    __tablename__ = 'Saved_Workouts'

    user_id    = Column(Integer, ForeignKey('Users.user_id',       ondelete='CASCADE'), primary_key=True)
    workout_id = Column(Integer, ForeignKey('Workouts.workout_id', ondelete='CASCADE'), primary_key=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)


class ScheduledWorkout(Base):
    __tablename__ = 'Scheduled_Workout'

    user_id        = Column(Integer, ForeignKey('Users.user_id',       ondelete='CASCADE'), primary_key=True)
    workout_id     = Column(Integer, ForeignKey('Workouts.workout_id', ondelete='CASCADE'), primary_key=True)
    scheduled_date = Column(Date, primary_key=True)
    status         = Column(String(50))
    created_at     = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated   = Column(DateTime(timezone=True), nullable=False, default=_now)
