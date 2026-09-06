"""Base definitions and intermediate representations for timeline builders."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class DraftTimelineEvent:
    """Intermediate candidate timeline event collected by a builder before deduplication and persistence."""

    patient_id: uuid.UUID
    event_type: str
    title: str
    description: str | None = None
    event_date: date | None = None
    date_precision: str = "EXACT"
    source_type: str = "PATIENT_HISTORY"
    source_id: str | None = None
    consultation_id: uuid.UUID | None = None
    medical_document_id: uuid.UUID | None = None
    evidence: str | None = None
    source_page: int | None = None
    verification_status: str = "SOURCE_CONFIRMED"
    metadata: dict[str, Any] = field(default_factory=dict)

    def deduplication_fingerprint(self) -> str:
        """Deterministic fingerprint used to detect duplicate real-world events."""
        norm_title = " ".join(self.title.strip().lower().split())
        date_str = self.event_date.isoformat() if self.event_date else "no_date"
        src_id = str(self.source_id or self.medical_document_id or self.consultation_id or "")
        return f"{self.patient_id}:{self.event_type}:{self.source_type}:{src_id}:{date_str}:{norm_title}"
