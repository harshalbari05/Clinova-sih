"""Timeline service layer for Clinova Step 8: Medical Timeline.

Coordinates:
- Extraction of draft events across all clinical builders (Consultation, ClinicalHistory,
  AIInterview, Document).
- Deduplication of clinical records without aggressive loss of distinct events.
- Idempotent database persistence and synchronization.
- Filtered and chronologically ordered retrieval.
- Strict multi-tenant patient and hospital authorization checks.
- Audit logging of access and rebuild events.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_session import AISession
from app.models.audit_log import AuditLog
from app.models.clinical_history import ClinicalHistory
from app.models.consultation import Consultation
from app.models.hospital_user import HospitalUser
from app.models.medical_document import MedicalDocument
from app.models.patient import Patient
from app.models.timeline_event import TimelineEvent
from app.models.user import User
from app.schemas.timeline import TimelineFilterParams
from app.timeline.builders import (
    AIInterviewTimelineBuilder,
    ClinicalHistoryTimelineBuilder,
    ConsultationTimelineBuilder,
    DocumentTimelineBuilder,
    DraftTimelineEvent,
)

logger = logging.getLogger(__name__)


def _make_fingerprint(
    patient_id: uuid.UUID,
    event_type: str,
    source_type: str,
    source_id: str | None,
    event_date: date | None,
    title: str,
) -> str:
    """Generate consistent composite key for idempotency matching."""
    norm_title = " ".join(title.strip().lower().split())
    date_str = event_date.isoformat() if event_date else "no_date"
    src_id = source_id or ""
    return f"{patient_id}:{event_type}:{source_type}:{src_id}:{date_str}:{norm_title}"


class TimelineService:
    """Service managing the generation, storage, and retrieval of clinical timeline events."""

    async def build_patient_timeline(
        self,
        db: AsyncSession,
        patient_id: uuid.UUID,
    ) -> list[TimelineEvent]:
        """Harvest, deduplicate, and synchronize timeline events from all structured clinical sources.

        Idempotent: Multiple runs will not generate duplicate database rows.
        """
        # 1. Fetch consultations with clinical history and AI sessions
        c_stmt = (
            select(Consultation)
            .options(
                selectinload(Consultation.hospital),
                selectinload(Consultation.clinical_history),
                selectinload(Consultation.ai_sessions).selectinload(AISession.messages),
            )
            .where(Consultation.patient_id == patient_id)
        )
        consultations = list((await db.execute(c_stmt)).scalars().all())

        # 2. Fetch medical documents with extracted data
        d_stmt = (
            select(MedicalDocument)
            .options(selectinload(MedicalDocument.extracted_data))
            .where(MedicalDocument.patient_id == patient_id)
        )
        documents = list((await db.execute(d_stmt)).scalars().all())

        # 3. Harvest candidate events using modular builders
        draft_events: list[DraftTimelineEvent] = []

        # A. Consultation encounters
        draft_events.extend(ConsultationTimelineBuilder.build_events(consultations))

        # B. Clinical history & AI interview per consultation
        for cons in consultations:
            draft_events.extend(
                ClinicalHistoryTimelineBuilder.build_events(cons, cons.clinical_history)
            )
            draft_events.extend(
                AIInterviewTimelineBuilder.build_events(cons, cons.ai_sessions)
            )

        # C. Medical documents & structured extraction
        draft_events.extend(DocumentTimelineBuilder.build_events(documents))

        # 4. Deduplicate candidate drafts
        unique_drafts: list[DraftTimelineEvent] = []
        seen_draft_fps: set[str] = set()

        for d in draft_events:
            fp = d.deduplication_fingerprint()
            if fp not in seen_draft_fps:
                seen_draft_fps.add(fp)
                unique_drafts.append(d)

        # 5. Fetch existing stored timeline events for patient
        existing_stmt = select(TimelineEvent).where(TimelineEvent.patient_id == patient_id)
        existing_events = list((await db.execute(existing_stmt)).scalars().all())

        existing_map: dict[str, TimelineEvent] = {}
        for ev in existing_events:
            fp = _make_fingerprint(
                ev.patient_id,
                ev.event_type,
                ev.source_type,
                ev.source_id,
                ev.event_date,
                ev.title,
            )
            existing_map[fp] = ev

        # 6. Synchronize: update existing or insert new
        for draft in unique_drafts:
            fp = _make_fingerprint(
                draft.patient_id,
                draft.event_type,
                draft.source_type,
                draft.source_id,
                draft.event_date,
                draft.title,
            )
            if fp in existing_map:
                existing = existing_map[fp]
                # Update details if not manually verified
                if existing.verification_status != "CLINICIAN_VERIFIED":
                    existing.description = draft.description
                    existing.evidence = draft.evidence
                    existing.source_page = draft.source_page
                    existing.metadata_ = draft.metadata
            else:
                new_event = TimelineEvent(
                    id=uuid.uuid4(),
                    patient_id=draft.patient_id,
                    consultation_id=draft.consultation_id,
                    medical_document_id=draft.medical_document_id,
                    event_type=draft.event_type,
                    title=draft.title,
                    description=draft.description,
                    event_date=draft.event_date,
                    date_precision=draft.date_precision,
                    source_type=draft.source_type,
                    source_id=draft.source_id,
                    evidence=draft.evidence,
                    source_page=draft.source_page,
                    verification_status=draft.verification_status,
                    metadata_=draft.metadata,
                )
                db.add(new_event)

        await db.commit()

        # Audit log the rebuild event
        audit = AuditLog(
            user_id=None,
            action="timeline_rebuilt",
            entity_type="patient",
            entity_id=str(patient_id),
            metadata_json={"total_events_synced": len(unique_drafts)},
        )
        db.add(audit)
        await db.commit()

        # Return updated ordered timeline
        return await self._query_events(db, patient_id, TimelineFilterParams())

    async def _query_events(
        self,
        db: AsyncSession,
        patient_id: uuid.UUID,
        filters: TimelineFilterParams,
    ) -> list[TimelineEvent]:
        """Query and sort stored timeline events for a patient."""
        query = select(TimelineEvent).where(TimelineEvent.patient_id == patient_id)

        if filters.event_type:
            query = query.where(TimelineEvent.event_type == filters.event_type.upper().strip())

        if filters.source_type:
            query = query.where(TimelineEvent.source_type == filters.source_type.upper().strip())

        if filters.start_date:
            query = query.where(TimelineEvent.event_date >= filters.start_date)

        if filters.end_date:
            query = query.where(TimelineEvent.event_date <= filters.end_date)

        events = list((await db.execute(query)).scalars().all())

        # Stable in-memory chronological sort:
        # 1. Events with known dates sorted chronologically
        # 2. Events with unknown dates (event_date is None) placed at the end stably
        is_desc = filters.order.lower() == "desc"

        dated_events = [e for e in events if e.event_date is not None]
        undated_events = [e for e in events if e.event_date is None]

        dated_events.sort(
            key=lambda x: (x.event_date, x.created_at, x.id),
            reverse=is_desc,
        )
        undated_events.sort(
            key=lambda x: (x.created_at, x.id),
            reverse=is_desc,
        )

        return dated_events + undated_events

    async def get_patient_timeline(
        self,
        db: AsyncSession,
        patient_id: uuid.UUID,
        filters: TimelineFilterParams | None = None,
    ) -> list[TimelineEvent]:
        """Query patient timeline events with optional filtering and stable chronological ordering."""
        filters = filters or TimelineFilterParams()

        # Check if events already exist; if not, perform initial build once
        count_stmt = (
            select(TimelineEvent)
            .where(TimelineEvent.patient_id == patient_id)
            .limit(1)
        )
        has_events = (await db.execute(count_stmt)).scalar_one_or_none() is not None

        if not has_events:
            p_stmt = select(Patient).where(Patient.id == patient_id)
            p = (await db.execute(p_stmt)).scalar_one_or_none()
            if p:
                return await self.build_patient_timeline(db, patient_id)

        return await self._query_events(db, patient_id, filters)

    async def authorize_patient_timeline_access(
        self,
        db: AsyncSession,
        user: User,
        patient_id: uuid.UUID,
    ) -> Patient:
        """Verify that the caller has authorization to view the patient's timeline.

        Rules:
        - Owning patient is allowed.
        - Hospital user is allowed only if their hospital facility has a consultation with the patient.
        - Unauthorized requests return safe 404 (preventing patient existence probing).
        """
        # 1. Check if patient exists
        p_stmt = select(Patient).where(Patient.id == patient_id)
        target_patient = (await db.execute(p_stmt)).scalar_one_or_none()
        if target_patient is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient timeline not found.",
            )

        # 2. Check if caller is the patient
        if target_patient.user_id == user.id:
            return target_patient

        # 3. Check if caller is a hospital staff member with facility relation
        h_stmt = select(HospitalUser).where(HospitalUser.user_id == user.id)
        h_user = (await db.execute(h_stmt)).scalar_one_or_none()

        if h_user is not None:
            if h_user.role == "receptionist":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Receptionist role is not authorized to access medical timeline.",
                )
            c_stmt = select(Consultation).where(
                Consultation.patient_id == patient_id,
                Consultation.hospital_id == h_user.hospital_id,
            )
            has_relation = (await db.execute(c_stmt)).first() is not None
            if has_relation:
                return target_patient

        # Safe 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient timeline not found.",
        )

    async def authorize_consultation_timeline_access(
        self,
        db: AsyncSession,
        user: User,
        consultation_id: uuid.UUID,
    ) -> Consultation:
        """Authorize access to timeline scoped by a consultation.

        Rules:
        - Patient must own the consultation.
        - Hospital staff must belong to the facility holding the consultation.
        - Cross-patient or cross-hospital access returns safe 404.
        """
        c_stmt = select(Consultation).where(Consultation.id == consultation_id)
        consultation = (await db.execute(c_stmt)).scalar_one_or_none()

        if consultation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation timeline not found.",
            )

        # Check Patient ownership
        p_stmt = select(Patient).where(Patient.user_id == user.id)
        patient = (await db.execute(p_stmt)).scalar_one_or_none()

        if patient is not None:
            if consultation.patient_id != patient.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Consultation timeline not found.",
                )
            return consultation

        # Check Hospital staff ownership
        h_stmt = select(HospitalUser).where(HospitalUser.user_id == user.id)
        h_user = (await db.execute(h_stmt)).scalar_one_or_none()

        if h_user is not None:
            if h_user.role == "receptionist":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Receptionist role is not authorized to access medical timeline.",
                )
            if consultation.hospital_id != h_user.hospital_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Consultation timeline not found.",
                )
            return consultation

        # Otherwise safe 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation timeline not found.",
        )


timeline_service = TimelineService()
