from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from sqlalchemy import func

from core.database import get_db
from dependencies.rbac import require_client
from models.coach import ClientCoach
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

    current_weight_lb = _grams_to_pounds(client.weight) if client else None
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
