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


# Helper to build CoachOut from a Coach ORM object
def _build_coach_out(coach: Coach, db: Session) -> CoachOut:
    from sqlalchemy import func
    from models.review import Review
    
    # Get avg rating from reviews
    avg_rating = db.query(func.avg(Review.rating)).filter(
        Review.coach_id == coach.coach_id
    ).scalar()
    
    # Get certifications
    certs = db.query(CoachCertification).filter(
        CoachCertification.coach_id == coach.coach_id
    ).all()
    cert_names = [c.certification_name for c in certs]
    
    # Get availability
    avail = db.query(CoachAvailability).filter(
        CoachAvailability.coach_id == coach.coach_id
    ).all()
    avail_strs = [f"{a.day_of_week.value if hasattr(a.day_of_week, 'value') else a.day_of_week} {a.start_time}-{a.end_time}" for a in avail]
    
    # Get specialties (goal type names)
    specialties = db.query(GoalType.goal_type_name).join(
        coach_specialities, GoalType.goal_type_id == coach_specialities.c.goal_type_id
    ).filter(
        coach_specialities.c.coach_id == coach.coach_id
    ).all()
    specialty_names = [s[0] for s in specialties]
    
    return CoachOut(
        coach_id=coach.coach_id,
        first_name=coach.user.first_name,
        last_name=coach.user.last_name,
        profile_picture=coach.user.profile_picture,
        bio=coach.bio,
        gender=coach.gender,
        hourly_rate=float(coach.hourly_rate) if coach.hourly_rate else 0.0,
        is_trainer=coach.is_trainer,
        is_nutritionist=coach.is_nutritionist,
        years_of_experience=coach.years_of_experience,
        accepting_clients=coach.accepting_clients,
        avg_rating=float(avg_rating) if avg_rating else None,
        specialties=specialty_names if specialty_names else None,
        certifications=cert_names if cert_names else None,
        availability=avail_strs if avail_strs else None,
    )


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
    return _build_coach_out(coach, db)


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
    # Base query: active coaches who are accepting clients
    query = (
        db.query(Coach)
        .join(User)
        .join(CoachStatus)
        .filter(Coach.accepting_clients == True)
        .filter(CoachStatus.status_name == 'Active')
    )

    # Filter by name
    if name:
        query = query.filter(
            (User.first_name.ilike(f"%{name}%")) | (User.last_name.ilike(f"%{name}%"))
        )
    if trainer:
        query = query.filter(Coach.is_trainer == True)
    if nutritionist:
        query = query.filter(Coach.is_nutritionist == True)
    if min_rate is not None:
        query = query.filter(Coach.hourly_rate >= min_rate)
    if max_rate is not None:
        query = query.filter(Coach.hourly_rate <= max_rate)
    
    # Filter by specialty requires joining coach_specialities
    if specialty:
        query = (
            query
            .join(coach_specialities, coach_specialities.c.coach_id == Coach.coach_id)
            .join(GoalType, GoalType.goal_type_id == coach_specialities.c.goal_type_id)
            .filter(GoalType.goal_type_name == specialty)
        )

    coaches = query.distinct().all()
    
    # Build response with flattened fields
    return [_build_coach_out(c, db) for c in coaches]