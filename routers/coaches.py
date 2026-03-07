# Handles coach discovery and contract endpoints (UC 5.1–5.4): browsing coaches, sending/accepting/declining requests, and ending contracts.

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from dependencies.rbac import require_client
from models.user import User, Coach, CoachStatus
from models.coach import CoachCertification, CoachAvailability, coach_specialities
from models.log import GoalType

from schemas.coach import CoachOut, CoachRegisterIn

router = APIRouter(prefix="/coaches", tags=["coaches"])


# Endpoint for coach registration
# Gets data for Coach table and other related tables to build out profile
@router.post("/register", response_model=CoachOut)
def register_coach(
    data: CoachRegisterIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_client)
):
    # check if coach already exists
    existing = db.query(Coach).filter(Coach.user_id == current_user.user_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="You have already applied to be a coach")

    # get info for coaches table
    coach = Coach(
        user_id=current_user.user_id,
        gender=data.gender,
        hourly_rate=data.hourly_rate,
        accepting_clients=data.accepting_clients,
        bio=data.bio,
        status_id=1,    # indicates "Pending" status
        is_trainer=data.is_trainer,
        is_nutritionist=data.is_nutritionist,
        years_of_experience=data.years_of_experience,
        max_clients=data.max_clients,
        session_format=data.session_format
    )
    db.add(coach)

    # flush sends the INSERT to the DB so SQLAlchemy assigns coach.coach_id,
    # but does NOT commit — everything is still inside one transaction.
    db.flush()

    # adds certs row by row into Coach_Certifications table
    for cert_name in data.certifications:
        db.add(CoachCertification(
            coach_id=coach.coach_id,
            certification_name=cert_name
        ))

    # add availability slots day by day into Coach_Availability table
    for slot in data.availability:
        db.add(CoachAvailability(
            coach_id=coach.coach_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time
        ))

    # add to Coach_Specialities
    for goal_id in data.specialty_goal_type_ids:
        db.execute(coach_specialities.insert().values(
            coach_id=coach.coach_id,
            goal_type_id=goal_id
        ))

    # Commit and return the newly created coach profile
    # db.refresh reloads the coach object with any DB-generated values (timestamps etc.)
    db.commit()
    db.refresh(coach)
    return coach

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