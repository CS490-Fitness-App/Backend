# Handles coach discovery and contract endpoints: browsing coaches, sending/accepting/declining requests, and ending contracts.

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from dependencies.rbac import require_client
from models.user import User, Coach, CoachStatus, Client
from models.coach import ClientCoach, CoachCertification, CoachAvailability, coach_specialities
from models.log import Goal, GoalType
from models.notification import Notification

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

@router.post("/request")
def send_request(
    client_id: int,
    coach_id: int,
    db: Session = Depends(get_db),
):
    #check whether request is valid and return error if necessary
    query = db.query(Coach).filter(Coach.coach_id == coach_id, Coach.accepting_clients == True).first()
    if not query:
        return {"error": "Coach not found or not accepting clients."}
    
    #check if there's already a pending request or active contract and return error if it does
    existing_relationship = db.query(ClientCoach).filter(
        ClientCoach.client_id == client_id,
        ClientCoach.coach_id == coach_id,
        ClientCoach.status_name.in_(['Pending', 'Active', 'Terminated', 'Declined'])
    ).first()
    if existing_relationship:
        return {"error": "A request or contract already exists between this client and coach."}
    
    #if valid add pending request to ClientCoach table and return success message
    new_request = ClientCoach(client_id=client_id, coach_id=coach_id, status_name='Pending')
    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    #get client's name for notification
    client = db.query(User).join(Client).filter(User.user_id == Client.user_id).first()
    client_name = f"{client.first_name} {client.last_name}"

    #notify the coach
    notification = Notification(
        user_id=coach_id,
        message=f"You have a new coaching request from client {client_name}."
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    return {"message": "Request sent successfully."}

@router.post("/request/accept")
def accept_request(
    client_id: int,
    coach_id: int,
    db: Session = Depends(get_db),
):
    #check if pending request exists and return error if not
    relationship = db.query(ClientCoach).filter(
        ClientCoach.client_id == client_id,
        ClientCoach.coach_id == coach_id,
        ClientCoach.status_name == 'Pending'
    ).first()
    if not relationship:
        return {"error": "No pending request found between this client and coach."}
    
    #update status to active and return success message
    relationship.status_name = 'Active'
    db.commit()

    #get coach's name for notification
    coach = db.query(User).join(Coach).filter(User.user_id == Coach.user_id).first()
    coach_name = f"{coach.first_name} {coach.last_name}"

    #notify the client
    notification = Notification(
        user_id=coach_id,
        message=f"Your coaching request to {coach_name} has been accepted."
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    return {"message": "Request accepted successfully."}