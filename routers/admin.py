# Handles admin-only endpoints (UC 6.2–6.7): approving/rejecting/suspending coaches, managing reports, and viewing financial and engagement analytics.

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from dependencies.rbac import require_admin
from models.log import DailySurvey, MoodType, UserDailyEngagement
from models.payment import CoachPaymentHistory
from models.user import Client, Coach, CoachStatus, User
from schemas.admin import (
    AdminCoachApplicationOut,
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
