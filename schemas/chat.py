# Pydantic schemas for the flat `chat` table.
# A "conversation" is a derived concept: a unique pair of users who have exchanged messages.
# The synthetic chat_id = min(uid_a, uid_b) * 1_000_000 + max(uid_a, uid_b).

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator


class ChatCreateIn(BaseModel):
    other_user_id:  Optional[int] = None   # user_id of the other participant
    other_coach_id: Optional[int] = None   # coach_id of the other participant (convenience)

    @model_validator(mode='after')
    def check_one(self):
        if self.other_user_id is None and self.other_coach_id is None:
            raise ValueError('other_user_id or other_coach_id is required')
        return self


class MessageIn(BaseModel):
    type:  str = 'text'          # only 'text' is supported; kept for frontend compatibility
    body:  Optional[str] = None  # the message text

    @model_validator(mode='after')
    def check_body(self):
        if not self.body:
            raise ValueError('body is required')
        return self


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id:   int
    chat_id:      int            # synthetic: min(uid_a, uid_b) * 1_000_000 + max(uid_a, uid_b)
    sender_id:    int
    sender_name:  str
    message_type: str
    body:         Optional[str]  # maps from Chat.message
    ref_id:       Optional[int]  # always None (not stored in DB)
    snapshot:     Optional[dict] # always None (not stored in DB)
    sent_at:      datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chat_id:         int         # synthetic conversation identifier
    coach_user_id:   int
    client_user_id:  int
    other_user_name: str
    created_at:      datetime    # sent_at of the most recent message in the conversation
