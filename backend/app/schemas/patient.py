"""Patient profile Pydantic schemas.

Reuses PatientProfileResponse from auth.py for read operations.
Defines a separate update schema for profile modification.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

# Re-export so consumers can import from one place when dealing with patients.
from app.schemas.auth import PatientProfileResponse as PatientResponse

__all__ = ["PatientProfileUpdate", "PatientResponse"]


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
