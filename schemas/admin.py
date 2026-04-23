from datetime import datetime

from pydantic import BaseModel


class AdminCoachApplicationOut(BaseModel):
    coach_id: int
    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    email: str
    specialization: str
    status: str
    active: bool
    accepting_clients: bool
    submitted_at: datetime


class AdminCoachDecisionOut(BaseModel):
    message: str
    coach_id: int
    status: str


class AdminFinancialChartPointOut(BaseModel):
    label: str
    revenue: float
    transaction_count: int


class AdminFinancialTransactionOut(BaseModel):
    payment_id: int
    client_id: int
    coach_id: int
    client_name: str
    coach_name: str
    amount: float
    platform_fee: float
    coach_payout_amount: float
    status: str
    payment_date: datetime


class AdminFinancialSummaryOut(BaseModel):
    period: str
    year: int | None = None
    query: str | None = None
    total_revenue: float
    platform_revenue: float
    coach_payout_total: float
    refunded_amount: float
    transaction_count: int
    average_transaction: float
    has_transactions: bool
    chart: list[AdminFinancialChartPointOut]
    recent_transactions: list[AdminFinancialTransactionOut]
