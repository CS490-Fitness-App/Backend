# Handles client endpoints like initial survey

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from dependencies.rbac import require_client
from models.user import User, Client
from models.log import Goal, GoalType

from schemas.client import ClientRegisterIn
from schemas.log import GoalOut

router = APIRouter(prefix="/users", tags=["users"])

# initial survey and registration for Client
@router.post("/register")
def register_client(
    data: ClientRegisterIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_client)
):
    # check if Client already has a profile
    existing_client = db.query(User).filter(User.user_id == current_user.user_id).first()
    if existing_client and existing_client.client_profile:
        raise HTTPException(status_code=400, detail="Client profile already exists for this user.")
    
    # get info for Client table
    client = Client(
        user_id=current_user.user_id,
        DOB=data.DOB,
        height=data.height,
        weight=data.weight,
        goal_weight=data.goal_weight,
        sex=data.sex,
        weekly_streak=0    # default to 0 for new customers
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


# Set goals for the current client (initial or additional)
@router.post("/goals", response_model=list[GoalOut])
def set_goals(
    goal_type_ids: list[int],
    db: Session = Depends(get_db),
    current_user=Depends(require_client)
):
    # validate every requested goal_type_id exists
    for gid in goal_type_ids:
        if not db.query(GoalType).filter(GoalType.goal_type_id == gid).first():
            raise HTTPException(status_code=400, detail=f"Invalid goal_type_id: {gid}")

    # add new goals for this user
    goals = []
    for gid in goal_type_ids:
        goal = Goal(user_id=current_user.user_id, goal_type_id=gid)
        db.add(goal)
        goals.append(goal)

    # commit all changes to the database at once
    db.commit()
    for g in goals:
        db.refresh(g)
    return goals


# Retrieve current client's goals
@router.get("/goals", response_model=list[GoalOut])
def get_goals(
    db: Session = Depends(get_db),
    current_user=Depends(require_client)
):
    return db.query(Goal).filter(Goal.user_id == current_user.user_id).all()


# Replace current client's goals
@router.put("/goals", response_model=list[GoalOut])
def update_goals(
    goal_type_ids: list[int],
    db: Session = Depends(get_db),
    current_user=Depends(require_client)
):
    # validate every requested goal_type_id exists
    for gid in goal_type_ids:
        if not db.query(GoalType).filter(GoalType.goal_type_id == gid).first():
            raise HTTPException(status_code=400, detail=f"Invalid goal_type_id: {gid}")

    # delete existing goals for this user
    db.query(Goal).filter(Goal.user_id == current_user.user_id).delete()

    # add new goals for this user
    goals = []
    for gid in goal_type_ids:
        goal = Goal(user_id=current_user.user_id, goal_type_id=gid)
        db.add(goal)
        goals.append(goal)

    # commit all changes to the database at once
    db.commit()
    for g in goals:
        db.refresh(g)
    return goals