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
    SECTION_PRIORITY_ORDER,
)
from app.ai.interview.state import derive_interview_state, is_interview_completable
from app.ai.prompts.clinical_history import build_system_prompt
from app.ai.router import task_router
from app.ai.schemas import AIMessageInput, AIProviderError, AIRequest
from app.ai.tasks import AITaskType
from app.models.clinical_history import ClinicalHistory
from app.models.consultation import Consultation
from app.models.patient import Patient
from app.schemas.ai_message import AIMessageResponse
from app.schemas.ai_session import AISessionResponse
from app.services import ai_message_service, ai_session_service
from app.triage import TriageUrgency, triage_service

logger = logging.getLogger(__name__)

__all__ = [
    "start_interview",
    "process_patient_message",
    "generate_next_question",
    "complete_interview",
]

# ---------------------------------------------------------------------------
# Multi-lingual clinical section questions & intake engine dictionary
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

_SECTION_QUESTIONS: dict[str, dict[str, str]] = {
    "chief_complaint": {
        "English": (
            "Could you please describe what brings you in today and what your main symptoms are?"
        ),
        "Hindi": (
            "कृपया बताएं कि आज आपको क्या मुख्य परेशानी या लक्षण महसूस हो रहे हैं?"
        ),
        "Marathi": (
            "कृपया सांगा आज आपल्याला काय मुख्य त्रास होत आहे आणि आपली लक्षणे कोणती आहेत?"
        ),
    },
    "history_of_present_illness": {
        "English": (
            "Could you tell me more about when this started, how severe it is, and what makes it better or worse?"
        ),
        "Hindi": (
            "कृपया बताएं कि यह परेशानी कब शुरू हुई, कितनी गंभीर है, और किस वजह से आराम या दर्द बढ़ता है?"
        ),
        "Marathi": (
            "हा त्रास नेमका कधीपासून सुरू झाला, किती तीव्र आहे, आणि कशामुळे आराम मिळतो किंवा त्रास वाढतो?"
        ),
    },
    "past_medical_history": {
        "English": (
            "Do you have any existing medical conditions, such as diabetes, high blood pressure, asthma, or thyroid disease?"
        ),
        "Hindi": (
            "क्या आपको पहले से कोई बीमारी है, जैसे कि मधुमेह (शुगर), उच्च रक्तचाप (बीपी), दमा, या थायराइड?"
        ),
        "Marathi": (
            "आपल्याला पूर्वीचा काही आजार आहे का, जसे की मधुमेह (डायबेटिस), रक्तदाब (बीपी), दमा, किंवा थायरॉईड?"
        ),
    },
    "past_surgical_history": {
        "English": (
            "Have you ever had any surgeries, operations, or hospital admissions in the past?"
        ),
        "Hindi": (
            "क्या आपकी पहले कोई सर्जरी (ऑपरेशन) हुई है या कभी अस्पताल में भर्ती होना पड़ा है?"
        ),
        "Marathi": (
            "आपली पूर्वी कोणती शस्त्रक्रिया (ऑपरेशन) झाली आहे का किंवा रुग्णालयात दाखल व्हावे लागले होते का?"
        ),
    },
    "drug_history": {
        "English": (
            "Are you currently taking any regular medications, ayurvedic medicines, or supplements?"
        ),
        "Hindi": (
            "क्या आप वर्तमान में कोई नियमित दवाइयां, आयुर्वेदिक दवाएं, या सप्लीमेंट्स ले रहे हैं?"
        ),
        "Marathi": (
            "आपण सध्या कोणतीही नियमित औषधे, आयुर्वेदिक उपचार, किंवा गोळ्या घेत आहात का?"
        ),
    },
    "allergy_history": {
        "English": (
            "Do you have any known allergies to medicines, food items, dust, or other substances?"
        ),
        "Hindi": (
            "क्या आपको किसी दवा, भोजन, धूल, या किसी अन्य चीज़ से एलर्जी है?"
        ),
        "Marathi": (
            "आपल्याला कोणत्याही औषधांची, अन्नाची, किंवा इतर कशाची ॲलर्जी आहे का?"
        ),
    },
    "family_history": {
        "English": (
            "Is there a history of chronic illnesses in your family, such as heart disease, diabetes, or cancer?"
        ),
        "Hindi": (
            "क्या आपके परिवार में किसी को हृदय रोग, मधुमेह, या कैंसर जैसी गंभीर बीमारी का इतिहास रहा है?"
        ),
        "Marathi": (
            "आपल्या कुटुंबात कोणाला हृदयविकार, मधुमेह, किंवा इतर गंभीर आजारांचा इतिहास आहे का?"
        ),
    },
    "personal_history": {
        "English": (
            "Could you briefly tell me about your daily routine, diet, sleep, and if you use tobacco or alcohol?"
        ),
        "Hindi": (
            "कृपया अपनी दिनचर्या, खान-पान, नींद, और तंबाकू या शराब के सेवन के बारे में संक्षेप में बताएं?"
        ),
        "Marathi": (
            "कृपया आपली दिनचर्या, आहार, झोप, आणि तंबाखू किंवा मद्यपानाचे व्यसन याविषयी थोडक्यात माहिती द्याल का?"
        ),
    },
    "review_of_systems": {
        "English": (
            "Are you experiencing any other symptoms, such as fever, cough, chest discomfort, or headache?"
        ),
        "Hindi": (
            "क्या आपको कोई अन्य लक्षण भी हैं, जैसे बुखार, खांसी, सीने में दर्द, या सिरदर्द?"
        ),
        "Marathi": (
            "आपल्याला ताप, खोकला, छातीत दुखणे, किंवा डोकेदुखी अशी इतर काही लक्षणे जाणवत आहेत का?"
        ),
    },
}

_COMPLETION_MESSAGES: dict[str, str] = {
    "English": (
        "Thank you for providing your details. Your clinical history intake is complete. "
        "The doctor will review your history during your consultation."
    ),
    "Hindi": (
        "विवरण देने के लिए धन्यवाद। आपका नैदानिक इतिहास पूरा हो गया है। "
        "डॉक्टर आपके परामर्श के दौरान इसकी समीक्षा करेंगे।"
    ),
    "Marathi": (
        "माहिती दिल्याबद्दल धन्यवाद. आपली वैद्यकीय माहिती नोंदवून पूर्ण झाली आहे. "
        "डॉक्टर आपल्या तपासणीच्या वेळी याची पाहणी करतील."
    ),
}

_FALLBACK_QUESTION = _SECTION_QUESTIONS["history_of_present_illness"]["English"]


def _get_localized_question(section: str, language: str) -> str:
    """Return the clinical question for a section in the requested language."""
    section_map = _SECTION_QUESTIONS.get(
        section, _SECTION_QUESTIONS["history_of_present_illness"]
    )
    return section_map.get(
        language, section_map.get("English", _FALLBACK_QUESTION)
    )


def _get_completion_message(language: str) -> str:
    """Return the intake completion message in the requested language."""
    return _COMPLETION_MESSAGES.get(
        language, _COMPLETION_MESSAGES["English"]
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
    is_fallback = not ai_settings.AI_INTERVIEW_ENABLED
    if is_fallback:
        logger.info(
            "AI_INTERVIEW_ENABLED is False; using adaptive clinical intake engine."
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

    parsed_response: ClinicalInterviewAIResponse | None = None

    if not is_fallback:
        # 5. Build system prompt with safety constraints and session language
        system_prompt = build_system_prompt(
            language=session.language,
            current_history_json=history_json,
            current_section=current_state.current_section,
            missing_sections=current_state.missing_sections,
        )

        # 6. Route through AITaskRouter (with fallback chain)
        ai_request = AIRequest(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=600,
            temperature=0.3,
        )

        try:
            response = await task_router.generate(
                task=AITaskType.HISTORY_INTERVIEW,
                request=ai_request,
            )
            parsed_response = parse_interview_response(response)
        except AIProviderError as exc:
            logger.warning(
                "AI provider error (task=HISTORY_INTERVIEW, kind=%s): %s. "
                "Switching to adaptive clinical intake engine.",
                exc.kind.value,
                exc.message,
            )
            is_fallback = True
        except Exception as exc:
            logger.warning(
                "Unexpected error in interview processing: %s. Using adaptive clinical intake engine.",
                exc,
            )
            is_fallback = True

    clinical_history_updates: dict[str, str | None] = {}

    # 7. State update and question generation
    if is_fallback or parsed_response is None:
        is_fallback = True

        # Fallback does NOT invent structured clinical history updates
        clinical_history_updates = {}

        if current_state.interview_complete:
            next_q = _get_completion_message(session.language)
        else:
            next_q = _get_localized_question(
                current_state.current_section, session.language
            )

        parsed_response = ClinicalInterviewAIResponse(
            next_question=next_q,
            current_section=current_state.current_section,
            interview_complete=current_state.interview_complete,
            missing_information=current_state.missing_sections,
        )
    else:
        # Merge extracted patient facts from live LLM structured output
        if (
            parsed_response.extracted_information
            and parsed_response.extracted_information.has_any_content()
        ):
            updates = parsed_response.extracted_information.to_update_dict()
            if updates:
                if history is None:
                    history = ClinicalHistory(
                        consultation_id=consultation_id,
                        **updates,
                    )
                    db.add(history)
                else:
                    for field, val in updates.items():
                        if hasattr(history, field) and val is not None and str(val).strip():
                            setattr(history, field, val)
                    db.add(history)

                await db.flush()
                await db.refresh(history)
                clinical_history_updates = updates

    # 7b. Evaluate red-flag triage and synchronize alerts
    consultation_stmt = select(Consultation).where(Consultation.id == consultation_id)
    consultation = (await db.execute(consultation_stmt)).scalar_one_or_none()

    patient_reply_message = parsed_response.next_question
    if consultation is not None:
        triage_result = await triage_service.evaluate_triage(
            db=db,
            consultation=consultation,
            patient_text=patient_message.message,
            history=history,
            use_ai_assistance=False,
        )
        if (
            triage_result.urgency == TriageUrgency.EMERGENCY_REVIEW
            and triage_result.patient_safety_guidance
        ):
            patient_reply_message = triage_result.patient_safety_guidance

    # 8. Check interview completion criteria
    is_complete = is_interview_completable(
        history, parsed_response.interview_complete, is_fallback=is_fallback
    )

    # 9. Store the AI assistant message (server-controlled)
    ai_msg = await ai_message_service.add_backend_message(
        db=db,
        session_id=session_id,
        sender="ai",
        message=patient_reply_message,
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
            next_question=patient_reply_message,
            current_section=parsed_response.current_section or current_state.current_section,
            interview_complete=is_complete,
            missing_information=parsed_response.missing_information,
            is_fallback=is_fallback,
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
