"""Timeline builder for Consultation encounters."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from app.timeline.builders.base import DraftTimelineEvent

if TYPE_CHECKING:
    from app.models.consultation import Consultation


class ConsultationTimelineBuilder:
    """Extracts encounter events from patient consultations."""

    @classmethod
    def build_events(cls, consultations: list[Consultation]) -> list[DraftTimelineEvent]:
        """Convert a list of Consultation entities into DraftTimelineEvent records."""
        events: list[DraftTimelineEvent] = []

        for cons in consultations:
            hospital_name = cons.hospital.name if getattr(cons, "hospital", None) else "Hospital"
            title = f"Consultation at {hospital_name}"
            
            desc_parts: list[str] = []
            if cons.chief_complaint:
                desc_parts.append(f"Chief Complaint: {cons.chief_complaint.strip()}")
            desc_parts.append(f"Status: {cons.status}")
            description = " — ".join(desc_parts)

            event_date = None
            if cons.started_at:
                event_date = cons.started_at.date()
            elif cons.created_at:
                event_date = cons.created_at.date()

            evidence = f"Consultation ID: {cons.id}, Status: {cons.status}"
            if cons.chief_complaint:
                evidence += f", Chief Complaint: {cons.chief_complaint}"

            events.append(
                DraftTimelineEvent(
                    patient_id=cons.patient_id,
                    consultation_id=cons.id,
                    medical_document_id=None,
                    event_type="CONSULTATION",
                    title=title,
                    description=description,
                    event_date=event_date,
                    date_precision="EXACT" if event_date else "UNKNOWN",
                    source_type="CONSULTATION",
                    source_id=str(cons.id),
                    evidence=evidence,
                    source_page=None,
                    verification_status="SOURCE_CONFIRMED",
                    metadata={
                        "hospital_id": str(cons.hospital_id) if cons.hospital_id else None,
                        "status": cons.status,
                    },
                )
            )

        return events
