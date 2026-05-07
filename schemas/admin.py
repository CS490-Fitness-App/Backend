from datetime import datetime

from pydantic import BaseModel


class AdminClientOut(BaseModel):
    client_id: int
    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    email: str
    is_active: bool
    weekly_streak: int
    joined_at: datetime


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


class AdminOverviewOut(BaseModel):
    total_users: int
    total_clients: int
    active_coaches: int
    pending_approvals: int
    revenue_this_month: float


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


class AdminEngagementChartPointOut(BaseModel):
    date: str
    label: str
    active_users: int
    survey_completions: int
    survey_completion_rate: float
    average_mood_score: float | None = None
    average_mood_label: str | None = None


class AdminMoodBreakdownOut(BaseModel):
    label: str
    count: int
    percentage: float


class AdminEngagementSummaryOut(BaseModel):
    period: str
    days: int
    total_clients: int
    today_active_users: int
    today_survey_completions: int
    unique_active_users: int
    repeat_active_users: int
    active_user_rate: float
    average_daily_active_users: float
    average_survey_completion_rate: float
    total_surveys_logged: int
    average_mood_score: float | None = None
    average_mood_label: str | None = None
    positive_mood_rate: float
    most_common_mood_label: str | None = None
    stickiness_rate: float
    surveys_per_active_user: float
    best_active_day_label: str | None = None
    best_completion_day_label: str | None = None
    mood_breakdown: list[AdminMoodBreakdownOut]
    chart: list[AdminEngagementChartPointOut]
