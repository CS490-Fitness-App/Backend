# Handles payment endpoints (UC 5.8–5.9): saving and deleting payment cards, and retrieving coach payment history.

import re
from calendar import monthrange
from datetime import date, datetime, time, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import require_client
from models.coach import ClientCoach
from models.notification import Notification
from models.payment import Card, CardType
from models.payment import CoachPaymentHistory
from models.user import Client, Coach, User
from routers.notifications import notify
from schemas.payment import (
    AutoChargeRunOut,
    BillingCounterpartyOut,
    BillingSummaryOut,
    CardIn,
    CardOut,
    PaymentHistoryOut,
)

router = APIRouter(prefix="/payments", tags=["payments"])

PLATFORM_FEE_RATE = Decimal("0.10")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _month_start_end(target_date: date) -> tuple[datetime, datetime]:
    start = datetime.combine(target_date.replace(day=1), time.min, tzinfo=timezone.utc)
    last_day = monthrange(target_date.year, target_date.month)[1]
    end = datetime.combine(target_date.replace(day=last_day), time.max, tzinfo=timezone.utc)
    return start, end


def _safe_due_date(year: int, month: int, anchor_day: int) -> date:
    return date(year, month, min(anchor_day, monthrange(year, month)[1]))


def _default_card_for_user(db: Session, user_id: int) -> Card | None:
    card = db.query(Card).filter_by(user_id=user_id, is_default=True).first()
    if card:
        return card
    return db.query(Card).filter_by(user_id=user_id).first()


def _payment_exists_for_current_month(
    db: Session,
    client_id: int,
    coach_id: int,
    target_date: date,
) -> bool:
    period_start, period_end = _month_start_end(target_date)
    existing = (
        db.query(CoachPaymentHistory.payment_id)
        .filter(
            CoachPaymentHistory.client_id == client_id,
            CoachPaymentHistory.coach_id == coach_id,
            CoachPaymentHistory.payment_date >= period_start,
            CoachPaymentHistory.payment_date <= period_end,
        )
        .first()
    )
    return existing is not None


def _notify_once_per_day(db: Session, user_id: int, message: str) -> None:
    now = _utc_now()
    today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    today_end = datetime.combine(now.date(), time.max, tzinfo=timezone.utc)
    existing = (
        db.query(Notification.notification_id)
        .filter(
            Notification.user_id == user_id,
            Notification.message == message,
            Notification.created_at >= today_start,
            Notification.created_at <= today_end,
        )
        .first()
    )
    if not existing:
        notify(db, user_id=user_id, message=message)


def _active_pairs_for_user(db: Session, current_user: User):
    if current_user.role == "client":
        client = db.query(Client).filter_by(user_id=current_user.user_id).first()
        if not client:
            return []
        return (
            db.query(ClientCoach, Coach, User)
            .join(Coach, Coach.coach_id == ClientCoach.coach_id)
            .join(User, User.user_id == Coach.user_id)
            .filter(
                ClientCoach.client_id == client.client_id,
                ClientCoach.status_name == "Active",
            )
            .all()
        )

    if current_user.role == "coach":
        coach = db.query(Coach).filter_by(user_id=current_user.user_id).first()
        if not coach:
            return []
        return (
            db.query(ClientCoach, Client, User)
            .join(Client, Client.client_id == ClientCoach.client_id)
            .join(User, User.user_id == Client.user_id)
            .filter(
                ClientCoach.coach_id == coach.coach_id,
                ClientCoach.status_name == "Active",
            )
            .all()
        )

    return []


def _build_counterparties(db: Session, current_user: User) -> list[BillingCounterpartyOut]:
    today = date.today()
    rows = _active_pairs_for_user(db, current_user)
    items: list[BillingCounterpartyOut] = []

    for row in rows:
        relationship = row[0]
        profile = row[1]
        person = row[2]

        activated = relationship.activated_at or relationship.created_at or _utc_now()
        if isinstance(activated, datetime):
            anchor_day = activated.day
        else:
            anchor_day = today.day

        due_date = _safe_due_date(today.year, today.month, anchor_day)
        if due_date < today:
            next_month = today.month + 1
            next_year = today.year
            if next_month == 13:
                next_month = 1
                next_year += 1
            next_due = _safe_due_date(next_year, next_month, anchor_day)
        else:
            next_due = due_date

        days_until_due = (next_due - today).days

        coach = profile if current_user.role == "client" else db.query(Coach).filter_by(coach_id=relationship.coach_id).first()
        amount = float(coach.hourly_rate) if coach and coach.hourly_rate is not None else 0.0

        has_payment_this_month = _payment_exists_for_current_month(
            db,
            relationship.client_id,
            relationship.coach_id,
            today,
        )

        if current_user.role == "client":
            counterparty_role = "coach"
            counterparty_id = relationship.coach_id
        else:
            counterparty_role = "client"
            counterparty_id = relationship.client_id

        items.append(
            BillingCounterpartyOut(
                counterparty_role=counterparty_role,
                counterparty_id=counterparty_id,
                counterparty_name=f"{person.first_name or ''} {person.last_name or ''}".strip() or "Unknown",
                amount=amount,
                next_charge_date=next_due,
                days_until_due=days_until_due,
                paid_this_month=has_payment_this_month,
            )
        )

    return items


def _run_auto_charge_for_user(db: Session, current_user: User) -> AutoChargeRunOut:
    today = date.today()
    now = _utc_now()
    rows = _active_pairs_for_user(db, current_user)
    charged = 0
    failed = 0
    skipped = 0

    for row in rows:
        relationship = row[0]

        if _payment_exists_for_current_month(db, relationship.client_id, relationship.coach_id, today):
            skipped += 1
            continue

        activated = relationship.activated_at or relationship.created_at or now
        due_day = activated.day if isinstance(activated, datetime) else today.day
        due_date = _safe_due_date(today.year, today.month, due_day)
        if today < due_date:
            skipped += 1
            continue

        client = db.query(Client).filter_by(client_id=relationship.client_id).first()
        coach = db.query(Coach).filter_by(coach_id=relationship.coach_id).first()
        if not client or not coach:
            skipped += 1
            continue

        if coach.status and coach.status.status_name == "Suspended":
            skipped += 1
            continue

        client_user = db.query(User).filter_by(user_id=client.user_id).first()
        coach_user = db.query(User).filter_by(user_id=coach.user_id).first()

        amount = Decimal(str(coach.hourly_rate or 0)).quantize(Decimal("0.01"))
        platform_fee = (amount * PLATFORM_FEE_RATE).quantize(Decimal("0.01"))
        payout = (amount - platform_fee).quantize(Decimal("0.01"))

        card = _default_card_for_user(db, client.user_id)
        if not card:
            failed += 1
            db.add(
                CoachPaymentHistory(
                    client_id=relationship.client_id,
                    coach_id=relationship.coach_id,
                    amount=amount,
                    platform_fee=Decimal("0.00"),
                    coach_payout_amount=Decimal("0.00"),
                    status="Failed",
                    payment_date=now,
                )
            )
            if client_user:
                _notify_once_per_day(
                    db,
                    client_user.user_id,
                    f"Payment failed for {coach_user.first_name if coach_user else 'your coach'}: no saved card on file.",
                )
            if coach_user and client_user:
                _notify_once_per_day(
                    db,
                    coach_user.user_id,
                    f"Auto-charge failed for client {client_user.first_name or 'Unknown'} {client_user.last_name or ''}.",
                )
            continue

        charged += 1
        db.add(
            CoachPaymentHistory(
                client_id=relationship.client_id,
                coach_id=relationship.coach_id,
                amount=amount,
                platform_fee=platform_fee,
                coach_payout_amount=payout,
                status="Completed",
                payment_date=now,
            )
        )

        if client_user and coach_user:
            _notify_once_per_day(
                db,
                client_user.user_id,
                f"Auto-charge successful: ${amount} paid to coach {coach_user.first_name} {coach_user.last_name}.",
            )
            _notify_once_per_day(
                db,
                coach_user.user_id,
                f"You received an auto-payment of ${payout} from {client_user.first_name} {client_user.last_name}.",
            )

    db.commit()
    return AutoChargeRunOut(charged=charged, failed=failed, skipped=skipped)


def _create_due_soon_reminders(db: Session, current_user: User) -> int:
    reminders_created = 0
    today = date.today()
    counterparties = _build_counterparties(db, current_user)

    for item in counterparties:
        if item.paid_this_month:
            continue
        if item.days_until_due < 0 or item.days_until_due > 3:
            continue

        message = (
            f"Payment reminder: ${item.amount:.2f} for {item.counterparty_name} is due on {item.next_charge_date.isoformat()}."
        )
        _notify_once_per_day(db, current_user.user_id, message)
        reminders_created += 1

    if reminders_created:
        db.commit()

    return reminders_created


def _recent_history_for_user(db: Session, current_user: User) -> list[PaymentHistoryOut]:
    query = db.query(CoachPaymentHistory)
    if current_user.role == "client":
        client = db.query(Client).filter_by(user_id=current_user.user_id).first()
        if not client:
            return []
        query = query.filter(CoachPaymentHistory.client_id == client.client_id)
    elif current_user.role == "coach":
        coach = db.query(Coach).filter_by(user_id=current_user.user_id).first()
        if not coach:
            return []
        query = query.filter(CoachPaymentHistory.coach_id == coach.coach_id)
    else:
        return []

    rows = query.order_by(CoachPaymentHistory.payment_date.desc()).limit(20).all()
    history: list[PaymentHistoryOut] = []
    for row in rows:
        client = db.query(Client).filter_by(client_id=row.client_id).first()
        coach = db.query(Coach).filter_by(coach_id=row.coach_id).first()
        client_user = db.query(User).filter_by(user_id=client.user_id).first() if client else None
        coach_user = db.query(User).filter_by(user_id=coach.user_id).first() if coach else None

        counterparty_name = "Unknown"
        if current_user.role == "client" and coach_user:
            counterparty_name = f"{coach_user.first_name or ''} {coach_user.last_name or ''}".strip() or "Unknown"
        if current_user.role == "coach" and client_user:
            counterparty_name = f"{client_user.first_name or ''} {client_user.last_name or ''}".strip() or "Unknown"

        history.append(
            PaymentHistoryOut(
                payment_id=row.payment_id,
                counterparty_name=counterparty_name,
                amount=float(row.amount),
                platform_fee=float(row.platform_fee),
                coach_payout_amount=float(row.coach_payout_amount),
                status=row.status,
                payment_date=row.payment_date,
            )
        )

    return history


def _current_month_total_for_user(db: Session, current_user: User) -> float:
    today = date.today()
    start, end = _month_start_end(today)

    query = db.query(CoachPaymentHistory).filter(
        CoachPaymentHistory.payment_date >= start,
        CoachPaymentHistory.payment_date <= end,
        CoachPaymentHistory.status == "Completed",
    )

    if current_user.role == "client":
        client = db.query(Client).filter_by(user_id=current_user.user_id).first()
        if not client:
            return 0.0
        rows = query.filter(CoachPaymentHistory.client_id == client.client_id).all()
        return round(sum(float(r.amount) for r in rows), 2)

    if current_user.role == "coach":
        coach = db.query(Coach).filter_by(user_id=current_user.user_id).first()
        if not coach:
            return 0.0
        rows = query.filter(CoachPaymentHistory.coach_id == coach.coach_id).all()
        return round(sum(float(r.coach_payout_amount) for r in rows), 2)

    return 0.0


def _detect_card_type(number: str) -> str | None:
    """Return 'Visa', 'Mastercard', or None based on card number prefix."""
    if number.startswith("4"):
        return "Visa"
    if len(number) >= 2:
        prefix2 = int(number[:2])
        if 51 <= prefix2 <= 55:
            return "Mastercard"
    if len(number) >= 4:
        prefix4 = int(number[:4])
        if 2221 <= prefix4 <= 2720:
            return "Mastercard"
    return None


def _luhn_valid(number: str) -> bool:
    """Standard Luhn algorithm check."""
    total = 0
    reverse_digits = number[::-1]
    for i, ch in enumerate(reverse_digits):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _validate_card(data: CardIn) -> str:
    """Validate card fields and return the card type name. Raises HTTPException(400) on failure."""
    if not data.card_number.isdigit() or len(data.card_number) != 16:
        raise HTTPException(status_code=400, detail="Card number must be exactly 16 digits.")

    # if not _luhn_valid(data.card_number):
    #     raise HTTPException(status_code=400, detail="Invalid card number.")

    card_type_name = _detect_card_type(data.card_number)
    if card_type_name is None:
        raise HTTPException(status_code=400, detail="Only Visa and Mastercard are accepted.")

    if not (1 <= data.expiry_month <= 12):
        raise HTTPException(status_code=400, detail="Expiry month must be between 1 and 12.")

    today = date.today()
    if (data.expiry_year, data.expiry_month) < (today.year, today.month):
        raise HTTPException(status_code=400, detail="Card is expired.")

    if data.zip_code is not None and not re.fullmatch(r"\d{5}(-\d{4})?", data.zip_code):
        raise HTTPException(status_code=400, detail="Zip code must be in format 12345 or 12345-6789.")

    return card_type_name


def _card_to_out(card: Card, card_type_name: str) -> CardOut:
    return CardOut(
        card_id=card.card_id,
        card_type_name=card_type_name,
        last_four=card.card_number[-4:],
        expiry_month=card.expiry_month,
        expiry_year=card.expiry_year,
        zip_code=card.zip_code,
        is_default=card.is_default,
    )


@router.get("/cards", response_model=list[CardOut])
def list_cards(
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    cards = db.query(Card).filter_by(user_id=current_user.user_id).all()
    return [_card_to_out(c, c.card_type.card_type_name) for c in cards]


@router.post("/cards", response_model=CardOut)
def add_card(
    data: CardIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    card_type_name = _validate_card(data)

    card_type = db.query(CardType).filter_by(card_type_name=card_type_name).first()
    if not card_type:
        raise HTTPException(status_code=400, detail=f"{card_type_name} is not a supported card type.")

    user_id = current_user.user_id
    masked_number = "*" * 12 + data.card_number[-4:]

    duplicate = db.query(Card).filter_by(
        user_id=user_id,
        card_number=masked_number,
        expiry_month=data.expiry_month,
        expiry_year=data.expiry_year,
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="This card is already saved.")

    if data.is_default:
        db.query(Card).filter_by(user_id=user_id, is_default=True).update({"is_default": False})

    card = Card(
        user_id=user_id,
        card_type_id=card_type.card_type_id,
        card_number=masked_number,
        expiry_month=data.expiry_month,
        expiry_year=data.expiry_year,
        zip_code=data.zip_code,
        is_default=data.is_default,
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    return _card_to_out(card, card_type_name)


@router.delete("/cards/{card_id}", status_code=204)
def delete_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    card = db.query(Card).filter_by(card_id=card_id, user_id=current_user.user_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found.")
    db.delete(card)
    db.commit()


@router.post("/billing/auto-charge", response_model=AutoChargeRunOut)
def run_auto_charge(
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    return _run_auto_charge_for_user(db, current_user)


@router.post("/billing/poll", response_model=AutoChargeRunOut)
def poll_billing_automation(
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    result = _run_auto_charge_for_user(db, current_user)
    _create_due_soon_reminders(db, current_user)
    return result


@router.get("/billing/summary", response_model=BillingSummaryOut)
def get_billing_summary(
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    _create_due_soon_reminders(db, current_user)
    return BillingSummaryOut(
        role=current_user.role,
        monthly_total=_current_month_total_for_user(db, current_user),
        counterparties=_build_counterparties(db, current_user),
        recent_payments=_recent_history_for_user(db, current_user),
    )
