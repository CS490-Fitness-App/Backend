# Pydantic schemas for saved payment cards and coach payment history.
# Used by the payments router to validate card input and format financial records.

from pydantic import BaseModel


class CardIn(BaseModel):
    card_number: str        # 16-digit string, digits only
    expiry_month: int       # 1–12
    expiry_year: int        # YYYY
    zip_code: str | None = None
    is_default: bool = False


class CardOut(BaseModel):
    card_id: int
    card_type_name: str     # "Visa" or "Mastercard"
    last_four: str
    expiry_month: int
    expiry_year: int
    zip_code: str | None
    is_default: bool
