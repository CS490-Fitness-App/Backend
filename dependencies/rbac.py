# Provides role-based access control dependencies: get_current_user, require_client, require_coach, require_admin.
# Each dependency resolves the authenticated user from the database and enforces their role

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.auth0 import auth
from core.database import get_db
from models.user import User


def get_current_user(
	claims: dict = Depends(auth),
	db: Session = Depends(get_db),
) -> User:
	
	"Raises 401 if the token is valid but no local DB user exists yet"

	auth0_sub = claims.get("sub")
	user = db.query(User).filter(User.auth0_sub == auth0_sub).first()

	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Authenticated token found, but no local user exists. call /auth/login.",
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

require_coach = _require_role("coach")
require_admin = _require_role("admin")
