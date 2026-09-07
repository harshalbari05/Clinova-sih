"""Pydantic schemas for patient informed consent tracking."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ConsentRecordRequest",
    "ConsentResponse",
]


class ConsentRecordRequest(BaseModel):
    """Payload to record explicit patient consent for a consultation."""

    consent_given: bool = Field(
        default=True,
        description="Whether patient grants informed consent for clinical intake and AI processing.",
    )
    consent_type: str = Field(
        default="clinical_intake",
        max_length=100,
        description="Type or purpose of consent (e.g., clinical_intake, document_processing).",
    )


class ConsentResponse(BaseModel):
    """Full consent record representation."""

    id: uuid.UUID
    patient_id: uuid.UUID
    consultation_id: uuid.UUID | None = None
    consent_type: str
    granted: bool
    version: str
    timestamp: datetime
    revoked_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
