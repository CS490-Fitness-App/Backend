# Pydantic schemas for coach reviews and misconduct reports.
# Covers both client-submitted star ratings and formal complaint submissions.

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ReviewOut(BaseModel):
    review_id: int
    coach_id: int
    rating: int
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
