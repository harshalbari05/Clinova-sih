"""Clinical Summary Service for Step 9: AI Clinical Summary & Physician Review.

Orchestrates:
- Multi-source clinical context assembly
- AI-drafted pre-consultation summary generation
- Guaranteed deterministic fallback synthesis
- Strict physician review workflows (edit, confirm, reject)
- Separation of AI draft vs. clinician edits
- Multi-tenant role authorization (patients read-only, clinicians can review)
- Promotion of consultation and timeline verification statuses
- Complete audit logging of all summary actions
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.consultation import Consultation
from app.models.hospital_user import HospitalUser
from app.models.patient import Patient
from app.models.summary import Summary
from app.models.timeline_event import TimelineEvent
from app.models.user import User
from app.schemas.summary import (
    SummaryConfirmRequest,
    SummaryEditRequest,
    SummaryRejectRequest,
    SummaryStatus,
)
from app.schemas.timeline import TimelineVerificationStatus
from app.summary.context_assembler import context_assembler
from app.summary.generator import clinical_summary_generator

logger = logging.getLogger(__name__)


class ClinicalSummaryService:
    """Service managing clinical summary drafts and physician review lifecycle."""

    async def get_or_generate_summary(
        self,
        db: AsyncSession,
        consultation_id: uuid.UUID,
        user: User,
        force_rebuild: bool = False,
    ) -> Summary:
        """Retrieve existing summary or generate a new AI draft if none exists.

        If force_rebuild is True, discards previous unconfirmed draft and generates fresh.
        """
        consultation = await self.authorize_summary_access(
            db, user, consultation_id, require_clinician=False
        )

        # Check for existing summary
        s_stmt = (
            select(Summary)
            .where(Summary.consultation_id == consultation_id)
            .order_by(Summary.version.desc())
            .limit(1)
        )
        existing = (await db.execute(s_stmt)).scalar_one_or_none()

        if existing is not None and not force_rebuild:
            return existing

        # Assemble clinical context
        context = await context_assembler.assemble_context(db, consultation_id)

        # Generate draft summary
        summary_text, structured_dict = await clinical_summary_generator.generate_summary(
            context
        )

        if existing is not None and existing.status == SummaryStatus.DRAFT.value:
            # Update existing draft
            existing.summary_text = summary_text
            existing.structured_summary = structured_dict
            existing.ai_draft_text = summary_text
            existing.version += 1
            summary = existing
        else:
            new_version = (existing.version + 1) if existing else 1
            summary = Summary(
                consultation_id=consultation_id,
                summary_text=summary_text,
                structured_summary=structured_dict,
                generated_by="Clinova AI",
                version=new_version,
                status=SummaryStatus.DRAFT.value,
                ai_draft_text=summary_text,
            )
            db.add(summary)

        await db.flush()
        await db.refresh(summary)

        # Audit log
        audit = AuditLog(
            user_id=user.id,
            action="summary_generated",
            entity_type="consultation",
            entity_id=str(consultation_id),
            metadata_json={
                "summary_id": str(summary.id),
                "version": summary.version,
                "status": summary.status,
                "force_rebuild": force_rebuild,
            },
        )
        db.add(audit)
        await db.commit()
        await db.refresh(summary)
        return summary

    async def get_summary(
        self,
        db: AsyncSession,
        consultation_id: uuid.UUID,
        user: User,
    ) -> Summary:
        """Retrieve the latest summary for a consultation (auto-generating if absent)."""
        await self.authorize_summary_access(
            db, user, consultation_id, require_clinician=False
        )

        s_stmt = (
            select(Summary)
            .where(Summary.consultation_id == consultation_id)
            .order_by(Summary.version.desc())
            .limit(1)
        )
        summary = (await db.execute(s_stmt)).scalar_one_or_none()

        if summary is None:
            summary = await self.get_or_generate_summary(
                db, consultation_id, user, force_rebuild=False
            )

        return summary

    async def edit_summary(
        self,
        db: AsyncSession,
        consultation_id: uuid.UUID,
        user: User,
        payload: SummaryEditRequest,
    ) -> Summary:
        """Allow an authorized clinician to edit the draft summary.

        Preserves the original AI draft in ai_draft_text and increments version.
        Patients are strictly prohibited from calling this method.
        """
        await self.authorize_summary_access(
            db, user, consultation_id, require_clinician=True
        )

        s_stmt = (
            select(Summary)
            .where(Summary.consultation_id == consultation_id)
            .order_by(Summary.version.desc())
            .limit(1)
        )
        summary = (await db.execute(s_stmt)).scalar_one_or_none()

        if summary is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clinical summary not found.",
            )

        if summary.status == SummaryStatus.REJECTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit a rejected summary. Generate a new draft instead.",
            )

        # Apply edits
        if payload.summary_text is not None:
            summary.summary_text = payload.summary_text
        if payload.structured_summary is not None:
            summary.structured_summary = payload.structured_summary
        if payload.clinician_notes is not None:
            summary.clinician_notes = payload.clinician_notes

        summary.version += 1

        # Audit log
        audit = AuditLog(
            user_id=user.id,
            action="summary_edited",
            entity_type="consultation",
            entity_id=str(consultation_id),
            metadata_json={
                "summary_id": str(summary.id),
                "version": summary.version,
                "edited_by": str(user.id),
            },
        )
        db.add(audit)
        await db.commit()
        await db.refresh(summary)
        return summary

    async def confirm_summary(
        self,
        db: AsyncSession,
        consultation_id: uuid.UUID,
        user: User,
        payload: SummaryConfirmRequest,
    ) -> Summary:
        """Allow an authorized clinician to confirm and finalize the clinical summary.

        Sets status='confirmed', records reviewer ID and timestamp, promotes consultation
        status to 'reviewed', and optionally upgrades consultation timeline events to
        CLINICIAN_VERIFIED.
        """
        consultation = await self.authorize_summary_access(
            db, user, consultation_id, require_clinician=True
        )

        s_stmt = (
            select(Summary)
            .where(Summary.consultation_id == consultation_id)
            .order_by(Summary.version.desc())
            .limit(1)
        )
        summary = (await db.execute(s_stmt)).scalar_one_or_none()

        if summary is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clinical summary not found.",
            )

        if summary.status == SummaryStatus.REJECTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot confirm a rejected summary. Generate a new draft instead.",
            )

        # Finalize summary
        now = datetime.now(timezone.utc)
        summary.status = SummaryStatus.CONFIRMED.value
        summary.reviewed_by_id = user.id
        summary.reviewed_at = now

        if payload.clinician_notes is not None:
            summary.clinician_notes = payload.clinician_notes

        # Promote consultation status to 'reviewed'
        consultation.status = "reviewed"

        # Upgrade timeline events if requested
        if payload.confirm_timeline_events:
            t_stmt = (
                update(TimelineEvent)
                .where(
                    (TimelineEvent.consultation_id == consultation_id)
                    | (TimelineEvent.patient_id == consultation.patient_id)
                )
                .values(
                    verification_status=TimelineVerificationStatus.CLINICIAN_VERIFIED.value
                )
            )
            await db.execute(t_stmt)

        # Audit log
        audit = AuditLog(
            user_id=user.id,
            action="summary_confirmed",
            entity_type="consultation",
            entity_id=str(consultation_id),
            metadata_json={
                "summary_id": str(summary.id),
                "version": summary.version,
                "reviewed_by": str(user.id),
                "confirmed_at": now.isoformat(),
            },
        )
        db.add(audit)
        await db.commit()
        await db.refresh(summary)
        return summary

    async def reject_summary(
        self,
        db: AsyncSession,
        consultation_id: uuid.UUID,
        user: User,
        payload: SummaryRejectRequest,
    ) -> Summary:
        """Allow an authorized clinician to reject/discard the AI draft summary."""
        await self.authorize_summary_access(
            db, user, consultation_id, require_clinician=True
        )

        s_stmt = (
            select(Summary)
            .where(Summary.consultation_id == consultation_id)
            .order_by(Summary.version.desc())
            .limit(1)
        )
        summary = (await db.execute(s_stmt)).scalar_one_or_none()

        if summary is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clinical summary not found.",
            )

        now = datetime.now(timezone.utc)
        summary.status = SummaryStatus.REJECTED.value
        summary.reviewed_by_id = user.id
        summary.reviewed_at = now
        summary.rejection_reason = payload.reason

        # Audit log
        audit = AuditLog(
            user_id=user.id,
            action="summary_rejected",
            entity_type="consultation",
            entity_id=str(consultation_id),
            metadata_json={
                "summary_id": str(summary.id),
                "rejected_by": str(user.id),
                "reason": payload.reason,
            },
        )
        db.add(audit)
        await db.commit()
        await db.refresh(summary)
        return summary

    async def authorize_summary_access(
        self,
        db: AsyncSession,
        user: User,
        consultation_id: uuid.UUID,
        require_clinician: bool = False,
    ) -> Consultation:
        """Enforces multi-tenant authorization for consultation summary access.

        Rules:
        - Consultation must exist, else return 404.
        - Patient: Can view summaries for their own consultation.
                   CANNOT edit, confirm, or reject (returns 403).
        - Hospital User: Must belong to the hospital holding the consultation.
                         Cross-hospital access returns safe 404.
                         Must have clinician role (doctor, hospital_staff, hospital_admin)
                         if require_clinician is True.
        - Any unauthorized user returns safe 404 (preventing consultation probing).
        """
        # 1. Fetch consultation
        c_stmt = select(Consultation).where(Consultation.id == consultation_id)
        consultation = (await db.execute(c_stmt)).scalar_one_or_none()

        if consultation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation summary not found.",
            )

        # 2. Check if caller is a Patient
        p_stmt = select(Patient).where(Patient.user_id == user.id)
        patient = (await db.execute(p_stmt)).scalar_one_or_none()

        if patient is not None:
            if consultation.patient_id != patient.id:
                # Different patient -> safe 404
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Consultation summary not found.",
                )
            if require_clinician:
                # Patients cannot edit, confirm, or reject summaries
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only authorized hospital clinicians may modify clinical summary verification state.",
                )
            return consultation

        # 3. Check if caller is a Hospital User
        h_stmt = select(HospitalUser).where(HospitalUser.user_id == user.id)
        hospital_user = (await db.execute(h_stmt)).scalar_one_or_none()

        if hospital_user is not None:
            if hospital_user.role == "receptionist":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Receptionist role is not authorized to access clinical summaries.",
                )
            if consultation.hospital_id != hospital_user.hospital_id:
                # Cross-hospital access -> safe 404
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Consultation summary not found.",
                )
            if require_clinician and hospital_user.role not in [
                "doctor",
                "hospital_staff",
                "hospital_admin",
            ]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Hospital role insufficient for clinical review.",
                )
            return consultation

        # 4. Caller has neither patient profile nor hospital affiliation
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation summary not found.",
        )


clinical_summary_service = ClinicalSummaryService()
