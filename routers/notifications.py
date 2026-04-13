# Handles in-app notification endpoints (UC 5.5): listing and dismissing notifications for the current user.
# notify() is a shared helper imported by other routers to create notifications on events.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import get_current_user, require_admin
from models.notification import Notification
from models.user import User
from schemas.notification import NotificationIn, NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"], redirect_slashes=False)


# ── Shared helper ──────────────────────────────────────────────────────────────

def notify(db: Session, user_id: int, message: str) -> Notification:
    """
    Create a notification for a user. Import this in any router that needs to
    trigger a notification — caller is responsible for calling db.commit().
    """
    n = Notification(user_id=user_id, message=message)
    db.add(n)
    return n


# ── Endpoints ──────────────────────────────────────────────────────────────────

# POST /notifications — admin-only internal trigger to create a notification
@router.post("/", response_model=NotificationOut, status_code=201)
def create_notification(
    data: NotificationIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    # validate the target user exists
    target = db.query(User).filter(User.user_id == data.user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target user not found.")

    n = notify(db, user_id=data.user_id, message=data.message)
    db.commit()
    db.refresh(n)
    return NotificationOut(
        notification_id=n.notification_id,
        user_id=n.user_id,
        message=n.message,
        is_read=n.is_read,
        created_at=n.created_at,
    )


# GET /notifications/{user_id}/count — return unread count without marking as read
@router.get("/{user_id}/count")
def get_unread_count(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.user_id != user_id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="You can only view your own notifications.")

    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)
        .count()
    )
    return {"unread_count": count}


# GET /notifications/{user_id} — fetch notifications sorted unread first, then mark all as read
@router.get("/{user_id}", response_model=list[NotificationOut])
def get_notifications(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # only the owner or an admin can view notifications
    if current_user.user_id != user_id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="You can only view your own notifications.")

    # fetch sorted: unread (is_read=False) first, then newest first within each group
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())
        .all()
    )

    # build response before marking as read so is_read values reflect pre-fetch state
    result = [
        NotificationOut(
            notification_id=n.notification_id,
            user_id=n.user_id,
            message=n.message,
            is_read=n.is_read,
            created_at=n.created_at,
        )
        for n in notifications
    ]

    # mark all unread notifications as read
    unread = [n for n in notifications if not n.is_read]
    if unread:
        for n in unread:
            n.is_read = True
        db.commit()

    return result


# DELETE /notifications/{notification_id} — dismiss a notification (own only)
@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    n = db.query(Notification).filter(Notification.notification_id == notification_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found.")

    # only the recipient can delete their own notification
    if n.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own notifications.")

    db.delete(n)
    db.commit()
    return {"message": "Notification deleted."}
