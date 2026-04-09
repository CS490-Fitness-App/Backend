# Handles admin-only endpoints (UC 6.2–6.7): approving/rejecting/suspending coaches, managing reports, and viewing financial and engagement analytics.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from dependencies.rbac import require_admin
from models.user import Coach, CoachStatus, User
from schemas.admin import AdminCoachApplicationOut, AdminCoachDecisionOut

router = APIRouter(prefix="/admin", tags=["admin"])


def _specialization_label(coach: Coach) -> str:
    if coach.is_trainer and coach.is_nutritionist:
        return "Both"
    if coach.is_nutritionist:
        return "Nutritionist"
    return "Workout Coach"


def _to_admin_coach_out(coach: Coach) -> AdminCoachApplicationOut:
    return AdminCoachApplicationOut(
        coach_id=coach.coach_id,
        user_id=coach.user_id,
        first_name=coach.user.first_name,
        last_name=coach.user.last_name,
        email=coach.user.email,
        specialization=_specialization_label(coach),
        status=coach.status.status_name,
        active=coach.status.status_name == "Active",
        accepting_clients=coach.accepting_clients,
        submitted_at=coach.created_at,
    )


def _get_status_or_404(db: Session, status_name: str) -> CoachStatus:
    status = db.query(CoachStatus).filter(CoachStatus.status_name == status_name).first()
    if not status:
        raise HTTPException(status_code=404, detail=f'Coach status "{status_name}" not found')
    return status


def _get_coach_or_404(coach_id: int, db: Session) -> Coach:
    coach = (
        db.query(Coach)
        .options(
            joinedload(Coach.user),
            joinedload(Coach.status),
        )
        .filter(Coach.coach_id == coach_id)
        .first()
    )
    if not coach:
        raise HTTPException(status_code=404, detail="Coach application not found")
    return coach


@router.get("/coaches", response_model=list[AdminCoachApplicationOut])
def list_coach_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    coaches = (
        db.query(Coach)
        .options(
            joinedload(Coach.user),
            joinedload(Coach.status),
        )
        .order_by(Coach.created_at.desc())
        .all()
    )
    return [_to_admin_coach_out(coach) for coach in coaches]


@router.post("/coaches/{coach_id}/approve", response_model=AdminCoachDecisionOut)
def approve_coach_application(
    coach_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    coach = _get_coach_or_404(coach_id, db)
    active_status = _get_status_or_404(db, "Active")

    if coach.status.status_name == "Active":
        raise HTTPException(status_code=409, detail="Coach is already approved")

    coach.status_id = active_status.status_id
    coach.accepting_clients = True
    db.commit()

    return AdminCoachDecisionOut(
        message="Coach application approved",
        coach_id=coach.coach_id,
        status="Active",
    )


@router.post("/coaches/{coach_id}/reject", response_model=AdminCoachDecisionOut)
def reject_coach_application(
    coach_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    coach = _get_coach_or_404(coach_id, db)
    rejected_status = _get_status_or_404(db, "Rejected")

    if coach.status.status_name == "Rejected":
        raise HTTPException(status_code=409, detail="Coach is already rejected")

    coach.status_id = rejected_status.status_id
    coach.accepting_clients = False
    db.commit()

    return AdminCoachDecisionOut(
        message="Coach application rejected",
        coach_id=coach.coach_id,
        status="Rejected",
    )


@router.post("/coaches/{coach_id}/suspend", response_model=AdminCoachDecisionOut)
def suspend_coach_account(
    coach_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    coach = _get_coach_or_404(coach_id, db)
    suspended_status = _get_status_or_404(db, "Suspended")

    if coach.status.status_name == "Suspended":
        raise HTTPException(status_code=409, detail="Coach account is already suspended")

    coach.status_id = suspended_status.status_id
    coach.accepting_clients = False
    db.commit()

    return AdminCoachDecisionOut(
        message="Coach account suspended",
        coach_id=coach.coach_id,
        status="Suspended",
    )


@router.post("/coaches/{coach_id}/reactivate", response_model=AdminCoachDecisionOut)
def reactivate_coach_account(
    coach_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    coach = _get_coach_or_404(coach_id, db)
    active_status = _get_status_or_404(db, "Active")

    if coach.status.status_name == "Active":
        raise HTTPException(status_code=409, detail="Coach account is already active")

    coach.status_id = active_status.status_id
    coach.accepting_clients = True
    db.commit()

    return AdminCoachDecisionOut(
        message="Coach account reactivated",
        coach_id=coach.coach_id,
        status="Active",
    )
