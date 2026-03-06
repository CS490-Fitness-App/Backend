# Pydantic schemas for coach profile data, certifications, availability slots, and client-coach relationships.
# Used by the coaches router to validate inputs and format responses.

from pydantic import BaseModel, ConfigDict
from typing import Optional

# schema for displaying coach information (in directory or browsing page)
class CoachOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # optional features in case coach hasn't set them
    coach_id:            int
    first_name:          str
    last_name:           str
    profile_picture:     Optional[str]
    bio:                 Optional[str]
    hourly_rate:         float
    is_trainer:          bool
    is_nutritionist:     bool
    years_of_experience: Optional[int]
    accepting_clients:   bool
    avg_rating:          Optional[float]
    specialties:         list[str]
    certifications:      list[str]
    availability:        list[str]
