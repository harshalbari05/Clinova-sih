"""AI interview service — routes clinical history-taking through the AI layer.

This module is the architectural core of Clinova's AI clinical intake engine.
It connects the patient's conversation, session state, clinical history,
and multi-provider AI architecture.

Step 5B Architecture:
    Patient Message
          ↓
    process_patient_message()
          ↓
    Build chronological conversation context (bounded window)
          ↓
    Fetch / derive current ClinicalHistory and InterviewState
          ↓
    Assemble clinical system prompt (safety rules + language + missing sections)
          ↓
    task_router.generate(HISTORY_INTERVIEW, AIRequest)
          ↓
    Provider fallback (Gemini → OpenAI / Groq → Ollama)
          ↓
    parse_interview_response() (Pydantic validation of structured output)
          ↓
    Merge extracted facts safely into ClinicalHistory (no overwrite with null)
          ↓
    Store AI Message (sender="ai") via server-controlled backend message
          ↓
    Evaluate completion criteria (core sections required)
          ↓
    Return enriched AIInterviewMessageResponse (backward-compatible)

Provider independence:
    This service imports ONLY from app.ai (the abstraction layer).
    It NEVER imports provider SDKs directly.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.config import ai_settings
from app.ai.interview.context import (
    build_conversation_context,
    count_session_messages,
    format_clinical_history_for_prompt,
)
from app.ai.interview.parser import parse_interview_response
from app.ai.interview.schemas import (
    AIInterviewMessageResponse,
    ClinicalInterviewAIResponse,
    InterviewSummary,
)
from app.ai.interview.state import derive_interview_state, is_interview_completable
from app.ai.prompts.clinical_history import build_system_prompt
from app.ai.router import task_router
from app.ai.schemas import AIMessageInput, AIProviderError, AIRequest
from app.ai.tasks import AITaskType
from app.models.clinical_history import ClinicalHistory
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
# Fallback questions (used when AI provider fails or AI_INTERVIEW_ENABLED=False)
# ---------------------------------------------------------------------------

_OPENING_QUESTIONS: dict[str, str] = {
    "English": (
        "Welcome to Clinova. I am your clinical history intake assistant. "
        "Could you please describe what brings you in today and what your main symptoms are?"
    ),
    "Hindi": (
        "क्लिनोव्हा में आपका स्वागत है। मैं आपका नैदानिक इतिहास सहायक हूँ। "
        "कृपया बताएं कि आज आपको क्या परेशानी है और आपके मुख्य लक्षण क्या हैं?"
    ),
    "Marathi": (
        "क्लिनोव्हा मध्ये आपले स्वागत आहे. मी आपला वैद्यकीय माहिती सहायक आहे. "
        "कृपया सांगा आज आपल्याला काय त्रास होत आहे आणि आपली मुख्य लक्षणे कोणती आहेत?"
    ),
}
_DEFAULT_OPENING_QUESTION = _OPENING_QUESTIONS["English"]

_FALLBACK_QUESTION = (
    "Thank you for sharing that. "
    "Could you tell me more about when this started and what makes it better or worse?"
)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def start_interview(
    db: AsyncSession,
    session: AISessionResponse,
) -> AIMessageResponse:
    """Begin the AI interview by storing the opening question.

    Selects an opening greeting matching the session's language.

    Args:
        db: Active async database session.
        session: The newly created AISession.

    Returns:
        AIMessageResponse for the stored opening question.
    """
    opening_question = _OPENING_QUESTIONS.get(
        session.language, _DEFAULT_OPENING_QUESTION
    )
    return await ai_message_service.add_backend_message(
        db=db,
        session_id=session.id,
        sender="ai",
        message=opening_question,
        message_type="text",
    )


async def process_patient_message(
    db: AsyncSession,
    patient: Patient,
    session_id: uuid.UUID,
    patient_message: AIMessageResponse,
) -> AIInterviewMessageResponse:
    """Process a patient's message through the real clinical interview engine.

    Pipeline:
      1. Verify session ownership and check terminal states.
      2. If AI_INTERVIEW_ENABLED is False, return safe fallback without LLM call.
      3. Build bounded conversation context chronologically.
      4. Fetch existing ClinicalHistory and derive runtime InterviewState.
      5. Construct system prompt with safety constraints and current progress.
      6. Route prompt through AITaskRouter (with fallback chain).
      7. Validate structured response via Pydantic schema.
      8. Persist extracted patient-provided facts to ClinicalHistory (safe merge).
      9. Evaluate interview completion criteria.
      10. Store AI response message server-side and return enriched result.

    Args:
        db: Active async database session.
        patient: Authenticated patient ORM object.
        session_id: UUID of the target AI session.
        patient_message: The patient's stored message.

    Returns:
        AIInterviewMessageResponse containing patient + AI messages,
        interview state, and updated clinical history fields.
    """
    # 1. Verify ownership and state
    session = await ai_session_service.get_owned_session(db, patient, session_id)
    if session.status in ("completed", "failed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot add message to an AI session with status '{session.status}'.",
        )

    consultation_id = session.consultation_id

    # Fetch existing ClinicalHistory for this consultation
    stmt = select(ClinicalHistory).where(
        ClinicalHistory.consultation_id == consultation_id
    )
    history = (await db.execute(stmt)).scalar_one_or_none()

    # 2. Check feature flag
    if not ai_settings.AI_INTERVIEW_ENABLED:
        logger.info(
            "AI_INTERVIEW_ENABLED is False; using controlled placeholder response."
        )
        ai_msg = await ai_message_service.add_backend_message(
            db=db,
            session_id=session_id,
            sender="ai",
            message=_FALLBACK_QUESTION,
            message_type="text",
        )
        return AIInterviewMessageResponse(
            id=patient_message.id,
            ai_session_id=patient_message.ai_session_id,
            sender=patient_message.sender,
            message=patient_message.message,
            message_type=patient_message.message_type,
            created_at=patient_message.created_at,
            patient_message=patient_message,
            ai_message=ai_msg,
            interview=InterviewSummary(
                next_question=_FALLBACK_QUESTION,
                current_section="chief_complaint",
                interview_complete=False,
                missing_information=[],
            ),
            clinical_history_updates={},
        )

    # 3. Build chronological conversation context (bounded)
    messages = await build_conversation_context(
        db=db,
        session_id=session_id,
        max_messages=ai_settings.AI_INTERVIEW_MAX_HISTORY_MESSAGES,
    )
    # Ensure current patient message is at the end of turns
    if not messages or messages[-1].content != patient_message.message:
        messages.append(AIMessageInput(role="user", content=patient_message.message))

    # 4. Fetch / derive current interview state
    total_messages = await count_session_messages(db, session_id)
    current_state = derive_interview_state(history, total_messages)
    history_json = format_clinical_history_for_prompt(history)

    # 5. Build system prompt with safety constraints and session language
    system_prompt = build_system_prompt(
        language=session.language,
        current_history_json=history_json,
        current_section=current_state.current_section,
        missing_sections=current_state.missing_sections,
    )

    # 6. Route through AITaskRouter
    ai_request = AIRequest(
        messages=messages,
        system_prompt=system_prompt,
        max_tokens=600,
        temperature=0.3,
    )

    parsed_response: ClinicalInterviewAIResponse
    try:
        response = await task_router.generate(
            task=AITaskType.HISTORY_INTERVIEW,
            request=ai_request,
        )
        parsed_response = parse_interview_response(response)
    except AIProviderError as exc:
        logger.warning(
            "AI provider error (task=HISTORY_INTERVIEW, kind=%s): %s. "
            "Falling back to safe placeholder response.",
            exc.kind.value,
            exc.message,
        )
        parsed_response = ClinicalInterviewAIResponse(
            next_question=_FALLBACK_QUESTION,
            current_section=current_state.current_section,
            interview_complete=False,
        )
    except Exception as exc:
        logger.warning(
            "Unexpected error in interview processing: %s. Using fallback response.",
            exc,
        )
        parsed_response = ClinicalInterviewAIResponse(
            next_question=_FALLBACK_QUESTION,
            current_section=current_state.current_section,
            interview_complete=False,
        )

    # 7. Merge extracted patient facts into ClinicalHistory
    clinical_history_updates: dict[str, str | None] = {}
    if (
        parsed_response.extracted_information
        and parsed_response.extracted_information.has_any_content()
    ):
        updates = parsed_response.extracted_information.to_update_dict()
        if updates:
            if history is None:
                # First clinical history creation
                history = ClinicalHistory(
                    consultation_id=consultation_id,
                    **updates,
                )
                db.add(history)
            else:
                # Merge updates: never overwrite existing content with None/empty
                for field, val in updates.items():
                    if hasattr(history, field) and val is not None and str(val).strip():
                        setattr(history, field, val)
                db.add(history)

            await db.flush()
            await db.refresh(history)
            clinical_history_updates = updates

    # 8. Check interview completion criteria
    is_complete = is_interview_completable(
        history, parsed_response.interview_complete
    )
    if is_complete and session.status != "completed":
        session.status = "completed"
        session.completed_at = datetime.now(tz=timezone.utc)
        db.add(session)
        await db.flush()

    # 9. Store the AI assistant message (server-controlled)
    ai_msg = await ai_message_service.add_backend_message(
        db=db,
        session_id=session_id,
        sender="ai",
        message=parsed_response.next_question,
        message_type="text",
    )

    # 10. Return enriched backward-compatible response
    return AIInterviewMessageResponse(
        id=patient_message.id,
        ai_session_id=patient_message.ai_session_id,
        sender=patient_message.sender,
        message=patient_message.message,
        message_type=patient_message.message_type,
        created_at=patient_message.created_at,
        patient_message=patient_message,
        ai_message=ai_msg,
        interview=InterviewSummary(
            next_question=parsed_response.next_question,
            current_section=parsed_response.current_section or current_state.current_section,
            interview_complete=is_complete,
            missing_information=parsed_response.missing_information,
        ),
        clinical_history_updates=clinical_history_updates,
    )


async def generate_next_question(
    patient_message: str,
) -> str:
    """Generate the next interview question via the AI task router.

    Retained for backward compatibility with external callers.
    Routes through AITaskType.HISTORY_INTERVIEW.

    Args:
        patient_message: The patient's latest answer text.

    Returns:
        The next question string.
    """
    request = AIRequest(
        messages=[
            AIMessageInput(role="user", content=patient_message),
        ],
        system_prompt=(
            "You are a compassionate clinical history-taking assistant at an Indian hospital. "
            "Ask ONE focused, patient-friendly follow-up question. Do not diagnose or prescribe."
        ),
        max_tokens=256,
        temperature=0.3,
    )

    try:
        response = await task_router.generate(
            task=AITaskType.HISTORY_INTERVIEW,
            request=request,
        )
        try:
            parsed = parse_interview_response(response)
            return parsed.next_question
        except ValueError:
            text = (response.text or "").strip()
            if text:
                return text
    except AIProviderError as exc:
        logger.warning(
            "AI provider error (task=HISTORY_INTERVIEW, kind=%s): %s.",
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

    Args:
        db: Active async database session.
        patient: Authenticated patient.
        session_id: UUID of the session to complete.

    Returns:
        Updated AISessionResponse with status="completed".
    """
    return await ai_session_service.complete_ai_session(db, patient, session_id)
