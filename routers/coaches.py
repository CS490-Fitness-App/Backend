# Handles coach discovery and contract endpoints: browsing coaches, sending/accepting/declining requests, and ending contracts.

from fastapi import APIRouter, Depends, HTTPException, Query
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


#Browse/search available coaches
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

# Send coaching request from client to coach
@router.post("/request")
def send_request(
    coach_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_client)
):
    #get client_id from current_user
    client_id = current_user.client.client_id

    #check whether request is valid and return error if necessary
    query = db.query(Coach).filter(Coach.coach_id == coach_id, Coach.accepting_clients == True).first()
    if not query:
        raise HTTPException(status_code=404, detail="Coach not found or not accepting clients.")

    #check if there's already a pending request or active contract and return error if it does
    existing_relationship = db.query(ClientCoach).filter(
        ClientCoach.client_id == client_id,
        ClientCoach.coach_id == coach_id,
        ClientCoach.status_name.in_(['Pending', 'Active', 'Terminated', 'Declined'])
    ).first()
    if existing_relationship:
        raise HTTPException(status_code=409, detail="A request or contract already exists between this client and coach.")
    
    #if valid add pending request to ClientCoach table and return success message
    new_request = ClientCoach(client_id=client_id, coach_id=coach_id, status_name='Pending')
    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    #get client's name for notification
    client_name = f"{current_user.first_name} {current_user.last_name}"

    #notify the coach by adding notification to Notifications table
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
    db: Session = Depends(get_db),
    current_user=Depends(require_client)
):
    #get coach_id from current_user
    coach_id = current_user.coach.coach_id

    #check if pending request exists and return error if not
    relationship = db.query(ClientCoach).filter(
        ClientCoach.client_id == client_id,
        ClientCoach.coach_id == coach_id,
        ClientCoach.status_name == 'Pending'
    ).first()
    if not relationship:
        raise HTTPException(status_code=404, detail="No pending request found between this client and coach.")

    #update status to active and return success message
    relationship.status_name = 'Active'
    db.commit()

    #get coach's name for notification
    coach_name = f"{current_user.first_name} {current_user.last_name}"

    #notify the client by adding notification to Notifications table
    notification = Notification(
        user_id=client_id,
        message=f"Your coaching request to {coach_name} has been accepted."
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    return {"message": "Request accepted successfully."}

@router.post("/request/decline")
def decline_request(
    client_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_client)
):
    #get coach_id from current_user
    coach_id = current_user.coach.coach_id

    #check if pending request exists and return error if not
    relationship = db.query(ClientCoach).filter(
        ClientCoach.client_id == client_id,
        ClientCoach.coach_id == coach_id,
        ClientCoach.status_name == 'Pending'
    ).first()
    if not relationship:
        raise HTTPException(status_code=404, detail="No pending request found between this client and coach.")

    #update status to declined and return success message
    relationship.status_name = 'Declined'
    db.commit()

    #get coach's name for notification
    coach_name = f"{current_user.first_name} {current_user.last_name}"

    #notify the client by adding notification to Notifications table
    notification = Notification(
        user_id=client_id,
        message=f"Your coaching request to {coach_name} has been declined."
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    return {"message": "Request declined successfully."}


@router.post("/contract/end")
def end_contract(
    other_user_id: int = Query(..., description="ID of the other party in the contract (coach or client)"),
    db: Session = Depends(get_db),
    current_user=Depends(require_client)
):
    #check if current_user is a Client
    if current_user.role == 'client':
        #assign ids to appropriate vars
        client_id = current_user.client.client_id
        coach_id = other_user_id

        #check if active contract exists and return error if not
        relationship = db.query(ClientCoach).filter(
            ClientCoach.client_id == client_id,
            ClientCoach.coach_id == coach_id,
            ClientCoach.status_name == 'Active'
        ).first()
        if not relationship:
            raise HTTPException(status_code=404, detail="No active contract found between this client and coach.")

        #update status to terminated
        relationship.status_name = 'Terminated'
        db.commit()

        #notify the coach by adding notification to Notifications table
        notification = Notification(
            user_id=other_user_id,
            message=f"{current_user.first_name} {current_user.last_name} terminated coaching contract."
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        return {"message": "Contract terminated successfully."}
    
    #if current_user is a Coach
    elif current_user.role == 'coach':
        #assign ids to appropriate vars
        coach_id = current_user.coach.coach_id
        client_id = other_user_id

        #check if active contract exists and return error if not
        relationship = db.query(ClientCoach).filter(
            ClientCoach.client_id == client_id,
            ClientCoach.coach_id == coach_id,
            ClientCoach.status_name == 'Active'
        ).first()
        if not relationship:
            raise HTTPException(status_code=404, detail="No active contract found between this client and coach.")

        #update status to terminated
        relationship.status_name = 'Terminated'
        db.commit()

        #notify the Client by adding notification to Notifications table
        notification = Notification(
            user_id=client_id,
            message=f"{current_user.first_name} {current_user.last_name} terminated coaching contract."
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)
        return {"message": "Contract terminated successfully."}
    
    else:
        raise HTTPException(status_code=403, detail="Invalid user role for Client-Coach relationship termination.")