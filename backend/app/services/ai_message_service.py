"""AI Message service layer.

Responsibilities:
- Add a patient-originated message to an AI session.
- Add a backend-generated AI/system message (not client-callable directly).
- List messages in a session (chronological order, paginated).
- Enforce session ownership before any operation.

Security contract:
    - sender is ALWAYS set server-side.
    - Clients calling the patient message endpoint always get sender="patient".
    - The client's message content is accepted, but their sender value is ignored.
    - Session ownership is verified by joining through AISession → Consultation → patient_id.
    - Cross-patient access returns HTTP 404.

Message ordering: chronological (created_at ASC).
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_message import AIMessage
from app.models.patient import Patient
from app.schemas.ai_message import AIMessageCreate, AIMessageListResponse, AIMessageResponse
from app.services.ai_session_service import get_owned_session

__all__ = [
    "add_patient_message",
    "add_backend_message",
    "list_messages",
]


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def add_patient_message(
    db: AsyncSession,
    patient: Patient,
    session_id: uuid.UUID,
    payload: AIMessageCreate,
) -> AIMessageResponse:
    """Add a patient-originated message to an AI session.

    The sender is ALWAYS set to "patient" server-side — the client cannot
    inject a different sender value.

    Args:
        db: Active async database session.
        patient: Authenticated patient ORM object.
        session_id: UUID of the target AI session (from URL path).
        payload: Validated AIMessageCreate (message + message_type).

    Returns:
        AIMessageResponse for the newly created message.

    Raises:
        HTTPException 404: Session not found or not owned by patient.
        HTTPException 409: Session is in terminal state (completed/failed).
    """
    # Verify ownership (raises 404 if not found or unauthorized)
    session = await get_owned_session(db, patient, session_id)

    if session.status in ("completed", "failed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot add message to an AI session with status '{session.status}'.",
        )

    # Transition to in_progress if still initiated
    if session.status == "initiated":
        session.status = "in_progress"
        if session.started_at is None:
            session.started_at = datetime.now(tz=timezone.utc)
        db.add(session)

    msg = AIMessage(
        ai_session_id=session_id,
        sender="patient",          # always server-controlled — never from client
        message=payload.message,
        message_type=payload.message_type,
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return AIMessageResponse.model_validate(msg)


async def add_backend_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    sender: str,
    message: str,
    message_type: str = "text",
) -> AIMessageResponse:
    """Add a backend-generated message to an AI session.

    This function is called exclusively by backend services (e.g., the future
    AI interview engine). It is NOT exposed as a public API endpoint.

    sender values: "ai" | "system"

    Args:
        db: Active async database session.
        session_id: UUID of the target session.
        sender: "ai" or "system" — identifies the message origin.
        message: Text content of the message.
        message_type: Type of message (default "text").

    Returns:
        AIMessageResponse for the created message.
    """
    msg = AIMessage(
        ai_session_id=session_id,
        sender=sender,
        message=message,
        message_type=message_type,
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return AIMessageResponse.model_validate(msg)


async def list_messages(
    db: AsyncSession,
    patient: Patient,
    session_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
) -> AIMessageListResponse:
    """Return paginated messages for an AI session in chronological order.

    Only messages belonging to a session owned by the authenticated patient
    are returned.

    Args:
        db: Active async database session.
        patient: Authenticated patient ORM object.
        session_id: UUID of the target AI session.
        limit: Maximum records to return (default 50, max 200).
        offset: Records to skip.

    Returns:
        AIMessageListResponse with items ordered by created_at ASC.

    Raises:
        HTTPException 404: Session not found or not owned by patient.
    """
    limit = min(limit, 200)

    # Verify ownership
    await get_owned_session(db, patient, session_id)

    # Total count
    count_stmt = select(func.count()).where(AIMessage.ai_session_id == session_id)
    total: int = (await db.execute(count_stmt)).scalar_one()

    # Fetch page, chronological order
    stmt = (
        select(AIMessage)
        .where(AIMessage.ai_session_id == session_id)
        .order_by(AIMessage.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()

    return AIMessageListResponse(
        items=[AIMessageResponse.model_validate(m) for m in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
