"""Patient profile Pydantic schemas.

Reuses PatientProfileResponse from auth.py for read operations.
Defines a separate update schema for profile modification.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

# Re-export so consumers can import from one place when dealing with patients.
from app.schemas.auth import PatientProfileResponse as PatientResponse

__all__ = ["ActiveVisitResponse", "PatientProfileUpdate", "PatientResponse"]


class PatientProfileUpdate(BaseModel):
    """Partial update schema for authenticated patient's own profile.

    All fields are optional — only supplied fields will be applied.
    Immutable fields (id, user_id, created_at) are never accepted here.
    """

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=50)
    abha_id: str | None = Field(default=None, max_length=100)
    address: str | None = None
    emergency_contact: str | None = Field(default=None, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class ActiveVisitResponse(BaseModel):
    """Real-time active hospital visit and token information for a patient."""

    has_active_visit: bool
    consultation_id: uuid.UUID | None = None
    hospital_id: uuid.UUID | None = None
    hospital_name: str | None = None
    department: str | None = None
    token_number: int | None = None
    now_serving: int | None = None
    people_ahead: int = 0
    status: str | None = None  # "waiting", "in_progress", "completed"
    checkin_time: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

