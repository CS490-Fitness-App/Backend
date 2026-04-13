# Handles client endpoints like initial survey

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import require_client
from models.user import Client
from models.log import Goal, GoalType

from schemas.client import ClientRegisterIn, ClientOut
from schemas.log import GoalOut

router = APIRouter(prefix="/users", tags=["users"])

# initial survey and registration for Client
@router.post("/register", response_model=ClientOut)
def register_client(
    data: ClientRegisterIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_client)
):
    # check if Client already has a profile
    existing = db.query(Client).filter(Client.user_id == current_user.user_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Client profile already exists for this user.")

    # validate every requested goal_type_id exists
    for gid in data.goal_type_ids:
        if not db.query(GoalType).filter(GoalType.goal_type_id == gid).first():
            raise HTTPException(status_code=404, detail=f"Invalid goal_type_id: {gid}")

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

    # flush so SQLAlchemy assigns client.client_id before creating related rows
    db.flush()

    # create initial goals from the survey
    for gid in data.goal_type_ids:
        db.add(Goal(user_id=current_user.user_id, goal_type_id=gid))

    db.commit()
    db.refresh(client)
    return client

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