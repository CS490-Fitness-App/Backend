# Handles payment endpoints (UC 5.8–5.9): saving and deleting payment cards, and retrieving coach payment history.

import re
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
