# Pydantic schemas for coach profile data, certifications, availability slots, and client-coach relationships.
# Used by the coaches router to validate inputs and format responses.

from pydantic import BaseModel, ConfigDict
from typing import Optional
from enum import Enum
from datetime import time

# Enum matching the day_of_week ENUM in Coach_Availability table
class DayOfWeek(str, Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"


# A single availability slot — one row in Coach_Availability
class AvailabilityIn(BaseModel):
    day_of_week: DayOfWeek
    start_time:  time
    end_time:    time


# Input schema for POST /coaches/register
# Captures all data needed to create a coach application across 5 tables
class CoachRegisterIn(BaseModel):
    # Information for coaches table
    gender:              str
    hourly_rate:         float
    is_trainer:          bool
    is_nutritionist:     bool
    bio:                 Optional[str]  = None
    years_of_experience: Optional[int]  = None
    max_clients:         Optional[int]  = None
    accepting_clients:   bool           = True

    # info for related tables
    # list of certification names for Coach_Certifications
    certifications: list[str] = []

    # list of availability slots for Coach_Availability (unique per day)
    availability: list[AvailabilityIn] = []
    
    # Matches session_format column on Coaches table (e.g. 'Virtual', 'In-Person', 'Both')
    session_format: str = "Virtual"
    
    # FK IDs from Goal_Types table → Coach_Specialities junction
    specialty_goal_type_ids: list[int] = []


# schema for displaying coach information (in directory or browsing page)
class CoachOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # optional features in case coach hasn't set them
    coach_id:            int
    first_name:          str
    last_name:           str
    profile_picture:     Optional[str]
    bio:                 Optional[str]
    gender:              str
    hourly_rate:         float
    is_trainer:          bool
    is_nutritionist:     bool
    years_of_experience: Optional[int]
    accepting_clients:   bool
    avg_rating:          Optional[float]
    specialties:         Optional[list[str]]
    certifications:      Optional[list[str]]
    availability:        Optional[list[str]]
