"""AI Message Pydantic schemas.

All fields derived directly from the AIMessage SQLAlchemy model:

    id              UUID (read-only)
    ai_session_id   UUID (read-only, set from URL path)
    sender          String(50), NOT NULL — values: patient | ai | system
    message         Text, NOT NULL
    message_type    String(50), default "text" — values: text | voice_transcript | structured_answer
    created_at      DateTime (read-only, no updated_at on AIMessage)

Security note:
    Clients may only submit messages with sender="patient".
    Messages with sender="ai" or sender="system" are created
    exclusively by backend services — never by the client.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = [
    "AIMessageCreate",
    "AIMessageListResponse",
    "AIMessageResponse",
]

# Values from the model comment
AIMessageSender = Literal["patient", "ai", "system"]
AIMessageType = Literal["text", "voice_transcript", "structured_answer"]


class AIMessageCreate(BaseModel):
    """Payload for a patient to send a message to their AI interview session.

    Only sender="patient" is accepted from the client.
    The sender field is fixed server-side to "patient" — it is NOT read from
    this schema in the service layer to prevent role spoofing.

    Accepted message_type values: text | voice_transcript | structured_answer
    """

    message: str = Field(
        min_length=1,
        description="The message content from the patient.",
    )
    message_type: AIMessageType = Field(
        default="text",
        description="Type of message: text, voice_transcript, or structured_answer.",
    )
    sender: str | None = Field(
        default="patient",
        description="Sender identity. Only 'patient' or 'user' is allowed.",
    )
    role: str | None = Field(
        default=None,
        description="Sender role. Only 'patient' or 'user' is allowed.",
    )

    @field_validator("sender")
    @classmethod
    def validate_sender(cls, v: str | None) -> str:
        if v is not None and v.lower() not in ("patient", "user"):
            raise ValueError("Clients may not send messages with sender='ai' or 'system'.")
        return "patient"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        if v is not None and v.lower() not in ("patient", "user"):
            raise ValueError("Clients may not spoof 'assistant' or 'system' role.")
        return v

    model_config = ConfigDict(from_attributes=True)


class AIMessageResponse(BaseModel):
    """Single AI message record returned to the client."""

    id: uuid.UUID
    ai_session_id: uuid.UUID
    sender: str
    message: str
    message_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIMessageListResponse(BaseModel):
    """Paginated list of messages in an AI session."""

    items: list[AIMessageResponse]
    total: int
    limit: int
    offset: int
