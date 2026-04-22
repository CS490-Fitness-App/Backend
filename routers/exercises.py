# Handles exercise inventory endpoints (UC 3.1, UC 6.1): read access for all users and full CRUD for admins.

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List

from core.database import get_db
from dependencies.rbac import require_admin
from models.exercise import Exercise, ExerciseCategory, ExperienceLevel, MuscleGroup
from models.workout import WorkoutPlan
from schemas.exercise import ExerciseIn, ExerciseLookupOption, ExerciseMetaOut, ExerciseOut

router = APIRouter(prefix="/exercises", tags=["exercises"])


def _exercise_query(db: Session):
    return (
        db.query(Exercise)
        .options(
            joinedload(Exercise.category),
            joinedload(Exercise.experience_level),
            selectinload(Exercise.muscle_groups),
        )
    )


def _to_out(e: Exercise) -> ExerciseOut:
    return ExerciseOut(
        exercise_id=e.exercise_id,
        name=e.name,
        category_id=e.category_id,
        image_url=e.image_url,
        video_url=e.video_url,
        experience_level_id=e.experience_level_id,
        experience_level=e.experience_level.experience_level_name if e.experience_level else None,
        category=e.category.category_name,
        equipment=e.equipment,
        instructions=e.instructions,
        tips=e.tips,
        muscle_group_ids=[mg.muscle_group_id for mg in e.muscle_groups],
        muscle_groups=[mg.muscle_group_name for mg in e.muscle_groups],
    )
  

def _get_exercise_or_404(exercise_id: int, db: Session) -> Exercise:
    exercise = _exercise_query(db).filter(Exercise.exercise_id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise


def _validate_exercise_payload(data: ExerciseIn, db: Session, exclude_exercise_id: int | None = None) -> list[MuscleGroup]:
    existing = db.query(Exercise).filter(Exercise.name.ilike(data.name.strip()))
    if exclude_exercise_id is not None:
        existing = existing.filter(Exercise.exercise_id != exclude_exercise_id)
    if existing.first():
        raise HTTPException(status_code=409, detail="An exercise with this name already exists")

    category = db.query(ExerciseCategory).filter(ExerciseCategory.category_id == data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Invalid category_id")

    if data.experience_level_id is not None:
        level = db.query(ExperienceLevel).filter(
            ExperienceLevel.experience_level_id == data.experience_level_id
        ).first()
        if not level:
            raise HTTPException(status_code=404, detail="Invalid experience_level_id")

    muscle_groups = []
    for muscle_group_id in data.muscle_group_ids:
        muscle_group = db.query(MuscleGroup).filter(MuscleGroup.muscle_group_id == muscle_group_id).first()
        if not muscle_group:
            raise HTTPException(status_code=404, detail=f"Invalid muscle_group_id: {muscle_group_id}")
        muscle_groups.append(muscle_group)

    return muscle_groups


@router.get("", response_model=List[ExerciseOut])
def list_exercises(name: str | None = Query(default=None),
                    category_id: int | None = Query(default=None),
                    experience_level_id: int | None = Query(default=None),
                    db: Session = Depends(get_db)):
    
    query = _exercise_query(db)

    if name and name.strip():
        query = query.filter(Exercise.name.ilike(f"%{name.strip()}%"))

    if category_id:
        query = query.filter(Exercise.category_id == category_id)

    if experience_level_id:
        query = query.filter(Exercise.experience_level_id == experience_level_id)

    exercises = query.all()
    return [_to_out(e) for e in exercises]


@router.get("/meta/options", response_model=ExerciseMetaOut)
def get_exercise_meta(db: Session = Depends(get_db)):
    categories = db.query(ExerciseCategory).order_by(ExerciseCategory.category_name.asc()).all()
    experience_levels = db.query(ExperienceLevel).order_by(ExperienceLevel.experience_level_name.asc()).all()
    muscle_groups = db.query(MuscleGroup).order_by(MuscleGroup.muscle_group_name.asc()).all()

    return ExerciseMetaOut(
        categories=[
            ExerciseLookupOption(id=category.category_id, name=category.category_name)
            for category in categories
        ],
        experience_levels=[
            ExerciseLookupOption(id=level.experience_level_id, name=level.experience_level_name)
            for level in experience_levels
        ],
        muscle_groups=[
            ExerciseLookupOption(id=muscle_group.muscle_group_id, name=muscle_group.muscle_group_name)
            for muscle_group in muscle_groups
        ],
    )


@router.get("/{exercise_id}", response_model=ExerciseOut)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    return _to_out(_get_exercise_or_404(exercise_id, db))


@router.post("", response_model=ExerciseOut, status_code=201)
def create_exercise(
    data: ExerciseIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    muscle_groups = _validate_exercise_payload(data, db)

    exercise = Exercise(
        name=data.name.strip(),
        category_id=data.category_id,
        experience_level_id=data.experience_level_id,
        equipment=data.equipment,
        instructions=data.instructions,
        tips=data.tips,
        image_url=data.image_url,
        video_url=data.video_url,
    )
    exercise.muscle_groups = muscle_groups

    db.add(exercise)
    db.commit()

    return _to_out(_get_exercise_or_404(exercise.exercise_id, db))


@router.put("/{exercise_id}", response_model=ExerciseOut)
def update_exercise(
    exercise_id: int,
    data: ExerciseIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    exercise = _get_exercise_or_404(exercise_id, db)
    muscle_groups = _validate_exercise_payload(data, db, exclude_exercise_id=exercise_id)

    exercise.name = data.name.strip()
    exercise.category_id = data.category_id
    exercise.experience_level_id = data.experience_level_id
    exercise.equipment = data.equipment
    exercise.instructions = data.instructions
    exercise.tips = data.tips
    exercise.image_url = data.image_url
    exercise.video_url = data.video_url
    exercise.muscle_groups = muscle_groups
    exercise.last_updated = datetime.now(timezone.utc)

    db.commit()

    return _to_out(_get_exercise_or_404(exercise.exercise_id, db))


@router.delete("/{exercise_id}", status_code=204)
def delete_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    exercise = _get_exercise_or_404(exercise_id, db)

    in_use = db.query(WorkoutPlan).filter(WorkoutPlan.exercise_id == exercise_id).first()
    if in_use:
        raise HTTPException(
            status_code=409,
            detail="Exercise is already used in workout plans and cannot be deleted",
        )

    db.delete(exercise)
    db.commit()
