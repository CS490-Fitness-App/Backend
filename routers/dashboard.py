from datetime import date, timedelta, datetime, time, timezone

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from sqlalchemy import func

from core.database import get_db
from dependencies.rbac import require_client, get_current_user, require_coach
from models.coach import ClientCoach
from models.log import DailySurvey, Goal, GoalType, MoodType, WeightLog
from models.review import Review
from models.user import User, Client, Coach
from models.workout import Workout, WorkoutLog, ScheduledWorkout, WorkoutPlan

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)


def _grams_to_pounds(value):
    if value is None:
        return None
    return round(value / 453.592, 1)


def _cm_to_ft_in(cm):
    if cm is None:
        return None
    total_inches = cm / 2.54
    feet = int(total_inches // 12)
    inches = round(total_inches % 12)
    return f"{feet}'{inches}\""


def _age_from_dob(dob):
    if dob is None:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _weekday_label(day: date) -> str:
    return day.strftime("%a")


def _date_label(day: date) -> str:
    month = day.month
    day_num = day.day
    return f"{month}/{day_num}"


_MOOD_TO_SCORE = {
    "amazing": 2,
    "great": 2,
    "good": 1,
    "okay": 0,
    "ok": 0,
    "bad": -1,
    "low": -1,
    "awful": -2,
}

_SCORE_TO_MOOD = {
    2: "Amazing",
    1: "Good",
    0: "Okay",
    -1: "Bad",
    -2: "Awful",
}


def _score_to_closest_mood(score: float | None) -> str:
    if score is None:
        return "Okay"
    closest_score = min(_SCORE_TO_MOOD.keys(), key=lambda value: abs(value - score))
    return _SCORE_TO_MOOD[closest_score]


@router.get("/client")
def get_client_dashboard(db: Session = Depends(get_db), current_user=Depends(require_client)):
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    client = db.query(Client).filter(Client.user_id == current_user.user_id).first()

    # Today's scheduled workouts from the calendar
    today = date.today()
    scheduled_today = (
        db.query(ScheduledWorkout)
        .options(joinedload(ScheduledWorkout.workout))
        .filter(
            ScheduledWorkout.user_id == current_user.user_id,
            ScheduledWorkout.scheduled_date == today,
        )
        .all()
    )

    next_scheduled = (
        db.query(ScheduledWorkout)
        .options(joinedload(ScheduledWorkout.workout))
        .filter(
            ScheduledWorkout.user_id == current_user.user_id,
            ScheduledWorkout.scheduled_date >= today,
        )
        .order_by(ScheduledWorkout.scheduled_date.asc())
        .first()
    )

    current_workout = (
        db.query(Workout)
        .filter(Workout.assigned_to == current_user.user_id)
        .order_by(Workout.last_updated.desc())
        .first()
    )

    latest_log = None
    if client:
        latest_log = (
            db.query(WorkoutLog)
            .filter(WorkoutLog.client_id == client.client_id)
            .order_by(WorkoutLog.logged_at.desc())
            .first()
        )

    full_name = "Client"
    if user:
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        full_name = f"{first_name} {last_name}".strip() or "Client"

    latest_weight_log = (
        db.query(WeightLog)
        .filter(WeightLog.user_id == current_user.user_id)
        .order_by(WeightLog.created_at.desc())
        .first()
    )

    current_weight_grams = latest_weight_log.weight if latest_weight_log else (client.weight if client else None)
    current_weight_lb = _grams_to_pounds(current_weight_grams)
    goal_weight_lb = _grams_to_pounds(client.goal_weight) if client else None
    weekly_streak = client.weekly_streak if client else 0

    recent_activity = "No recent activity."
    if latest_log:
        log_date = latest_log.logged_at.strftime("%b %d, %Y")
        recent_activity = f"Last workout: {log_date}"

    # Active coach for this client
    active_coach = None
    if client:
        cc = (
            db.query(ClientCoach.coach_id, ClientCoach.status_name)
            .filter(ClientCoach.client_id == client.client_id, ClientCoach.status_name == "Active")
            .first()
        )
        if cc:
            coach_id, relationship_status = cc
            coach = db.query(Coach).filter(Coach.coach_id == coach_id).first()
            if coach:
                coach_user = db.query(User).filter(User.user_id == coach.user_id).first()
                avg_rating = db.query(func.avg(Review.rating)).filter(Review.coach_id == coach.coach_id).scalar()
                specialization = (
                    "Trainer & Nutritionist" if coach.is_trainer and coach.is_nutritionist
                    else "Trainer" if coach.is_trainer
                    else "Nutritionist" if coach.is_nutritionist
                    else "Coach"
                )
                active_coach = {
                    "coach_id": coach.coach_id,
                    "user_id": coach.user_id,
                    "first_name": coach_user.first_name if coach_user else "",
                    "last_name": coach_user.last_name if coach_user else "",
                    "specialization": specialization,
                    "avg_rating": round(float(avg_rating), 1) if avg_rating else None,
                    "status": relationship_status,
                }
    today_workout = scheduled_today[0].workout.name if scheduled_today else "No workout available."
    today_descriptor = f"{len(scheduled_today)} workout scheduled today" if scheduled_today else "Nothing scheduled for today"

    current_plan_name = current_workout.name if current_workout else "No active workout plan"
    next_workout_name = next_scheduled.workout.name if next_scheduled and next_scheduled.workout else "No upcoming workout"
    next_workout_date = next_scheduled.scheduled_date.strftime("%a, %b %d") if next_scheduled else "No workout scheduled"

    weeks_completed = 0
    if current_workout:
        plan_rows = db.query(WorkoutPlan).filter(WorkoutPlan.workout_id == current_workout.workout_id).all()
        if plan_rows:
            weeks_completed = max((row.weeks_completed or 0) for row in plan_rows)

    coach_name = "No coach assigned"
    coach_status = "No active coach"
    if active_coach:
        coach_name = f"{active_coach['first_name'] or ''} {active_coach['last_name'] or ''}".strip() or "No coach assigned"
        coach_status = active_coach["status"]

    weight_descriptor = "No goal weight set"
    if current_weight_lb is not None and goal_weight_lb is not None:
        delta = round(current_weight_lb - goal_weight_lb, 1)
        if delta > 0:
            weight_descriptor = f"Goal: {goal_weight_lb} lb - {delta} lb to go"
        elif delta < 0:
            weight_descriptor = f"Goal: {goal_weight_lb} lb - {abs(delta)} lb below goal"
        else:
            weight_descriptor = f"Goal: {goal_weight_lb} lb - on target"

    return {
        "name": full_name,
        "full_name": full_name,
        "today_workout": today_workout,
        "today_descriptor": today_descriptor,
        "weekly_streak": weekly_streak,
        "streak_descriptor": recent_activity,
        "current_weight_lb": current_weight_lb,
        "goal_weight_lb": goal_weight_lb,
        "weight_descriptor": weight_descriptor,
        "current_plan_name": current_plan_name,
        "next_workout_name": next_workout_name,
        "next_workout_date": next_workout_date,
        "weeks_completed": weeks_completed,
        "intended_duration_weeks": current_workout.intended_duration_weeks if current_workout else None,
        "coach_name": coach_name,
        "coach_status": coach_status,
        "today_workouts": [
            {
                "workout_id": sw.workout_id,
                "name": sw.workout.name,
                "status": sw.status,
            }
            for sw in scheduled_today
        ],
        "recent_activity": recent_activity,
        "weight_lbs": current_weight_lb,
        "goal_weight_lbs": goal_weight_lb,
        "active_coach": active_coach,
    }


@router.get("/client/progress")
def get_client_progress(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    time_range: str = "weekly",
    selected_month: str | None = None,
    client_user_id: Optional[int] = Query(None, description="Coach-only: view a specific client's progress by user_id"),
):
    # If a coach is requesting a client's progress, verify the relationship.
    if client_user_id is not None and client_user_id != current_user.user_id:
        coach = db.query(Coach).filter(Coach.user_id == current_user.user_id).first()
        if not coach:
            raise HTTPException(status_code=403, detail="Only coaches can view other users' progress.")
        target_client = db.query(Client).filter(Client.user_id == client_user_id).first()
        if not target_client:
            raise HTTPException(status_code=404, detail="Client not found.")
        rel = db.query(ClientCoach).filter(
            ClientCoach.coach_id == coach.coach_id,
            ClientCoach.client_id == target_client.client_id,
            ClientCoach.status_name == "Active",
        ).first()
        if not rel:
            raise HTTPException(status_code=403, detail="You do not have an active relationship with this client.")
        target_user_id = client_user_id
    else:
        target_user_id = current_user.user_id

    client = db.query(Client).filter(Client.user_id == target_user_id).first()
    target_user = db.query(User).filter(User.user_id == target_user_id).first()
    client_name = f"{target_user.first_name or ''} {target_user.last_name or ''}".strip() if target_user else None

    today = date.today()

    # Build a list of months where the user has logged weight data.
    month_rows = (
        db.query(func.date_format(WeightLog.created_at, "%Y-%m").label("month_key"))
        .filter(WeightLog.user_id == target_user_id)
        .distinct()
        .order_by(func.date_format(WeightLog.created_at, "%Y-%m").desc())
        .all()
    )

    available_month_keys = [row.month_key for row in month_rows if row.month_key]
    current_month_key = f"{today.year}-{today.month:02d}"

    effective_month_key = selected_month if selected_month in available_month_keys else current_month_key

    if effective_month_key not in available_month_keys:
        available_month_keys.insert(0, effective_month_key)

    available_months = []
    for month_key in available_month_keys:
        parsed = datetime.strptime(month_key, "%Y-%m")
        available_months.append({
            "value": month_key,
            "label": parsed.strftime("%B %Y"),
        })

    # Determine weight chart date range based on time_range parameter
    if time_range == "monthly":
        selected_year, selected_month_num = map(int, effective_month_key.split("-"))
        weight_start = date(selected_year, selected_month_num, 1)

        if selected_year == today.year and selected_month_num == today.month:
            # Current month only shows up to today.
            weight_end = today
        else:
            # Historical month shows full month.
            if selected_month_num == 12:
                next_month_start = date(selected_year + 1, 1, 1)
            else:
                next_month_start = date(selected_year, selected_month_num + 1, 1)
            weight_end = next_month_start - timedelta(days=1)
    else:
        # Default to weekly view: 3 days ago to 3 days in future
        weight_start = today - timedelta(days=3)
        weight_end = today + timedelta(days=3)

    weight_logs = (
        db.query(WeightLog)
        .filter(WeightLog.user_id == target_user_id)
        .order_by(WeightLog.created_at.desc())
        .all()
    )

    latest_weight_by_day = {}
    for log in weight_logs:
        log_day = log.created_at.date()
        if log_day < weight_start or log_day > weight_end:
            continue
        if log_day not in latest_weight_by_day:
            latest_weight_by_day[log_day] = log

    latest_weight_in_range = next(
        (log for log in weight_logs if weight_start <= log.created_at.date() <= weight_end),
        None,
    )

    current_weight_lb = None
    latest_weight = latest_weight_in_range or (weight_logs[0] if weight_logs else None)
    if latest_weight:
        current_weight_lb = _grams_to_pounds(latest_weight.weight)
    elif client and client.weight is not None:
        current_weight_lb = _grams_to_pounds(client.weight)

    goal_weight_lb = _grams_to_pounds(client.goal_weight) if client and client.goal_weight is not None else None

    weight_points = []
    day_cursor = weight_start
    while day_cursor <= weight_end:
        survey_weight_lb = None
        if day_cursor in latest_weight_by_day:
            survey_weight_lb = _grams_to_pounds(latest_weight_by_day[day_cursor].weight)

        weight_points.append({
            "date": day_cursor.isoformat(),
            "label": _date_label(day_cursor),
            "user_weight_lb": current_weight_lb,
            "goal_weight_lb": goal_weight_lb,
            "survey_weight_lb": survey_weight_lb,
        })
        day_cursor += timedelta(days=1)

    week_start = today - timedelta(days=6)
    week_days = [week_start + timedelta(days=index) for index in range(7)]

    week_surveys = (
        db.query(DailySurvey, MoodType)
        .outerjoin(MoodType, DailySurvey.mood_type_id == MoodType.mood_type_id)
        .filter(
            DailySurvey.user_id == target_user_id,
            DailySurvey.survey_date >= week_start,
            DailySurvey.survey_date <= today,
        )
        .all()
    )

    survey_by_date = {}
    for survey, mood in week_surveys:
        survey_by_date[survey.survey_date] = {
            "survey": survey,
            "mood_name": mood.mood_type_name if mood else None,
        }

    weekly_step_points = []
    step_values = []
    water_values = []
    calories_values = []
    mood_scores = []

    for day in week_days:
        survey_row = survey_by_date.get(day)
        survey = survey_row["survey"] if survey_row else None
        mood_name = (survey_row.get("mood_name") or "").strip().lower() if survey_row else ""
        mood_score = _MOOD_TO_SCORE.get(mood_name)

        steps = survey.step_count if survey and survey.step_count is not None else 0
        water = survey.water_intake if survey and survey.water_intake is not None else None
        calories = survey.calories_intake if survey and survey.calories_intake is not None else None

        weekly_step_points.append({
            "date": day.isoformat(),
            "label": _date_label(day),
            "steps": steps,
        })

        step_values.append(steps)
        if water is not None:
            water_values.append(water)
        if calories is not None:
            calories_values.append(calories)
        if mood_score is not None:
            mood_scores.append(mood_score)

    average_steps = round(sum(step_values) / len(step_values), 1) if step_values else 0
    average_water = round(sum(water_values) / len(water_values), 1) if water_values else None
    average_calories = round(sum(calories_values) / len(calories_values), 1) if calories_values else None
    average_mood_score = round(sum(mood_scores) / len(mood_scores), 2) if mood_scores else None
    average_mood_label = _score_to_closest_mood(average_mood_score)

    # Calculate progress towards goal weight
    month_start = weight_start if time_range == "monthly" else date(today.year, today.month, 1)
    start_weight_lb = None
    progress_percent = None
    progress_message = None
    
    # Get weight at the beginning of the month
    start_weight_log = (
        db.query(WeightLog)
        .filter(
            WeightLog.user_id == target_user_id,
            WeightLog.created_at >= datetime.combine(month_start, time.min).replace(tzinfo=timezone.utc),
            WeightLog.created_at < datetime.combine(month_start + timedelta(days=1), time.min).replace(tzinfo=timezone.utc)
        )
        .order_by(WeightLog.created_at.asc())
        .first()
    )
    
    if start_weight_log:
        start_weight_lb = _grams_to_pounds(start_weight_log.weight)
    
    # Calculate progress if we have current weight, goal weight, and starting weight
    if current_weight_lb is not None and goal_weight_lb is not None and start_weight_lb is not None:
        start_distance = start_weight_lb - goal_weight_lb
        current_distance = current_weight_lb - goal_weight_lb
        
        if start_distance != 0:
            progress_percent = round(((start_distance - current_distance) / abs(start_distance)) * 100, 1)
            
            if progress_percent > 0:
                progress_message = f"On track: {progress_percent}% closer to goal"
            elif progress_percent < 0:
                progress_message = f"Off track: {abs(progress_percent)}% further from goal"
            else:
                progress_message = "No progress yet"
        else:
            # Already at goal weight at start of month
            if current_weight_lb == goal_weight_lb:
                progress_message = "At goal weight"
                progress_percent = 100
            elif current_distance > 0:
                progress_message = f"Above goal by {current_distance} lb"
                progress_percent = 0
            else:
                progress_message = f"Below goal by {abs(current_distance)} lb"
                progress_percent = 0

    # Current assigned workout plan
    current_workout = (
        db.query(Workout)
        .filter(Workout.assigned_to == target_user_id)
        .order_by(Workout.last_updated.desc())
        .first()
    )
    weeks_completed_plan = 0
    if current_workout:
        plan_rows = db.query(WorkoutPlan).filter(WorkoutPlan.workout_id == current_workout.workout_id).all()
        if plan_rows:
            weeks_completed_plan = max((row.weeks_completed or 0) for row in plan_rows)

    latest_workout_log = None
    if client:
        latest_workout_log = (
            db.query(WorkoutLog)
            .filter(WorkoutLog.client_id == client.client_id)
            .order_by(WorkoutLog.logged_at.desc())
            .first()
        )

    # Scheduled workouts for calendar (past 30 days → next 90 days)
    cal_start = today - timedelta(days=30)
    cal_end = today + timedelta(days=90)
    scheduled_rows = (
        db.query(ScheduledWorkout)
        .options(joinedload(ScheduledWorkout.workout))
        .filter(
            ScheduledWorkout.user_id == target_user_id,
            ScheduledWorkout.scheduled_date >= cal_start,
            ScheduledWorkout.scheduled_date <= cal_end,
        )
        .order_by(ScheduledWorkout.scheduled_date)
        .all()
    )
    calendar_events = [
        {
            "date": sw.scheduled_date.isoformat(),
            "workout_name": sw.workout.name if sw.workout else "Unknown",
            "workout_id": sw.workout_id,
            "status": sw.status,
        }
        for sw in scheduled_rows
    ]

    # Goals
    goals_rows = (
        db.query(Goal, GoalType)
        .join(GoalType, GoalType.goal_type_id == Goal.goal_type_id)
        .filter(Goal.user_id == target_user_id)
        .order_by(Goal.created_at.asc())
        .all()
    )
    goals = [{"goal_type": gt.goal_type_name, "set_on": g.created_at.date().isoformat()} for g, gt in goals_rows]

    # Weight history (last 20 entries, most recent first)
    weight_history = [
        {
            "date": log.created_at.date().isoformat(),
            "weight_lb": _grams_to_pounds(log.weight),
        }
        for log in weight_logs[:20]
    ]

    return {
        "client_name": client_name,
        "summary": {
            "weekly_streak": client.weekly_streak if client else 0,
            "current_plan_name": current_workout.name if current_workout else None,
            "weeks_completed": weeks_completed_plan,
            "intended_duration_weeks": current_workout.intended_duration_weeks if current_workout else None,
            "last_workout_date": latest_workout_log.logged_at.strftime("%b %d, %Y") if latest_workout_log else None,
            "current_weight_lb": current_weight_lb,
            "goal_weight_lb": goal_weight_lb,
            "height": _cm_to_ft_in(client.height) if client else None,
            "age": _age_from_dob(client.DOB) if client else None,
            "sex": client.sex if client else None,
        },
        "goals": goals,
        "weight_history": weight_history,
        "calendar_events": calendar_events,
        "weight_chart": {
            "current_weight_lb": current_weight_lb,
            "goal_weight_lb": goal_weight_lb,
            "points": weight_points,
            "start_weight_lb": start_weight_lb,
            "progress_percent": progress_percent,
            "progress_message": progress_message,
            "available_months": available_months,
            "selected_month": effective_month_key,
        },
        "steps_chart": {
            "average_steps": average_steps,
            "points": weekly_step_points,
        },
        "weekly_averages": {
            "water_intake": average_water,
            "calories_intake": average_calories,
            "mood_score": average_mood_score,
            "mood_label": average_mood_label,
        },
    }
