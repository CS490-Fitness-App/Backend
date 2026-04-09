# Handles activity and wellness logging endpoints (UC 3.5, 3.7, 6.5): workout session logs, set results, daily surveys, and weight entries.

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import require_client
from models.log import DailySurvey
from models.workout import Workout, WorkoutLog, WorkoutPlan, SetResult
from schemas.log import (
    CaloriesLogIn,
    DailySurveyOut,
    LogIn,
    LogsOut,
    SetResultOut,
    StepsLogIn,
    WorkoutLogIn,
    WorkoutLogOut,
)

router = APIRouter(prefix="/logs", tags=["logs"], redirect_slashes=False)

_DEFAULT_MOOD = 3  # mood_type_id for "Okay" — used when auto-creating a daily survey row


# POST /logs — create a workout log, or upsert steps/calories into the daily survey
@router.post("/", status_code=201)
def create_log(
    data: LogIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    if isinstance(data, WorkoutLogIn):
        workout = db.query(Workout).filter(Workout.workout_id == data.workout_id).first()
        if not workout:
            raise HTTPException(status_code=404, detail="Workout not found.")

        log = WorkoutLog(
            workout_id=data.workout_id,
            client_id=current_user.client.client_id,
        )
        db.add(log)
        db.flush()  # populate log.workout_log_id before inserting set results

        for sr in data.sets:
            db.add(SetResult(
                workout_log_id=log.workout_log_id,
                exercise_id=sr.exercise_id,
                actual_weight=sr.actual_weight,
                actual_value=sr.actual_value,
            ))

        db.commit()
        db.refresh(log)
        return WorkoutLogOut(
            workout_log_id=log.workout_log_id,
            workout_id=log.workout_id,
            logged_at=log.logged_at,
            sets=[SetResultOut.model_validate(sr) for sr in log.set_results],
        )

    # steps or calories — upsert into daily_surveys
    survey = db.query(DailySurvey).filter(
        DailySurvey.user_id == current_user.user_id,
        DailySurvey.survey_date == data.date,
    ).first()

    if not survey:
        survey = DailySurvey(
            user_id=current_user.user_id,
            survey_date=data.date,
            mood_type_id=_DEFAULT_MOOD,
        )
        db.add(survey)

    if isinstance(data, StepsLogIn):
        survey.step_count = data.step_count
    elif isinstance(data, CaloriesLogIn):
        if data.calories_intake is not None:
            survey.calories_intake = data.calories_intake
        if data.calories_burned is not None:
            survey.calories_burned = data.calories_burned

    db.commit()
    db.refresh(survey)
    return DailySurveyOut.model_validate(survey)


# GET /logs?userId=&date= — return workout logs and daily survey for a user on a given date
@router.get("/", response_model=LogsOut)
def get_logs(
    userId: int,
    date: date,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    if userId != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only view your own logs.")

    workout_logs = (
        db.query(WorkoutLog)
        .filter(
            WorkoutLog.client_id == current_user.client.client_id,
            func.date(WorkoutLog.logged_at) == date,
        )
        .all()
    )

    survey = db.query(DailySurvey).filter(
        DailySurvey.user_id == current_user.user_id,
        DailySurvey.survey_date == date,
    ).first()

    return LogsOut(
        workout_logs=[
            WorkoutLogOut(
                workout_log_id=log.workout_log_id,
                workout_id=log.workout_id,
                logged_at=log.logged_at,
                sets=[SetResultOut.model_validate(sr) for sr in log.set_results],
            )
            for log in workout_logs
        ],
        daily_survey=DailySurveyOut.model_validate(survey) if survey else None,
    )


# DELETE /logs/{log_id} — delete a workout log only if it was created today; update progress metrics
@router.delete("/{log_id}")
def delete_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    log = db.query(WorkoutLog).filter(WorkoutLog.workout_log_id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found.")

    if log.client_id != current_user.client.client_id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this log.")

    today = datetime.now(timezone.utc).date()
    log_date = log.created_at.date()
    if log_date != today:
        raise HTTPException(status_code=403, detail="Logs can only be deleted on the day they were created.")

    # decrement weeks_completed for each exercise in this log (floor at 0)
    for sr in log.set_results:
        plan = db.query(WorkoutPlan).filter(
            WorkoutPlan.workout_id == log.workout_id,
            WorkoutPlan.exercise_id == sr.exercise_id,
        ).first()
        if plan and plan.weeks_completed > 0:
            plan.weeks_completed -= 1

    db.delete(log)
    db.commit()
    return {"message": "Log deleted."}
