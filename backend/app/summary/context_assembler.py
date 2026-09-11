"""Context Assembler for Clinical Summary Generation.

Gathers all clinical facts across:
- Patient Profile & Demographics
- Consultation Details
- AI Interview Sessions & Turns
- Prior Structured Clinical History
- Uploaded Medical Documents & Structured Extractions
- Red Flag Triage Alerts
- Medical Timeline Highlights
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_message import AIMessage
from app.models.ai_session import AISession
from app.models.alert import Alert
from app.models.clinical_history import ClinicalHistory
from app.models.consultation import Consultation
from app.models.extracted_data import ExtractedData
from app.models.medical_document import MedicalDocument
from app.models.patient import Patient
from app.models.timeline_event import TimelineEvent

logger = logging.getLogger(__name__)


class ClinicalContextAssembler:
    """Collects and organizes clinical data into a unified context payload."""

    async def assemble_context(
        self,
        db: AsyncSession,
        consultation_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Assemble all patient records and history for a given consultation."""
        # 1. Fetch consultation
        c_stmt = (
            select(Consultation)
            .where(Consultation.id == consultation_id)
            .options(selectinload(Consultation.patient))
        )
        consultation = (await db.execute(c_stmt)).scalar_one_or_none()
        if consultation is None:
            raise ValueError(f"Consultation {consultation_id} not found.")

        patient_id = consultation.patient_id
        patient = consultation.patient

        # 2. Patient details
        patient_data: dict[str, Any] = {
            "id": str(patient.id),
            "name": patient.full_name,
            "gender": patient.gender,
            "dob": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "blood_group": getattr(patient, "blood_group", None),
        }

        consultation_data: dict[str, Any] = {
            "id": str(consultation.id),
            "hospital_id": str(consultation.hospital_id) if consultation.hospital_id else None,
            "chief_complaint": consultation.chief_complaint,
            "status": consultation.status,
            "started_at": (
                consultation.started_at.isoformat() if consultation.started_at else None
            ),
        }

        # 3. Clinical History
        h_stmt = select(ClinicalHistory).where(
            ClinicalHistory.consultation_id == consultation_id
        )
        clinical_history = (await db.execute(h_stmt)).scalar_one_or_none()
        history_data: dict[str, str | None] = {}
        if clinical_history:
            history_data = {
                "chief_complaint": clinical_history.chief_complaint,
                "history_of_present_illness": clinical_history.history_of_present_illness,
                "past_medical_history": clinical_history.past_medical_history,
                "past_surgical_history": clinical_history.past_surgical_history,
                "drug_history": clinical_history.drug_history,
                "allergy_history": clinical_history.allergy_history,
                "family_history": clinical_history.family_history,
                "personal_history": clinical_history.personal_history,
                "review_of_systems": clinical_history.review_of_systems,
            }

        # 4. AI Sessions & Messages
        s_stmt = (
            select(AISession)
            .where(AISession.consultation_id == consultation_id)
            .order_by(AISession.created_at.desc())
        )
        sessions = (await db.execute(s_stmt)).scalars().all()

        interview_data: dict[str, Any] = {"symptoms": [], "turns": []}
        if sessions:
            latest_session = sessions[0]
            # Fetch messages
            m_stmt = (
                select(AIMessage)
                .where(AIMessage.ai_session_id == latest_session.id)
                .order_by(AIMessage.created_at.asc())
            )
            messages = (await db.execute(m_stmt)).scalars().all()

            turns = []
            for i in range(0, len(messages), 2):
                msg_user = messages[i] if i < len(messages) else None
                msg_ai = messages[i + 1] if i + 1 < len(messages) else None
                if msg_user and msg_user.sender == "patient":
                    turns.append({
                        "patient_message": msg_user.message,
                        "ai_response": msg_ai.message if msg_ai else "",
                    })

            interview_data = {
                "session_id": str(latest_session.id),
                "turns": turns,
                "symptoms": [],
            }

        # 5. Triage Alerts
        a_stmt = (
            select(Alert)
            .where(Alert.consultation_id == consultation_id)
            .order_by(Alert.created_at.desc())
        )
        alerts = (await db.execute(a_stmt)).scalars().all()
        alerts_data = [
            {
                "id": str(a.id),
                "alert_type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "status": a.status,
            }
            for a in alerts
        ]

        # 6. Medical Documents & Extractions
        d_stmt = (
            select(MedicalDocument)
            .where(MedicalDocument.patient_id == patient_id)
            .options(selectinload(MedicalDocument.extracted_data))
            .order_by(MedicalDocument.created_at.desc())
        )
        documents = (await db.execute(d_stmt)).scalars().all()
        docs_data = []
        for doc in documents:
            extractions = None
            if doc.extracted_data and doc.extracted_data.extracted_json:
                extractions = doc.extracted_data.extracted_json
            docs_data.append({
                "id": str(doc.id),
                "file_name": doc.file_name,
                "document_type": doc.document_type,
                "extractions": extractions,
            })

        # 7. Timeline Highlights
        t_stmt = (
            select(TimelineEvent)
            .where(TimelineEvent.patient_id == patient_id)
            .order_by(TimelineEvent.event_date.desc().nullslast())
            .limit(10)
        )
        timeline_events = (await db.execute(t_stmt)).scalars().all()
        timeline_data = [
            {
                "id": str(e.id),
                "event_date": e.event_date.isoformat() if e.event_date else None,
                "event_type": e.event_type,
                "title": e.title,
                "verification_status": e.verification_status,
            }
            for e in timeline_events
        ]

        return {
            "patient": patient_data,
            "consultation": consultation_data,
            "clinical_history": history_data,
            "interview": interview_data,
            "alerts": alerts_data,
            "documents": docs_data,
            "timeline_highlights": timeline_data,
        }


context_assembler = ClinicalContextAssembler()
