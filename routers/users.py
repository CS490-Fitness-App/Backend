# Handles user profile endpoints: profile get/update, profile picture upload, and account deletion.

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import get_current_user
from models.log import Goal
from models.user import Admin, Client, Coach, User
from schemas.user import AdminProfileOut, ClientProfileOut, CoachProfileOut, UserProfileOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfileOut)
def get_my_profile(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
):
	client_profile = None
	coach_profile = None
	admin_profile = None

	client = db.query(Client).filter(Client.user_id == current_user.user_id).first()
	if client:
		goals = db.query(Goal).filter(Goal.user_id == current_user.user_id).all()
		client_profile = ClientProfileOut(
			client_id=client.client_id,
			DOB=client.DOB,
			height=client.height,
			weight=client.weight,
			goal_weight=client.goal_weight,
			sex=client.sex,
			weekly_streak=client.weekly_streak,
			goals=[goal.goal_type.goal_type_name for goal in goals if goal.goal_type],
		)

	coach = db.query(Coach).filter(Coach.user_id == current_user.user_id).first()
	if coach:
		coach_profile = CoachProfileOut(
			coach_id=coach.coach_id,
			gender=coach.gender,
			hourly_rate=float(coach.hourly_rate) if coach.hourly_rate else 0.0,
			bio=coach.bio,
			is_trainer=coach.is_trainer,
			is_nutritionist=coach.is_nutritionist,
			years_of_experience=coach.years_of_experience,
			max_clients=coach.max_clients,
			accepting_clients=coach.accepting_clients,
			status=coach.status.status_name if coach.status else None,
		)

	admin = db.query(Admin).filter(Admin.user_id == current_user.user_id).first()
	if admin:
		admin_profile = AdminProfileOut(admin_id=admin.admin_id)

	return UserProfileOut(
		user_id=current_user.user_id,
		email=current_user.email,
		first_name=current_user.first_name,
		last_name=current_user.last_name,
		profile_picture=current_user.profile_picture,
		role=current_user.role,
		created_at=current_user.created_at,
		last_updated=current_user.last_updated,
		client_profile=client_profile,
		coach_profile=coach_profile,
		admin_profile=admin_profile,
	)
