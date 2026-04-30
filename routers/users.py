# Handles user profile endpoints: profile get/update, profile picture upload, and account deletion.

from pathlib import Path
from uuid import uuid4
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import get_current_user
from models.log import Goal
from models.user import Admin, Client, Coach, User
from schemas.user import AdminProfileOut, ClientProfileOut, CoachProfileOut, UserProfileOut, UserProfileUpdateIn

router = APIRouter(prefix="/users", tags=["users"])

UPLOADS_ROOT = Path(__file__).resolve().parents[1] / "uploads" / "profile_pictures"
MAX_PROFILE_PICTURE_SIZE = 5 * 1024 * 1024
ALLOWED_PROFILE_PICTURE_TYPES = {
	"image/jpeg": ".jpg",
	"image/png": ".png",
	"image/webp": ".webp",
	"image/gif": ".gif",
}


def _build_profile_response(db: Session, current_user: User) -> UserProfileOut:
	client_profile = None
	coach_profile = None
	admin_profile = None

	def _calculate_age(dob: date | None) -> int | None:
		if not dob:
			return None
		today = date.today()
		return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

	client = db.query(Client).filter(Client.user_id == current_user.user_id).first()
	if client:
		goals = db.query(Goal).filter(Goal.user_id == current_user.user_id).all()
		client_profile = ClientProfileOut(
			client_id=client.client_id,
			age=_calculate_age(client.DOB),
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
		is_active=current_user.is_active,
		created_at=current_user.created_at,
		last_updated=current_user.last_updated,
		client_profile=client_profile,
		coach_profile=coach_profile,
		admin_profile=admin_profile,
	)


@router.get("/me", response_model=UserProfileOut)
def get_my_profile(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
):
	return _build_profile_response(db, current_user)


@router.patch("/me", response_model=UserProfileOut)
def update_my_profile(
	payload: UserProfileUpdateIn,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
):
	now = datetime.now(timezone.utc)
	has_changes = False

	if payload.first_name is not None:
		current_user.first_name = (payload.first_name or "").strip() or None
		has_changes = True

	if payload.last_name is not None:
		current_user.last_name = (payload.last_name or "").strip() or None
		has_changes = True

	if payload.goal_weight_lb is not None:
		if payload.goal_weight_lb <= 0:
			raise HTTPException(status_code=400, detail="Goal weight must be greater than 0.")

		client = db.query(Client).filter(Client.user_id == current_user.user_id).first()
		if not client:
			raise HTTPException(status_code=400, detail="Goal weight can only be set for client profiles.")

		client.goal_weight = int(round(payload.goal_weight_lb * 453.592))
		client.last_updated = now
		has_changes = True

	if payload.bio is not None:
		coach = db.query(Coach).filter(Coach.user_id == current_user.user_id).first()
		if not coach:
			raise HTTPException(status_code=400, detail="Bio can only be set for coach profiles.")

		coach.bio = (payload.bio or "").strip() or None
		coach.last_updated = now
		has_changes = True

	if has_changes:
		current_user.last_updated = now
		db.commit()
		db.refresh(current_user)

	return _build_profile_response(db, current_user)


@router.post("/me/profile-picture", response_model=UserProfileOut, status_code=status.HTTP_200_OK)
async def upload_my_profile_picture(
	profile_picture: UploadFile = File(...),
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
):
	if profile_picture.content_type not in ALLOWED_PROFILE_PICTURE_TYPES:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Profile picture must be a JPG, PNG, WEBP, or GIF image.",
		)

	file_bytes = await profile_picture.read()
	if not file_bytes:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Profile picture file is empty.",
		)

	if len(file_bytes) > MAX_PROFILE_PICTURE_SIZE:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Profile picture must be 5 MB or smaller.",
		)

	UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)
	file_extension = ALLOWED_PROFILE_PICTURE_TYPES[profile_picture.content_type]
	file_name = f"user_{current_user.user_id}_{uuid4().hex}{file_extension}"
	file_path = UPLOADS_ROOT / file_name
	file_path.write_bytes(file_bytes)

	previous_picture = current_user.profile_picture
	current_user.profile_picture = f"/uploads/profile_pictures/{file_name}"
	db.commit()
	db.refresh(current_user)

	if previous_picture and previous_picture.startswith("/uploads/profile_pictures/"):
		previous_file_path = Path(__file__).resolve().parents[1] / previous_picture.lstrip("/")
		if previous_file_path.exists() and previous_file_path != file_path:
			previous_file_path.unlink()

	return _build_profile_response(db, current_user)


@router.post("/me/deactivate", response_model=UserProfileOut)
def deactivate_my_account(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
):
	current_user.is_active = False
	current_user.last_updated = datetime.now(timezone.utc)
	db.commit()
	db.refresh(current_user)
	return _build_profile_response(db, current_user)


@router.post("/me/reactivate", response_model=UserProfileOut)
def reactivate_my_account(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
):
	current_user.is_active = True
	current_user.last_updated = datetime.now(timezone.utc)
	db.commit()
	db.refresh(current_user)
	return _build_profile_response(db, current_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
):
	if current_user.profile_picture and current_user.profile_picture.startswith("/uploads/profile_pictures/"):
		previous_file_path = Path(__file__).resolve().parents[1] / current_user.profile_picture.lstrip("/")
		if previous_file_path.exists():
			previous_file_path.unlink()

	db.delete(current_user)
	db.commit()
