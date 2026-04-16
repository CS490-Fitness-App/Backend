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
    step_count:      Optional[int]
    calories_intake: Optional[int]
    calories_burned: Optional[int]


class LogsOut(BaseModel):
    workout_logs: list[WorkoutLogOut]
    daily_survey: Optional[DailySurveyOut]
