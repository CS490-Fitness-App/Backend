# Handles admin-only endpoints (UC 6.2–6.7): approving/rejecting/suspending coaches, managing reports, and viewing financial and engagement analytics.

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from dependencies.rbac import require_admin
from models.user import User, Coach, CoachStatus
from schemas.user import UserAdminOut, UsersListOut

router = APIRouter(prefix="/admin", tags=["admin"], redirect_slashes=False)


# UC 6.2 — Admin views all registered users
# Supports optional filtering by role (client/coach/admin) and by coach account status.
# Coach status filter implicitly restricts results to coach-role users only.
@router.get("/users", response_model=UsersListOut)
def list_users(
    role:   Optional[str] = Query(None, description="Filter by role: client, coach, admin"),
    status: Optional[str] = Query(None, description="Filter coaches by status: Pending, Active, Suspended, Rejected"),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    # eager-load coach + coach.status in the same query to avoid N+1 queries
    query = db.query(User).options(
        joinedload(User.coach).joinedload(Coach.status)
    )

    # narrow by role — normalize to lowercase so "Client" and "client" both work
    if role:
        query = query.filter(User.role == role.lower())

    # status only applies to coaches — join through Coach → CoachStatus
    if status:
        query = (
            query
            .join(Coach, Coach.user_id == User.user_id)
            .join(CoachStatus, CoachStatus.status_id == Coach.status_id)
            .filter(CoachStatus.status_name == status)
        )

    users = query.all()

    # build response manually to resolve the coach_status relationship
    result = []
    for user in users:
        # resolve coach status — None for non-coach users
        coach_status = None
        if user.coach:
            coach_status = user.coach.status.status_name if user.coach.status else None

        result.append(UserAdminOut(
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            coach_status=coach_status,
            created_at=user.created_at,
        ))

    return UsersListOut(total=len(result), users=result)
