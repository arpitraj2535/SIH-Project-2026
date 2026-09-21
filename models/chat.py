from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )
    conversation_id: Optional[int] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, value):
        if not value.strip():
            raise ValueError("Message cannot be empty or contain only spaces")
        return value


class SourceResponse(BaseModel):
    text: str
    standard_id: str
    page: int
    clause: str
    score: float
    source_url: str = ""


class ChatResponse(BaseModel):
    response: str
    confidence: str
    sources: list[SourceResponse]
    conversation_id: int


class MessageResponse(BaseModel):
    id: int
    user_message: str
    assistant_response: str
    created_at: datetime


class ConversationResponse(BaseModel):
    conversation_id: int
    messages: list[MessageResponse]