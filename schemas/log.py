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
    step_count: Optional[int] = None
    water_intake: Optional[int] = None
    weight_lb: Optional[float] = None
    mood_label: Optional[Literal["Amazing", "Good", "Okay", "Bad", "Awful"]] = None


LogIn = Annotated[
    Union[WorkoutLogIn, StepsLogIn, CaloriesLogIn],
    Field(discriminator="type")
]


# ── Output schemas ─────────────────────────────────────────────────────────────

class SetResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    set_results_id: int
    exercise_id:    Optional[int]
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


class DailyCheckInStatusOut(BaseModel):
    completed: bool
    date: date
    next_reset_at: datetime


class LogsOut(BaseModel):
    workout_logs: list[WorkoutLogOut]
    daily_survey: Optional[DailySurveyOut]


# ── Activity Day endpoint schemas ──────────────────────────────────────────────

class ExercisePlanOut(BaseModel):
    exercise_id: int
    exercise_name: str
    category_name: Optional[str]
    allow_weight_input: bool
    sets: Optional[int]
    target_value: Optional[float]
    unit_name: Optional[str]
    rest: Optional[int]


class ScheduledWorkoutDetailOut(BaseModel):
    workout_id: int
    name: str
    workout_time_mins: Optional[int]
    exercises: list[ExercisePlanOut]


class SetResultDetailOut(BaseModel):
    exercise_id: Optional[int]
    exercise_name: Optional[str]
    actual_weight: Optional[float]
    actual_value: Optional[float]
    skipped: bool


class LoggedWorkoutDetailOut(BaseModel):
    workout_id: int
    workout_name: str
    set_results: list[SetResultDetailOut]


class DailySurveyActivityOut(BaseModel):
    step_count: Optional[int]
    calories_intake: Optional[int]
    calories_burned: Optional[int]
    water_intake: Optional[int]
    weight_lb: Optional[float]
    mood_label: Optional[str]
    notes: Optional[str]


class MoodOptionOut(BaseModel):
    mood_label: str


class ActivityDayOut(BaseModel):
    daily_survey: Optional[DailySurveyActivityOut]
    mood_options: list[MoodOptionOut]
    scheduled_workouts: list[ScheduledWorkoutDetailOut]
    logged_workouts: list[LoggedWorkoutDetailOut]
    has_logged_data: bool
    can_delete: bool


class SetResultActivityIn(BaseModel):
    exercise_id: int
    skipped: bool = False
    actual_weight: Optional[float] = None
    actual_value: Optional[float] = None


class WorkoutLogActivityIn(BaseModel):
    workout_id: int
    set_results: list[SetResultActivityIn]


class DailySurveyActivityIn(BaseModel):
    step_count: Optional[int] = None
    calories_intake: Optional[int] = None
    calories_burned: Optional[int] = None
    water_intake: Optional[int] = None
    weight_lb: Optional[float] = None
    mood_label: Optional[str] = None
    notes: Optional[str] = None


class ActivityDayIn(BaseModel):
    daily_survey: Optional[DailySurveyActivityIn] = None
    workout_logs: list[WorkoutLogActivityIn] = []
