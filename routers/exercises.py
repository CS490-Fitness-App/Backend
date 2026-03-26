# Handles exercise inventory endpoints (UC 3.1, UC 6.1): read access for all users and full CRUD for admins.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List

from core.database import get_db
from models.exercise import Exercise
from schemas.exercise import ExerciseOut

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=List[ExerciseOut])
def list_exercises(db: Session = Depends(get_db)):
    exercises = (
        db.query(Exercise)
        .options(
            joinedload(Exercise.category),
            joinedload(Exercise.experience_level),
            selectinload(Exercise.muscle_groups),
        )
        .all()
    )
    return [
        ExerciseOut(
            exercise_id=e.exercise_id,
            name=e.name,
            image_url=e.image_url,
            experience_level=e.experience_level.experience_level_name if e.experience_level else None,
            category=e.category.category_name,
            equipment=e.equipment,
            muscle_groups=[mg.muscle_group_name for mg in e.muscle_groups],
        )
        for e in exercises
    ]


@router.get("/{exercise_id}", response_model=ExerciseOut)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    e = (
        db.query(Exercise)
        .options(
            joinedload(Exercise.category),
            joinedload(Exercise.experience_level),
            selectinload(Exercise.muscle_groups),
        )
        .filter(Exercise.exercise_id == exercise_id)
        .first()
    )
    if not e:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return ExerciseOut(
        exercise_id=e.exercise_id,
        name=e.name,
        image_url=e.image_url,
        experience_level=e.experience_level.experience_level_name if e.experience_level else None,
        category=e.category.category_name,
        equipment=e.equipment,
        muscle_groups=[mg.muscle_group_name for mg in e.muscle_groups],
    )
