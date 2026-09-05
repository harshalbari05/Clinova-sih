"""Clinical history service layer.

Responsibilities:
- Verify consultation ownership (patient → consultation → clinical_history chain).
- Create a clinical history for a consultation.
- Retrieve the clinical history for a consultation.
- Apply partial updates to an existing clinical history.

Security contract:
    The patient_id is NEVER trusted from the client.
    Ownership is established by:
        JWT → authenticated User → Patient → Consultation (patient_id match)
    Only after the consultation's patient_id matches the authenticated
    patient's id is the ClinicalHistory accessible.

Architecture:
    Endpoint → clinical_history_service → Consultation / ClinicalHistory models → PostgreSQL
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinical_history import ClinicalHistory
from app.models.consultation import Consultation
from app.models.patient import Patient
from app.schemas.clinical_history import (
    ClinicalHistoryCreate,
    ClinicalHistoryResponse,
    ClinicalHistoryUpdate,
)

__all__ = [
    "create_clinical_history",
    "get_clinical_history",
    "update_clinical_history",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_owned_consultation(
    db: AsyncSession,
    patient: Patient,
    consultation_id: uuid.UUID,
) -> Consultation:
    """Retrieve a Consultation that belongs to the authenticated patient.

    Returns the ORM object (not a schema) so callers can further query
    related entities (e.g. clinical_history).

    Raises:
        HTTPException 404: If the consultation does not exist OR belongs to
            another patient (deliberately indistinguishable to prevent leakage).
    """
    stmt = select(Consultation).where(
        Consultation.id == consultation_id,
        Consultation.patient_id == patient.id,  # ownership enforced
    )
    consultation = (await db.execute(stmt)).scalar_one_or_none()

    if consultation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found.",
        )
    return consultation


async def _get_history_for_consultation(
    db: AsyncSession,
    consultation_id: uuid.UUID,
) -> ClinicalHistory | None:
    """Return the ClinicalHistory for a consultation, or None if absent."""
    return (
        await db.execute(
            select(ClinicalHistory).where(
                ClinicalHistory.consultation_id == consultation_id
            )
        )
    ).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def get_clinical_history(
    db: AsyncSession,
    patient: Patient,
    consultation_id: uuid.UUID,
) -> ClinicalHistoryResponse:
    """Return the clinical history for a patient-owned consultation.

    Args:
        db: Active async database session.
        patient: Authenticated patient ORM object.
        consultation_id: UUID of the target consultation.

    Returns:
        ClinicalHistoryResponse if the record exists.

    Raises:
        HTTPException 404: Consultation not found / not owned, or no history exists.
    """
    # Verify ownership first
    consultation = await _get_owned_consultation(db, patient, consultation_id)

    history = await _get_history_for_consultation(db, consultation.id)
    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No clinical history found for this consultation.",
        )
    return ClinicalHistoryResponse.model_validate(history)


async def create_clinical_history(
    db: AsyncSession,
    patient: Patient,
    consultation_id: uuid.UUID,
    payload: ClinicalHistoryCreate,
) -> ClinicalHistoryResponse:
    """Create a new clinical history record for a patient-owned consultation.

    The consultation_id is taken from the URL path — never from the request body.
    The patient's ownership of the consultation is verified before creation.

    Args:
        db: Active async database session.
        patient: Authenticated patient ORM object.
        consultation_id: UUID of the target consultation (from URL path).
        payload: Validated ClinicalHistoryCreate payload.

    Returns:
        ClinicalHistoryResponse for the newly created record.

    Raises:
        HTTPException 404: Consultation not found or not owned by patient.
        HTTPException 409: A clinical history already exists for this consultation.
    """
    consultation = await _get_owned_consultation(db, patient, consultation_id)

    # Enforce 1:1 — reject duplicate creation
    existing = await _get_history_for_consultation(db, consultation.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A clinical history already exists for this consultation.",
        )

    history = ClinicalHistory(
        consultation_id=consultation.id,
        chief_complaint=payload.chief_complaint,
        history_of_present_illness=payload.history_of_present_illness,
        past_medical_history=payload.past_medical_history,
        past_surgical_history=payload.past_surgical_history,
        drug_history=payload.drug_history,
        allergy_history=payload.allergy_history,
        family_history=payload.family_history,
        personal_history=payload.personal_history,
        review_of_systems=payload.review_of_systems,
    )
    db.add(history)
    await db.flush()
    await db.refresh(history)
    return ClinicalHistoryResponse.model_validate(history)


async def update_clinical_history(
    db: AsyncSession,
    patient: Patient,
    consultation_id: uuid.UUID,
    payload: ClinicalHistoryUpdate,
) -> ClinicalHistoryResponse:
    """Partially update an existing clinical history record.

    Only fields explicitly provided (non-unset) in the payload are applied.
    Immutable fields (id, consultation_id, created_at) are never modifiable.

    A clinical history MUST already exist — this function does NOT create one.

    Args:
        db: Active async database session.
        patient: Authenticated patient ORM object.
        consultation_id: UUID of the target consultation (from URL path).
        payload: Validated ClinicalHistoryUpdate payload (partial update).

    Returns:
        ClinicalHistoryResponse after applying changes.

    Raises:
        HTTPException 404: Consultation not found, not owned, or no history exists.
    """
    consultation = await _get_owned_consultation(db, patient, consultation_id)

    history = await _get_history_for_consultation(db, consultation.id)
    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No clinical history found for this consultation. Create one first.",
        )

    # Apply only explicitly provided fields (exclude_unset for true partial update)
    changes = payload.model_dump(exclude_unset=True)
    if changes:
        for field, value in changes.items():
            setattr(history, field, value)
        db.add(history)
        await db.flush()
        await db.refresh(history)

    return ClinicalHistoryResponse.model_validate(history)
