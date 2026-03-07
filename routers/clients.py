# Handles client endpoints like initial survey

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from dependencies.rbac import require_client
from models.user import User, Client

from schemas.client import ClientRegisterIn

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