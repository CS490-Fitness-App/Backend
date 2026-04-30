# Pydantic schemas for saved payment cards and coach payment history.
# Used by the payments router to validate card input and format financial records.

from datetime import date, datetime
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


class BillingCounterpartyOut(BaseModel):
    counterparty_role: str
    counterparty_id: int
    counterparty_name: str
    amount: float
    next_charge_date: date
    days_until_due: int
    paid_this_month: bool


class PaymentHistoryOut(BaseModel):
    payment_id: int
    counterparty_name: str
    amount: float
    platform_fee: float
    coach_payout_amount: float
    status: str
    payment_date: datetime


class AutoChargeRunOut(BaseModel):
    charged: int
    failed: int
    skipped: int


class BillingSummaryOut(BaseModel):
    role: str
    monthly_total: float
    counterparties: list[BillingCounterpartyOut]
    recent_payments: list[PaymentHistoryOut]
