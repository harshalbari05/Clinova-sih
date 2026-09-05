"""AI Sessions and Messages API endpoints.

Routes:
    POST /api/v1/consultations/{consultation_id}/ai-sessions
        Create a new AI interview session for a consultation.

    GET  /api/v1/ai-sessions/{session_id}
        Retrieve an AI session by ID.

    POST /api/v1/ai-sessions/{session_id}/messages
        Add a patient message to an AI session.
        Also triggers the AI interview service to generate and store
        a follow-up AI response (placeholder until LLM is connected).

    GET  /api/v1/ai-sessions/{session_id}/messages
        List all messages in an AI session (chronological order).

    POST /api/v1/ai-sessions/{session_id}/complete
        Mark an AI session as completed.

Security:
    - All endpoints require a valid Bearer JWT for a patient account.
    - Patient identity comes from the JWT — never from the request body.
    - Session/consultation ownership verified at the service layer.
    - Cross-patient access returns HTTP 404.
"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentPatientDep, DatabaseDep
from app.schemas.ai_message import AIMessageCreate, AIMessageListResponse, AIMessageResponse
from app.schemas.ai_session import AISessionCreate, AISessionResponse
from app.services import ai_interview_service, ai_message_service, ai_session_service

router = APIRouter()


# ---------------------------------------------------------------------------
# AI Session — Creation (nested under consultations)
# ---------------------------------------------------------------------------


@router.post(
    "/consultations/{consultation_id}/ai-sessions",
    response_model=AISessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create AI Interview Session",
    description=(
        "Creates a new AI clinical history interview session for the specified "
        "consultation. The consultation must belong to the authenticated patient. "
        "Multiple sessions per consultation are permitted (e.g., for resuming). "
        "Also stores an opening interview question from the AI (placeholder until "
        "LLM integration). Language defaults to 'English'."
    ),
)
async def create_ai_session(
    consultation_id: uuid.UUID,
    payload: AISessionCreate,
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
) -> AISessionResponse:
    """Create an AI session for the authenticated patient's consultation."""
    _user, patient = current_patient
    session = await ai_session_service.create_ai_session(
        db, patient, consultation_id, payload
    )
    # Store the opening interview question (placeholder — future LLM call)
    await ai_interview_service.start_interview(db=db, session=session)
    return session


# ---------------------------------------------------------------------------
# AI Session — Retrieval and Completion (standalone /ai-sessions prefix)
# ---------------------------------------------------------------------------


@router.get(
    "/ai-sessions/{session_id}",
    response_model=AISessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI Session",
    description=(
        "Returns an AI session by ID. "
        "The session must belong to the authenticated patient. "
        "Returns HTTP 404 if not found or unauthorized."
    ),
)
async def get_ai_session(
    session_id: uuid.UUID,
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
) -> AISessionResponse:
    """Get an AI session owned by the authenticated patient."""
    _user, patient = current_patient
    return await ai_session_service.get_ai_session(db, patient, session_id)


@router.post(
    "/ai-sessions/{session_id}/complete",
    response_model=AISessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete AI Session",
    description=(
        "Marks the AI session as completed and records the completion timestamp. "
        "Only the patient who owns the session may complete it. "
        "Returns HTTP 409 if the session is already in a terminal state "
        "(completed or failed)."
    ),
)
async def complete_ai_session(
    session_id: uuid.UUID,
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
) -> AISessionResponse:
    """Complete an AI session owned by the authenticated patient."""
    _user, patient = current_patient
    return await ai_session_service.complete_ai_session(db, patient, session_id)


# ---------------------------------------------------------------------------
# AI Messages
# ---------------------------------------------------------------------------


@router.post(
    "/ai-sessions/{session_id}/messages",
    response_model=AIMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send Patient Message",
    description=(
        "Adds a patient message to the AI interview session and triggers an "
        "AI follow-up response (placeholder until LLM integration in a future step). "
        "The sender is always set to 'patient' server-side — the client cannot "
        "inject a different sender. Returns the stored patient message."
    ),
)
async def add_patient_message(
    session_id: uuid.UUID,
    payload: AIMessageCreate,
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
) -> AIMessageResponse:
    """Add a patient message; store AI follow-up (placeholder)."""
    _user, patient = current_patient

    # Store the patient's message (sender forced to "patient" server-side)
    patient_msg = await ai_message_service.add_patient_message(
        db, patient, session_id, payload
    )

    # Generate and store the AI follow-up (placeholder — future LLM call)
    await ai_interview_service.process_patient_message(
        db=db,
        patient=patient,
        session_id=session_id,
        patient_message=patient_msg,
    )

    # Return the patient's message (not the AI response)
    return patient_msg


@router.get(
    "/ai-sessions/{session_id}/messages",
    response_model=AIMessageListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Session Messages",
    description=(
        "Returns all messages in the AI session in chronological order "
        "(oldest first). Includes both patient and AI messages. "
        "Supports optional limit and offset query parameters."
    ),
)
async def list_messages(
    session_id: uuid.UUID,
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
    limit: int = Query(default=50, ge=1, le=200, description="Max messages to return."),
    offset: int = Query(default=0, ge=0, description="Messages to skip."),
) -> AIMessageListResponse:
    """List messages for an AI session owned by the authenticated patient."""
    _user, patient = current_patient
    return await ai_message_service.list_messages(db, patient, session_id, limit=limit, offset=offset)
