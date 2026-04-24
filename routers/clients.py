# Handles client endpoints like initial survey

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import require_client, get_current_user
from models.user import Client
from models.log import Goal, GoalType

from schemas.client import ClientRegisterIn, ClientOut
from schemas.log import GoalOut

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

    # _ensure_role_record() creates an empty Client row on first login, so upsert
    client = db.query(Client).filter(Client.user_id == current_user.user_id).first()
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

    db.flush()

    # replace goals from the survey
    db.query(Goal).filter(Goal.user_id == current_user.user_id).delete()
    for gid in data.goal_type_ids:
        db.add(Goal(user_id=current_user.user_id, goal_type_id=gid))

    db.commit()
    return {"message": "Profile saved."}

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