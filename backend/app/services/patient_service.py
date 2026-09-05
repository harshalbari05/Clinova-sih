"""Patient profile service layer.

Responsibilities:
- Return the authenticated patient's profile (read-only pass-through).
- Apply partial profile updates with uniqueness constraint validation.

Architecture:
    Endpoint → patient_service → Patient model → PostgreSQL
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.schemas.patient import PatientProfileUpdate

__all__ = ["get_patient_profile", "update_patient_profile"]


async def get_patient_profile(db: AsyncSession, patient: Patient) -> Patient:
    """Return the patient's own profile record (no DB call needed — already loaded)."""
    return patient


async def update_patient_profile(
    db: AsyncSession,
    patient: Patient,
    update_data: PatientProfileUpdate,
) -> Patient:
    """Apply a partial update to the authenticated patient's profile.

    Validates uniqueness constraints on phone and abha_id before committing.
    Only fields explicitly provided (non-None) are applied.

    Args:
        db: Active async database session.
        patient: The current authenticated patient ORM object.
        update_data: Pydantic model with optional fields to update.

    Returns:
        Refreshed Patient ORM object after commit.

    Raises:
        HTTPException 409: If phone or abha_id already belongs to another record.
    """
    # Collect only the fields the caller actually sent (exclude_unset prevents
    # overwriting existing values with None when the client omits a field).
    changes = update_data.model_dump(exclude_unset=True)

    if not changes:
        # Nothing to update — return existing record as-is.
        return patient

    # --- Uniqueness checks before any writes ---

    if "phone" in changes and changes["phone"] is not None:
        new_phone: str = changes["phone"]
        if new_phone != patient.phone:
            # Check patients table for duplicate phone
            dup = (
                await db.execute(
                    select(Patient).where(
                        Patient.phone == new_phone,
                        Patient.id != patient.id,
                    )
                )
            ).scalar_one_or_none()
            if dup is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A patient with this phone number already exists.",
                )

    if "abha_id" in changes and changes["abha_id"] is not None:
        new_abha: str = changes["abha_id"]
        if new_abha != patient.abha_id:
            dup_abha = (
                await db.execute(
                    select(Patient).where(
                        Patient.abha_id == new_abha,
                        Patient.id != patient.id,
                    )
                )
            ).scalar_one_or_none()
            if dup_abha is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A patient with this ABHA ID already exists.",
                )

    # Apply validated changes to the ORM object
    for field, value in changes.items():
        setattr(patient, field, value)

    db.add(patient)
    await db.flush()
    await db.refresh(patient)
    return patient


async def get_patient_by_id(
    db: AsyncSession, patient_id: uuid.UUID
) -> Patient | None:
    """Retrieve a Patient record by primary key."""
    return (
        await db.execute(select(Patient).where(Patient.id == patient_id))
    ).scalar_one_or_none()
