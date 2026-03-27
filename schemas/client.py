# Pydantic schemas for client registration (initial survey) request body.

from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional

# schema for Client registration (initial survey) request body
class ClientRegisterIn(BaseModel):
    DOB: Optional[date] = None
    height: Optional[int] = None      # centimetres
    weight: Optional[int] = None      # grams
    goal_weight: Optional[int] = None # grams
    sex: Optional[str] = None
    goal_type_ids: list[int] = []

# schema for displaying Client information on profile
class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    client_id:          int
    first_name:         str
    last_name:          str
    profile_picture:    Optional[str]
    age:                Optional[int]
    height:             Optional[int]
    weight:             Optional[int]
    goal_weight:        Optional[int]
    sex:                Optional[str]
    weekly_streak:      Optional[int]
    goal_types:         Optional[list[str]]