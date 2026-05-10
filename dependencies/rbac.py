# Provides role-based access control dependencies: get_current_user, require_client, require_coach, require_admin.
# Each dependency resolves the authenticated user from the database and enforces their role

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.account_lifecycle import purge_if_self_deactivation_expired
from core.auth0 import auth
from core.database import get_db
from models.user import User

SELF_DEACTIVATION_RETENTION_DAYS = 30
_INACTIVE_ACCOUNT_MESSAGE = "Your account is currently deactivated."


def build_inactive_account_detail(user: User) -> dict:
    is_admin_hold = bool(user.deactivated_by_admin) or not user.scheduled_deletion_at

    if is_admin_hold:
        return {
            "code": "admin_deactivated",
            "message": "Your account has been deactivated by an administrator. Contact support if you believe this is a mistake.",
            "can_self_reactivate": False,
            "deactivated_by_admin": True,
            "scheduled_deletion_at": None,
            "role": user.role,
        }

    remaining_days = None
    if user.scheduled_deletion_at:
        delta = user.scheduled_deletion_at - datetime.now(timezone.utc)
        remaining_days = max(0, delta.days)

    deletion_date = user.scheduled_deletion_at.isoformat() if user.scheduled_deletion_at else None
    message = (
        f"Your account is deactivated. Reactivate within {remaining_days} day(s) or it will be permanently deleted on "
        f"{user.scheduled_deletion_at.date().isoformat()}."
        if user.scheduled_deletion_at and remaining_days is not None
        else f"Your account is deactivated. Reactivate within {SELF_DEACTIVATION_RETENTION_DAYS} days to keep it."
    )
    return {
        "code": "self_deactivated",
        "message": message,
        "can_self_reactivate": True,
        "deactivated_by_admin": False,
        "scheduled_deletion_at": deletion_date,
        "remaining_days": remaining_days,
        "role": user.role,
    }


def _resolve_authenticated_user(
    claims: dict,
    db: Session,
) -> User:
    auth0_sub = claims.get("sub")
    user = db.query(User).filter(User.auth0_sub == auth0_sub).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated token found, but no local user exists. call /auth/login.",
        )

    if purge_if_self_deactivation_expired(db, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "account_deleted",
                "message": "Your deactivated account passed its retention window and has been permanently deleted.",
                "can_self_reactivate": False,
            },
        )

    return user


def get_current_user_allow_inactive(
    claims: dict = Depends(auth),
    db: Session = Depends(get_db),
) -> User:
    return _resolve_authenticated_user(claims, db)


def get_current_user(
	claims: dict = Depends(auth),
	db: Session = Depends(get_db),
) -> User:
	
	"Raises 401 if the token is valid but no local DB user exists yet"

	user = _resolve_authenticated_user(claims, db)
	if user.is_active is False:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail=build_inactive_account_detail(user),
		)

	return user


def _require_role(expected_role: str):
	"role check"

	def _role_checker(current_user: User = Depends(get_current_user)) -> User:
		if current_user.role != expected_role:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail=f"Access denied. This endpoint requires role: {expected_role}.",
			)
		return current_user

	return _role_checker


# Use in routes: current_user=Depends(require_client)
def require_client(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("client", "coach"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint requires role: client.",
        )
    return current_user

def require_active_coach(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "coach":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint requires role: coach.",
        )
    coach = current_user.coach
    if coach and coach.status and coach.status.status_name == "Suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended.",
        )
    return current_user


require_coach = _require_role("coach")
require_admin = _require_role("admin")
