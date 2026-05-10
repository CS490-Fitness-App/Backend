# Handles activity and wellness logging endpoints (UC 3.5, 3.7, 6.5): workout session logs, set results, daily surveys, and weight entries.

from datetime import date, datetime, time, timedelta, timezone
from urllib.parse import urlparse

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from types import SimpleNamespace

from core.config import settings
from core.database import get_db
from dependencies.rbac import require_client
from models.coach import ClientCoach
from models.log import DailySurvey, Goal, Goal, MoodType, ProgressPhoto, UserDailyEngagement, WeightLog
from models.user import Client
from models.workout import ScheduledWorkout, Workout, WorkoutLog, WorkoutPlan, SetResult
from schemas.log import (
    ActivityDayOut,
    ActivityDaySurveyOut,
    ActivityDayUpdateIn,
    ActivityExercisePlanOut,
    ActivityGoalOut,
    ActivityScheduledWorkoutOut,
    ActivitySetResultOut,
    ActivityWorkoutLogOut,
    CaloriesLogIn,
    DailyCheckInIn,
    DailyCheckInStatusOut,
    DailySurveyOut,
    LogIn,
    LogsOut,
    ProgressPhotoOut,
    SetResultOut,
    StepsLogIn,
    WorkoutLogIn,
    WorkoutLogOut,
)

router = APIRouter(prefix="/logs", tags=["logs"], redirect_slashes=False)

cloudinary.config(cloudinary_url=settings.cloudinary_url)

_DEFAULT_MOOD = 3  # mood_type_id for "Okay" — used when auto-creating a daily survey row


_LB_TO_GRAMS = 453.59237
_DEFAULT_MOOD_LABEL = "Okay"
_PROGRESS_PHOTO_FOLDER = "primalfitness/progress_photos"
_ALLOWED_PROGRESS_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_PROGRESS_PHOTO_SIZE = 5 * 1024 * 1024
_LEGACY_MOOD_ALIASES = {
    "amazing": "Great",
    "bad": "Low",
}


def _current_utc_date() -> date:
    return date.today()  # Use local date to match client expectations


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


def _mark_survey_completed(db: Session, user_id: int, survey_date: date) -> None:
    now = datetime.now(timezone.utc)
    engagement = db.query(UserDailyEngagement).filter(
        UserDailyEngagement.user_id == user_id,
        UserDailyEngagement.activity_date == survey_date,
    ).first()
    if engagement:
        engagement.survey_completed = 1
        engagement.last_updated = now
        return

    db.add(UserDailyEngagement(
        user_id=user_id,
        activity_date=survey_date,
        first_login_at=now,
        last_login_at=now,
        survey_completed=1,
        created_at=now,
        last_updated=now,
    ))
def _current_client(current_user, db: Session) -> Client:
    client = current_user.client if hasattr(current_user, "client") else None
    if not client:
        client = db.query(Client).filter(Client.user_id == current_user.user_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client profile not found.")
    return client


def _resolve_activity_target(current_user, db: Session, client_user_id: int | None):
    if client_user_id is not None and client_user_id != current_user.user_id:
        if current_user.role != "coach":
            raise HTTPException(status_code=403, detail="Only coaches can view another user's activity log.")

        coach_profile = current_user.coach
        if not coach_profile:
            raise HTTPException(status_code=403, detail="Coach profile not found.")

        target_client = db.query(Client).filter(Client.user_id == client_user_id).first()
        if not target_client:
            raise HTTPException(status_code=404, detail="Client profile not found.")

        relationship = (
            db.query(ClientCoach)
            .filter(
                ClientCoach.client_id == target_client.client_id,
                ClientCoach.coach_id == coach_profile.coach_id,
                ClientCoach.status_name == "Active",
            )
            .first()
        )
        if not relationship:
            raise HTTPException(status_code=403, detail="No active coaching relationship with this client.")

        return target_client.user_id, target_client.client_id

    client = _current_client(current_user, db)
    return current_user.user_id, client.client_id


def _serialize_progress_photo(photo: ProgressPhoto) -> ProgressPhotoOut:
    return ProgressPhotoOut(
        progress_photo_id=photo.progress_photo_id,
        user_id=photo.user_id,
        photo_type=photo.photo_type,
        image_url=photo.image_url,
        note=photo.note,
        taken_on=photo.taken_on,
        created_at=photo.created_at,
    )


def _progress_photos_for_date(db: Session, user_id: int, target_date: date) -> list[ProgressPhoto]:
    return (
        db.query(ProgressPhoto)
        .filter(
            ProgressPhoto.user_id == user_id,
            ProgressPhoto.taken_on == target_date,
        )
        .order_by(ProgressPhoto.created_at.desc(), ProgressPhoto.progress_photo_id.desc())
        .all()
    )


def _date_bounds(target_date: date) -> tuple[datetime, datetime]:
    start = datetime.combine(target_date, time.min).replace(tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


def _grams_to_pounds(weight_grams: int | None) -> float | None:
    if weight_grams is None:
        return None
    return round(weight_grams / _LB_TO_GRAMS, 1)


def _set_result_has_values(set_result) -> bool:
    return set_result.actual_weight is not None or set_result.actual_value is not None


def _derive_workout_status(set_results) -> str:
    if not set_results:
        return "Scheduled"
    if all(getattr(set_result, "skipped", False) for set_result in set_results):
        return "Skipped"
    if all(getattr(set_result, "skipped", False) or _set_result_has_values(set_result) for set_result in set_results):
        return "Completed"
    if any(getattr(set_result, "skipped", False) or _set_result_has_values(set_result) for set_result in set_results):
        return "In Progress"
    return "Scheduled"


def _decrement_workout_plan_progress(db: Session, workout_log: WorkoutLog) -> None:
    for sr in workout_log.set_results:
        if sr.exercise_id is None or getattr(sr, "skipped", False) or not _set_result_has_values(sr):
            continue
        plan = db.query(WorkoutPlan).filter(
            WorkoutPlan.workout_id == workout_log.workout_id,
            WorkoutPlan.exercise_id == sr.exercise_id,
        ).first()
        if plan and plan.weeks_completed > 0:
            plan.weeks_completed -= 1


def _weight_log_for_date(db: Session, user_id: int, target_date: date) -> WeightLog | None:
    start, end = _date_bounds(target_date)
    return (
        db.query(WeightLog)
        .filter(
            WeightLog.user_id == user_id,
            WeightLog.created_at >= start,
            WeightLog.created_at < end,
        )
        .order_by(WeightLog.created_at.desc())
        .first()
    )


def _serialize_daily_survey(db: Session, survey: DailySurvey | None, target_date: date, user_id: int) -> ActivityDaySurveyOut | None:
    if not survey:
        return None

    weight_log = _weight_log_for_date(db, user_id, target_date)
    return ActivityDaySurveyOut(
        survey_id=survey.survey_id,
        survey_date=survey.survey_date,
        mood_type_id=survey.mood_type_id,
        mood_label=survey.mood_type.mood_type_name if survey.mood_type else _DEFAULT_MOOD_LABEL,
        step_count=survey.step_count,
        calories_intake=survey.calories_intake,
        calories_burned=survey.calories_burned,
        water_intake=survey.water_intake,
        notes=survey.notes,
        weight_lb=_grams_to_pounds(weight_log.weight) if weight_log else None,
    )


def _serialize_scheduled_workout(db: Session, scheduled: ScheduledWorkout) -> ActivityScheduledWorkoutOut:
    exercises = []
    plans = (
        db.query(WorkoutPlan)
        .options(
            joinedload(WorkoutPlan.exercise),
            joinedload(WorkoutPlan.unit),
        )
        .filter(WorkoutPlan.workout_id == scheduled.workout_id)
        .order_by(WorkoutPlan.order_in_workout.asc())
        .all()
    )
    for plan in plans:
        category_name = plan.exercise.category.category_name if plan.exercise and plan.exercise.category else None
        equipment = (plan.exercise.equipment or "").strip().lower() if plan.exercise and plan.exercise.equipment else ""
        allow_weight_input = bool(
            category_name == "Strength"
            and equipment
            and equipment != "none"
        )
        exercises.append(ActivityExercisePlanOut(
            exercise_id=plan.exercise_id,
            exercise_name=plan.exercise.name if plan.exercise else "Exercise",
            category_name=category_name,
            allow_weight_input=allow_weight_input,
            skipped=False,
            sets=plan.sets,
            target_value=float(plan.target_value) if plan.target_value is not None else None,
            unit_name=plan.unit.unit_name if plan.unit else None,
            rest=plan.rest,
        ))
    return ActivityScheduledWorkoutOut(
        workout_id=scheduled.workout_id,
        name=scheduled.workout.name if scheduled.workout else "Workout",
        scheduled_date=scheduled.scheduled_date,
        status=scheduled.status,
        workout_time_mins=scheduled.workout.workout_time_mins if scheduled.workout else None,
        image_url=scheduled.workout.image_url if scheduled.workout else None,
        exercises=exercises,
    )


def _serialize_workout_log(log: WorkoutLog) -> ActivityWorkoutLogOut:
    status = _derive_workout_status(log.set_results)
    return ActivityWorkoutLogOut(
        workout_log_id=log.workout_log_id,
        workout_id=log.workout_id,
        workout_name=log.workout.name if log.workout else "Workout",
        status=status,
        logged_at=log.logged_at,
        set_results=[
            ActivitySetResultOut(
                exercise_id=sr.exercise_id,
                exercise_name=sr.exercise.name if sr.exercise else None,
                skipped=bool(sr.skipped),
                actual_weight=float(sr.actual_weight) if sr.actual_weight is not None else None,
                actual_value=float(sr.actual_value) if sr.actual_value is not None else None,
            )
            for sr in log.set_results
        ],
    )


def _scheduled_workouts_for_date(db: Session, user_id: int, target_date: date) -> list[ScheduledWorkout]:
    return (
        db.query(ScheduledWorkout)
        .options(
            joinedload(ScheduledWorkout.workout),
        )
        .filter(
            ScheduledWorkout.user_id == user_id,
            ScheduledWorkout.scheduled_date == target_date,
        )
        .order_by(ScheduledWorkout.created_at.asc())
        .all()
    )


def _logged_workouts_for_date(db: Session, client_id: int, target_date: date) -> list[WorkoutLog]:
    return (
        db.query(WorkoutLog)
        .options(
            joinedload(WorkoutLog.workout),
            joinedload(WorkoutLog.set_results).joinedload(SetResult.exercise),
        )
        .filter(
            WorkoutLog.client_id == client_id,
            func.date(WorkoutLog.logged_at) == target_date,
        )
        .order_by(WorkoutLog.logged_at.asc())
        .all()
    )


def _goal_tags_for_user(db: Session, user_id: int) -> list[ActivityGoalOut]:
    goals = (
        db.query(Goal)
        .options(joinedload(Goal.goal_type))
        .filter(Goal.user_id == user_id)
        .order_by(Goal.created_at.desc())
        .all()
    )
    return [
        ActivityGoalOut(goal_id=goal.goal_id, goal_type_name=goal.goal_type.goal_type_name)
        for goal in goals
        if goal.goal_type
    ]


def _mood_options(db: Session):
    moods = db.query(MoodType).order_by(MoodType.mood_type_name.asc()).all()
    return [{"mood_type_id": mood.mood_type_id, "mood_label": mood.mood_type_name} for mood in moods]


def _upsert_daily_survey_for_day(db: Session, user_id: int, target_date: date, survey_input):
    if survey_input is None:
        return None

    survey = db.query(DailySurvey).filter(
        DailySurvey.user_id == user_id,
        DailySurvey.survey_date == target_date,
    ).first()

    has_values = any(
        value is not None and value != ""
        for value in [
            survey_input.step_count,
            survey_input.calories_intake,
            survey_input.calories_burned,
            survey_input.water_intake,
            survey_input.weight_lb,
            survey_input.mood_label,
            survey_input.notes,
        ]
    )

    if not survey and not has_values:
        return None

    if not survey:
        survey = DailySurvey(
            user_id=user_id,
            survey_date=target_date,
            mood_type_id=_resolve_mood_type_id(db, survey_input.mood_label),
        )
        db.add(survey)

    if survey_input.step_count is not None:
        survey.step_count = survey_input.step_count
    if survey_input.calories_intake is not None:
        survey.calories_intake = survey_input.calories_intake
    if survey_input.calories_burned is not None:
        survey.calories_burned = survey_input.calories_burned
    if survey_input.water_intake is not None:
        survey.water_intake = survey_input.water_intake
    if survey_input.mood_label is not None:
        survey.mood_type_id = _resolve_mood_type_id(db, survey_input.mood_label)
    if survey_input.notes is not None:
        survey.notes = survey_input.notes.strip() or None

    if survey_input.weight_lb is not None:
        weight_grams = int(round(survey_input.weight_lb * _LB_TO_GRAMS))
        weight_log = _weight_log_for_date(db, user_id, target_date)
        if weight_log:
            weight_log.weight = weight_grams
            weight_log.last_updated = datetime.now(timezone.utc)
        else:
            created_at = datetime.combine(target_date, time(hour=12)).replace(tzinfo=timezone.utc)
            db.add(WeightLog(
                user_id=user_id,
                weight=weight_grams,
                created_at=created_at,
                last_updated=datetime.now(timezone.utc),
            ))
        client = db.query(Client).filter(Client.user_id == user_id).first()
        if client:
            client.weight = weight_grams
            client.last_updated = datetime.now(timezone.utc)

    return survey


def _upsert_workout_logs_for_day(db: Session, client_id: int, user_id: int, target_date: date, workout_logs_input):
    scheduled_rows = {
        row.workout_id: row
        for row in _scheduled_workouts_for_date(db, user_id, target_date)
    }

    for workout_input in workout_logs_input:
        tracked_sets = [
            set_result
            for set_result in workout_input.set_results
            if set_result.skipped or set_result.actual_weight is not None or set_result.actual_value is not None
        ]

        if tracked_sets:
            planned_exercise_ids = [
                row.exercise_id
                for row in db.query(WorkoutPlan.exercise_id)
                .filter(WorkoutPlan.workout_id == workout_input.workout_id)
                .all()
            ]
            logged_exercise_ids = {set_result.exercise_id for set_result in tracked_sets}
            for exercise_id in planned_exercise_ids:
                if exercise_id not in logged_exercise_ids:
                    tracked_sets.append(SimpleNamespace(
                        exercise_id=exercise_id,
                        skipped=True,
                        actual_weight=None,
                        actual_value=None,
                    ))

        effective_status = _derive_workout_status(tracked_sets)

        scheduled = scheduled_rows.get(workout_input.workout_id)
        if scheduled:
            scheduled.status = effective_status

        existing_log = (
            db.query(WorkoutLog)
            .filter(
                WorkoutLog.client_id == client_id,
                WorkoutLog.workout_id == workout_input.workout_id,
                func.date(WorkoutLog.logged_at) == target_date,
            )
            .first()
        )

        if effective_status != "Completed":
            if existing_log:
                db.query(SetResult).filter(SetResult.workout_log_id == existing_log.workout_log_id).delete()
                db.delete(existing_log)
            continue

        if existing_log is None:
            logged_at = datetime.combine(target_date, time(hour=12)).replace(tzinfo=timezone.utc)
            existing_log = WorkoutLog(
                workout_id=workout_input.workout_id,
                client_id=client_id,
                logged_at=logged_at,
                created_at=datetime.now(timezone.utc),
                last_updated=datetime.now(timezone.utc),
            )
            db.add(existing_log)
            db.flush()
        else:
            existing_log.last_updated = datetime.now(timezone.utc)
            db.query(SetResult).filter(SetResult.workout_log_id == existing_log.workout_log_id).delete()
            db.flush()

        for set_result in tracked_sets:
            db.add(SetResult(
                workout_log_id=existing_log.workout_log_id,
                exercise_id=set_result.exercise_id,
                skipped=bool(set_result.skipped),
                actual_weight=set_result.actual_weight,
                actual_value=set_result.actual_value,
            ))


@router.get("/activity-day", response_model=ActivityDayOut)
def get_activity_day(
    date: date = Query(...),
    client_user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    target_user_id, target_client_id = _resolve_activity_target(current_user, db, client_user_id)

    survey = (
        db.query(DailySurvey)
        .options(joinedload(DailySurvey.mood_type))
        .filter(
            DailySurvey.user_id == target_user_id,
            DailySurvey.survey_date == date,
        )
        .first()
    )
    scheduled_workouts = _scheduled_workouts_for_date(db, target_user_id, date)
    logged_workouts = _logged_workouts_for_date(db, target_client_id, date)
    day_weight_log = _weight_log_for_date(db, target_user_id, date)
    progress_photos = _progress_photos_for_date(db, target_user_id, date)
    has_logged_data = bool(survey or logged_workouts or day_weight_log or progress_photos)

    is_coach_viewing_client = (
        current_user.role == "coach"
        and client_user_id is not None
        and client_user_id != current_user.user_id
    )
    return ActivityDayOut(
        date=date,
        is_today=not is_coach_viewing_client and date == _current_utc_date(),
        can_delete=not is_coach_viewing_client and date == _current_utc_date() and has_logged_data,
        has_logged_data=has_logged_data,
        mood_options=_mood_options(db),
        goals=_goal_tags_for_user(db, target_user_id),
        scheduled_workouts=[_serialize_scheduled_workout(db, row) for row in scheduled_workouts],
        logged_workouts=[_serialize_workout_log(log) for log in logged_workouts],
        daily_survey=_serialize_daily_survey(db, survey, date, target_user_id),
        progress_photos=[_serialize_progress_photo(photo) for photo in progress_photos],
    )


@router.put("/activity-day", response_model=ActivityDayOut)
def save_activity_day(
    payload: ActivityDayUpdateIn,
    date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    client = _current_client(current_user, db)

    _upsert_daily_survey_for_day(db, current_user.user_id, date, payload.daily_survey)
    _upsert_workout_logs_for_day(db, client.client_id, current_user.user_id, date, payload.workout_logs)

    db.commit()

    return get_activity_day(date=date, db=db, current_user=current_user)


@router.delete("/activity-day", response_model=ActivityDayOut)
def delete_activity_day(
    date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    if date != _current_utc_date():
        raise HTTPException(
            status_code=403,
            detail="Only logs created today can be deleted.",
        )

    client = _current_client(current_user, db)

    workout_logs = _logged_workouts_for_date(db, client.client_id, date)
    for workout_log in workout_logs:
        _decrement_workout_plan_progress(db, workout_log)
        db.delete(workout_log)

    survey = db.query(DailySurvey).filter(
        DailySurvey.user_id == current_user.user_id,
        DailySurvey.survey_date == date,
    ).first()
    if survey:
        db.delete(survey)

    weight_log = _weight_log_for_date(db, current_user.user_id, date)
    if weight_log:
        db.delete(weight_log)

    for photo in _progress_photos_for_date(db, current_user.user_id, date):
        db.delete(photo)

    db.commit()

    return get_activity_day(date=date, db=db, current_user=current_user)


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

    _mark_survey_completed(db, current_user.user_id, data.date)

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

    _mark_survey_completed(db, current_user.user_id, data.date)

    db.commit()
    db.refresh(survey)

    return {
        "daily_survey": DailySurveyOut.model_validate(survey),
        "weight_logged_lb": weight_logged_lb,
    }


@router.post("/activity-day/photos", response_model=ProgressPhotoOut, status_code=status.HTTP_201_CREATED)
async def upload_activity_day_photo(
    date: date = Query(...),
    photo_type: str = Form(...),
    note: str | None = Form(default=None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    _current_client(current_user, db)

    if date < _current_utc_date():
        raise HTTPException(status_code=403, detail="Historical logs are locked and cannot be edited.")

    normalized_type = (photo_type or "").strip().lower()
    if normalized_type not in {"before", "after"}:
        raise HTTPException(status_code=400, detail="photo_type must be either 'before' or 'after'.")

    if image.content_type not in _ALLOWED_PROGRESS_PHOTO_TYPES:
        raise HTTPException(status_code=400, detail="Please upload a JPG, PNG, WEBP, or GIF image.")

    file_bytes = await image.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image was empty.")
    if len(file_bytes) > _MAX_PROGRESS_PHOTO_SIZE:
        raise HTTPException(status_code=400, detail="Images must be 5 MB or smaller.")

    uploaded = cloudinary.uploader.upload(
        file_bytes,
        folder=_PROGRESS_PHOTO_FOLDER,
        resource_type="image",
        public_id=f"user_{current_user.user_id}_{date.isoformat()}_{normalized_type}_{int(datetime.now(timezone.utc).timestamp())}",
        overwrite=False,
    )

    photo = ProgressPhoto(
        user_id=current_user.user_id,
        photo_type=normalized_type,
        image_url=uploaded["secure_url"],
        note=(note or "").strip() or None,
        taken_on=date,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return _serialize_progress_photo(photo)


@router.delete("/activity-day/photos/{progress_photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity_day_photo(
    progress_photo_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    _current_client(current_user, db)

    photo = (
        db.query(ProgressPhoto)
        .filter(
            ProgressPhoto.progress_photo_id == progress_photo_id,
            ProgressPhoto.user_id == current_user.user_id,
        )
        .first()
    )
    if not photo:
        raise HTTPException(status_code=404, detail="Progress photo not found.")

    if photo.taken_on < _current_utc_date():
        raise HTTPException(status_code=403, detail="Historical logs are locked and cannot be edited.")

    cloud_name = cloudinary.config().cloud_name
    if cloud_name and photo.image_url:
        parsed = urlparse(photo.image_url)
        marker = f"/{cloud_name}/image/upload/"
        if marker in parsed.path:
            public_id = parsed.path.split(marker, 1)[1]
            if "." in public_id:
                public_id = public_id.rsplit(".", 1)[0]
            try:
                cloudinary.uploader.destroy(public_id)
            except Exception:
                pass

    db.delete(photo)
    db.commit()
    return None


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
    _decrement_workout_plan_progress(db, log)

    db.delete(log)
    db.commit()
    return {"message": "Log deleted."}
