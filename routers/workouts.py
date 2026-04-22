# Handles workout plan endpoints (UC 3.2–3.4): creating/editing workout plans, browsing the library, managing saved workouts, and scheduling.

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import date

from core.database import get_db
from dependencies.rbac import get_current_user
from models.coach import ClientCoach
from models.user import Client
from models.workout import Workout, WorkoutPlan, SavedWorkout, ScheduledWorkout, WorkoutLog, SetResult
from schemas.workout import (
    WorkoutIn, WorkoutOut, WorkoutDetailOut, WorkoutExerciseOut,
    ScheduledWorkoutIn, ScheduledWorkoutOut,
    WorkoutLogIn, CalendarWorkoutOut,
)

router = APIRouter(prefix="/workouts", tags=["workouts"])


# --- Helpers ---

def _get_or_404(workout_id: int, db: Session) -> Workout:
    """Fetch a workout with its related lookups, or raise 404."""
    w = (
        db.query(Workout)
        .options(
            joinedload(Workout.experience_level),
            joinedload(Workout.goal_type),
        )
        .filter(Workout.workout_id == workout_id)
        .first()
    )
    if not w:
        raise HTTPException(status_code=404, detail="Workout not found")
    return w


def _can_view_workout(w: Workout, current_user) -> bool:
    return w.creator_id == current_user.user_id or w.assigned_to == current_user.user_id


def _require_workout_access(w: Workout, current_user):
    if not _can_view_workout(w, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to view this workout")


def _to_out(w: Workout) -> WorkoutOut:
    """Map a Workout ORM object to a WorkoutOut schema, resolving FK names."""
    return WorkoutOut(
        workout_id=w.workout_id,
        name=w.name,
        image_url=w.image_url,
        experience_level_id=w.experience_level_id,
        experience_level=w.experience_level.experience_level_name if w.experience_level else None,
        goal_type_id=w.goal_type_id,
        goal_type=w.goal_type.goal_type_name if w.goal_type else None,
        equipment_required=w.equipment_required,
        workout_time_mins=w.workout_time_mins,
        intended_duration_weeks=w.intended_duration_weeks,
        status=w.status,
        creator_id=w.creator_id,
        assigned_to=w.assigned_to,
    )


def _get_exercises(workout_id: int, db: Session) -> List[WorkoutExerciseOut]:
    """Fetch all exercises in a workout, ordered by their position in the plan."""
    plans = (
        db.query(WorkoutPlan)
        .options(
            joinedload(WorkoutPlan.exercise),
            joinedload(WorkoutPlan.unit),
        )
        .filter(WorkoutPlan.workout_id == workout_id)
        .order_by(WorkoutPlan.order_in_workout)
        .all()
    )
    return [
        WorkoutExerciseOut(
            exercise_id=p.exercise_id,
            exercise_name=p.exercise.name,
            sets=p.sets,
            target_value=float(p.target_value) if p.target_value is not None else None,
            unit_id=p.unit_id,
            unit_name=p.unit.unit_name,
            order_in_workout=p.order_in_workout,
            rest=p.rest,
        )
        for p in plans
    ]


def _insert_exercises(workout_id: int, exercises, db: Session):
    """Bulk-insert WorkoutPlan rows for a given workout."""
    for ex in exercises:
        db.add(WorkoutPlan(
            workout_id=workout_id,
            exercise_id=ex.exercise_id,
            sets=ex.sets,
            target_value=ex.target_value,
            unit_id=ex.unit_id,
            order_in_workout=ex.order_in_workout,
            rest=ex.rest,
        ))


# --- Endpoints ---

# Browse workouts owned by the current user or assigned to them
@router.get("", response_model=List[WorkoutOut])
def list_workouts(
    name: Optional[str] = Query(None),
    goal_type_id: Optional[int] = Query(None),
    experience_level_id: Optional[int] = Query(None),

    db: Session = Depends(get_db), 
    current_user=Depends(get_current_user
)):

    query = (
        db.query(Workout)
        .options(
            joinedload(Workout.experience_level),
            joinedload(Workout.goal_type),
        )
        .filter(
            or_(
                Workout.creator_id == current_user.user_id,
                Workout.assigned_to != current_user.user_id,
            )
        )
    )

    if name:
        query = query.filter(Workout.name.ilike(f"%{name}%"))

    if goal_type_id:
        query = query.filter(Workout.goal_type_id == goal_type_id)

    if experience_level_id:
        query = query.filter(Workout.experience_level_id == experience_level_id)

    workouts = query.all()
    return [_to_out(w) for w in workouts]


# Get the current user's saved/bookmarked workouts
# NOTE: must be declared BEFORE /{workout_id} so FastAPI doesn't match "saved" as an integer ID
@router.get("/saved", response_model=List[WorkoutOut])
def list_saved_workouts(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    saved_rows = db.query(SavedWorkout).filter(SavedWorkout.user_id == current_user.user_id).all()
    if not saved_rows:
        return []
    ids = [s.workout_id for s in saved_rows]
    workouts = (
        db.query(Workout)
        .options(
            joinedload(Workout.experience_level),
            joinedload(Workout.goal_type),
        )
        .filter(Workout.workout_id.in_(ids))
        .all()
    )
    return [_to_out(w) for w in workouts]


# Get the current user's scheduled workouts for the calendar, optionally filtered by date range
# NOTE: must be declared BEFORE /{workout_id} so FastAPI doesn't match "scheduled" as an integer ID
@router.get("/scheduled", response_model=List[CalendarWorkoutOut])
def list_scheduled_workouts(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(ScheduledWorkout).filter(ScheduledWorkout.user_id == current_user.user_id)
    if start_date:
        query = query.filter(ScheduledWorkout.scheduled_date >= start_date)
    if end_date:
        query = query.filter(ScheduledWorkout.scheduled_date <= end_date)
    rows = query.order_by(ScheduledWorkout.scheduled_date).all()

    result = []
    for row in rows:
        w = _get_or_404(row.workout_id, db)
        out = _to_out(w)
        result.append(CalendarWorkoutOut(
            scheduled_date=row.scheduled_date,
            status=row.status,
            workout_id=w.workout_id,
            name=w.name,
            image_url=w.image_url,
            experience_level=out.experience_level,
            goal_type=out.goal_type,
            workout_time_mins=w.workout_time_mins,
            exercises=_get_exercises(w.workout_id, db),
        ))
    return result


# Get a single workout with its full ordered exercise list
@router.get("/{workout_id}", response_model=WorkoutDetailOut)
def get_workout(workout_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    w = _get_or_404(workout_id, db)
    _require_workout_access(w, current_user)
    return WorkoutDetailOut(**_to_out(w).model_dump(), exercises=_get_exercises(workout_id, db))


# Create a workout and its exercises in one request (frontend submits everything on save)
@router.post("", response_model=WorkoutDetailOut, status_code=201)
def create_workout(data: WorkoutIn, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    ids = [ex.exercise_id for ex in data.exercises]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=400, detail="Duplicate exercise IDs in workout plan")

    workout = Workout(
        creator_id=current_user.user_id,
        assigned_to=data.assigned_to,
        name=data.name,
        goal_type_id=data.goal_type_id,
        experience_level_id=data.experience_level_id,
        equipment_required=data.equipment_required,
        workout_time_mins=data.workout_time_mins,
        intended_duration_weeks=data.intended_duration_weeks,
        image_url=data.image_url,
    )
    db.add(workout)
    db.flush()
    _insert_exercises(workout.workout_id, data.exercises, db)
    db.commit()

    w = _get_or_404(workout.workout_id, db)
    return WorkoutDetailOut(**_to_out(w).model_dump(), exercises=_get_exercises(workout.workout_id, db))


# Replace a workout's metadata and full exercise list
@router.put("/{workout_id}", response_model=WorkoutDetailOut)
def update_workout(workout_id: int, data: WorkoutIn, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    ids = [ex.exercise_id for ex in data.exercises]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=400, detail="Duplicate exercise IDs in workout plan")

    w = _get_or_404(workout_id, db)
    _require_workout_access(w, current_user)
    if w.creator_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this workout")

    w.name = data.name
    w.assigned_to = data.assigned_to
    w.goal_type_id = data.goal_type_id
    w.experience_level_id = data.experience_level_id
    w.equipment_required = data.equipment_required
    w.workout_time_mins = data.workout_time_mins
    w.intended_duration_weeks = data.intended_duration_weeks
    w.image_url = data.image_url

    db.query(WorkoutPlan).filter(WorkoutPlan.workout_id == workout_id).delete()
    _insert_exercises(workout_id, data.exercises, db)
    db.commit()

    w = _get_or_404(workout_id, db)
    return WorkoutDetailOut(**_to_out(w).model_dump(), exercises=_get_exercises(workout_id, db))


# Delete a workout — only the creator can do this
@router.delete("/{workout_id}", status_code=204)
def delete_workout(workout_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    w = _get_or_404(workout_id, db)
    _require_workout_access(w, current_user)
    if w.creator_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this workout")
    db.delete(w)
    db.commit()


# Bookmark a workout to the user's saved list
@router.post("/{workout_id}/save", status_code=201)
def save_workout(workout_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    w = _get_or_404(workout_id, db)
    _require_workout_access(w, current_user)
    if db.query(SavedWorkout).filter_by(user_id=current_user.user_id, workout_id=workout_id).first():
        raise HTTPException(status_code=409, detail="Workout already saved")
    db.add(SavedWorkout(user_id=current_user.user_id, workout_id=workout_id))
    db.commit()


# Remove a workout from the user's saved list
@router.delete("/{workout_id}/save", status_code=204)
def unsave_workout(workout_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    saved = db.query(SavedWorkout).filter_by(user_id=current_user.user_id, workout_id=workout_id).first()
    if not saved:
        raise HTTPException(status_code=404, detail="Workout not saved")
    db.delete(saved)
    db.commit()


# Add a workout to the calendar on a specific date.
# Coaches can supply client_user_id to schedule on behalf of an active client.
@router.post("/{workout_id}/schedule", response_model=ScheduledWorkoutOut, status_code=201)
def schedule_workout(workout_id: int, data: ScheduledWorkoutIn, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    w = _get_or_404(workout_id, db)

    target_user_id = current_user.user_id

    if data.client_user_id is not None:
        if current_user.role != 'coach':
            raise HTTPException(status_code=403, detail="Only coaches can schedule workouts for clients")
        target_client = db.query(Client).filter(Client.user_id == data.client_user_id).first()
        if not target_client:
            raise HTTPException(status_code=404, detail="Client not found")
        active_rel = db.query(ClientCoach).filter_by(
            client_id=target_client.client_id,
            coach_id=current_user.coach.coach_id,
            status_name='Active',
        ).first()
        if not active_rel:
            raise HTTPException(status_code=403, detail="No active coaching relationship with this client")
        target_user_id = data.client_user_id
    else:
        _require_workout_access(w, current_user)

    if db.query(ScheduledWorkout).filter_by(user_id=target_user_id, workout_id=workout_id, scheduled_date=data.scheduled_date).first():
        raise HTTPException(status_code=409, detail="Workout already scheduled for this date")

    db.add(ScheduledWorkout(
        user_id=target_user_id,
        workout_id=workout_id,
        scheduled_date=data.scheduled_date,
        status='Scheduled',
    ))
    db.commit()
    return ScheduledWorkoutOut(workout_id=workout_id, scheduled_date=data.scheduled_date, status='Scheduled')


# Update a scheduled workout's status and optionally log performance (weight/reps/distance)
@router.patch("/{workout_id}/schedule/{scheduled_date}", response_model=ScheduledWorkoutOut)
def log_scheduled_workout(
    workout_id: int,
    scheduled_date: date,
    data: WorkoutLogIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    scheduled = db.query(ScheduledWorkout).filter_by(
        user_id=current_user.user_id,
        workout_id=workout_id,
        scheduled_date=scheduled_date,
    ).first()
    if not scheduled:
        raise HTTPException(status_code=404, detail="Scheduled workout not found")

    scheduled.status = data.status

    if data.status == 'Completed' and data.set_results:
        client = db.query(Client).filter(Client.user_id == current_user.user_id).first()
        if not client:
            raise HTTPException(status_code=400, detail="Only clients can log workout performance")
        log = WorkoutLog(workout_id=workout_id, client_id=client.client_id)
        db.add(log)
        db.flush()  # populate log.workout_log_id before inserting set results
        for sr in data.set_results:
            db.add(SetResult(
                workout_log_id=log.workout_log_id,
                exercise_id=sr.exercise_id,
                actual_weight=sr.actual_weight,
                actual_value=sr.actual_value,
            ))

    db.commit()
    return ScheduledWorkoutOut(workout_id=workout_id, scheduled_date=scheduled_date, status=data.status)


# Remove a specific workout from the calendar by date
@router.delete("/{workout_id}/schedule/{scheduled_date}", status_code=204)
def unschedule_workout(workout_id: int, scheduled_date: date, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    scheduled = db.query(ScheduledWorkout).filter_by(user_id=current_user.user_id, workout_id=workout_id, scheduled_date=scheduled_date).first()
    if not scheduled:
        raise HTTPException(status_code=404, detail="Scheduled workout not found")
    db.delete(scheduled)
    db.commit()
