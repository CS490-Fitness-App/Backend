# Handles coach review endpoints (UC 5.6): listing reviews for a coach and submitting or deleting a client review.

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from models.review import Review
from schemas.review import ReviewOut

router = APIRouter(prefix="/reviews", tags=["reviews"], redirect_slashes=False)


@router.get("/{coach_id}", response_model=list[ReviewOut])
def get_coach_reviews(
    coach_id: int,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Return reviews for a given coach, most recent first."""
    query = (
        db.query(Review)
        .filter(Review.coach_id == coach_id)
        .order_by(Review.created_at.desc())
    )
    if limit:
        query = query.limit(limit)
    return query.all()
