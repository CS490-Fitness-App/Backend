# Handles activity and wellness logging endpoints (UC 3.5, 3.7, 6.5): workout session logs, set results, daily surveys, and weight entries.

from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import require_client
from models.log import DailySurvey, MoodType, WeightLog
from models.user import Client
from models.workout import Workout, WorkoutLog, WorkoutPlan, ScheduledWorkout, SetResult
from schemas.log import (
    ActivityDayIn,
    ActivityDayOut,
    CaloriesLogIn,
    DailyCheckInIn,
    DailyCheckInStatusOut,
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


_LB_TO_GRAMS = 453.59237
_DEFAULT_MOOD_LABEL = "Okay"
_LEGACY_MOOD_ALIASES = {
    "amazing": "Great",
    "bad": "Low",
}


def _current_utc_date() -> date:
    return datetime.now(timezone.utc).date()


def _next_utc_midnight() -> datetime:
    now = datetime.now(timezone.utc)
    tomorrow = now.date().toordinal() + 1
    return datetime.fromordinal(tomorrow).replace(tzinfo=timezone.utc)


def _next_local_midnight_in_utc(target_date: date, tz_offset_minutes: int) -> datetime:
    # JS Date.getTimezoneOffset() uses UTC - local (minutes).
    local_next_midnight = datetime.combine(target_date + timedelta(days=1), time.min)
    return (local_next_midnight + timedelta(minutes=tz_offset_minutes)).replace(tzinfo=timezone.utc)


def _resolve_mood_type_id(db: Session, mood_label: str | None) -> int:
    selected_label = (mood_label or _DEFAULT_MOOD_LABEL).strip()
    if not selected_label:
        selected_label = _DEFAULT_MOOD_LABEL

    existing = db.query(MoodType).filter(
        func.lower(MoodType.mood_type_name) == selected_label.lower()
    ).first()
    if existing:
        return existing.mood_type_id

    legacy_label = _LEGACY_MOOD_ALIASES.get(selected_label.lower())
    if legacy_label:
        legacy = db.query(MoodType).filter(
            func.lower(MoodType.mood_type_name) == legacy_label.lower()
        ).first()
        if legacy:
            return legacy.mood_type_id

    mood = MoodType(mood_type_name=selected_label)
    db.add(mood)
    db.flush()
    return mood.mood_type_id


@router.get("/daily-checkin/status", response_model=DailyCheckInStatusOut)
def get_daily_checkin_status(
    for_date: date | None = Query(default=None),
    tz_offset_minutes: int | None = Query(default=None, ge=-840, le=840),
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    target_date = for_date or _current_utc_date()
    survey = db.query(DailySurvey).filter(
        DailySurvey.user_id == current_user.user_id,
        DailySurvey.survey_date == target_date,
    ).first()

    if tz_offset_minutes is not None:
        next_reset_at = _next_local_midnight_in_utc(target_date, tz_offset_minutes)
    else:
        next_reset_at = _next_utc_midnight()

    return DailyCheckInStatusOut(
        completed=survey is not None,
        date=target_date,
        next_reset_at=next_reset_at,
    )


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


@router.post("/daily-checkin", status_code=201)
def create_daily_checkin(
    data: DailyCheckInIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    survey = db.query(DailySurvey).filter(
        DailySurvey.user_id == current_user.user_id,
        DailySurvey.survey_date == data.date,
    ).first()

    if survey:
        raise HTTPException(
            status_code=409,
            detail="Daily check-in already submitted for today. Please return after midnight.",
        )

    survey = DailySurvey(
        user_id=current_user.user_id,
        survey_date=data.date,
        mood_type_id=_resolve_mood_type_id(db, data.mood_label),
    )
    db.add(survey)

    if data.calories_intake is not None:
        survey.calories_intake = data.calories_intake
    if data.step_count is not None:
        survey.step_count = data.step_count
    if data.water_intake is not None:
        survey.water_intake = data.water_intake
    if data.mood_label is not None:
        survey.mood_type_id = _resolve_mood_type_id(db, data.mood_label)

    weight_logged_lb = None
    if data.weight_lb is not None:
        weight_grams = int(round(data.weight_lb * _LB_TO_GRAMS))
        db.add(WeightLog(user_id=current_user.user_id, weight=weight_grams))
        client = db.query(Client).filter(Client.user_id == current_user.user_id).first()
        if client:
            client.weight = weight_grams
            client.last_updated = datetime.now(timezone.utc)
        weight_logged_lb = data.weight_lb

    db.commit()
    db.refresh(survey)

    return {
        "daily_survey": DailySurveyOut.model_validate(survey),
        "weight_logged_lb": weight_logged_lb,
    }


def _build_activity_day_response(db: Session, current_user, target_date: date) -> dict:
    client = current_user.client
    today = _current_utc_date()

    survey = db.query(DailySurvey).filter(
        DailySurvey.user_id == current_user.user_id,
        DailySurvey.survey_date == target_date,
    ).first()

    weight_log = (
        db.query(WeightLog)
        .filter(
            WeightLog.user_id == current_user.user_id,
            func.date(WeightLog.created_at) == target_date,
        )
        .order_by(WeightLog.created_at.desc())
        .first()
    )
    weight_lb = round(weight_log.weight / _LB_TO_GRAMS, 1) if weight_log else None

    daily_survey_out = None
    if survey:
        mood_label = survey.mood_type.mood_type_name if survey.mood_type else None
        daily_survey_out = {
            "step_count": survey.step_count,
            "calories_intake": survey.calories_intake,
            "calories_burned": survey.calories_burned,
            "water_intake": survey.water_intake,
            "weight_lb": weight_lb,
            "mood_label": mood_label,
            "notes": survey.notes,
        }

    mood_options = [{"mood_label": m.mood_type_name} for m in db.query(MoodType).all()]

    scheduled = db.query(ScheduledWorkout).filter(
        ScheduledWorkout.user_id == current_user.user_id,
        ScheduledWorkout.scheduled_date == target_date,
    ).all()

    scheduled_workouts_out = []
    for sw in scheduled:
        workout = sw.workout
        plans = (
            db.query(WorkoutPlan)
            .filter(WorkoutPlan.workout_id == workout.workout_id)
            .order_by(WorkoutPlan.order_in_workout)
            .all()
        )
        exercises_out = [
            {
                "exercise_id": plan.exercise.exercise_id,
                "exercise_name": plan.exercise.name,
                "category_name": plan.exercise.category.category_name if plan.exercise.category else None,
                "allow_weight_input": True,
                "sets": plan.sets,
                "target_value": float(plan.target_value) if plan.target_value is not None else None,
                "unit_name": plan.unit.unit_name if plan.unit else None,
                "rest": plan.rest,
            }
            for plan in plans
        ]
        scheduled_workouts_out.append({
            "workout_id": workout.workout_id,
            "name": workout.name,
            "workout_time_mins": workout.workout_time_mins,
            "exercises": exercises_out,
        })

    workout_logs = db.query(WorkoutLog).filter(
        WorkoutLog.client_id == client.client_id,
        func.date(WorkoutLog.logged_at) == target_date,
    ).all()

    logged_workouts_out = [
        {
            "workout_id": log.workout_id,
            "workout_name": log.workout.name,
            "set_results": [
                {
                    "exercise_id": sr.exercise_id,
                    "exercise_name": sr.exercise.name if sr.exercise else None,
                    "actual_weight": float(sr.actual_weight) if sr.actual_weight is not None else None,
                    "actual_value": float(sr.actual_value) if sr.actual_value is not None else None,
                    "skipped": False,
                }
                for sr in log.set_results
            ],
        }
        for log in workout_logs
    ]

    has_logged_data = survey is not None or len(workout_logs) > 0
    return {
        "daily_survey": daily_survey_out,
        "mood_options": mood_options,
        "scheduled_workouts": scheduled_workouts_out,
        "logged_workouts": logged_workouts_out,
        "has_logged_data": has_logged_data,
        "can_delete": has_logged_data and target_date == today,
    }


@router.get("/activity-day", response_model=ActivityDayOut)
def get_activity_day(
    date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    return _build_activity_day_response(db, current_user, date or _current_utc_date())


@router.put("/activity-day", response_model=ActivityDayOut)
def upsert_activity_day(
    data: ActivityDayIn,
    date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    target_date = date or _current_utc_date()
    client = current_user.client

    if data.daily_survey:
        survey = db.query(DailySurvey).filter(
            DailySurvey.user_id == current_user.user_id,
            DailySurvey.survey_date == target_date,
        ).first()

        if not survey:
            survey = DailySurvey(
                user_id=current_user.user_id,
                survey_date=target_date,
                mood_type_id=_resolve_mood_type_id(db, data.daily_survey.mood_label),
            )
            db.add(survey)
        else:
            if data.daily_survey.mood_label:
                survey.mood_type_id = _resolve_mood_type_id(db, data.daily_survey.mood_label)

        survey.step_count = data.daily_survey.step_count
        survey.calories_intake = data.daily_survey.calories_intake
        survey.calories_burned = data.daily_survey.calories_burned
        survey.water_intake = data.daily_survey.water_intake
        survey.notes = data.daily_survey.notes

        if data.daily_survey.weight_lb is not None:
            weight_grams = int(round(data.daily_survey.weight_lb * _LB_TO_GRAMS))
            existing_weight = (
                db.query(WeightLog)
                .filter(
                    WeightLog.user_id == current_user.user_id,
                    func.date(WeightLog.created_at) == target_date,
                )
                .first()
            )
            if existing_weight:
                existing_weight.weight = weight_grams
            else:
                db.add(WeightLog(user_id=current_user.user_id, weight=weight_grams))
            if client:
                client.weight = weight_grams
                client.last_updated = datetime.now(timezone.utc)

    for wl_data in data.workout_logs:
        existing_log = db.query(WorkoutLog).filter(
            WorkoutLog.client_id == client.client_id,
            WorkoutLog.workout_id == wl_data.workout_id,
            func.date(WorkoutLog.logged_at) == target_date,
        ).first()

        if existing_log:
            for sr in existing_log.set_results:
                db.delete(sr)
            db.flush()
            log = existing_log
        else:
            log = WorkoutLog(workout_id=wl_data.workout_id, client_id=client.client_id)
            db.add(log)
            db.flush()

        for sr_data in wl_data.set_results:
            db.add(SetResult(
                workout_log_id=log.workout_log_id,
                exercise_id=sr_data.exercise_id,
                actual_weight=sr_data.actual_weight,
                actual_value=sr_data.actual_value,
            ))

    db.commit()
    return _build_activity_day_response(db, current_user, target_date)


@router.delete("/activity-day", response_model=ActivityDayOut)
def delete_activity_day(
    date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    target_date = date or _current_utc_date()
    if target_date != _current_utc_date():
        raise HTTPException(status_code=403, detail="You can only delete today's activity log.")

    client = current_user.client

    survey = db.query(DailySurvey).filter(
        DailySurvey.user_id == current_user.user_id,
        DailySurvey.survey_date == target_date,
    ).first()
    if survey:
        db.delete(survey)

    for wl in db.query(WeightLog).filter(
        WeightLog.user_id == current_user.user_id,
        func.date(WeightLog.created_at) == target_date,
    ).all():
        db.delete(wl)

    for wl in db.query(WorkoutLog).filter(
        WorkoutLog.client_id == client.client_id,
        func.date(WorkoutLog.logged_at) == target_date,
    ).all():
        db.delete(wl)

    db.commit()
    return _build_activity_day_response(db, current_user, target_date)


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
