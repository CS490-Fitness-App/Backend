# Handles user profile endpoints: profile get/update, profile picture upload, and account deletion.

import cloudinary
import cloudinary.uploader
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.config import settings
from dependencies.rbac import (
	get_current_user,
	get_current_user_allow_inactive,
	SELF_DEACTIVATION_RETENTION_DAYS,
)
from models.coach import ClientCoach
from models.log import Goal
from models.user import Admin, Client, Coach, User
from routers.notifications import notify
from schemas.user import AdminProfileOut, ClientProfileOut, CoachProfileOut, UserProfileOut, UserProfileUpdateIn

router = APIRouter(prefix="/users", tags=["users"])

cloudinary.config(cloudinary_url=settings.cloudinary_url)

MAX_PROFILE_PICTURE_SIZE = 5 * 1024 * 1024
ALLOWED_PROFILE_PICTURE_TYPES = {
	"image/jpeg": ".jpg",
	"image/png": ".png",
	"image/webp": ".webp",
	"image/gif": ".gif",
}
_CLOUDINARY_FOLDER = "primalfitness/profile_pictures"


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

	normalized_profile_picture = _normalize_profile_picture_reference(current_user.profile_picture)
	if normalized_profile_picture != current_user.profile_picture:
		current_user.profile_picture = normalized_profile_picture
		current_user.last_updated = datetime.now(timezone.utc)
		db.commit()
		db.refresh(current_user)

	return UserProfileOut(
		user_id=current_user.user_id,
		email=current_user.email,
		first_name=current_user.first_name,
		last_name=current_user.last_name,
		profile_picture=normalized_profile_picture,
		role=current_user.role,
		is_active=current_user.is_active,
		deactivated_at=current_user.deactivated_at,
		scheduled_deletion_at=current_user.scheduled_deletion_at,
		deactivated_by_admin=current_user.deactivated_by_admin,
		created_at=current_user.created_at,
		last_updated=current_user.last_updated,
		client_profile=client_profile,
		coach_profile=coach_profile,
		admin_profile=admin_profile,
	)


def _normalize_profile_picture_reference(value: str | None) -> str | None:
	if not value:
		return None

	normalized = value.strip()
	if not normalized:
		return None

	lower = normalized.lower()

	# Accept any absolute URL (Cloudinary, Auth0, etc.)
	if lower.startswith("http://") or lower.startswith("https://"):
		return normalized

	# Keep legacy local paths from before Cloudinary migration
	if normalized.startswith("uploads/profile_pictures/"):
		return f"/{normalized}"
	if normalized.startswith("/uploads/profile_pictures/"):
		return normalized

	return None


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

	if payload.hourly_rate is not None:
		if payload.hourly_rate < 0:
			raise HTTPException(status_code=400, detail="Hourly rate cannot be negative.")

		coach = db.query(Coach).filter(Coach.user_id == current_user.user_id).first()
		if not coach:
			raise HTTPException(status_code=400, detail="Hourly rate can only be set for coach profiles.")

		old_rate = float(coach.hourly_rate) if coach.hourly_rate else 0.0
		new_rate = round(payload.hourly_rate, 2)
		coach.hourly_rate = new_rate
		coach.last_updated = now
		has_changes = True

		active_contracts = (
			db.query(ClientCoach)
			.filter(ClientCoach.coach_id == coach.coach_id, ClientCoach.status_name == "Active")
			.all()
		)
		coach_name = f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or "Your coach"
		for contract in active_contracts:
			client_row = db.query(Client).filter(Client.client_id == contract.client_id).first()
			if client_row:
				notify(
					db,
					user_id=client_row.user_id,
					message=f"{coach_name} has updated their hourly rate from ${old_rate:.2f} to ${new_rate:.2f}.",
				)

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

	public_id = f"{_CLOUDINARY_FOLDER}/user_{current_user.user_id}"
	try:
		result = cloudinary.uploader.upload(
			file_bytes,
			public_id=public_id,
			overwrite=True,
			resource_type="image",
		)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_502_BAD_GATEWAY,
			detail=f"Cloudinary upload failed: {exc}",
		) from exc

	current_user.profile_picture = result["secure_url"]
	db.commit()
	db.refresh(current_user)

	return _build_profile_response(db, current_user)


@router.post("/me/deactivate", response_model=UserProfileOut)
def deactivate_my_account(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
):
	now = datetime.now(timezone.utc)
	current_user.is_active = False
	current_user.deactivated_at = now
	current_user.scheduled_deletion_at = now + timedelta(days=SELF_DEACTIVATION_RETENTION_DAYS)
	current_user.deactivated_by_admin = False
	current_user.last_updated = now

	if current_user.client:
		client_id = current_user.client.client_id
		active_contracts = (
			db.query(ClientCoach)
			.filter(
				ClientCoach.client_id == client_id,
				ClientCoach.status_name.in_(["Active", "Pending"]),
			)
			.all()
		)
		for contract in active_contracts:
			contract.status_name = "Terminated"
			coach = db.query(Coach).filter(Coach.coach_id == contract.coach_id).first()
			if coach:
				notify(
					db,
					user_id=coach.user_id,
					message=f"Your client {current_user.first_name or ''} {current_user.last_name or ''} has deactivated their account. The coaching contract has been terminated.".strip(),
				)

	db.commit()
	db.refresh(current_user)
	return _build_profile_response(db, current_user)


@router.post("/me/reactivate", response_model=UserProfileOut)
def reactivate_my_account(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user_allow_inactive),
):
	if current_user.deactivated_by_admin or not current_user.scheduled_deletion_at:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="This account was deactivated by an administrator and can only be reactivated by an administrator.",
		)
	current_user.is_active = True
	current_user.deactivated_at = None
	current_user.scheduled_deletion_at = None
	current_user.deactivated_by_admin = False
	current_user.last_updated = datetime.now(timezone.utc)
	db.commit()
	db.refresh(current_user)
	return _build_profile_response(db, current_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
):
	try:
		cloudinary.uploader.destroy(f"{_CLOUDINARY_FOLDER}/user_{current_user.user_id}")
	except Exception:
		pass

	db.delete(current_user)
	db.commit()
