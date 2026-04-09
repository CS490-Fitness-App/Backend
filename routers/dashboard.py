from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from sqlalchemy import func

from core.database import get_db
from dependencies.rbac import get_current_user
from models.user import User, Client, Coach
from models.coach import ClientCoach
from models.review import Review
from models.workout import Workout, WorkoutLog, ScheduledWorkout

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)


@router.get("/client")
def get_client_dashboard(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
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

    recent_activity = "No recent activity."
    if latest_log:
        log_date = latest_log.logged_at.strftime("%b %d, %Y")
        recent_activity = f"Last workout: {log_date}"

    weight_lbs = round(client.weight / 453.592, 1) if client and client.weight else None
    goal_weight_lbs = round(client.goal_weight / 453.592, 1) if client and client.goal_weight else None

    # Active coach for this client
    active_coach = None
    if client:
        cc = (
            db.query(ClientCoach)
            .filter(ClientCoach.client_id == client.client_id, ClientCoach.status_name == "Active")
            .first()
        )
        if cc:
            coach = db.query(Coach).filter(Coach.coach_id == cc.coach_id).first()
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
                    "status": cc.status_name,
                }

    return {
        "name": (user.first_name or full_name) if user else full_name,
        "today_workouts": [
            {
                "workout_id": sw.workout_id,
                "name": sw.workout.name,
                "status": sw.status,
            }
            for sw in scheduled_today
        ],
        "recent_activity": recent_activity,
        "weight_lbs": weight_lbs,
        "goal_weight_lbs": goal_weight_lbs,
        "active_coach": active_coach,
    }
