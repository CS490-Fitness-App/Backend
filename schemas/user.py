# Pydantic schemas for user and client profile data: creation, updates, and API responses.

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id:      int
    email:        str
    first_name:   Optional[str]
    last_name:    Optional[str]
    role:         str
    coach_status: Optional[str]   # populated for coach users only (Pending/Active/Suspended/Rejected)
    created_at:   datetime


class UsersListOut(BaseModel):
    total: int
    users: list[UserAdminOut]
