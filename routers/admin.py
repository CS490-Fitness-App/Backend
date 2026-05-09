# Handles admin-only endpoints (UC 6.2–6.7): approving/rejecting/suspending coaches, managing reports, and viewing financial and engagement analytics.

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from core.account_lifecycle import delete_user_account
from dependencies.rbac import require_admin
from models.log import DailySurvey, Goal, GoalType, MoodType, UserDailyEngagement
from models.payment import CoachPaymentHistory
from models.coach import ClientCoach, CoachAvailability, CoachCertification
from models.review import Review, Report
from models.user import Client, Coach, CoachStatus, User
from models.workout import Workout
from routers.notifications import notify
from schemas.admin import (
    AdminClientOut,
    AdminClientProfileOut,
    AdminClientStatusOut,
    AdminCoachApplicationOut,
    AdminCoachProfileOut,
    AdminReviewOut,
    AdminReportOut,
    AdminReportUpdateIn,
    AdminCoachDecisionOut,
    AdminEngagementSummaryOut,
    AdminFinancialSummaryOut,
    AdminOverviewOut,
)

router = APIRouter(prefix="/admin", tags=["admin"])

_MOOD_TO_SCORE = {
    "amazing": 2,
    "great": 2,
    "good": 1,
    "okay": 0,
    "ok": 0,
    "bad": -1,
    "low": -1,
    "awful": -2,
}

_SCORE_TO_MOOD = {
    2: "Amazing",
    1: "Good",
    0: "Okay",
    -1: "Bad",
    -2: "Awful",
}


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


def _to_admin_report_out(report: Report) -> AdminReportOut:
    coach_user = report.coach.user if report.coach else None
    reporter = report.reporter
    coach_name = _full_name(coach_user)
    reporter_name = _full_name(reporter)

    return AdminReportOut(
        report_id=report.report_id,
        reporter_id=report.reporter_id,
        reporter_name=reporter_name,
        reporter_email=reporter.email if reporter else None,
        coach_id=report.coach_id,
        coach_name=coach_name,
        coach_email=coach_user.email if coach_user else None,
        coach_status=report.coach.status.status_name if report.coach and report.coach.status else None,
        reason=report.reason,
        status=report.status or "Pending",
        created_at=report.created_at,
        last_updated=report.last_updated,
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


def _get_report_or_404(report_id: int, db: Session) -> Report:
    report = (
        db.query(Report)
        .options(
            joinedload(Report.reporter),
            joinedload(Report.coach).joinedload(Coach.user),
            joinedload(Report.coach).joinedload(Coach.status),
        )
        .filter(Report.report_id == report_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


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


def _calculate_age(dob: date | None) -> int | None:
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _grams_to_lb(value: int | None) -> float | None:
    if value is None:
        return None
    return round(value / 453.592, 1)


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


def _engagement_period_days(period: str) -> int:
    mapping = {
        "week": 7,
        "month": 30,
        "quarter": 90,
        "year": 365,
    }
    if period not in mapping:
        raise HTTPException(status_code=400, detail="Invalid engagement period.")
    return mapping[period]


def _normalize_mood_label(label: str | None) -> str | None:
    if not label:
        return None
    score = _MOOD_TO_SCORE.get(label.strip().lower())
    if score is None:
        return None
    return _SCORE_TO_MOOD[score]


def _score_to_closest_mood(score: float | None) -> str | None:
    if score is None:
        return None
    closest_score = min(_SCORE_TO_MOOD.keys(), key=lambda value: abs(value - score))
    return _SCORE_TO_MOOD[closest_score]


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


@router.get("/clients", response_model=list[AdminClientOut])
def list_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    clients = (
        db.query(Client)
        .options(joinedload(Client.user))
        .order_by(Client.created_at.desc())
        .all()
    )
    return [
        AdminClientOut(
            client_id=client.client_id,
            user_id=client.user_id,
            first_name=client.user.first_name,
            last_name=client.user.last_name,
            email=client.user.email,
            profile_picture=client.user.profile_picture,
            is_active=client.user.is_active,
            deactivated_at=client.user.deactivated_at,
            scheduled_deletion_at=client.user.scheduled_deletion_at,
            deactivated_by_admin=client.user.deactivated_by_admin,
            weekly_streak=client.weekly_streak,
            joined_at=client.created_at,
        )
        for client in clients
    ]


@router.get("/clients/{client_id}/profile", response_model=AdminClientProfileOut)
def get_client_profile(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    client = (
        db.query(Client)
        .options(joinedload(Client.user))
        .filter(Client.client_id == client_id)
        .first()
    )
    if not client or not client.user:
        raise HTTPException(status_code=404, detail="Client not found")

    goals = (
        db.query(GoalType.goal_type_name)
        .join(Goal, Goal.goal_type_id == GoalType.goal_type_id)
        .filter(Goal.user_id == client.user_id)
        .all()
    )

    active_contract = (
        db.query(ClientCoach)
        .filter(
            ClientCoach.client_id == client.client_id,
            ClientCoach.status_name == "Active",
        )
        .first()
    )

    latest_survey = (
        db.query(DailySurvey.survey_date)
        .filter(DailySurvey.user_id == client.user_id)
        .order_by(DailySurvey.survey_date.desc())
        .first()
    )

    active_coach = None
    if active_contract:
        active_coach = (
            db.query(Coach)
            .options(joinedload(Coach.user))
            .filter(Coach.coach_id == active_contract.coach_id)
            .first()
        )
    active_coach_user = active_coach.user if active_coach and active_coach.user else None

    return AdminClientProfileOut(
        client_id=client.client_id,
        user_id=client.user_id,
        first_name=client.user.first_name,
        last_name=client.user.last_name,
        email=client.user.email,
        profile_picture=client.user.profile_picture,
        is_active=client.user.is_active,
        deactivated_at=client.user.deactivated_at,
        scheduled_deletion_at=client.user.scheduled_deletion_at,
        deactivated_by_admin=client.user.deactivated_by_admin,
        joined_at=client.created_at,
        weekly_streak=client.weekly_streak,
        age=_calculate_age(client.DOB),
        height_cm=client.height,
        weight_lb=_grams_to_lb(client.weight),
        goal_weight_lb=_grams_to_lb(client.goal_weight),
        sex=client.sex,
        goals=[row.goal_type_name for row in goals],
        active_coach_name=_full_name(active_coach_user) if active_coach_user else None,
        active_coach_email=active_coach_user.email if active_coach_user else None,
        last_survey_date=latest_survey[0] if latest_survey else None,
    )


@router.post("/clients/{client_id}/deactivate", response_model=AdminClientStatusOut)
def deactivate_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    client = db.query(Client).filter(Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    user = client.user
    if not user:
        raise HTTPException(status_code=404, detail="Client user not found")
    if user.is_active is False:
        raise HTTPException(status_code=409, detail="Client account is already inactive")

    user.is_active = False
    user.deactivated_at = datetime.now(timezone.utc)
    user.scheduled_deletion_at = None
    user.deactivated_by_admin = True
    user.last_updated = datetime.now(timezone.utc)

    active_contracts = (
        db.query(ClientCoach)
        .filter(
            ClientCoach.client_id == client.client_id,
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
                message=f"Your client {_full_name(user)} has been deactivated by an admin. The coaching contract has been terminated.",
            )

    db.commit()

    return AdminClientStatusOut(
        message="Client account deactivated",
        client_id=client.client_id,
        is_active=False,
    )


@router.post("/clients/{client_id}/reactivate", response_model=AdminClientStatusOut)
def reactivate_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    client = db.query(Client).filter(Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    user = client.user
    if not user:
        raise HTTPException(status_code=404, detail="Client user not found")
    if user.is_active is True:
        raise HTTPException(status_code=409, detail="Client account is already active")

    user.is_active = True
    user.deactivated_at = None
    user.scheduled_deletion_at = None
    user.deactivated_by_admin = False
    user.last_updated = datetime.now(timezone.utc)
    db.commit()

    return AdminClientStatusOut(
        message="Client account reactivated",
        client_id=client.client_id,
        is_active=True,
    )


@router.delete("/clients/{client_id}", status_code=204)
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    client = db.query(Client).filter(Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    user = client.user
    if not user:
        raise HTTPException(status_code=404, detail="Client user not found")
    if user.is_active:
        raise HTTPException(status_code=409, detail="Deactivate the client before deleting the account.")

    delete_user_account(db, user.user_id)


@router.get("/reviews", response_model=list[AdminReviewOut])
def list_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    reviews = db.query(Review).order_by(Review.created_at.desc()).all()
    result = []
    for r in reviews:
        coach_name = None
        if r.coach and r.coach.user:
            coach_name = f"{r.coach.user.first_name or ''} {r.coach.user.last_name or ''}".strip() or r.coach.user.email
        client_name = None
        if r.client and r.client.user:
            client_name = f"{r.client.user.first_name or ''} {r.client.user.last_name or ''}".strip() or r.client.user.email
        result.append(AdminReviewOut(
            review_id=r.review_id,
            coach_id=r.coach_id,
            coach_name=coach_name,
            client_name=client_name,
            rating=r.rating,
            description=r.description,
            created_at=r.created_at,
        ))
    return result


@router.get("/reports", response_model=list[AdminReportOut])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    reports = (
        db.query(Report)
        .options(
            joinedload(Report.reporter),
            joinedload(Report.coach).joinedload(Coach.user),
            joinedload(Report.coach).joinedload(Coach.status),
        )
        .order_by(Report.created_at.desc())
        .all()
    )
    return [_to_admin_report_out(report) for report in reports]


@router.post("/reports/{report_id}/status", response_model=AdminReportOut)
def update_report_status(
    report_id: int,
    body: AdminReportUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    allowed_statuses = {"Pending", "Resolved", "Dismissed"}
    normalized_status = (body.status or "").strip().title()
    if normalized_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid report status.")

    report = _get_report_or_404(report_id, db)
    report.status = normalized_status
    report.last_updated = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)

    return _to_admin_report_out(_get_report_or_404(report_id, db))


@router.delete("/reviews/{review_id}", status_code=204)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    review = db.query(Review).filter(Review.review_id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)
    db.commit()


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


@router.get("/coaches/{coach_id}/profile", response_model=AdminCoachProfileOut)
def get_coach_profile(
    coach_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    coach = (
        db.query(Coach)
        .options(
            joinedload(Coach.user),
            joinedload(Coach.status),
        )
        .filter(Coach.coach_id == coach_id)
        .first()
    )
    if not coach or not coach.user:
        raise HTTPException(status_code=404, detail="Coach not found")

    certifications = (
        db.query(CoachCertification.certification_name)
        .filter(CoachCertification.coach_id == coach.coach_id)
        .order_by(CoachCertification.certification_name.asc())
        .all()
    )
    availability_rows = (
        db.query(CoachAvailability)
        .filter(CoachAvailability.coach_id == coach.coach_id)
        .order_by(CoachAvailability.day_of_week.asc(), CoachAvailability.start_time.asc())
        .all()
    )
    active_client_count = (
        db.query(ClientCoach)
        .filter(ClientCoach.coach_id == coach.coach_id, ClientCoach.status_name == "Active")
        .count()
    )
    pending_client_count = (
        db.query(ClientCoach)
        .filter(ClientCoach.coach_id == coach.coach_id, ClientCoach.status_name == "Pending")
        .count()
    )

    availability = [
        f"{slot.day_of_week} {slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}"
        for slot in availability_rows
    ]

    return AdminCoachProfileOut(
        coach_id=coach.coach_id,
        user_id=coach.user_id,
        first_name=coach.user.first_name,
        last_name=coach.user.last_name,
        email=coach.user.email,
        profile_picture=coach.user.profile_picture,
        specialization=_specialization_label(coach),
        status=coach.status.status_name if coach.status else "Unknown",
        is_active_user=coach.user.is_active,
        accepting_clients=coach.accepting_clients,
        hourly_rate=float(coach.hourly_rate or 0),
        gender=coach.gender,
        bio=coach.bio,
        years_of_experience=coach.years_of_experience,
        max_clients=coach.max_clients,
        active_client_count=active_client_count,
        pending_client_count=pending_client_count,
        certifications=[row.certification_name for row in certifications],
        availability=availability,
        submitted_at=coach.created_at,
    )


@router.get("/overview", response_model=AdminOverviewOut)
def get_admin_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    total_users = db.query(User).count()
    total_clients = db.query(Client).count()

    active_coaches = (
        db.query(Coach)
        .join(CoachStatus, Coach.status_id == CoachStatus.status_id)
        .filter(CoachStatus.status_name == "Active")
        .count()
    )
    pending_approvals = (
        db.query(Coach)
        .join(CoachStatus, Coach.status_id == CoachStatus.status_id)
        .filter(CoachStatus.status_name == "Pending")
        .count()
    )

    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_payments = (
        db.query(CoachPaymentHistory)
        .filter(CoachPaymentHistory.payment_date >= month_start)
        .all()
    )
    revenue_this_month = sum(
        float(payment.amount)
        for payment in month_payments
        if _payment_status(payment) == "Completed"
    )

    return AdminOverviewOut(
        total_users=total_users,
        total_clients=total_clients,
        active_coaches=active_coaches,
        pending_approvals=pending_approvals,
        revenue_this_month=round(revenue_this_month, 2),
    )


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


@router.get("/engagement-summary", response_model=AdminEngagementSummaryOut)
def get_engagement_summary(
    period: str = "month",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    days = _engagement_period_days(period)
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=days - 1)

    clients = db.query(Client).all()
    client_user_ids = [client.user_id for client in clients]
    total_clients = len(client_user_ids)

    active_users_by_date: dict[date, set[int]] = defaultdict(set)
    survey_counts_by_date: Counter[date] = Counter()
    active_days_by_user: dict[int, set[date]] = defaultdict(set)
    mood_counts: Counter[str] = Counter()
    mood_scores_by_date: dict[date, list[int]] = defaultdict(list)
    total_mood_score = 0
    total_mood_entries = 0
    positive_mood_entries = 0

    if client_user_ids:
        engagement_rows = (
            db.query(
                UserDailyEngagement.user_id,
                UserDailyEngagement.activity_date,
                UserDailyEngagement.survey_completed,
            )
            .filter(
                UserDailyEngagement.user_id.in_(client_user_ids),
                UserDailyEngagement.activity_date >= start_date,
                UserDailyEngagement.activity_date <= today,
            )
            .all()
        )
        for user_id, activity_date, survey_completed in engagement_rows:
            active_users_by_date[activity_date].add(user_id)
            active_days_by_user[user_id].add(activity_date)
            if survey_completed:
                survey_counts_by_date[activity_date] += 1

        survey_rows = (
            db.query(
                DailySurvey.user_id,
                DailySurvey.survey_date,
                MoodType.mood_type_name,
            )
            .outerjoin(MoodType, MoodType.mood_type_id == DailySurvey.mood_type_id)
            .filter(
                DailySurvey.user_id.in_(client_user_ids),
                DailySurvey.survey_date >= start_date,
                DailySurvey.survey_date <= today,
            )
            .all()
        )
        for survey_user_id, survey_date, mood_type_name in survey_rows:
            active_users_by_date[survey_date].add(survey_user_id)
            active_days_by_user[survey_user_id].add(survey_date)
            survey_counts_by_date[survey_date] += 1
            normalized_label = _normalize_mood_label(mood_type_name)
            if not normalized_label:
                continue
            score = _MOOD_TO_SCORE[normalized_label.lower()]
            mood_counts[normalized_label] += 1
            mood_scores_by_date[survey_date].append(score)
            total_mood_score += score
            total_mood_entries += 1
            if score >= 1:
                positive_mood_entries += 1

    chart = []
    best_active_point = None
    best_completion_point = None
    total_active_sum = 0
    total_completion_rate_sum = 0.0
    total_survey_completions = 0

    for offset in range(days):
        current_day = start_date + timedelta(days=offset)
        active_users = len(active_users_by_date.get(current_day, set()))
        survey_completions = survey_counts_by_date.get(current_day, 0)
        completion_rate = round((survey_completions / total_clients) * 100, 1) if total_clients else 0.0
        day_mood_scores = mood_scores_by_date.get(current_day, [])
        day_average_mood_score = round(sum(day_mood_scores) / len(day_mood_scores), 2) if day_mood_scores else None
        point = {
            "date": current_day.isoformat(),
            "label": current_day.strftime("%m/%d"),
            "active_users": active_users,
            "survey_completions": survey_completions,
            "survey_completion_rate": completion_rate,
            "average_mood_score": day_average_mood_score,
            "average_mood_label": _score_to_closest_mood(day_average_mood_score),
        }
        chart.append(point)
        total_active_sum += active_users
        total_completion_rate_sum += completion_rate
        total_survey_completions += survey_completions

        if best_active_point is None or active_users > best_active_point["active_users"]:
            best_active_point = point
        if best_completion_point is None or completion_rate > best_completion_point["survey_completion_rate"]:
            best_completion_point = point

    unique_active_users = len(active_days_by_user)
    repeat_active_users = sum(1 for active_days in active_days_by_user.values() if len(active_days) >= 2)
    active_user_rate = round((unique_active_users / total_clients) * 100, 1) if total_clients else 0.0
    stickiness_rate = round((total_active_sum / days) / unique_active_users * 100, 1) if days and unique_active_users else 0.0
    surveys_per_active_user = round(total_survey_completions / unique_active_users, 2) if unique_active_users else 0.0
    average_mood_score = round(total_mood_score / total_mood_entries, 2) if total_mood_entries else None
    average_mood_label = _score_to_closest_mood(average_mood_score)
    positive_mood_rate = round((positive_mood_entries / total_mood_entries) * 100, 1) if total_mood_entries else 0.0
    most_common_mood_label = None
    if mood_counts:
        ordered_moods = ["Amazing", "Good", "Okay", "Bad", "Awful"]
        most_common_mood_label = max(
            ordered_moods,
            key=lambda label: (mood_counts.get(label, 0), _MOOD_TO_SCORE[label.lower()]),
        )
    mood_breakdown = [
        {
            "label": label,
            "count": mood_counts.get(label, 0),
            "percentage": round((mood_counts.get(label, 0) / total_mood_entries) * 100, 1) if total_mood_entries else 0.0,
        }
        for label in ["Amazing", "Good", "Okay", "Bad", "Awful"]
    ]

    return AdminEngagementSummaryOut(
        period=period,
        days=days,
        total_clients=total_clients,
        today_active_users=len(active_users_by_date.get(today, set())),
        today_survey_completions=survey_counts_by_date.get(today, 0),
        unique_active_users=unique_active_users,
        repeat_active_users=repeat_active_users,
        active_user_rate=active_user_rate,
        average_daily_active_users=round(total_active_sum / days, 1) if days else 0.0,
        average_survey_completion_rate=round(total_completion_rate_sum / days, 1) if days else 0.0,
        total_surveys_logged=total_survey_completions,
        average_mood_score=average_mood_score,
        average_mood_label=average_mood_label,
        positive_mood_rate=positive_mood_rate,
        most_common_mood_label=most_common_mood_label,
        stickiness_rate=stickiness_rate,
        surveys_per_active_user=surveys_per_active_user,
        best_active_day_label=best_active_point["label"] if best_active_point else None,
        best_completion_day_label=best_completion_point["label"] if best_completion_point else None,
        mood_breakdown=mood_breakdown,
        chart=chart,
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

    active_contracts = (
        db.query(ClientCoach)
        .filter(
            ClientCoach.coach_id == coach_id,
            ClientCoach.status_name.in_(["Active", "Pending"]),
        )
        .all()
    )
    for contract in active_contracts:
        contract.status_name = "Terminated"
        client = db.query(Client).filter(Client.client_id == contract.client_id).first()
        if client:
            notify(
                db,
                user_id=client.user_id,
                message="Your coach's account has been suspended. Your coaching contract has been terminated.",
            )

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
