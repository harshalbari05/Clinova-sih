"""Timeline builder for AI Clinical Interview sessions and messages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.timeline.builders.base import DraftTimelineEvent
from app.timeline.date_utils import parse_clinical_date

if TYPE_CHECKING:
    from app.models.ai_session import AISession
    from app.models.consultation import Consultation


class AIInterviewTimelineBuilder:
    """Extracts patient-reported clinical timeline events from AI history-taking sessions."""

    @classmethod
    def build_events(
        cls,
        consultation: Consultation,
        ai_sessions: list[AISession],
    ) -> list[DraftTimelineEvent]:
        """Harvest timeline events from AI interview messages and sessions."""
        events: list[DraftTimelineEvent] = []
        patient_id = consultation.patient_id

        for session in ai_sessions:
            if not session.messages:
                continue

            session_date = (
                session.started_at.date()
                if session.started_at
                else (session.created_at.date() if session.created_at else None)
            )

            # Analyze patient messages for explicit clinical declarations (e.g. past diagnosis, surgery)
            for msg in session.messages:
                if msg.sender != "patient" or not msg.message.strip():
                    continue

                content = msg.message.strip()
                lower = content.lower()

                # Case: Patient reports diagnosis during interview
                # e.g., "I was diagnosed with asthma when I was 12"
                if "diagnosed with" in lower or "have a history of" in lower:
                    parsed_date, precision = parse_clinical_date(content)
                    events.append(
                        DraftTimelineEvent(
                            patient_id=patient_id,
                            consultation_id=consultation.id,
                            medical_document_id=None,
                            event_type="MEDICAL_HISTORY",
                            title=f"Patient-Reported History: {content[:50]}",
                            description=f"Patient reports during AI interview: {content}",
                            event_date=parsed_date,
                            date_precision=precision,
                            source_type="AI_INTERVIEW",
                            source_id=str(msg.id),
                            evidence=content,
                            source_page=None,
                            verification_status="UNVERIFIED",
                            metadata={
                                "session_id": str(session.id),
                                "message_id": str(msg.id),
                            },
                        )
                    )

                # Case: Patient reports prior surgery
                elif "surgery" in lower or "operation" in lower or "operated" in lower:
                    parsed_date, precision = parse_clinical_date(content)
                    events.append(
                        DraftTimelineEvent(
                            patient_id=patient_id,
                            consultation_id=consultation.id,
                            medical_document_id=None,
                            event_type="SURGERY",
                            title=f"Patient-Reported Surgery: {content[:50]}",
                            description=f"Patient reports prior surgery during AI interview: {content}",
                            event_date=parsed_date,
                            date_precision=precision,
                            source_type="AI_INTERVIEW",
                            source_id=str(msg.id),
                            evidence=content,
                            source_page=None,
                            verification_status="UNVERIFIED",
                            metadata={
                                "session_id": str(session.id),
                                "message_id": str(msg.id),
                            },
                        )
                    )

        return events
