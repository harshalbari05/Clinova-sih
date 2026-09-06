"""Pydantic schemas for Clinova Alert responses.

Used to serialize alerts stored in the database for client and clinical dashboard consumption.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    """Schema representing an individual red-flag alert."""

    id: uuid.UUID
    consultation_id: uuid.UUID
    patient_id: uuid.UUID
    alert_type: str
    severity: str  # low, medium, high, critical
    message: str
    source: str
    status: str  # active, acknowledged, resolved
    created_at: datetime
    updated_at: datetime
    acknowledged_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AlertListResponse(BaseModel):
    """Paginated list of alerts for a consultation or hospital."""

    items: list[AlertResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)
