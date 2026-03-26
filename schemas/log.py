# Pydantic schemas for daily surveys, weight logs, goal types, and mood types.
# Used by the logs router to validate wellness check-in data submitted by clients.

from pydantic import BaseModel, ConfigDict


class GoalTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    goal_type_id:   int
    goal_type_name: str


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    goal_id:   int
    goal_type: GoalTypeOut
