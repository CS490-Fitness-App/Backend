# Pydantic schemas for chat messages between users.
# Defines the request body for sending a message and the response shape for message history.

from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator


class ChatCreateIn(BaseModel):
    other_user_id: int   # user_id of the other conversation participant


class MessageIn(BaseModel):
    type:     Literal['text', 'exercise_link', 'workout_plan_link', 'survey_snapshot'] = 'text'
    body:     Optional[str]  = None   # required for type='text'
    ref_id:   Optional[int]  = None   # required for exercise_link / workout_plan_link
    snapshot: Optional[dict] = None   # required for survey_snapshot

    @model_validator(mode='after')
    def check_type_fields(self):
        if self.type == 'text' and not self.body:
            raise ValueError('body is required for text messages')
        if self.type in ('exercise_link', 'workout_plan_link') and self.ref_id is None:
            raise ValueError('ref_id is required for link messages')
        if self.type == 'survey_snapshot' and self.snapshot is None:
            raise ValueError('snapshot is required for survey_snapshot messages')
        return self


class MessageOut(BaseModel):
    # sender_name and other computed fields are built manually in the router
    message_id:   int
    chat_id:      int
    sender_id:    int
    sender_name:  str            # "{first_name} {last_name}" resolved from sender relationship
    message_type: str
    body:         Optional[str]
    ref_id:       Optional[int]
    snapshot:     Optional[dict]
    sent_at:      datetime


class ConversationOut(BaseModel):
    # other_user_name is computed in the router — not a direct ORM attribute
    chat_id:         int
    coach_user_id:   int
    client_user_id:  int
    other_user_name: str         # name of the participant who is NOT the caller
    created_at:      datetime
