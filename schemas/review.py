# Pydantic schemas for coach reviews and misconduct reports.
# Covers both client-submitted star ratings and formal complaint submissions.

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ReviewIn(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    description: Optional[str] = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_id: int
    coach_id: int
    rating: int
    description: Optional[str] = None
    created_at: datetime
    client_name: Optional[str] = None

    class Config:
        from_attributes = True


class ReportIn(BaseModel):
    reason: str
    details: Optional[str] = None
