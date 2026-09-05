"""AI interview service — placeholder abstraction for future LLM integration.

This module defines the architectural boundary between the AI session
infrastructure and the AI interview logic (LLM-powered question generation,
answer parsing, clinical history extraction).

Current state (Step 4):
    No real LLM is connected. All functions are stubs that document
    the intended interface and return placeholder responses.

Future state (Step 5+):
    These functions will integrate with an LLM provider
    (e.g., Gemini, OpenAI, Groq) to generate contextual questions
    and extract structured clinical history from patient answers.

Architecture:
    Patient Message
          ↓
    process_patient_message()
          ↓
    generate_next_question()  →  [Future: LLM Provider]
          ↓
    AI Message (sender="ai") stored in DB
          ↓
    [Eventually] extract_to_clinical_history()
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.schemas.ai_message import AIMessageResponse
from app.schemas.ai_session import AISessionResponse
from app.services import ai_message_service, ai_session_service

__all__ = [
    "start_interview",
    "process_patient_message",
    "generate_next_question",
    "complete_interview",
]

# ---------------------------------------------------------------------------
# Placeholder interview questions — will be replaced by LLM in a future step
# ---------------------------------------------------------------------------

_OPENING_QUESTION = (
    "Welcome to your clinical interview. "
    "Could you please describe your main concern or symptom today?"
)
_FALLBACK_QUESTION = (
    "Thank you for sharing that. "
    "Could you tell me more about when this started and what makes it better or worse?"
)


# ---------------------------------------------------------------------------
# Public interface (stubs ready for LLM integration)
# ---------------------------------------------------------------------------


async def start_interview(
    db: AsyncSession,
    session: AISessionResponse,
) -> AIMessageResponse:
    """Begin the AI interview by sending the opening question.

    In a future step, this will:
    - Load the patient's existing clinical history context.
    - Determine which sections are missing.
    - Generate a contextually appropriate opening question via LLM.

    Currently: stores a fixed opening message with sender="ai".

    Args:
        db: Active async database session.
        session: The newly created AISession.

    Returns:
        AIMessageResponse for the stored opening question.
    """
    return await ai_message_service.add_backend_message(
        db=db,
        session_id=session.id,
        sender="ai",
        message=_OPENING_QUESTION,
        message_type="text",
    )


async def process_patient_message(
    db: AsyncSession,
    patient: Patient,
    session_id: uuid.UUID,
    patient_message: AIMessageResponse,
) -> AIMessageResponse:
    """Process a patient's message and generate the next AI response.

    In a future step, this will:
    - Pass the full conversation history and patient message to an LLM.
    - Parse the LLM's response.
    - Detect if a clinical history section has been answered.
    - Call extract_to_clinical_history() if a complete answer is found.
    - Return the LLM's next question/acknowledgement.

    Currently: stores a fixed follow-up question with sender="ai".

    Args:
        db: Active async database session.
        patient: The authenticated patient.
        session_id: UUID of the AI session.
        patient_message: The patient's message that was just stored.

    Returns:
        AIMessageResponse for the stored AI follow-up message.
    """
    # Placeholder — generate_next_question will become an LLM call
    next_question = await generate_next_question(
        patient_message=patient_message.message,
    )
    return await ai_message_service.add_backend_message(
        db=db,
        session_id=session_id,
        sender="ai",
        message=next_question,
        message_type="text",
    )


async def generate_next_question(
    patient_message: str,
) -> str:
    """Generate the next interview question based on the patient's response.

    In a future step, this will call an LLM with:
    - System prompt (clinical interviewer persona, Indian medical context)
    - Conversation history
    - Patient's latest answer
    - Remaining clinical history sections to collect

    Currently: returns a fixed follow-up question.

    Args:
        patient_message: The patient's latest answer text.

    Returns:
        The next question string to be stored as an AI message.
    """
    # TODO (Step 5+): Replace with LLM API call
    # Example future implementation:
    #   response = await llm_client.generate(
    #       system_prompt=CLINICAL_INTERVIEWER_PROMPT,
    #       history=conversation_history,
    #       user_message=patient_message,
    #   )
    #   return response.text
    return _FALLBACK_QUESTION


async def complete_interview(
    db: AsyncSession,
    patient: Patient,
    session_id: uuid.UUID,
) -> AISessionResponse:
    """Complete the AI interview session.

    In a future step, this will also:
    - Extract all clinical history fields from the conversation.
    - Update the ClinicalHistory record with structured data.
    - Generate a preliminary clinical summary.

    Currently: marks the session as completed.

    Args:
        db: Active async database session.
        patient: Authenticated patient.
        session_id: UUID of the session to complete.

    Returns:
        Updated AISessionResponse with status="completed".
    """
    return await ai_session_service.complete_ai_session(db, patient, session_id)
