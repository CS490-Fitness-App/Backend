# Pydantic schemas for exercises, categories, and muscle groups.
# Covers creating and updating exercises in the admin-managed exercise inventory.

from pydantic import BaseModel
from typing import List, Optional


class ExerciseOut(BaseModel):
    exercise_id: int
    name: str
    image_url: Optional[str] = None
    experience_level: Optional[str] = None
    category: str
    equipment: Optional[str] = None
    muscle_groups: List[str] = []

    model_config = {"from_attributes": True}
