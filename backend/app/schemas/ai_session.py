"""AI Session Pydantic schemas.

All fields derived directly from the AISession SQLAlchemy model:

    id              UUID (read-only)
    consultation_id UUID (read-only, set from URL path)
    language        String(50), default "English"
    status          String(50), values: initiated | in_progress | completed | failed
    started_at      DateTime | None
    completed_at    DateTime | None
    created_at      DateTime (read-only)
    updated_at      DateTime (read-only)

Note: consultation_id is NOT unique — one consultation supports
multiple AI sessions (e.g., resuming a failed interview).
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AISessionCreate",
    "AISessionResponse",
    "AISessionStatusUpdate",
]

# Valid status values from the model comment
AISessionStatus = Literal["initiated", "in_progress", "completed", "failed"]


class AISessionCreate(BaseModel):
    """Payload to start a new AI interview session for a consultation.

    consultation_id is NOT accepted here; it is derived from the URL path.
    Patient identity comes exclusively from the authenticated Bearer JWT.
    """

    language: str = Field(
        default="English",
        max_length=50,
        description="Language for the interview session, e.g. 'English', 'Hindi', 'Marathi'.",
    )

    model_config = ConfigDict(from_attributes=True)


class AISessionResponse(BaseModel):
    """Full AI session record returned to the client."""

    id: uuid.UUID
    consultation_id: uuid.UUID
    language: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AISessionStatusUpdate(BaseModel):
    """Internal schema used by the service layer to update session status.

    Not directly accepted as a client-facing request body.
    """

    status: AISessionStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
