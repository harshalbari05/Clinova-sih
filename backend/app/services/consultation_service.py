"""Consultation service layer.

Responsibilities:
- Create a consultation for the authenticated patient.
- List consultations for authenticated patient (newest-first) or hospital staff (OPD queue, FIFO).
- Retrieve a single consultation with ownership/facility enforcement.
- Record explicit patient consent for clinical intake and AI processing.
- Validate referenced hospital exists.

Architecture:
    Endpoint → consultation_service → Models → PostgreSQL
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.consent import Consent
from app.models.consultation import Consultation
from app.models.hospital import Hospital
from app.models.hospital_user import HospitalUser
from app.models.patient import Patient
from app.models.user import User
from app.schemas.consent import ConsentRecordRequest, ConsentResponse
from app.schemas.consultation import (
    ConsultationCreate,
    ConsultationListResponse,
    ConsultationResponse,
)

__all__ = [
    "create_consultation",
    "get_consultation",
    "list_consultations",
    "record_consent",
]


async def _assert_hospital_exists(db: AsyncSession, hospital_id: uuid.UUID) -> Hospital:
    """Verify a hospital record exists; raise HTTP 404 if not."""
    hospital = (
        await db.execute(select(Hospital).where(Hospital.id == hospital_id))
    ).scalar_one_or_none()
    if hospital is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found.",
        )
    return hospital


async def create_consultation(
    db: AsyncSession,
    patient: Patient,
    payload: ConsultationCreate,
) -> ConsultationResponse:
    """Create a new consultation record owned by the authenticated patient.

    patient_id is taken from the authenticated patient object — never from
    client-supplied data — to prevent patient_id injection attacks.
    """
    # Validate hospital exists if provided before creating the consultation
    if payload.hospital_id is not None:
        await _assert_hospital_exists(db, payload.hospital_id)

    consultation = Consultation(
        patient_id=patient.id,  # always from JWT — never from client
        hospital_id=payload.hospital_id,
        chief_complaint=payload.chief_complaint,
        status="initiated",
    )
    db.add(consultation)
    await db.flush()
    await db.refresh(consultation)
    return ConsultationResponse.model_validate(consultation)


async def list_consultations(
    db: AsyncSession,
    user: User,
    status_filter: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> ConsultationListResponse:
    """Return paginated list of consultations for the authenticated user.

    If caller is a Patient:
        Returns only consultations owned by that patient.
        Ordered newest-first (created_at DESC).
    If caller is a Hospital User (doctor, hospital_admin, hospital_staff):
        Returns only consultations belonging to their associated hospital facility.
        Ordered oldest-first (created_at ASC) for OPD queue FIFO discipline.
    If caller has neither association:
        Raises HTTP 403 Forbidden.

    Optional status_filter allows filtering by consultation status (e.g. 'initiated').
    """
    limit = min(limit, 100)

    # 1. Check patient context (patients viewing own history)
    patient_stmt = select(Patient).where(Patient.user_id == user.id)
    patient = (await db.execute(patient_stmt)).scalar_one_or_none()

    if patient is not None and user.role == "patient":
        base_filter = [Consultation.patient_id == patient.id]
        if status_filter:
            base_filter.append(Consultation.status == status_filter)

        count_stmt = select(func.count()).where(*base_filter)
        total: int = (await db.execute(count_stmt)).scalar_one()

        stmt = (
            select(Consultation)
            .where(*base_filter)
            .order_by(Consultation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return ConsultationListResponse(
            items=[ConsultationResponse.model_validate(c) for c in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    # 2. Check hospital staff context (doctors/staff viewing facility queue)
    hu_stmt = select(HospitalUser).where(HospitalUser.user_id == user.id)
    hospital_user = (await db.execute(hu_stmt)).scalar_one_or_none()

    if hospital_user is not None:
        base_filter = [Consultation.hospital_id == hospital_user.hospital_id]
        if status_filter:
            base_filter.append(Consultation.status == status_filter)

        count_stmt = select(func.count()).where(*base_filter)
        total: int = (await db.execute(count_stmt)).scalar_one()

        # For OPD waiting queue, prefer created_at ascending (oldest waiting first)
        stmt = (
            select(Consultation)
            .where(*base_filter)
            .order_by(Consultation.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return ConsultationListResponse(
            items=[ConsultationResponse.model_validate(c) for c in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    # 3. Fallback: If user had patient record but role was not explicitly "patient"
    if patient is not None:
        base_filter = [Consultation.patient_id == patient.id]
        if status_filter:
            base_filter.append(Consultation.status == status_filter)

        count_stmt = select(func.count()).where(*base_filter)
        total = (await db.execute(count_stmt)).scalar_one()

        stmt = (
            select(Consultation)
            .where(*base_filter)
            .order_by(Consultation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return ConsultationListResponse(
            items=[ConsultationResponse.model_validate(c) for c in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have permission to access consultations.",
    )


async def get_consultation(
    db: AsyncSession,
    user: User,
    consultation_id: uuid.UUID,
) -> ConsultationResponse:
    """Retrieve a single consultation, enforcing strict ownership and facility isolation.

    Patients may only access their own consultations.
    Hospital staff may only access consultations affiliated with their facility.
    If not found or not authorized, returns 404 (safe 404, never leaks existence).
    """
    stmt = select(Consultation).where(Consultation.id == consultation_id)
    consultation = (await db.execute(stmt)).scalar_one_or_none()

    if consultation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found.",
        )

    # 1. Patient check
    patient_stmt = select(Patient).where(Patient.user_id == user.id)
    patient = (await db.execute(patient_stmt)).scalar_one_or_none()
    if patient is not None and consultation.patient_id == patient.id:
        return ConsultationResponse.model_validate(consultation)

    # 2. Hospital staff check
    hu_stmt = select(HospitalUser).where(HospitalUser.user_id == user.id)
    hospital_user = (await db.execute(hu_stmt)).scalar_one_or_none()
    if hospital_user is not None and consultation.hospital_id == hospital_user.hospital_id:
        return ConsultationResponse.model_validate(consultation)

    # Safe 404 for unauthorized access (avoids leaking cross-tenant existence)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Consultation not found.",
    )


async def record_consent(
    db: AsyncSession,
    patient: Patient,
    consultation_id: uuid.UUID,
    payload: ConsentRecordRequest,
) -> ConsentResponse:
    """Record explicit patient consent for a consultation encounter.

    Guarantees:
    - Caller must own the consultation (404 otherwise).
    - Hospital users cannot impersonate patient consent.
    - Idempotent: repeated submissions for the same consultation + consent_type
      update the existing consent record with fresh server timestamp instead of
      creating duplicate rows.
    - Authoritative server timestamp (client timestamp not accepted).
    - Audit log entry created.
    """
    # Verify patient ownership of the consultation
    stmt = select(Consultation).where(
        Consultation.id == consultation_id,
        Consultation.patient_id == patient.id,
    )
    consultation = (await db.execute(stmt)).scalar_one_or_none()
    if consultation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found.",
        )

    now = datetime.now(timezone.utc)

    # Check for existing consent for this consultation and consent_type (idempotency)
    consent_stmt = select(Consent).where(
        Consent.consultation_id == consultation.id,
        Consent.consent_type == payload.consent_type,
    )
    existing_consent = (await db.execute(consent_stmt)).scalar_one_or_none()

    if existing_consent is not None:
        existing_consent.granted = payload.consent_given
        existing_consent.version = "v1.0"
        existing_consent.timestamp = now
        consent = existing_consent
    else:
        consent = Consent(
            patient_id=patient.id,
            consultation_id=consultation.id,
            consent_type=payload.consent_type,
            granted=payload.consent_given,
            version="v1.0",
            timestamp=now,
        )
        db.add(consent)

    await db.flush()
    await db.refresh(consent)

    # Record audit log
    audit = AuditLog(
        user_id=patient.user_id,
        action="consultation_consent_recorded",
        entity_type="consultation",
        entity_id=str(consultation.id),
        metadata_json={
            "consent_id": str(consent.id),
            "consent_type": consent.consent_type,
            "granted": consent.granted,
            "version": consent.version,
        },
    )
    db.add(audit)
    await db.commit()
    await db.refresh(consent)

    return ConsentResponse.model_validate(consent)
