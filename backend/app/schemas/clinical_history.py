"""Clinical history Pydantic schemas.

All fields are derived directly from the ClinicalHistory SQLAlchemy model:

    id                          UUID (read-only)
    consultation_id             UUID (read-only, set server-side)
    chief_complaint             Text | None
    history_of_present_illness  Text | None
    past_medical_history        Text | None
    past_surgical_history       Text | None
    drug_history                Text | None
    allergy_history             Text | None
    family_history              Text | None
    personal_history            Text | None
    review_of_systems           Text | None
    created_at                  datetime (read-only)
    updated_at                  datetime (read-only)
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

__all__ = [
    "ClinicalHistoryCreate",
    "ClinicalHistoryResponse",
    "ClinicalHistoryUpdate",
]


class ClinicalHistoryCreate(BaseModel):
    """Payload to create a clinical history record for a consultation.

    All clinical content fields are optional — a record can be created empty
    and filled in progressively (e.g., during an AI interview session).

    consultation_id is NOT accepted here; it is derived from the URL path
    parameter and the authenticated patient's ownership of that consultation.
    """

    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    past_medical_history: str | None = None
    past_surgical_history: str | None = None
    drug_history: str | None = None
    allergy_history: str | None = None
    family_history: str | None = None
    personal_history: str | None = None
    review_of_systems: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ClinicalHistoryUpdate(BaseModel):
    """Partial update schema for an existing clinical history record.

    Only fields that are explicitly provided (non-unset) will be applied.
    Immutable fields (id, consultation_id, created_at) are never accepted.
    """

    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    past_medical_history: str | None = None
    past_surgical_history: str | None = None
    drug_history: str | None = None
    allergy_history: str | None = None
    family_history: str | None = None
    personal_history: str | None = None
    review_of_systems: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ClinicalHistoryResponse(BaseModel):
    """Full clinical history record returned to the client."""

    id: uuid.UUID
    consultation_id: uuid.UUID
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    past_medical_history: str | None = None
    past_surgical_history: str | None = None
    drug_history: str | None = None
    allergy_history: str | None = None
    family_history: str | None = None
    personal_history: str | None = None
    review_of_systems: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
