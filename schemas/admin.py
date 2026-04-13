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
