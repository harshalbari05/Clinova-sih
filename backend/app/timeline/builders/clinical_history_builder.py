"""Timeline builder for ClinicalHistory entities."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from app.timeline.builders.base import DraftTimelineEvent
from app.timeline.date_utils import parse_clinical_date

if TYPE_CHECKING:
    from app.models.clinical_history import ClinicalHistory
    from app.models.consultation import Consultation


def _split_history_items(text: str) -> list[str]:
    """Split comma, semicolon, or newline delimited clinical history notes."""
    # Split by newline, semicolon, or bullet points
    lines = [line.strip() for line in re.split(r"[\n;•]+", text) if line.strip()]
    if not lines:
        return [text.strip()] if text.strip() else []
    return lines


class ClinicalHistoryTimelineBuilder:
    """Extracts historical events from patient-reported ClinicalHistory records."""

    @classmethod
    def build_events(
        cls,
        consultation: Consultation,
        history: ClinicalHistory | None,
    ) -> list[DraftTimelineEvent]:
        """Convert a ClinicalHistory record into DraftTimelineEvent instances."""
        if history is None:
            return []

        events: list[DraftTimelineEvent] = []
        patient_id = consultation.patient_id
        cons_id = consultation.id
        cons_date = (
            consultation.started_at.date()
            if consultation.started_at
            else (consultation.created_at.date() if consultation.created_at else None)
        )

        # 1. Chief Complaint & History of Present Illness -> SYMPTOM event associated with consultation
        if history.chief_complaint or history.history_of_present_illness:
            cc = (history.chief_complaint or "").strip()
            hpi = (history.history_of_present_illness or "").strip()
            title = f"Reported Symptoms: {cc}" if cc else "Reported Present Illness Symptoms"
            desc_parts = []
            if cc:
                desc_parts.append(f"Complaint: {cc}")
            if hpi:
                desc_parts.append(f"History: {hpi}")
            description = " — ".join(desc_parts)

            # Check if HPI mentions a relative onset date, else anchor to consultation date
            hpi_date, hpi_precision = parse_clinical_date(hpi)
            ev_date = hpi_date if hpi_date else cons_date
            precision = hpi_precision if hpi_date else ("EXACT" if cons_date else "UNKNOWN")

            events.append(
                DraftTimelineEvent(
                    patient_id=patient_id,
                    consultation_id=cons_id,
                    medical_document_id=None,
                    event_type="SYMPTOM",
                    title=title,
                    description=description,
                    event_date=ev_date,
                    date_precision=precision,
                    source_type="PATIENT_HISTORY",
                    source_id=str(history.id),
                    evidence=f"Chief complaint: {cc}; HPI: {hpi}",
                    source_page=None,
                    verification_status="UNVERIFIED",
                    metadata={"section": "history_of_present_illness"},
                )
            )

        # 2. Past Surgical History -> SURGERY
        if history.past_surgical_history and history.past_surgical_history.strip():
            items = _split_history_items(history.past_surgical_history)
            for item in items:
                parsed_date, precision = parse_clinical_date(item)
                events.append(
                    DraftTimelineEvent(
                        patient_id=patient_id,
                        consultation_id=cons_id,
                        medical_document_id=None,
                        event_type="SURGERY",
                        title=f"Reported Surgery: {item[:60]}",
                        description=f"Patient-reported surgical history: {item}",
                        event_date=parsed_date,
                        date_precision=precision,
                        source_type="PATIENT_HISTORY",
                        source_id=str(history.id),
                        evidence=item,
                        source_page=None,
                        verification_status="UNVERIFIED",
                        metadata={"section": "past_surgical_history"},
                    )
                )

        # 3. Past Medical History -> MEDICAL_HISTORY
        if history.past_medical_history and history.past_medical_history.strip():
            items = _split_history_items(history.past_medical_history)
            for item in items:
                parsed_date, precision = parse_clinical_date(item)
                events.append(
                    DraftTimelineEvent(
                        patient_id=patient_id,
                        consultation_id=cons_id,
                        medical_document_id=None,
                        event_type="MEDICAL_HISTORY",
                        title=f"Reported Medical History: {item[:60]}",
                        description=f"Patient-reported prior medical condition: {item}",
                        event_date=parsed_date,
                        date_precision=precision,
                        source_type="PATIENT_HISTORY",
                        source_id=str(history.id),
                        evidence=item,
                        source_page=None,
                        verification_status="UNVERIFIED",
                        metadata={"section": "past_medical_history"},
                    )
                )

        # 4. Drug History -> MEDICATION
        if history.drug_history and history.drug_history.strip():
            items = _split_history_items(history.drug_history)
            for item in items:
                parsed_date, precision = parse_clinical_date(item)
                events.append(
                    DraftTimelineEvent(
                        patient_id=patient_id,
                        consultation_id=cons_id,
                        medical_document_id=None,
                        event_type="MEDICATION",
                        title=f"Reported Medication: {item[:60]}",
                        description=f"Patient-reported medication: {item}",
                        event_date=parsed_date,
                        date_precision=precision,
                        source_type="PATIENT_HISTORY",
                        source_id=str(history.id),
                        evidence=item,
                        source_page=None,
                        verification_status="UNVERIFIED",
                        metadata={"section": "drug_history"},
                    )
                )

        # 5. Allergy History -> ALLERGY
        if history.allergy_history and history.allergy_history.strip():
            items = _split_history_items(history.allergy_history)
            for item in items:
                events.append(
                    DraftTimelineEvent(
                        patient_id=patient_id,
                        consultation_id=cons_id,
                        medical_document_id=None,
                        event_type="ALLERGY",
                        title=f"Reported Allergy: {item[:60]}",
                        description=f"Patient-reported allergy: {item}",
                        event_date=None,
                        date_precision="UNKNOWN",
                        source_type="PATIENT_HISTORY",
                        source_id=str(history.id),
                        evidence=item,
                        source_page=None,
                        verification_status="UNVERIFIED",
                        metadata={"section": "allergy_history"},
                    )
                )

        return events
