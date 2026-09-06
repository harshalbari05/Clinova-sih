"""AI interview service — routes clinical history-taking through the AI layer.

This module is the architectural boundary between the AI session
infrastructure and the AI interview logic (LLM-powered question generation,
answer parsing, clinical history extraction).

Current state (Step 5A):
    The provider architecture is wired in. When AI_ENABLED=True and a
    provider is configured, real LLM calls are made via the AI task router.
    If AI is not enabled or the provider is not available, the service
    falls back to placeholder responses so the session infrastructure
    continues to work without breaking.

Future state (Step 5B+):
    generate_next_question() will pass full conversation history and
    a clinical interviewer system prompt to the LLM. Structured extraction
    and clinical summary generation will be added as separate task calls.

Architecture:
    Patient Message
          ↓
    process_patient_message()
          ↓
    generate_next_question()
          ↓
    task_router.generate(HISTORY_INTERVIEW, AIRequest)   ← [Step 5A]
          ↓
    AIProvider.generate() → AIResponse
          ↓
    AI Message (sender="ai") stored in DB
          ↓
    [Eventually Step 5B+] extract_to_clinical_history()

Provider independence:
    This service imports ONLY from app.ai (the abstraction layer).
    It MUST NOT import any provider SDK (google.genai, openai, httpx, etc.).
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.router import task_router
from app.ai.schemas import AIMessageInput, AIProviderError, AIRequest
from app.ai.tasks import AITaskType
from app.models.patient import Patient
from app.schemas.ai_message import AIMessageResponse
from app.schemas.ai_session import AISessionResponse
from app.services import ai_message_service, ai_session_service

logger = logging.getLogger(__name__)

__all__ = [
    "start_interview",
    "process_patient_message",
    "generate_next_question",
    "complete_interview",
]

# ---------------------------------------------------------------------------
# Placeholder responses — used when AI provider is unavailable
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
# System prompt for the clinical interviewer (Step 5A — placeholder)
# Future steps will expand this into a full clinical interviewer prompt.
# ---------------------------------------------------------------------------

_CLINICAL_INTERVIEWER_SYSTEM_PROMPT = (
    "You are a compassionate and professional clinical history-taking assistant "
    "at an Indian hospital. Your role is to ask clear, empathetic follow-up "
    "questions to help gather the patient's clinical history. "
    "Ask ONE focused question at a time. Be concise and professional."
)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def start_interview(
    db: AsyncSession,
    session: AISessionResponse,
) -> AIMessageResponse:
    """Begin the AI interview by sending the opening question.

    Currently uses a fixed opening question. Future steps will:
    - Load patient's existing clinical history context.
    - Determine which sections are missing.
    - Generate a contextually appropriate opening question via LLM.

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

    Calls generate_next_question() which routes through the AI task router.
    If the provider is unavailable or not configured, falls back to a
    placeholder response so the session infrastructure is never broken.

    Args:
        db: Active async database session.
        patient: The authenticated patient.
        session_id: UUID of the AI session.
        patient_message: The patient's message that was just stored.

    Returns:
        AIMessageResponse for the stored AI follow-up message.
    """
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
    """Generate the next interview question via the AI task router.

    Routes through AITaskType.HISTORY_INTERVIEW → configured provider.
    If the provider is unavailable or not configured, returns the
    placeholder follow-up question so the session never breaks.

    Args:
        patient_message: The patient's latest answer text.

    Returns:
        The next question string to be stored as an AI message.
    """
    request = AIRequest(
        messages=[
            AIMessageInput(role="user", content=patient_message),
        ],
        system_prompt=_CLINICAL_INTERVIEWER_SYSTEM_PROMPT,
        max_tokens=256,
        temperature=0.7,
    )

    try:
        response = await task_router.generate(
            task=AITaskType.HISTORY_INTERVIEW,
            request=request,
        )
        text = (response.text or "").strip()
        if text:
            return text
        # Provider returned empty response — fall through to placeholder
        logger.warning(
            "AI provider '%s' returned empty response; using placeholder.",
            response.provider,
        )
    except AIProviderError as exc:
        # Provider not configured or unavailable — this is expected in
        # environments without AI credentials. Never crash the interview.
        logger.warning(
            "AI provider error (task=HISTORY_INTERVIEW, kind=%s): %s. "
            "Falling back to placeholder response.",
            exc.kind.value,
            exc.message,
        )

    return _FALLBACK_QUESTION


async def complete_interview(
    db: AsyncSession,
    patient: Patient,
    session_id: uuid.UUID,
) -> AISessionResponse:
    """Complete the AI interview session.

    Future steps will also:
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
