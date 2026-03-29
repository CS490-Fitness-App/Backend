# Handles payment endpoints (UC 5.8–5.9): saving and deleting payment cards, and retrieving coach payment history.

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import require_client
from models.payment import Card, CardType
from schemas.payment import CardIn, CardOut

router = APIRouter(prefix="/payments", tags=["payments"])


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


def _validate_card(data: CardIn) -> None:
    """Raise HTTPException(400) for any invalid card field."""
    if not data.card_number.isdigit() or len(data.card_number) != 16:
        raise HTTPException(status_code=400, detail="Card number must be exactly 16 digits.")

    if not _luhn_valid(data.card_number):
        raise HTTPException(status_code=400, detail="Invalid card number.")

    if _detect_card_type(data.card_number) is None:
        raise HTTPException(status_code=400, detail="Only Visa and Mastercard are accepted.")

    if not (1 <= data.expiry_month <= 12):
        raise HTTPException(status_code=400, detail="Expiry month must be between 1 and 12.")

    today = date.today()
    if (data.expiry_year, data.expiry_month) < (today.year, today.month):
        raise HTTPException(status_code=400, detail="Card is expired.")


@router.post("/cards", response_model=CardOut)
def add_card(
    data: CardIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    _validate_card(data)

    card_type_name = _detect_card_type(data.card_number)
    card_type = db.query(CardType).filter_by(card_type_name=card_type_name).first()
    if not card_type:
        raise HTTPException(status_code=400, detail=f"{card_type_name} is not a supported card type.")

    user_id = current_user.user_id

    if data.is_default:
        db.query(Card).filter_by(user_id=user_id, is_default=True).update({"is_default": False})

    masked_number = "*" * 12 + data.card_number[-4:]  # e.g. "************1111"

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

    return CardOut(
        card_id=card.card_id,
        card_type_name=card_type.card_type_name,
        last_four=card.card_number[-4:],
        expiry_month=card.expiry_month,
        expiry_year=card.expiry_year,
        zip_code=card.zip_code,
        is_default=card.is_default,
    )
