# Pydantic schemas for workouts, workout plans, logs, set results, and scheduling.
# Supports all workout-related endpoints from plan creation through session logging.

from pydantic import BaseModel
from typing import List, Optional
from datetime import date


# --- Input schemas ---

class WorkoutExerciseIn(BaseModel):
    exercise_id: int
    sets: Optional[int] = None
    target_value: Optional[float] = None
    unit_id: int
    order_in_workout: Optional[int] = None
    rest: Optional[int] = None          # seconds


class WorkoutIn(BaseModel):
    name: str
    goal_type_id: Optional[int] = None
    experience_level_id: Optional[int] = None
    equipment_required: Optional[str] = None
    workout_time_mins: Optional[int] = None
    intended_duration_weeks: Optional[int] = None
    image_url: Optional[str] = None
    assigned_to: Optional[int] = None   # user_id of client; coaches set this to assign a workout
    exercises: List[WorkoutExerciseIn] = []


# --- Output schemas ---

class WorkoutExerciseOut(BaseModel):
    exercise_id: int
    exercise_name: str
    sets: Optional[int] = None
    target_value: Optional[float] = None
    unit_name: str
    order_in_workout: Optional[int] = None
    rest: Optional[int] = None


class WorkoutOut(BaseModel):
    workout_id: int
    name: str
    image_url: Optional[str] = None
    experience_level: Optional[str] = None
    goal_type: Optional[str] = None
    equipment_required: Optional[str] = None
    workout_time_mins: Optional[int] = None
    intended_duration_weeks: Optional[int] = None
    status: Optional[str] = None
    creator_id: int
    assigned_to: Optional[int] = None


class WorkoutDetailOut(WorkoutOut):
    exercises: List[WorkoutExerciseOut] = []


class ScheduledWorkoutIn(BaseModel):
    scheduled_date: date


class ScheduledWorkoutOut(BaseModel):
    workout_id: int
    scheduled_date: date
    status: Optional[str] = None


# --- Logging schemas ---

class SetResultIn(BaseModel):
    exercise_id: int
    actual_weight: Optional[float] = None   # kg / lbs
    actual_value: Optional[float] = None    # reps / distance / time


class WorkoutLogIn(BaseModel):
    status: str                                     # Completed | Skipped | etc.
    set_results: Optional[List[SetResultIn]] = []   # only needed when Completed


# --- Calendar schemas ---

class CalendarWorkoutOut(BaseModel):
    scheduled_date: date
    status: Optional[str] = None
    workout_id: int
    name: str
    image_url: Optional[str] = None
    experience_level: Optional[str] = None
    goal_type: Optional[str] = None
    workout_time_mins: Optional[int] = None
    exercises: List[WorkoutExerciseOut] = []


class RescheduleIn(BaseModel):
    new_date: date


class RecurringScheduleIn(BaseModel):
    start_date: date                        # anchors to the Monday of this date's week
    days_of_week: List[int]                 # 0=Monday … 6=Sunday
    num_weeks: int
    client_user_id: Optional[int] = None   # coaches only


class RecurringScheduleOut(BaseModel):
    scheduled: List[ScheduledWorkoutOut]
    skipped_dates: List[date]               # dates that were already scheduled
