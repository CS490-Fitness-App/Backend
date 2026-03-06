# ORM models for the exercise library: Exercises, Exercise_Categories, Muscle_Groups, Exercise_Muscles, Experience_Levels, and Units.
# Represents every exercise in the system along with its categorization and targeted muscle groups.

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship
from database import Base


def _now():
    return datetime.now(timezone.utc)


# Junction table: exercises ↔ muscle groups (no extra columns)
exercise_muscles = Table(
    'Exercise_Muscles',
    Base.metadata,
    Column('exercise_id',     Integer, ForeignKey('Exercises.exercise_id',         ondelete='CASCADE'), primary_key=True),
    Column('muscle_group_id', Integer, ForeignKey('Muscle_Groups.muscle_group_id', ondelete='CASCADE'), primary_key=True),
)


class ExerciseCategory(Base):
    __tablename__ = 'Exercise_Categories'

    category_id   = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(50), nullable=False, unique=True)


class MuscleGroup(Base):
    __tablename__ = 'Muscle_Groups'

    muscle_group_id   = Column(Integer, primary_key=True, autoincrement=True)
    muscle_group_name = Column(String(100), nullable=False, unique=True)


class ExperienceLevel(Base):
    __tablename__ = 'Experience_Levels'

    experience_level_id   = Column(Integer, primary_key=True, autoincrement=True)
    experience_level_name = Column(String(50), nullable=False, unique=True)


class Unit(Base):
    __tablename__ = 'Units'

    unit_id   = Column(Integer, primary_key=True, autoincrement=True)
    unit_name = Column(String(50), nullable=False, unique=True)


class Exercise(Base):
    __tablename__ = 'Exercises'

    exercise_id         = Column(Integer, primary_key=True, autoincrement=True)
    name                = Column(String(255), nullable=False)
    category_id         = Column(Integer, ForeignKey('Exercise_Categories.category_id'), nullable=False)
    experience_level_id = Column(Integer, ForeignKey('Experience_Levels.experience_level_id'))
    equipment           = Column(String(255))
    instructions        = Column(Text)
    tips                = Column(Text)
    image_url           = Column(Text)
    video_url           = Column(Text)
    created_at          = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated        = Column(DateTime(timezone=True), nullable=False, default=_now)

    category         = relationship('ExerciseCategory')
    experience_level = relationship('ExperienceLevel')
    muscle_groups    = relationship('MuscleGroup', secondary=exercise_muscles)
