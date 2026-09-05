"""Consultation Pydantic schemas.

Derived directly from the Consultation SQLAlchemy model fields:
  id, patient_id, hospital_id, status, chief_complaint,
  started_at, completed_at, created_at, updated_at
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ConsultationCreate",
    "ConsultationListResponse",
    "ConsultationResponse",
]

# Valid status transitions documented here for reference (enforced in service layer).
# initiated → in_progress → completed → reviewed | cancelled
VALID_STATUSES = ("initiated", "in_progress", "completed", "reviewed", "cancelled")


class ConsultationCreate(BaseModel):
    """Payload to start a new consultation.

    patient_id is intentionally absent — it is derived from the authenticated
    JWT to prevent any client-side patient_id injection.
    """

    hospital_id: uuid.UUID
    chief_complaint: str | None = Field(default=None, max_length=2000)

    model_config = ConfigDict(from_attributes=True)


class ConsultationResponse(BaseModel):
    """Full consultation record returned to the patient."""

    id: uuid.UUID
    patient_id: uuid.UUID
    hospital_id: uuid.UUID
    status: str
    chief_complaint: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsultationListResponse(BaseModel):
    """Paginated list of consultations."""

    items: list[ConsultationResponse]
    total: int
    limit: int
    offset: int
