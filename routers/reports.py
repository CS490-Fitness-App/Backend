# Handles coach misconduct report submission (UC 5.7): allows authenticated users
# to file a report against a coach they interacted with.

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import get_current_user
from models.review import Report
from models.user import Coach, User

from schemas.review import ReportIn

router = APIRouter(prefix="/coaches", tags=["reports"], redirect_slashes=False)


@router.post("/{coach_id}/report", status_code=status.HTTP_201_CREATED)
def submit_coach_report(
    coach_id: int,
    body: ReportIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    coach = db.query(Coach).filter(Coach.coach_id == coach_id).first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found.")

    reason = (body.reason or "").strip()
    details = (body.details or "").strip()
    if not reason:
        raise HTTPException(status_code=400, detail="A report reason is required.")

    report_text = reason if not details else f"{reason}\n\n{details}"
    now = datetime.now(timezone.utc)

    report = Report(
        reporter_id=current_user.user_id,
        coach_id=coach_id,
        reason=report_text,
        status="Pending",
        created_at=now,
        last_updated=now,
    )
    db.add(report)
    db.commit()

    return {"message": "Report submitted successfully."}
