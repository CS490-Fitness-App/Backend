# Handles admin-only endpoints (UC 6.2–6.7): approving/rejecting/suspending coaches, managing reports, and viewing financial and engagement analytics.

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from dependencies.rbac import require_admin
from models.payment import CoachPaymentHistory
from models.user import Client, Coach, CoachStatus, User
from schemas.admin import AdminCoachApplicationOut, AdminCoachDecisionOut, AdminFinancialSummaryOut

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


def _period_start(period: str) -> datetime | None:
    now = datetime.now(timezone.utc)
    if period == "this_month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period == "this_year":
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    if period == "last_90_days":
        return now - timedelta(days=90)
    return None


def _month_label(value: datetime) -> str:
    return value.strftime("%b %Y")


def _full_name(user: User | None) -> str:
    if not user:
        return "Unknown"
    return f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email


def _payment_status(payment: CoachPaymentHistory) -> str:
    return payment.status or "Completed"


def _payment_platform_fee(payment: CoachPaymentHistory) -> float:
    if payment.platform_fee is not None and float(payment.platform_fee) > 0:
        return float(payment.platform_fee)
    return round(float(payment.amount) * 0.10, 2)


def _payment_coach_payout(payment: CoachPaymentHistory) -> float:
    if payment.coach_payout_amount is not None and float(payment.coach_payout_amount) > 0:
        return float(payment.coach_payout_amount)
    return round(float(payment.amount) - _payment_platform_fee(payment), 2)


def _payment_people(payment: CoachPaymentHistory, db: Session) -> tuple[str, str]:
    client = db.query(Client).filter(Client.client_id == payment.client_id).first()
    coach = db.query(Coach).filter(Coach.coach_id == payment.coach_id).first()
    client_name = _full_name(client.user if client else None)
    coach_name = _full_name(coach.user if coach else None)
    return client_name, coach_name


def _matches_financial_query(payment: CoachPaymentHistory, query: str | None, db: Session) -> bool:
    if not query:
        return True
    client_name, coach_name = _payment_people(payment, db)
    haystack = f"{client_name} {coach_name} {payment.payment_id}".lower()
    return query.lower() in haystack


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


@router.get("/financial-summary", response_model=AdminFinancialSummaryOut)
def get_financial_summary(
    period: str = "all",
    year: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    allowed_periods = {"all", "this_month", "this_year", "last_90_days"}
    if period not in allowed_periods:
        raise HTTPException(status_code=400, detail="Invalid period filter.")

    query = db.query(CoachPaymentHistory).order_by(CoachPaymentHistory.payment_date.asc())
    start = _period_start(period)
    if start:
        query = query.filter(CoachPaymentHistory.payment_date >= start)
    if year is not None:
        query = query.filter(
            CoachPaymentHistory.payment_date >= datetime(year, 1, 1),
            CoachPaymentHistory.payment_date < datetime(year + 1, 1, 1),
        )

    payments = [
        payment
        for payment in query.all()
        if _matches_financial_query(payment, q, db)
    ]
    completed_payments = [payment for payment in payments if _payment_status(payment) == "Completed"]
    refunded_payments = [payment for payment in payments if _payment_status(payment) == "Refunded"]

    total_revenue = sum(float(payment.amount) for payment in completed_payments)
    platform_revenue = sum(_payment_platform_fee(payment) for payment in completed_payments)
    coach_payout_total = sum(_payment_coach_payout(payment) for payment in completed_payments)
    refunded_amount = sum(float(payment.amount) for payment in refunded_payments)
    transaction_count = len(payments)
    average_transaction = total_revenue / len(completed_payments) if completed_payments else 0

    monthly_totals: dict[str, dict[str, float | int]] = {}
    for payment in completed_payments:
        label = _month_label(payment.payment_date)
        if label not in monthly_totals:
            monthly_totals[label] = {"revenue": 0.0, "transaction_count": 0}
        monthly_totals[label]["revenue"] += float(payment.amount)
        monthly_totals[label]["transaction_count"] += 1

    chart = [
        {
            "label": label,
            "revenue": round(float(values["revenue"]), 2),
            "transaction_count": int(values["transaction_count"]),
        }
        for label, values in monthly_totals.items()
    ]

    recent_transactions = []
    for payment in sorted(payments, key=lambda row: row.payment_date, reverse=True)[:8]:
        client_name, coach_name = _payment_people(payment, db)
        recent_transactions.append(
            {
                "payment_id": payment.payment_id,
                "client_id": payment.client_id,
                "coach_id": payment.coach_id,
                "client_name": client_name,
                "coach_name": coach_name,
                "amount": float(payment.amount),
                "platform_fee": round(_payment_platform_fee(payment), 2),
                "coach_payout_amount": round(_payment_coach_payout(payment), 2),
                "status": _payment_status(payment),
                "payment_date": payment.payment_date,
            }
        )

    return AdminFinancialSummaryOut(
        period=period,
        year=year,
        query=q,
        total_revenue=round(total_revenue, 2),
        platform_revenue=round(platform_revenue, 2),
        coach_payout_total=round(coach_payout_total, 2),
        refunded_amount=round(refunded_amount, 2),
        transaction_count=transaction_count,
        average_transaction=round(average_transaction, 2),
        has_transactions=transaction_count > 0,
        chart=chart,
        recent_transactions=recent_transactions,
    )


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
