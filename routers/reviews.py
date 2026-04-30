# Handles coach review endpoints: listing, submitting, updating, and deleting client reviews.

import os
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import require_client
from models.coach import ClientCoach
from models.review import Review
from models.user import Coach, User
from routers.notifications import notify
from schemas.review import ReviewIn, ReviewOut

router = APIRouter(prefix="/coaches", tags=["reviews"], redirect_slashes=False)

_OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")


def _is_flagged(text: str | None) -> bool:
    """Call OpenAI Moderation API; fails open if API is unavailable."""
    if not text or not _OPENAI_KEY:
        return False
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/moderations",
            headers={"Authorization": f"Bearer {_OPENAI_KEY}"},
            json={"input": text},
            timeout=5.0,
        )
        resp.raise_for_status()
        return resp.json()["results"][0]["flagged"]
    except Exception:
        return False


def _build_review_out(review: Review) -> ReviewOut:
    client_name = None
    if review.client and review.client.user:
        u: User = review.client.user
        client_name = f"{u.first_name} {u.last_name}".strip() or None
    return ReviewOut(
        review_id=review.review_id,
        coach_id=review.coach_id,
        rating=review.rating,
        description=review.description,
        created_at=review.created_at,
        client_name=client_name,
    )


@router.get("/{coach_id}/reviews/can-review")
def can_review(
    coach_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    client = current_user.client
    if not client:
        return {"allowed": False}
    contract = (
        db.query(ClientCoach)
        .filter(
            ClientCoach.client_id == client.client_id,
            ClientCoach.coach_id == coach_id,
            ClientCoach.status_name.in_(["Active", "Terminated"]),
        )
        .first()
    )
    return {"allowed": bool(contract)}


@router.get("/{coach_id}/reviews/mine", response_model=ReviewOut | None)
def get_my_review_for_coach(
    coach_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    client = current_user.client
    if not client:
        return None

    review = (
        db.query(Review)
        .filter(
            Review.client_id == client.client_id,
            Review.coach_id == coach_id,
        )
        .first()
    )
    if not review:
        return None
    return _build_review_out(review)


@router.get("/{coach_id}/reviews", response_model=list[ReviewOut])
def get_coach_reviews(
    coach_id: int,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(Review)
        .filter(Review.coach_id == coach_id)
        .order_by(Review.created_at.desc())
    )
    if limit:
        query = query.limit(limit)
    return [_build_review_out(r) for r in query.all()]


@router.post("/{coach_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def post_review(
    coach_id: int,
    body: ReviewIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    client = current_user.client
    if not client:
        raise HTTPException(status_code=404, detail="Client profile not found.")

    contract = (
        db.query(ClientCoach)
        .filter(
            ClientCoach.client_id == client.client_id,
            ClientCoach.coach_id == coach_id,
            ClientCoach.status_name.in_(["Active", "Terminated"]),
        )
        .first()
    )
    if not contract:
        raise HTTPException(
            status_code=403,
            detail="You can only review a coach you have or had a contract with.",
        )

    existing = (
        db.query(Review)
        .filter(Review.client_id == client.client_id, Review.coach_id == coach_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="You have already reviewed this coach.")

    if _is_flagged(body.description):
        raise HTTPException(
            status_code=422,
            detail="Your review contains content that violates our community guidelines.",
        )

    coach = db.query(Coach).filter(Coach.coach_id == coach_id).first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found.")

    review = Review(
        client_id=client.client_id,
        coach_id=coach_id,
        rating=body.rating,
        description=body.description,
    )
    db.add(review)
    db.flush()

    notify(db, coach.user_id, f"You received a new {body.rating}-star review.")
    db.commit()
    db.refresh(review)
    return _build_review_out(review)


@router.put("/{coach_id}/reviews/{review_id}", response_model=ReviewOut)
def update_review(
    coach_id: int,
    review_id: int,
    body: ReviewIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    review = db.query(Review).filter(Review.review_id == review_id).first()
    if not review or review.coach_id != coach_id:
        raise HTTPException(status_code=404, detail="Review not found.")

    client = current_user.client
    if not client or review.client_id != client.client_id:
        raise HTTPException(status_code=403, detail="You can only edit your own reviews.")

    if _is_flagged(body.description):
        raise HTTPException(
            status_code=422,
            detail="Your review contains content that violates our community guidelines.",
        )

    review.rating = body.rating
    review.description = body.description
    review.last_updated = datetime.now(timezone.utc)
    db.commit()
    db.refresh(review)
    return _build_review_out(review)


@router.delete("/{coach_id}/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    coach_id: int,
    review_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    review = db.query(Review).filter(Review.review_id == review_id).first()
    if not review or review.coach_id != coach_id:
        raise HTTPException(status_code=404, detail="Review not found.")

    client = current_user.client
    if not client or review.client_id != client.client_id:
        raise HTTPException(status_code=403, detail="You can only delete your own reviews.")

    db.delete(review)
    db.commit()
