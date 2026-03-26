from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from models.user import User, Client
from models.workout import Workout, WorkoutLog

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

@router.get("/client")
def get_client_dashboard(db: Session = Depends(get_db)):
    demo_user_id = 1

    user = db.query(User).filter(User.user_id == demo_user_id).first()
    client = db.query(Client).filter(Client.user_id == demo_user_id).first()

    latest_workout = (
        db.query(Workout)
        .filter(Workout.assigned_to == demo_user_id)
        .order_by(Workout.created_at.desc())
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

    recent_activity = "No recent activity."
    if latest_log:
        log_date = latest_log.logged_at.strftime("%b %d, %Y")
        recent_activity = f"Last workout: {log_date}"

    return {
        "name": full_name,
        "today_workout": latest_workout.name if latest_workout else "No workout assigned.",
        "recent_activity": recent_activity,
    }
