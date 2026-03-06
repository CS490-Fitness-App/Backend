# Handles coach discovery and contract endpoints (UC 5.1–5.4): browsing coaches, sending/accepting/declining requests, and ending contracts.

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from dependencies.rbac import require_client
from models.user import User, Coach, CoachStatus
from models.coach import CoachCertification, CoachAvailability, coach_specialities
from models.log import Goal, GoalType

from schemas.coach import CoachOut

router = APIRouter(prefix="/coaches", tags=["coaches"])


# UC 5.1 — Browse/search available coaches
@router.get("/", response_model=list[CoachOut])
def browse_coaches(
    name: Optional[str] = Query(None, description="Search by coach's first or last name"),
    trainer: Optional[bool] = Query(None),
    nutritionist: Optional[bool] = Query(None),
    specialty: Optional[str] = Query(None),
    min_rate: Optional[float] = Query(None),
    max_rate: Optional[float] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    #basic query to get active coaches who are accepting clients
    #with joins to get certs and specialities for display and filtering
    query = (
        db.query(Coach)
        .join(User)
        .join(CoachStatus)
        .join(CoachCertification, Coach.coach_id == CoachCertification.coach_id, isouter=True)
        .join(coach_specialities, coach_specialities.c.coach_id == Coach.coach_id, isouter=True)
        .join(GoalType, GoalType.goal_type_id == coach_specialities.c.goal_type_id, isouter=True)
        .join(GoalType, isouter=True)
        .filter(Coach.accepting_clients == True)
        .filter(CoachStatus.status_name == 'Active')
    )

    #filtering added based on input
    if name:
        query = query.filter((User.first_name.ilike(f"%{name}%")) | (User.last_name.ilike(f"%{name}%")))
    if trainer:
        query = query.filter(Coach.is_trainer == True)
    if nutritionist:
        query = query.filter(Coach.is_nutritionist == True)
    if specialty:
        query = query.filter(GoalType.goal_type_name == specialty)
    if min_rate is not None:
        query = query.filter(Coach.hourly_rate >= min_rate)
    if max_rate is not None:
        query = query.filter(Coach.hourly_rate <= max_rate)

    #use distinct to avoid duplicates and get all matching results and return
    coaches = query.distinct().all()
    return coaches