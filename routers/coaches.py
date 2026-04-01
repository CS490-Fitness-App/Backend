# Handles coach discovery and contract endpoints: browsing coaches, sending/accepting/declining requests, and ending contracts.

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from dependencies.rbac import require_client, require_coach, get_current_user
from models.user import User, Coach, CoachStatus, Client
from models.coach import ClientCoach, CoachCertification, CoachAvailability, coach_specialities
from models.log import Goal, GoalType
from models.notification import Notification

from schemas.coach import CoachOut, CoachRegisterIn, CoachClientsOut, ClientEntry

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
    session_format: Optional[str] = Query(None, description="Filter by session format: Virtual, In-Person, Both"),
    db: Session = Depends(get_db)
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
    if session_format:
        if session_format == 'Virtual':
            query = query.filter(Coach.session_formats.in_(['Virtual', 'Both']))
        elif session_format == 'In-Person':
            query = query.filter(Coach.session_formats.in_(['In-Person', 'Both']))
    
    # Filter by specialty requires joining coach_specialities
    if specialty:
        query = (
            query
            .join(coach_specialities, coach_specialities.c.coach_id == Coach.coach_id)
            .join(GoalType, GoalType.goal_type_id == coach_specialities.c.goal_type_id)
            .filter(GoalType.goal_type_name == specialty)
        )

    coaches = query.distinct().all()
    return [_build_coach_out(coach, db) for coach in coaches]

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
        user_id=query.user_id,
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
    current_user=Depends(require_coach)
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
    client = db.query(Client).filter(Client.client_id == client_id).first()
    notification = Notification(
        user_id=client.user_id,
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
    current_user=Depends(require_coach)
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
    client = db.query(Client).filter(Client.client_id == client_id).first()
    notification = Notification(
        user_id=client.user_id,
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
    current_user=Depends(get_current_user)
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
        coach = db.query(Coach).filter(Coach.coach_id == coach_id).first()
        notification = Notification(
            user_id=coach.user_id,
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
        client = db.query(Client).filter(Client.client_id == client_id).first()
        notification = Notification(
            user_id=client.user_id,
            message=f"{current_user.first_name} {current_user.last_name} terminated coaching contract."
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)
        return {"message": "Contract terminated successfully."}
    
    else:
        raise HTTPException(status_code=403, detail="Invalid user role for Client-Coach relationship termination.")


@router.get("/{coach_id}/clients", response_model=CoachClientsOut)
def get_coach_clients(
    coach_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach),
):
    if current_user.coach.coach_id != coach_id:
        raise HTTPException(status_code=403, detail="You are not authorized to view this coach's clients.")

    rows = (
        db.query(ClientCoach, Client, User)
        .join(Client, Client.client_id == ClientCoach.client_id)
        .join(User, User.user_id == Client.user_id)
        .filter(
            ClientCoach.coach_id == coach_id,
            ClientCoach.status_name.in_(["Active", "Pending"]),
        )
        .all()
    )

    active_clients   = []
    pending_requests = []
    for cc, client, user in rows:
        entry = ClientEntry(
            client_id=client.client_id,
            first_name=user.first_name,
            last_name=user.last_name,
            profile_picture=user.profile_picture,
            status=cc.status_name,
            since=cc.created_at,
        )
        if cc.status_name == "Active":
            active_clients.append(entry)
        else:
            pending_requests.append(entry)

    return CoachClientsOut(active_clients=active_clients, pending_requests=pending_requests)
