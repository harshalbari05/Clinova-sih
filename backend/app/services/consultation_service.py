"""Consultation service layer.

Responsibilities:
- Create a consultation for the authenticated patient.
- List all consultations owned by the authenticated patient (paginated).
- Retrieve a single consultation with ownership enforcement.
- Validate referenced hospital exists.

Architecture:
    Endpoint → consultation_service → Consultation/Hospital models → PostgreSQL
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import Consultation
from app.models.hospital import Hospital
from app.models.patient import Patient
from app.schemas.consultation import ConsultationCreate, ConsultationListResponse, ConsultationResponse

__all__ = [
    "create_consultation",
    "get_consultation",
    "list_consultations",
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

    Args:
        db: Active async database session.
        patient: Authenticated patient ORM object (from JWT dependency).
        payload: Validated ConsultationCreate payload.

    Returns:
        ConsultationResponse for the newly created record.

    Raises:
        HTTPException 404: If the referenced hospital_id does not exist.
    """
    # Validate hospital exists before creating the consultation
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
    patient: Patient,
    limit: int = 20,
    offset: int = 0,
) -> ConsultationListResponse:
    """Return paginated list of consultations belonging to the authenticated patient.

    Results are ordered newest-first (created_at DESC).

    Args:
        db: Active async database session.
        patient: Authenticated patient — only their consultations are returned.
        limit: Maximum number of records to return (default 20, max 100).
        offset: Number of records to skip.

    Returns:
        ConsultationListResponse with items, total, limit, offset.
    """
    limit = min(limit, 100)  # cap at 100

    # Total count for the patient
    count_stmt = select(func.count()).where(Consultation.patient_id == patient.id)
    total: int = (await db.execute(count_stmt)).scalar_one()

    # Fetch page
    stmt = (
        select(Consultation)
        .where(Consultation.patient_id == patient.id)
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


async def get_consultation(
    db: AsyncSession,
    patient: Patient,
    consultation_id: uuid.UUID,
) -> ConsultationResponse:
    """Retrieve a single consultation, enforcing strict ownership.

    A patient may only access their own consultations.  If the consultation
    doesn't exist OR belongs to another patient, a 404 is returned — we
    deliberately do not differentiate to avoid leaking existence information.

    Args:
        db: Active async database session.
        patient: Authenticated patient.
        consultation_id: UUID of the requested consultation.

    Returns:
        ConsultationResponse if found and owned by the patient.

    Raises:
        HTTPException 404: If not found or owned by a different patient.
    """
    stmt = select(Consultation).where(
        Consultation.id == consultation_id,
        Consultation.patient_id == patient.id,  # ownership enforced here
    )
    consultation = (await db.execute(stmt)).scalar_one_or_none()

    if consultation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found.",
        )

    return ConsultationResponse.model_validate(consultation)
