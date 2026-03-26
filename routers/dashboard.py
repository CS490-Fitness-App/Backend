from fastapi import APIRouter

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

@router.get("/client")
def get_client_dashboard():
    return {
        "today_workout": "Push Day (Chest, Triceps)",
        "recent_activity": "Last workout: 2 days ago",
        "coach": "Alex Johnson",
        "survey_completed": True
    }