# Pydantic schemas for exercises, categories, and muscle groups.
# Covers creating and updating exercises in the admin-managed exercise inventory.

from pydantic import BaseModel
from typing import List, Optional


class ExerciseIn(BaseModel):
    name: str
    category_id: int
    experience_level_id: Optional[int] = None
    equipment: Optional[str] = None
    instructions: Optional[str] = None
    tips: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    muscle_group_ids: List[int] = []


class ExerciseLookupOption(BaseModel):
    id: int
    name: str


class ExerciseMetaOut(BaseModel):
    categories: List[ExerciseLookupOption]
    experience_levels: List[ExerciseLookupOption]
    muscle_groups: List[ExerciseLookupOption]


class ExerciseOut(BaseModel):
    exercise_id: int
    name: str
    category_id: int
    image_url: Optional[str] = None
    experience_level_id: Optional[int] = None
    experience_level: Optional[str] = None
    category: str
    equipment: Optional[str] = None
    instructions: Optional[str] = None
    tips: Optional[str] = None
    video_url: Optional[str] = None
    muscle_group_ids: List[int] = []
    muscle_groups: List[str] = []

    model_config = {"from_attributes": True}
