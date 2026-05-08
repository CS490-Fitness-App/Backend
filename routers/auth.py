# Handles authentication endpoints (UC 4.1–4.4): syncing an Auth0 user into the database on first login and logging out.

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.auth0 import auth, bearer_scheme
from core.account_lifecycle import purge_if_self_deactivation_expired
from core.config import settings
from core.database import get_db
from dependencies.rbac import (
    build_inactive_account_detail,
    get_current_user,
    require_client,
    require_coach,
    require_admin,
)
from models.log import UserDailyEngagement
from models.user import Admin, Client, Coach, User
from schemas.auth import AuthRequestIn, AuthUserOut, LogoutOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _now():
    return datetime.now(timezone.utc)


def _normalize_email(email: str | None) -> str | None:
    if not email:
        return None
    normalized = email.strip().lower()
    return normalized or None


def _find_user_by_email(db: Session, email: str | None) -> User | None:
    normalized_email = _normalize_email(email)
    if not normalized_email:
        return None
    return db.query(User).filter(func.lower(User.email) == normalized_email).first()


def _normalize_profile_picture_reference(value: str | None) -> str | None:
    if not value:
        return None

    normalized = value.strip()
    if not normalized:
        return None

    if normalized.startswith("uploads/profile_pictures/"):
        return f"/{normalized}"

    if normalized.startswith("/uploads/profile_pictures/"):
        return normalized

    lower = normalized.lower()
    if lower.startswith("http://") or lower.startswith("https://"):
        return normalized

    # Reject non-reference payloads like base64/blob/bytes literals.
    if lower.startswith("data:") or lower.startswith("blob:") or normalized.startswith("b'") or normalized.startswith('b"'):
        return None

    return None


def _auth_user_out(user: User, is_new_user: bool) -> AuthUserOut:
    return AuthUserOut(
        user_id=user.user_id,
        auth0_sub=user.auth0_sub,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_new_user=is_new_user,
    )


def _raise_if_inactive(user: User) -> None:
    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=build_inactive_account_detail(user),
        )


def _commit_or_resolve_user(
	db: Session,
	*,
	auth0_sub: str,
	email: str | None,
	is_new_user: bool,
) -> AuthUserOut:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        resolved_user = db.query(User).filter(User.auth0_sub == auth0_sub).first()
        if not resolved_user:
            resolved_user = _find_user_by_email(db, email)
        if resolved_user:
            db.refresh(resolved_user)
            return _auth_user_out(resolved_user, False)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account sync conflict. Please try logging in again.",
        )

    user = db.query(User).filter(User.auth0_sub == auth0_sub).first()
    if not user:
        user = _find_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account sync completed but user could not be reloaded.",
        )
    db.refresh(user)
    return _auth_user_out(user, is_new_user)


def _ensure_role_record(db: Session, user: User) -> None:
    # Keep role tables (Clients/Coaches/Admins) synced with the Users.role field.
    # Coaches also get a Client row so they can use client-facing features.
    if user.role == "coach":
        # Coach row is created by POST /coaches/register during the survey — don't pre-create it.
        if not db.query(Client).filter(Client.user_id == user.user_id).first():
            db.add(Client(user_id=user.user_id))
    elif user.role == "admin":
        if not db.query(Admin).filter(Admin.user_id == user.user_id).first():
            db.add(Admin(user_id=user.user_id))
    else:
        if not db.query(Client).filter(Client.user_id == user.user_id).first():
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

    email = _normalize_email(payload.email or claims.get("email"))
    profile_picture = _normalize_profile_picture_reference(payload.profile_picture)
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
        profile_picture=profile_picture,
        role=payload.role,
        created_at=_now(),
        last_active_at=_now(),
        last_updated=_now(),
    )
    db.add(user)
    db.flush()
    _ensure_role_record(db, user)
    _track_daily_login(db, user.user_id, user.last_active_at)
    return _commit_or_resolve_user(
        db,
        auth0_sub=auth0_sub,
        email=email,
        is_new_user=True,
    )


def _track_daily_login(db: Session, user_id: int, timestamp: datetime) -> None:
    today = timestamp.date()
    engagement = db.query(UserDailyEngagement).filter(
        UserDailyEngagement.user_id == user_id,
        UserDailyEngagement.activity_date == today,
    ).first()
    if engagement:
        engagement.last_login_at = timestamp
        engagement.last_updated = timestamp
        return

    db.add(UserDailyEngagement(
        user_id=user_id,
        activity_date=today,
        first_login_at=timestamp,
        last_login_at=timestamp,
        survey_completed=0,
        created_at=timestamp,
        last_updated=timestamp,
    ))


@router.post("/login", response_model=AuthUserOut)
def login_or_sync_account(
    payload: AuthRequestIn,
    claims: dict = Depends(auth),
    db: Session = Depends(get_db),
):
    # call whenever, will create user or retreive them
    auth0_sub = claims["sub"]
    profile_picture = _normalize_profile_picture_reference(payload.profile_picture)
    user = db.query(User).filter(User.auth0_sub == auth0_sub).first()

    if not user:
        email = _normalize_email(payload.email or claims.get("email"))
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required for first login.",
            )

        existing_email_user = _find_user_by_email(db, email)
        if existing_email_user:
            if purge_if_self_deactivation_expired(db, existing_email_user):
                existing_email_user = None
        if existing_email_user:
            _raise_if_inactive(existing_email_user)
            existing_email_user.auth0_sub = auth0_sub
            existing_email_user.email = email
            if payload.first_name and not existing_email_user.first_name:
                existing_email_user.first_name = payload.first_name
            if payload.last_name and not existing_email_user.last_name:
                existing_email_user.last_name = payload.last_name
            if profile_picture and not existing_email_user.profile_picture:
                existing_email_user.profile_picture = profile_picture
            now = _now()
            existing_email_user.last_active_at = now
            existing_email_user.last_updated = now
            _ensure_role_record(db, existing_email_user)
            _track_daily_login(db, existing_email_user.user_id, now)
            return _commit_or_resolve_user(
                db,
                auth0_sub=auth0_sub,
                email=email,
                is_new_user=False,
            )

        user = User(
            auth0_sub=auth0_sub,
            email=email,
            first_name=payload.first_name,
            last_name=payload.last_name,
            profile_picture=profile_picture,
            role=payload.role,
            created_at=_now(),
            last_active_at=_now(),
            last_updated=_now(),
        )
        db.add(user)
        db.flush()
        _ensure_role_record(db, user)
        _track_daily_login(db, user.user_id, user.last_active_at)
        return _commit_or_resolve_user(
            db,
            auth0_sub=auth0_sub,
            email=email,
            is_new_user=True,
        )

    # Optional one-time profile fill
    purge_if_self_deactivation_expired(db, user)
    _raise_if_inactive(user)
    normalized_email = _normalize_email(payload.email or claims.get("email"))
    if normalized_email and user.email != normalized_email:
        user.email = normalized_email
    if payload.first_name and not user.first_name:
        user.first_name = payload.first_name
    if payload.last_name and not user.last_name:
        user.last_name = payload.last_name
    if profile_picture and not user.profile_picture:
        user.profile_picture = profile_picture

    now = _now()
    user.last_active_at = now
    user.last_updated = now
    _ensure_role_record(db, user)
    _track_daily_login(db, user.user_id, now)
    return _commit_or_resolve_user(
        db,
        auth0_sub=auth0_sub,
        email=user.email,
        is_new_user=False,
    )


@router.get("/me", response_model=AuthUserOut)
def get_current_account(current_user: User = Depends(get_current_user)):
	# Frontend connection check
	# 1) valid token 2) active user exists in local DB 3) return user profile for app state.
	return AuthUserOut(
		user_id=current_user.user_id,
		auth0_sub=current_user.auth0_sub,
		email=current_user.email,
		first_name=current_user.first_name,
		last_name=current_user.last_name,
		role=current_user.role,
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
