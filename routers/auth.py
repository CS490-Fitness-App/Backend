# Handles authentication endpoints (UC 4.1–4.4): syncing an Auth0 user into the database on first login and logging out.

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.auth0 import auth, bearer_scheme
from core.config import settings
from core.database import get_db
from models.user import Admin, Client, Coach, User
from schemas.auth import AuthRequestIn, AuthUserOut, LogoutOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _now():
    return datetime.now(timezone.utc)


def _ensure_role_record(db: Session, user: User) -> None:
    # Keep role tables (Clients/Coaches/Admins) synced with the Users.role field.
    if user.role == "coach":
        existing = db.query(Coach).filter(Coach.user_id == user.user_id).first()
        if not existing:
            db.add(Coach(user_id=user.user_id))
    elif user.role == "admin":
        existing = db.query(Admin).filter(Admin.user_id == user.user_id).first()
        if not existing:
            db.add(Admin(user_id=user.user_id))
    else:
        existing = db.query(Client).filter(Client.user_id == user.user_id).first()
        if not existing:
            db.add(Client(user_id=user.user_id))


@router.post("/signup", response_model=AuthUserOut, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AuthRequestIn,
    claims: dict = Depends(auth),
    db: Session = Depends(get_db),
):
    # Frontend sends Bearer token.
    auth0_sub = claims["sub"]
    existing = db.query(User).filter(User.auth0_sub == auth0_sub).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists. Call /auth/login instead.",
        )

    email = payload.email or claims.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required to create an account.",
        )

    user = User(
        auth0_sub=auth0_sub,
        email=email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        profile_picture=payload.profile_picture,
        role=payload.role,
        created_at=_now(),
        last_updated=_now(),
    )
    db.add(user)
    db.flush()

    _ensure_role_record(db, user)
    db.commit()
    db.refresh(user)

    return AuthUserOut(
        user_id=user.user_id,
        auth0_sub=user.auth0_sub,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_new_user=True,
    )


@router.post("/login", response_model=AuthUserOut)
def login_or_sync_account(
	payload: AuthRequestIn,
	claims: dict = Depends(auth),
	db: Session = Depends(get_db),
):
	# call whenever, will create user or retreive them
	auth0_sub = claims["sub"]
	user = db.query(User).filter(User.auth0_sub == auth0_sub).first()

	if not user:
		email = payload.email or claims.get("email")
		if not email:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Email is required for first login.",
			)

		user = User(
			auth0_sub=auth0_sub,
			email=email,
			first_name=payload.first_name,
			last_name=payload.last_name,
			profile_picture=payload.profile_picture,
			role=payload.role,
			created_at=_now(),
			last_updated=_now(),
		)
		db.add(user)
		db.flush()
		_ensure_role_record(db, user)
		db.commit()
		db.refresh(user)

		return AuthUserOut(
			user_id=user.user_id,
			auth0_sub=user.auth0_sub,
			email=user.email,
			first_name=user.first_name,
			last_name=user.last_name,
			role=user.role,
			is_new_user=True,
		)

	# Optional one-time profile fill
	if payload.first_name and not user.first_name:
		user.first_name = payload.first_name
	if payload.last_name and not user.last_name:
		user.last_name = payload.last_name
	if payload.profile_picture and not user.profile_picture:
		user.profile_picture = payload.profile_picture

	user.last_updated = _now()
	_ensure_role_record(db, user)
	db.commit()
	db.refresh(user)

	return AuthUserOut(
		user_id=user.user_id,
		auth0_sub=user.auth0_sub,
		email=user.email,
		first_name=user.first_name,
		last_name=user.last_name,
		role=user.role,
		is_new_user=False,
	)


@router.get("/me", response_model=AuthUserOut)
def get_current_account(
	claims: dict = Depends(auth),
	db: Session = Depends(get_db),
):
	# Frontend connection check
	# 1) valid token 2) user exists in local DB 3) return user profile for app state.
	auth0_sub = claims["sub"]
	user = db.query(User).filter(User.auth0_sub == auth0_sub).first()
	if not user:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="User not found in local database. Call /auth/signup or /auth/login first.",
		)

	return AuthUserOut(
		user_id=user.user_id,
		auth0_sub=user.auth0_sub,
		email=user.email,
		first_name=user.first_name,
		last_name=user.last_name,
		role=user.role,
		is_new_user=False,
	)


@router.post("/logout", response_model=LogoutOut)
def logout_user():
    return LogoutOut(message="Logged out. Clear client token and call Auth0 logout in frontend.")

@router.get("/debug-token")
def debug_token(credentials=Depends(bearer_scheme)):
    """Debug: decode incoming JWT and compare against backend config. Remove before prod."""
    from core.auth0 import _decode_jwt_payload
    if not credentials:
        return {"error": "No Authorization header"}
    try:
        claims = _decode_jwt_payload(credentials.credentials)
    except Exception as exc:
        return {"error": f"Cannot decode JWT: {exc}", "hint": "Token may be opaque (audience not configured in Auth0)"}

    expected_iss = f"https://{settings.auth0_domain}/"
    aud = claims.get("aud")
    aud_ok = settings.auth0_api_audience in (aud if isinstance(aud, list) else [aud])

    return {
        "token": {"iss": claims.get("iss"), "aud": aud, "sub": claims.get("sub")},
        "backend_expects": {"iss": expected_iss, "aud": settings.auth0_api_audience},
        "checks": {
            "iss_match": claims.get("iss") == expected_iss,
            "aud_match": aud_ok,
            "sub_present": bool(claims.get("sub")),
        },
    }


@router.get("/rbac/client")
def client_access_check(current_user: User = Depends(require_client)):
	# Frontend can call this to verify a client token has client-only access.
	return {
		"ok": True,
		"message": "Client access granted",
		"role": current_user.role,
		"user_id": current_user.user_id,
	}


@router.get("/rbac/coach")
def coach_access_check(current_user: User = Depends(require_coach)):
	# Frontend can call this to verify a coach token has coach-only access.
	return {
		"ok": True,
		"message": "Coach access granted",
		"role": current_user.role,
		"user_id": current_user.user_id,
	}


@router.get("/rbac/admin")
def admin_access_check(current_user: User = Depends(require_admin)):
	# Frontend can call this to verify an admin token has admin-only access.
	return {
		"ok": True,
		"message": "Admin access granted",
		"role": current_user.role,
		"user_id": current_user.user_id,
	}
