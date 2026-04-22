# Pydantic schemas for user and client profile data: creation, updates, and API responses.

from typing import Optional
from datetime import date, datetime
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


class ClientProfileOut(BaseModel):
    client_id: int
    DOB: Optional[date]
    height: Optional[int]
    weight: Optional[int]
    goal_weight: Optional[int]
    sex: Optional[str]
    weekly_streak: int
    goals: list[str]


class CoachProfileOut(BaseModel):
    coach_id: int
    gender: Optional[str]
    hourly_rate: float
    bio: Optional[str]
    is_trainer: bool
    is_nutritionist: bool
    years_of_experience: Optional[int]
    max_clients: Optional[int]
    accepting_clients: bool
    status: Optional[str]


class AdminProfileOut(BaseModel):
    admin_id: int


class UserProfileOut(BaseModel):
    user_id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    profile_picture: Optional[str]
    role: str
    created_at: datetime
    last_updated: datetime
    client_profile: Optional[ClientProfileOut] = None
    coach_profile: Optional[CoachProfileOut] = None
    admin_profile: Optional[AdminProfileOut] = None
