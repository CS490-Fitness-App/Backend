# Pydantic schema for notification responses.
# Shapes the data returned when listing or dismissing in-app notifications.

from datetime import datetime
from pydantic import BaseModel


class NotificationIn(BaseModel):
    user_id: int
    message: str


class NotificationOut(BaseModel):
    notification_id: int
    user_id:         int
    message:         str
    is_read:         bool
    created_at:      datetime
