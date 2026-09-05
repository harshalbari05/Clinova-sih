"""AI Session service layer.

Responsibilities:
- Create an AI session for a patient-owned consultation.
- Retrieve an AI session by ID (with ownership verification).
- Complete (or update status of) an AI session.
- Shared helper: verify patient owns the session's consultation.

Ownership chain enforced:
    JWT → Authenticated Patient → Consultation (patient_id match) → AISession

Security contract:
    - patient_id is NEVER trusted from the client.
    - consultation_id comes from the URL path.
    - session_id comes from the URL path.
    - A patient cannot access or modify another patient's sessions.
    - Cross-patient access returns HTTP 404 (not 403) to prevent information leakage.

Valid AISession status values (from model comment):
    initiated | in_progress | completed | failed
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_session import AISession
from app.models.consultation import Consultation
from app.models.patient import Patient
from app.schemas.ai_session import AISessionCreate, AISessionResponse

__all__ = [
    "complete_ai_session",
    "create_ai_session",
    "get_ai_session",
    "get_owned_session",
]

# Valid status values from the model
_VALID_STATUSES = frozenset({"initiated", "in_progress", "completed", "failed"})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_owned_consultation(
    db: AsyncSession,
    patient: Patient,
    consultation_id: uuid.UUID,
) -> Consultation:
    """Return a Consultation owned by the authenticated patient.

    Raises HTTP 404 if the consultation does not exist or belongs to
    another patient (deliberately indistinguishable).
    """
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
    return consultation


# ---------------------------------------------------------------------------
# Public: ownership helper used by ai_message_service
# ---------------------------------------------------------------------------


async def get_owned_session(
    db: AsyncSession,
    patient: Patient,
    session_id: uuid.UUID,
) -> AISession:
    """Retrieve an AISession that belongs to the authenticated patient.

    Joins through the consultation to verify the patient_id ownership chain.
    Raises HTTP 404 if not found or unauthorized.
    """
    stmt = (
        select(AISession)
        .join(Consultation, AISession.consultation_id == Consultation.id)
        .where(
            AISession.id == session_id,
            Consultation.patient_id == patient.id,
        )
    )
    session = (await db.execute(stmt)).scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI session not found.",
        )
    return session


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def create_ai_session(
    db: AsyncSession,
    patient: Patient,
    consultation_id: uuid.UUID,
    payload: AISessionCreate,
) -> AISessionResponse:
    """Create a new AI interview session for a patient-owned consultation.

    Multiple sessions per consultation are permitted (e.g., resuming a failed
    interview). The consultation_id comes from the URL path, never the body.

    Args:
        db: Active async database session.
        patient: Authenticated patient ORM object (from JWT).
        consultation_id: UUID from the URL path.
        payload: Validated AISessionCreate (language only).

    Returns:
        AISessionResponse for the newly created session.

    Raises:
        HTTPException 404: Consultation not found or not owned by patient.
    """
    await _get_owned_consultation(db, patient, consultation_id)

    session = AISession(
        consultation_id=consultation_id,
        language=payload.language,
        status="initiated",
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return AISessionResponse.model_validate(session)


async def get_ai_session(
    db: AsyncSession,
    patient: Patient,
    session_id: uuid.UUID,
) -> AISessionResponse:
    """Retrieve a single AI session with ownership verification.

    Args:
        db: Active async database session.
        patient: Authenticated patient ORM object.
        session_id: UUID of the requested session.

    Returns:
        AISessionResponse if found and owned by patient.

    Raises:
        HTTPException 404: Not found or owned by a different patient.
    """
    session = await get_owned_session(db, patient, session_id)
    return AISessionResponse.model_validate(session)


async def complete_ai_session(
    db: AsyncSession,
    patient: Patient,
    session_id: uuid.UUID,
) -> AISessionResponse:
    """Mark an AI session as completed.

    Sets status → "completed" and records completed_at timestamp.
    Only the patient who owns the session may complete it.

    Args:
        db: Active async database session.
        patient: Authenticated patient ORM object.
        session_id: UUID of the session to complete.

    Returns:
        Updated AISessionResponse.

    Raises:
        HTTPException 404: Not found or not owned.
        HTTPException 409: Session is already in a terminal state (completed/failed).
    """
    session = await get_owned_session(db, patient, session_id)

    if session.status in ("completed", "failed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"AI session is already in a terminal state: '{session.status}'.",
        )

    session.status = "completed"
    session.completed_at = datetime.now(tz=timezone.utc)
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return AISessionResponse.model_validate(session)
