# Pydantic schemas for daily surveys, weight logs, goal types, and mood types.
# Used by the logs router to validate wellness check-in data submitted by clients.

from typing import Annotated, Literal, Optional, Union
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class GoalTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    goal_type_id:   int
    goal_type_name: str


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    goal_id:   int
    goal_type: GoalTypeOut


# ── Input schemas ──────────────────────────────────────────────────────────────

class SetResultIn(BaseModel):
    exercise_id:   int
    actual_weight: Optional[float] = None   # kg / lbs
    actual_value:  Optional[float] = None   # reps, minutes, or distance


class WorkoutLogIn(BaseModel):
    type:       Literal["workout"]
    workout_id: int
    sets:       list[SetResultIn]


class StepsLogIn(BaseModel):
    type:       Literal["steps"]
    date:       date
    step_count: int


class CaloriesLogIn(BaseModel):
    type:            Literal["calories"]
    date:            date
    calories_intake: Optional[int] = None
    calories_burned: Optional[int] = None


class DailyCheckInIn(BaseModel):
    date: date
    calories_intake: Optional[int] = None
    calories_burned: Optional[int] = None
    step_count: Optional[int] = None
    water_intake: Optional[int] = None
    weight_lb: Optional[float] = None
    mood_label: Optional[Literal["Amazing", "Good", "Okay", "Bad", "Awful"]] = None
    notes: Optional[str] = None


LogIn = Annotated[
    Union[WorkoutLogIn, StepsLogIn, CaloriesLogIn],
    Field(discriminator="type")
]


# ── Output schemas ─────────────────────────────────────────────────────────────

class SetResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    set_results_id: int
    exercise_id:    Optional[int]
    skipped:        bool = False
    actual_weight:  Optional[float]
    actual_value:   Optional[float]


class WorkoutLogOut(BaseModel):
    workout_log_id: int
    workout_id:     int
    logged_at:      datetime
    sets:           list[SetResultOut]


class DailySurveyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    survey_id:       int
    survey_date:     date
    mood_type_id:    int
    step_count:      Optional[int]
    calories_intake: Optional[int]
    calories_burned: Optional[int]
    water_intake:    Optional[int]
    notes:           Optional[str] = None


class DailyCheckInStatusOut(BaseModel):
    completed: bool
    date: date
    next_reset_at: datetime


class LogsOut(BaseModel):
    workout_logs: list[WorkoutLogOut]
    daily_survey: Optional[DailySurveyOut]


# ── Activity Day endpoint schemas ──────────────────────────────────────────────

class MoodOptionOut(BaseModel):
    mood_type_id: int
    mood_label: str


class ActivityGoalOut(BaseModel):
    goal_id: int
    goal_type_name: str


class ActivityExercisePlanOut(BaseModel):
    exercise_id: int
    exercise_name: str
    category_name: Optional[str] = None
    allow_weight_input: bool = True
    skipped: bool = False
    sets: Optional[int] = None
    target_value: Optional[float] = None
    unit_name: Optional[str] = None
    rest: Optional[int] = None


class ActivityScheduledWorkoutOut(BaseModel):
    workout_id: int
    name: str
    scheduled_date: date
    status: Optional[str] = None
    workout_time_mins: Optional[int] = None
    image_url: Optional[str] = None
    exercises: list[ActivityExercisePlanOut] = []


class ActivitySetResultOut(BaseModel):
    exercise_id: Optional[int] = None
    exercise_name: Optional[str] = None
    skipped: bool = False
    actual_weight: Optional[float] = None
    actual_value: Optional[float] = None


class ActivityWorkoutLogOut(BaseModel):
    workout_log_id: int
    workout_id: int
    workout_name: str
    status: str
    logged_at: datetime
    set_results: list[ActivitySetResultOut] = []


class ActivityDaySurveyOut(BaseModel):
    survey_id: int
    survey_date: date
    mood_type_id: int
    mood_label: str
    step_count: Optional[int] = None
    calories_intake: Optional[int] = None
    calories_burned: Optional[int] = None
    water_intake: Optional[int] = None
    notes: Optional[str] = None
    weight_lb: Optional[float] = None


class ActivityDayOut(BaseModel):
    date: date
    is_today: bool
    can_delete: bool = False
    has_logged_data: bool = False
    mood_options: list[MoodOptionOut] = []
    goals: list[ActivityGoalOut] = []
    scheduled_workouts: list[ActivityScheduledWorkoutOut] = []
    logged_workouts: list[ActivityWorkoutLogOut] = []
    daily_survey: Optional[ActivityDaySurveyOut] = None
    progress_photos: list["ProgressPhotoOut"] = []


class ActivityDaySurveyIn(BaseModel):
    step_count: Optional[int] = None
    calories_intake: Optional[int] = None
    calories_burned: Optional[int] = None
    water_intake: Optional[int] = None
    weight_lb: Optional[float] = None
    mood_label: Optional[Literal["Amazing", "Good", "Okay", "Bad", "Awful"]] = None
    notes: Optional[str] = None


class ActivityWorkoutSetIn(BaseModel):
    exercise_id: int
    skipped: bool = False
    actual_weight: Optional[float] = None
    actual_value: Optional[float] = None


class ActivityWorkoutLogIn(BaseModel):
    workout_id: int
    set_results: list[ActivityWorkoutSetIn] = []


class ActivityDayUpdateIn(BaseModel):
    daily_survey: Optional[ActivityDaySurveyIn] = None
    workout_logs: list[ActivityWorkoutLogIn] = []


class ProgressPhotoOut(BaseModel):
    progress_photo_id: int
    user_id: int
    photo_type: str
    image_url: str
    note: Optional[str] = None
    taken_on: date
    created_at: datetime
