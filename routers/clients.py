# Handles client endpoints like initial survey

from datetime import date as _date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import require_client, get_current_user
from models.user import Client, User
from models.log import Goal, GoalType

from schemas.client import ClientRegisterIn, ClientOut
from schemas.log import GoalOut

def _age(dob) -> Optional[int]:
    if dob is None:
        return None
    today = _date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _build_client_out(client: Client, db: Session) -> ClientOut:
    user = db.query(User).filter(User.user_id == client.user_id).first()
    goals = db.query(Goal).filter(Goal.user_id == client.user_id).all()
    goal_type_names = [g.goal_type.goal_type_name for g in goals if g.goal_type]
    return ClientOut(
        client_id=client.client_id,
        first_name=(user.first_name or "") if user else "",
        last_name=(user.last_name or "") if user else "",
        profile_picture=user.profile_picture if user else None,
        age=_age(client.DOB),
        height=client.height,
        weight=client.weight,
        goal_weight=client.goal_weight,
        sex=client.sex,
        weekly_streak=client.weekly_streak,
        goal_types=goal_type_names,
    )

router = APIRouter(prefix="/users", tags=["users"])

# initial survey and registration for Client
@router.post("/register")
def register_client(
    data: ClientRegisterIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # validate every requested goal_type_id exists
    for gid in data.goal_type_ids:
        if not db.query(GoalType).filter(GoalType.goal_type_id == gid).first():
            raise HTTPException(status_code=404, detail=f"Invalid goal_type_id: {gid}")

    # _ensure_role_record() creates an empty Client row on first login, so upsert only for blank records
    client = db.query(Client).filter(Client.user_id == current_user.user_id).first()
    already_registered = False
    if client:
        has_profile_data = any(
            value is not None
            for value in (
                client.DOB,
                client.height,
                client.weight,
                client.goal_weight,
                client.sex,
            )
        )
        has_goals = db.query(Goal).filter(Goal.user_id == current_user.user_id).first() is not None
        already_registered = has_profile_data or has_goals

    if client and already_registered:
        raise HTTPException(status_code=409, detail="Client has already completed registration.")

    if client:
        client.DOB = data.DOB
        client.height = data.height
        client.weight = data.weight
        client.goal_weight = data.goal_weight
        client.sex = data.sex
    else:
        client = Client(
            user_id=current_user.user_id,
            DOB=data.DOB,
            height=data.height,
            weight=data.weight,
            goal_weight=data.goal_weight,
            sex=data.sex,
            weekly_streak=0,
        )
        db.add(client)

    # flush so SQLAlchemy assigns client.client_id before creating related rows
    db.flush()

    # replace goals with the survey selection
    db.query(Goal).filter(Goal.user_id == current_user.user_id).delete()
    for gid in data.goal_type_ids:
        db.add(Goal(user_id=current_user.user_id, goal_type_id=gid))

    db.commit()
    db.refresh(client)
    return _build_client_out(client, db)

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
            raise HTTPException(status_code=404, detail=f"Invalid goal_type_id: {gid}")

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


@router.get("/goal-types")
def get_goal_types(db: Session = Depends(get_db)):
    goal_types = db.query(GoalType).all()
    return [{"goal_type_id": gt.goal_type_id, "goal_type_name": gt.goal_type_name} for gt in goal_types]