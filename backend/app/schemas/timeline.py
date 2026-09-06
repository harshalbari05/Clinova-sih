"""Pydantic schemas for Step 8: Medical Timeline.

Controlled enums, response models, and query filter schemas for the
structured, chronological clinical timeline.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TimelineEventType(str, enum.Enum):
    """Controlled set of clinical timeline event types."""

    CONSULTATION = "CONSULTATION"
    SYMPTOM = "SYMPTOM"
    DIAGNOSIS_DOCUMENTED = "DIAGNOSIS_DOCUMENTED"
    LAB_TEST = "LAB_TEST"
    LAB_RESULT = "LAB_RESULT"
    IMAGING = "IMAGING"
    PROCEDURE = "PROCEDURE"
    SURGERY = "SURGERY"
    HOSPITAL_ADMISSION = "HOSPITAL_ADMISSION"
    HOSPITAL_DISCHARGE = "HOSPITAL_DISCHARGE"
    MEDICATION = "MEDICATION"
    ALLERGY = "ALLERGY"
    MEDICAL_HISTORY = "MEDICAL_HISTORY"
    FOLLOW_UP = "FOLLOW_UP"
    OTHER = "OTHER"


class TimelineSourceType(str, enum.Enum):
    """Identifies the origin and authority of the timeline event."""

    PATIENT_HISTORY = "PATIENT_HISTORY"
    AI_INTERVIEW = "AI_INTERVIEW"
    MEDICAL_DOCUMENT = "MEDICAL_DOCUMENT"
    OCR_EXTRACTION = "OCR_EXTRACTION"
    CONSULTATION = "CONSULTATION"
    CLINICIAN_ENTERED = "CLINICIAN_ENTERED"


class TimelineDatePrecision(str, enum.Enum):
    """Confidence / precision level of the documented date."""

    EXACT = "EXACT"
    MONTH = "MONTH"
    YEAR = "YEAR"
    APPROXIMATE = "APPROXIMATE"
    UNKNOWN = "UNKNOWN"


class TimelineVerificationStatus(str, enum.Enum):
    """Verification and review state of the clinical event."""

    UNVERIFIED = "UNVERIFIED"
    SOURCE_CONFIRMED = "SOURCE_CONFIRMED"
    CLINICIAN_VERIFIED = "CLINICIAN_VERIFIED"


# ---------------------------------------------------------------------------
# API Schemas
# ---------------------------------------------------------------------------


class TimelineEventResponse(BaseModel):
    """Serialized representation of a single clinical timeline event."""

    id: uuid.UUID
    patient_id: uuid.UUID
    consultation_id: uuid.UUID | None = None
    medical_document_id: uuid.UUID | None = None
    event_type: str
    title: str
    description: str | None = None
    event_date: date | None = None
    date_precision: str
    source_type: str
    source_id: str | None = None
    evidence: str | None = None
    source_page: int | None = None
    verification_status: str
    metadata_: dict[str, Any] | None = Field(
        default=None,
        validation_alias="metadata_",
        serialization_alias="metadata",
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PatientTimelineResponse(BaseModel):
    """Complete chronological medical timeline response for a patient."""

    patient_id: uuid.UUID
    total_events: int
    events: list[TimelineEventResponse]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class TimelineFilterParams(BaseModel):
    """Query parameters to filter and paginate/order the timeline."""

    event_type: str | None = None
    source_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    order: str = Field(default="asc", pattern="^(asc|desc)$")
