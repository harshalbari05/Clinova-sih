"""Pydantic schemas for public hospital directory."""

import uuid

from pydantic import BaseModel, ConfigDict

__all__ = [
    "HospitalDirectoryResponse",
]


class HospitalDirectoryResponse(BaseModel):
    """Public read-only hospital directory entry for patient facility selection."""

    id: uuid.UUID
    name: str
    city: str | None = None
    state: str | None = None

    model_config = ConfigDict(from_attributes=True)
