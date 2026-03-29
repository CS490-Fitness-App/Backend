from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from dependencies.rbac import get_current_user
from models.user import User, Client
from models.workout import Workout, WorkoutLog, ScheduledWorkout

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
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
    }
