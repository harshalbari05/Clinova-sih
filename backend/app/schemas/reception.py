"""Reception and patient registration Pydantic schemas.

Strict privacy rules:
- QR lookup and registration schemas return ONLY registration-safe demographic fields.
- NEVER return or expose:
    * clinical summaries
    * clinical history
    * interview transcripts
    * medical documents / reports
    * OCR extracted data
    * medications or allergies
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AdvanceQueueRequest",
    "AdvanceQueueResponse",
    "ConfirmRegistrationRequest",
    "DepartmentQueueResponse",
    "DepartmentsListResponse",
    "ManualRegistrationRequest",
    "QRLookupRequest",
    "QueueEntry",
    "RegistrationResponse",
    "SafePatientLookupResponse",
]


class QRLookupRequest(BaseModel):
    """Payload to scan or look up a patient via Clinova QR code."""

    qr_code: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Raw QR code data, e.g. CLINOVA:PATIENT:{uuid}",
    )


class SafePatientLookupResponse(BaseModel):
    """Safe demographic profile returned to the hospital receptionist.

    Strictly devoid of any clinical history, AI summary, or medical data.
    """

    patient_id: uuid.UUID
    full_name: str
    date_of_birth: date | None = None
    age: int | None = None
    gender: str | None = None
    phone: str | None = None
    abha_id: str | None = None
    blood_group: str | None = None
    has_active_intake: bool = False
    active_consultation_id: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class ConfirmRegistrationRequest(BaseModel):
    """Payload to complete patient registration for a hospital visit."""

    patient_id: uuid.UUID
    department: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Assigned OPD department (e.g. General Medicine)",
    )
    consultation_id: uuid.UUID | None = Field(
        default=None,
        description="Optional ID of pre-existing intake consultation to link to this hospital",
    )


class ManualRegistrationRequest(BaseModel):
    """Payload for manual patient registration when QR scan is unavailable."""

    full_name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=10, max_length=20)
    date_of_birth: date | None = None
    age: int | None = Field(default=None, ge=0, le=130)
    gender: str | None = Field(default=None, max_length=50)
    abha_id: str | None = Field(default=None, max_length=100)
    department: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Assigned OPD department",
    )
    chief_complaint: str | None = Field(
        default="Walk-in OPD Registration",
        max_length=2000,
    )


class RegistrationResponse(BaseModel):
    """Confirmation record returned upon successful hospital visit registration."""

    consultation_id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str
    hospital_id: uuid.UUID
    hospital_name: str
    department: str
    token_number: int
    status: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartmentsListResponse(BaseModel):
    """Available OPD departments for the hospital facility."""

    departments: list[str]


class QueueEntry(BaseModel):
    """Non-clinical operational record of a patient in a department queue."""

    token_number: int
    token: int | None = None  # Alias for ease of use in UI clients
    patient_display_name: str
    department: str
    status: str  # "waiting", "in_progress", "completed"
    position: int  # 1-indexed queue position among waiting patients
    consultation_id: uuid.UUID
    checkin_time: datetime
    chief_complaint: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DepartmentQueueResponse(BaseModel):
    """Real-time operational OPD queue for a hospital department."""

    hospital_id: uuid.UUID
    hospital_name: str
    department: str
    now_serving: int | None = None
    waiting_count: int = 0
    entries: list[QueueEntry] = []


class AdvanceQueueRequest(BaseModel):
    """Request to advance a department queue to the next patient."""

    department: str = Field(..., min_length=2, max_length=100)


class AdvanceQueueResponse(BaseModel):
    """Result of advancing the department queue."""

    department: str
    previous_token: int | None = None
    now_serving: int | None = None
    waiting_count: int
    message: str

