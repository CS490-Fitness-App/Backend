# Pydantic schemas for login/account creation endpoints used by the frontend auth flow.
# Defines request and response bodies for syncing Auth0 users with local SQL tables.

from typing import Optional, Literal
from pydantic import BaseModel


class AuthRequestIn(BaseModel):
    # Frontend sends signup deatails 
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_picture: Optional[str] = None
    role: Literal["client", "coach", "admin"] = "client"


class AuthUserOut(BaseModel):
    user_id: int
    auth0_sub: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_new_user: bool


class LogoutOut(BaseModel):
    message: str
