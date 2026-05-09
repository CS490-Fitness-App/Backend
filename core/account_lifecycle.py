from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.user import User
from models.workout import Workout


def delete_user_account(db: Session, user_id: int) -> None:
    db.query(Workout).filter(Workout.creator_id == user_id).delete(synchronize_session=False)
    db.query(Workout).filter(Workout.assigned_to == user_id).update(
        {Workout.assigned_to: None}, synchronize_session=False
    )
    db.query(User).filter(User.user_id == user_id).delete(synchronize_session=False)
    db.commit()


def purge_if_self_deactivation_expired(db: Session, user: User | None) -> bool:
    if not user:
        return False
    if user.is_active is not False:
        return False
    if user.deactivated_by_admin:
        return False
    if not user.scheduled_deletion_at:
        return False
    if user.scheduled_deletion_at > datetime.now(timezone.utc):
        return False

    delete_user_account(db, user.user_id)
    return True
