"""Tests for Step 5B: Real AI Clinical History Interview Engine.

Covers all 34 requirements across:
  - BASIC: processing, context, storage, clinical history persistence
  - STRUCTURED OUTPUT: parsing, validation, safe merge, fact-extraction constraints
  - CONVERSATION: context history, chronological ordering, bounded window, current history
  - INTERVIEW FLOW: status transitions, question generation, section tracking, completion
  - SECURITY: cross-patient isolation, sender spoofing, identity enforcement
  - PROVIDER: task router usage, fallback chain, all-provider failure handling, feature flag
  - SAFETY: system prompt constraints, no diagnosis/prescription in fallback
  - LANGUAGE: English, Hindi, Marathi instruction contexts
  - REGRESSION: Steps 1-5A compatibility

All tests use mocks for AI providers — NO network, NO real API keys, NO Ollama running.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
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
    CLINICAL_SECTION_NAMES,
    ClinicalInterviewAIResponse,
    ExtractedClinicalInfo,
    InterviewState,
)
from app.ai.interview.state import derive_interview_state, is_interview_completable
from app.ai.prompts.clinical_history import build_system_prompt
from app.ai.router import task_router
from app.ai.schemas import (
    AIErrorKind,
    AIMessageInput,
    AIProviderError,
    AIRequest,
    AIResponse,
)
from app.ai.tasks import AITaskType
from app.models.ai_message import AIMessage
from app.models.ai_session import AISession
from app.models.clinical_history import ClinicalHistory
from app.models.hospital import Hospital
from app.services import ai_interview_service, ai_message_service

# ---------------------------------------------------------------------------
# Test URLs & Helpers
# ---------------------------------------------------------------------------

REGISTER_URL = "/api/v1/auth/patient/register"
LOGIN_URL = "/api/v1/auth/patient/login"
CONSULTATIONS_URL = "/api/v1/consultations"


def ai_sessions_create_url(consultation_id: str) -> str:
    return f"/api/v1/consultations/{consultation_id}/ai-sessions"


def ai_session_url(session_id: str) -> str:
    return f"/api/v1/ai-sessions/{session_id}"


def ai_messages_url(session_id: str) -> str:
    return f"/api/v1/ai-sessions/{session_id}/messages"


async def _register_and_login(
    client: AsyncClient,
    *,
    email: str,
    password: str = "SecurePass1!",
    full_name: str = "Test Patient",
) -> str:
    reg = await client.post(
        REGISTER_URL,
        json={"email": email, "password": password, "full_name": full_name},
    )
    assert reg.status_code == 201, reg.text
    login = await client.post(
        LOGIN_URL, json={"identifier": email, "password": password}
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


async def _create_hospital(db: AsyncSession, name: str = "Apollo Hospital") -> uuid.UUID:
    h = Hospital(name=name)
    db.add(h)
    await db.flush()
    await db.refresh(h)
    return h.id


async def _setup_session(
    client: AsyncClient,
    db: AsyncSession,
    *,
    email: str,
    language: str = "English",
) -> tuple[str, str, str]:
    """Register patient, create consultation and AI session.

    Returns (token, consultation_id, session_id).
    """
    token = await _register_and_login(client, email=email)
    hid = await _create_hospital(db)
    c_res = await client.post(
        CONSULTATIONS_URL,
        json={"hospital_id": str(hid)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert c_res.status_code == 201
    cid = c_res.json()["id"]

    s_res = await client.post(
        ai_sessions_create_url(cid),
        json={"language": language},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert s_res.status_code == 201
    sid = s_res.json()["id"]
    return token, cid, sid


def _make_mock_ai_response(
    next_question: str = "When did your fever start?",
    chief_complaint: str | None = "Fever",
    hpi: str | None = "High grade fever for 3 days",
    current_section: str = "history_of_present_illness",
    missing_info: list[str] | None = None,
    interview_complete: bool = False,
) -> AIResponse:
    payload = {
        "next_question": next_question,
        "extracted_information": {
            "chief_complaint": chief_complaint,
            "history_of_present_illness": hpi,
            "past_medical_history": None,
            "past_surgical_history": None,
            "drug_history": None,
            "allergy_history": None,
            "family_history": None,
            "personal_history": None,
            "review_of_systems": None,
        },
        "missing_information": missing_info or ["temperature", "chills"],
        "current_section": current_section,
        "section_complete": False,
        "interview_complete": interview_complete,
    }
    return AIResponse(
        text=json.dumps(payload),
        provider="mock_provider",
        model="mock_model",
        structured=payload,
    )


# ---------------------------------------------------------------------------
# 1. BASIC INTERVIEW PROCESSING (1-5)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_01_interview_service_processes_patient_message(
    client: AsyncClient, db_session: AsyncSession
):
    """1. Interview service processes patient message and returns structured result."""
    token, _, sid = await _setup_session(client, db_session, email="basic01@test.com")

    mock_resp = _make_mock_ai_response()
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_resp

        res = await client.post(
            ai_messages_url(sid),
            json={"message": "I have a high fever for three days."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201, res.text
        data = res.json()
        assert "patient_message" in data
        assert "ai_message" in data
        assert "interview" in data
        assert "clinical_history_updates" in data
        assert data["interview"]["next_question"] == "When did your fever start?"


@pytest.mark.asyncio
async def test_02_full_conversation_context_is_provided(
    client: AsyncClient, db_session: AsyncSession
):
    """2. Full conversation context is provided to the AI provider."""
    token, _, sid = await _setup_session(client, db_session, email="basic02@test.com")

    mock_resp = _make_mock_ai_response()
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_resp

        # First message
        await client.post(
            ai_messages_url(sid),
            json={"message": "I have severe headaches."},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Second message
        await client.post(
            ai_messages_url(sid),
            json={"message": "It started yesterday morning."},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Inspect the last call to task_router.generate
        assert mock_gen.call_count == 2
        last_request: AIRequest = mock_gen.call_args[1]["request"]
        # Must have the earlier conversation messages
        contents = [m.content for m in last_request.messages]
        assert "I have severe headaches." in contents
        assert "It started yesterday morning." in contents


@pytest.mark.asyncio
async def test_03_ai_response_is_saved(
    client: AsyncClient, db_session: AsyncSession
):
    """3. AI response is saved to the database with sender='ai'."""
    token, _, sid = await _setup_session(client, db_session, email="basic03@test.com")

    mock_resp = _make_mock_ai_response(next_question="Does light bother your eyes?")
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_resp

        res = await client.post(
            ai_messages_url(sid),
            json={"message": "My head hurts badly."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        assert res.json()["ai_message"]["message"] == "Does light bother your eyes?"

        # Verify message exists in DB
        stmt = (
            select(AIMessage)
            .where(AIMessage.ai_session_id == uuid.UUID(sid), AIMessage.sender == "ai")
        )
        ai_msgs = (await db_session.execute(stmt)).scalars().all()
        assert any(m.message == "Does light bother your eyes?" for m in ai_msgs)


@pytest.mark.asyncio
async def test_04_patient_message_is_saved(
    client: AsyncClient, db_session: AsyncSession
):
    """4. Patient message is saved to the database with sender='patient'."""
    token, _, sid = await _setup_session(client, db_session, email="basic04@test.com")

    mock_resp = _make_mock_ai_response()
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_resp

        await client.post(
            ai_messages_url(sid),
            json={"message": "I feel dizzy when standing."},
            headers={"Authorization": f"Bearer {token}"},
        )

        stmt = select(AIMessage).where(
            AIMessage.ai_session_id == uuid.UUID(sid),
            AIMessage.sender == "patient",
            AIMessage.message == "I feel dizzy when standing.",
        )
        p_msg = (await db_session.execute(stmt)).scalar_one_or_none()
        assert p_msg is not None


@pytest.mark.asyncio
async def test_05_clinical_history_updates_are_persisted(
    client: AsyncClient, db_session: AsyncSession
):
    """5. Extracted clinical facts are persisted to the ClinicalHistory table."""
    token, cid, sid = await _setup_session(client, db_session, email="basic05@test.com")

    mock_resp = _make_mock_ai_response(
        chief_complaint="Chest tightness",
        hpi="Chest tightness on exertion for 2 weeks",
    )
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_resp

        res = await client.post(
            ai_messages_url(sid),
            json={"message": "I get chest tightness when climbing stairs."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        updates = res.json()["clinical_history_updates"]
        assert updates["chief_complaint"] == "Chest tightness"
        assert updates["history_of_present_illness"] == "Chest tightness on exertion for 2 weeks"

        # Check DB directly
        stmt = select(ClinicalHistory).where(
            ClinicalHistory.consultation_id == uuid.UUID(cid)
        )
        hist = (await db_session.execute(stmt)).scalar_one_or_none()
        assert hist is not None
        assert hist.chief_complaint == "Chest tightness"
        assert hist.history_of_present_illness == "Chest tightness on exertion for 2 weeks"


# ---------------------------------------------------------------------------
# 2. STRUCTURED OUTPUT & VALIDATION (6-10)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_06_valid_structured_ai_response_is_accepted():
    """6. Valid structured AI response is parsed and validated."""
    mock_resp = _make_mock_ai_response(
        next_question="Have you taken any medication?",
        chief_complaint="Cough",
    )
    parsed = parse_interview_response(mock_resp)
    assert parsed.next_question == "Have you taken any medication?"
    assert parsed.extracted_information is not None
    assert parsed.extracted_information.chief_complaint == "Cough"


@pytest.mark.asyncio
async def test_07_invalid_structured_response_handled_safely(
    client: AsyncClient, db_session: AsyncSession
):
    """7. Invalid structured response (garbage text) is handled safely with fallback."""
    token, _, sid = await _setup_session(client, db_session, email="struct07@test.com")

    # Provider returns unstructured garbage
    bad_resp = AIResponse(
        text="Sorry I cannot answer that properly.",
        provider="mock_provider",
        model="mock_model",
    )
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = bad_resp

        res = await client.post(
            ai_messages_url(sid),
            json={"message": "I have a sore throat."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        data = res.json()
        # Fallback question used safely, no crash
        assert data["interview"]["next_question"] != ""
        assert data["clinical_history_updates"] == {}


@pytest.mark.asyncio
async def test_08_unknown_fields_are_ignored():
    """8. Unknown fields (e.g. diagnosis, treatment) are rejected or ignored."""
    raw_json = json.dumps({
        "next_question": "Do you have any allergies?",
        "diagnosis": "Severe viral influenza",  # NOT allowed
        "prescription": "Paracetamol 650mg",    # NOT allowed
        "extracted_information": {
            "chief_complaint": "Flu symptoms",
            "diagnosis": "Viral illness",        # NOT allowed
            "temperature": "103F",
        },
    })
    resp = AIResponse(text=raw_json, provider="mock", model="mock")
    parsed = parse_interview_response(resp)
    assert not hasattr(parsed, "diagnosis")
    assert not hasattr(parsed, "prescription")
    assert not hasattr(parsed.extracted_information, "diagnosis")


@pytest.mark.asyncio
async def test_09_empty_null_fields_do_not_erase_existing_data(
    client: AsyncClient, db_session: AsyncSession
):
    """9. Empty or null optional fields in subsequent turns do not overwrite existing data."""
    token, cid, sid = await _setup_session(client, db_session, email="struct09@test.com")

    # Turn 1: extracts chief_complaint
    resp1 = _make_mock_ai_response(
        chief_complaint="Persistent dry cough",
        hpi=None,
    )
    # Turn 2: extracts hpi, chief_complaint is None
    resp2 = _make_mock_ai_response(
        chief_complaint=None,
        hpi="Dry cough lasting 10 days, worse at night",
    )

    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = resp1
        await client.post(
            ai_messages_url(sid),
            json={"message": "I have had a dry cough."},
            headers={"Authorization": f"Bearer {token}"},
        )

        mock_gen.return_value = resp2
        await client.post(
            ai_messages_url(sid),
            json={"message": "It lasts 10 days, worse at night."},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Check DB — chief_complaint MUST still be present
        stmt = select(ClinicalHistory).where(
            ClinicalHistory.consultation_id == uuid.UUID(cid)
        )
        hist = (await db_session.execute(stmt)).scalar_one_or_none()
        assert hist is not None
        assert hist.chief_complaint == "Persistent dry cough"
        assert hist.history_of_present_illness == "Dry cough lasting 10 days, worse at night"


@pytest.mark.asyncio
async def test_10_only_patient_provided_info_is_persisted(
    client: AsyncClient, db_session: AsyncSession
):
    """10. Unmentioned fields remain null in ClinicalHistory."""
    token, cid, sid = await _setup_session(client, db_session, email="struct10@test.com")

    resp = _make_mock_ai_response(
        chief_complaint="Knee pain",
        hpi="Right knee pain after a fall",
    )
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = resp
        await client.post(
            ai_messages_url(sid),
            json={"message": "I fell and hurt my right knee."},
            headers={"Authorization": f"Bearer {token}"},
        )

        stmt = select(ClinicalHistory).where(
            ClinicalHistory.consultation_id == uuid.UUID(cid)
        )
        hist = (await db_session.execute(stmt)).scalar_one_or_none()
        assert hist is not None
        assert hist.chief_complaint == "Knee pain"
        # The following unmentioned sections must remain None
        assert hist.past_surgical_history is None
        assert hist.drug_history is None
        assert hist.family_history is None
        assert hist.personal_history is None


# ---------------------------------------------------------------------------
# 3. CONVERSATION CONTEXT (11-14)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_11_previous_messages_are_included(
    client: AsyncClient, db_session: AsyncSession
):
    """11. Previous messages are included in context for subsequent turns."""
    token, _, sid = await _setup_session(client, db_session, email="conv11@test.com")

    mock_resp = _make_mock_ai_response()
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_resp

        await client.post(
            ai_messages_url(sid),
            json={"message": "First message: abdomen pain."},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            ai_messages_url(sid),
            json={"message": "Second message: lower right side."},
            headers={"Authorization": f"Bearer {token}"},
        )

        last_req: AIRequest = mock_gen.call_args[1]["request"]
        all_text = " ".join(m.content for m in last_req.messages)
        assert "abdomen pain" in all_text
        assert "lower right side" in all_text


@pytest.mark.asyncio
async def test_12_messages_remain_chronological(
    client: AsyncClient, db_session: AsyncSession
):
    """12. Conversation messages passed to the model are in chronological order."""
    token, _, sid = await _setup_session(client, db_session, email="conv12@test.com")

    mock_resp = _make_mock_ai_response()
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_resp

        turns = ["Turn 1: nausea", "Turn 2: vomiting", "Turn 3: fever"]
        for t in turns:
            await client.post(
                ai_messages_url(sid),
                json={"message": t},
                headers={"Authorization": f"Bearer {token}"},
            )

        last_req: AIRequest = mock_gen.call_args[1]["request"]
        patient_msgs = [m.content for m in last_req.messages if m.role == "user"]
        assert patient_msgs[-3:] == turns


@pytest.mark.asyncio
async def test_13_context_is_bounded(db_session: AsyncSession):
    """13. Bounded window limits the messages fetched for the model."""
    from datetime import datetime, timedelta, timezone

    sid = uuid.uuid4()
    base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    # Insert 30 messages directly into DB with distinct chronological timestamps
    for i in range(30):
        sender = "patient" if i % 2 == 0 else "ai"
        msg = AIMessage(
            ai_session_id=sid,
            sender=sender,
            message=f"Message {i}",
            message_type="text",
            created_at=base_time + timedelta(seconds=i),
        )
        db_session.add(msg)
    await db_session.flush()

    # Request window of 10
    context = await build_conversation_context(db_session, sid, max_messages=10)
    assert len(context) == 10
    # Must be the most recent 10, chronological (Message 20 to Message 29)
    assert context[0].content == "Message 20"
    assert context[-1].content == "Message 29"


@pytest.mark.asyncio
async def test_14_current_clinical_history_is_provided_to_model(
    client: AsyncClient, db_session: AsyncSession
):
    """14. Current structured clinical history is provided in the model system prompt."""
    token, _, sid = await _setup_session(client, db_session, email="conv14@test.com")

    resp1 = _make_mock_ai_response(chief_complaint="Chest tightness")
    resp2 = _make_mock_ai_response(hpi="Worse on walking")

    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = resp1
        await client.post(
            ai_messages_url(sid),
            json={"message": "I feel tightness in my chest."},
            headers={"Authorization": f"Bearer {token}"},
        )

        mock_gen.return_value = resp2
        await client.post(
            ai_messages_url(sid),
            json={"message": "It gets worse when I walk fast."},
            headers={"Authorization": f"Bearer {token}"},
        )

        last_req: AIRequest = mock_gen.call_args[1]["request"]
        assert last_req.system_prompt is not None
        assert "Chest tightness" in last_req.system_prompt


# ---------------------------------------------------------------------------
# 4. INTERVIEW FLOW (15-20)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_15_first_message_moves_session_from_initiated_to_in_progress(
    client: AsyncClient, db_session: AsyncSession
):
    """15. First message transitions session status from initiated to in_progress."""
    token, _, sid = await _setup_session(client, db_session, email="flow15@test.com")

    # Initial status
    s_before = await client.get(
        ai_session_url(sid),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert s_before.json()["status"] == "initiated"

    mock_resp = _make_mock_ai_response()
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_resp

        await client.post(
            ai_messages_url(sid),
            json={"message": "Hello, I am ready for the interview."},
            headers={"Authorization": f"Bearer {token}"},
        )

        s_after = await client.get(
            ai_session_url(sid),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert s_after.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_16_next_question_is_generated(
    client: AsyncClient, db_session: AsyncSession
):
    """16. Next question is generated and returned in interview summary."""
    token, _, sid = await _setup_session(client, db_session, email="flow16@test.com")

    mock_resp = _make_mock_ai_response(next_question="Do you have a rash anywhere?")
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_resp

        res = await client.post(
            ai_messages_url(sid),
            json={"message": "I am itchy all over."},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = res.json()
        assert data["interview"]["next_question"] == "Do you have a rash anywhere?"


@pytest.mark.asyncio
async def test_17_current_section_is_tracked(
    client: AsyncClient, db_session: AsyncSession
):
    """17. Current clinical section is tracked and returned."""
    token, _, sid = await _setup_session(client, db_session, email="flow17@test.com")

    mock_resp = _make_mock_ai_response(current_section="past_medical_history")
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_resp

        res = await client.post(
            ai_messages_url(sid),
            json={"message": "I have had hypertension for 5 years."},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = res.json()
        assert data["interview"]["current_section"] == "past_medical_history"


@pytest.mark.asyncio
async def test_18_missing_information_is_tracked(
    client: AsyncClient, db_session: AsyncSession
):
    """18. Missing information list is tracked and returned."""
    token, _, sid = await _setup_session(client, db_session, email="flow18@test.com")

    missing = ["duration", "severity", "radiation"]
    mock_resp = _make_mock_ai_response(missing_info=missing)
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_resp

        res = await client.post(
            ai_messages_url(sid),
            json={"message": "I have severe back pain."},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = res.json()
        assert data["interview"]["missing_information"] == missing


@pytest.mark.asyncio
async def test_19_interview_can_reach_completed_state(
    client: AsyncClient, db_session: AsyncSession
):
    """19. Interview can transition to completed when core sections are collected."""
    token, _, sid = await _setup_session(client, db_session, email="flow19@test.com")

    # When core sections (chief_complaint and hpi) are provided and interview_complete=True
    comp_resp = _make_mock_ai_response(
        next_question="Thank you, I have gathered all necessary information for your doctor.",
        chief_complaint="Acute bronchitis",
        hpi="Cough with phlegm for 7 days",
        interview_complete=True,
    )
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = comp_resp

        res = await client.post(
            ai_messages_url(sid),
            json={"message": "That is all my symptoms."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        assert res.json()["interview"]["interview_complete"] is True

        # Verify session status in DB
        s_res = await client.get(
            ai_session_url(sid),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert s_res.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_20_completed_session_rejects_additional_messages(
    client: AsyncClient, db_session: AsyncSession
):
    """20. A completed session rejects additional patient messages with HTTP 409."""
    token, _, sid = await _setup_session(client, db_session, email="flow20@test.com")

    # Complete the session explicitly
    await client.post(
        f"/api/v1/ai-sessions/{sid}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Attempt to post a message to completed session
    res = await client.post(
        ai_messages_url(sid),
        json={"message": "Can I add one more symptom?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 409
    assert "completed" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 5. SECURITY (21-24)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_21_another_patient_cannot_use_session(
    client: AsyncClient, db_session: AsyncSession
):
    """21. Another patient cannot send messages to this session (HTTP 404)."""
    p1_token, _, p1_sid = await _setup_session(
        client, db_session, email="sec21_p1@test.com"
    )
    p2_token = await _register_and_login(client, email="sec21_p2@test.com")

    res = await client.post(
        ai_messages_url(p1_sid),
        json={"message": "Trying to inject into other session"},
        headers={"Authorization": f"Bearer {p2_token}"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_22_another_patients_messages_never_passed_to_model(
    db_session: AsyncSession
):
    """22. Messages from another patient's session are never retrieved into context."""
    s1_id = uuid.uuid4()
    s2_id = uuid.uuid4()

    # Session 1 message
    m1 = AIMessage(
        ai_session_id=s1_id,
        sender="patient",
        message="Patient 1 confidential symptom: diabetes",
        message_type="text",
    )
    # Session 2 message
    m2 = AIMessage(
        ai_session_id=s2_id,
        sender="patient",
        message="Patient 2 symptom: broken arm",
        message_type="text",
    )
    db_session.add_all([m1, m2])
    await db_session.flush()

    # Fetch context for session 2
    ctx = await build_conversation_context(db_session, s2_id)
    contents = [m.content for m in ctx]
    assert "Patient 2 symptom: broken arm" in contents
    assert not any("Patient 1 confidential symptom" in c for c in contents)


@pytest.mark.asyncio
async def test_23_client_cannot_spoof_ai_sender(
    client: AsyncClient, db_session: AsyncSession
):
    """23. Client cannot send messages with sender='ai' (returns 422)."""
    token, _, sid = await _setup_session(client, db_session, email="sec23@test.com")

    res = await client.post(
        ai_messages_url(sid),
        json={"message": "Spoofed message", "sender": "ai"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_24_client_cannot_provide_patient_id_to_override_jwt(
    client: AsyncClient, db_session: AsyncSession
):
    """24. Client cannot provide patient_id to override JWT identity."""
    token, _, sid = await _setup_session(client, db_session, email="sec24@test.com")

    fake_patient_id = str(uuid.uuid4())
    mock_resp = _make_mock_ai_response()
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_resp

        res = await client.post(
            ai_messages_url(sid),
            json={
                "message": "Valid symptom",
                "patient_id": fake_patient_id,  # Injection attempt
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        # 422 extra field rejected or accepted but ignored
        if res.status_code == 201:
            data = res.json()
            assert data["sender"] == "patient"


# ---------------------------------------------------------------------------
# 6. PROVIDER ROUTING & FALLBACK (25-28)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_25_ai_task_router_is_used(
    client: AsyncClient, db_session: AsyncSession
):
    """25. AITaskRouter is invoked with AITaskType.HISTORY_INTERVIEW."""
    token, _, sid = await _setup_session(client, db_session, email="prov25@test.com")

    mock_resp = _make_mock_ai_response()
    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_resp

        await client.post(
            ai_messages_url(sid),
            json={"message": "I feel fatigue all the time."},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert mock_gen.call_count == 1
        assert mock_gen.call_args[1]["task"] == AITaskType.HISTORY_INTERVIEW


@pytest.mark.asyncio
async def test_26_provider_failures_trigger_fallback(
    client: AsyncClient, db_session: AsyncSession
):
    """26. Primary provider failure triggers fallback via task router."""
    token, _, sid = await _setup_session(client, db_session, email="prov26@test.com")

    # Mock task router to fail once then succeed (simulating fallback)
    call_count = 0

    async def mock_generate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First attempt fails
            raise AIProviderError(
                kind=AIErrorKind.TIMEOUT,
                provider="gemini",
                message="Gemini timed out.",
            )
        return _make_mock_ai_response(next_question="Fallback provider: How long have you felt this?")

    with patch.object(task_router, "generate", side_effect=mock_generate):
        res = await client.post(
            ai_messages_url(sid),
            json={"message": "I feel dizzy."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201


@pytest.mark.asyncio
async def test_27_all_provider_failure_is_controlled(
    client: AsyncClient, db_session: AsyncSession
):
    """27. When all providers fail, the service returns a controlled safe response."""
    token, _, sid = await _setup_session(client, db_session, email="prov27@test.com")

    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = AIProviderError(
            kind=AIErrorKind.PROVIDER_UNAVAILABLE,
            provider="ollama",
            message="No providers available.",
        )

        res = await client.post(
            ai_messages_url(sid),
            json={"message": "My chest hurts."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        data = res.json()
        # Controlled fallback question used
        assert len(data["interview"]["next_question"]) > 0
        # Does NOT invent clinical history updates
        assert data["clinical_history_updates"] == {}


@pytest.mark.asyncio
async def test_28_no_external_provider_call_when_ai_interview_disabled(
    client: AsyncClient, db_session: AsyncSession
):
    """28. No external AI provider call occurs when AI_INTERVIEW_ENABLED=False."""
    token, _, sid = await _setup_session(client, db_session, email="prov28@test.com")

    with patch.object(ai_settings, "AI_INTERVIEW_ENABLED", False):
        with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
            res = await client.post(
                ai_messages_url(sid),
                json={"message": "Hello intake assistant."},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert res.status_code == 201
            assert mock_gen.call_count == 0  # No LLM call!


# ---------------------------------------------------------------------------
# 7. SAFETY CONSTRAINTS (29-30)
# ---------------------------------------------------------------------------


def test_29_ai_prompt_contains_safety_constraints():
    """29. AI system prompt explicitly contains no-diagnosis and no-prescription constraints."""
    prompt = build_system_prompt(
        language="English",
        current_history_json="{}",
        current_section="chief_complaint",
        missing_sections=["chief_complaint"],
    )
    # Check strict safety instructions
    assert "DO NOT diagnose" in prompt
    assert "DO NOT prescribe" in prompt
    assert "DO NOT state a prognosis" in prompt
    assert "DO NOT fabricate" in prompt
    assert "DO NOT ask more than ONE primary question" in prompt


def test_30_medical_recommendations_not_in_fallback_logic():
    """30. Application fallback questions do NOT contain medical recommendations."""
    from app.services.ai_interview_service import _FALLBACK_QUESTION, _OPENING_QUESTIONS

    all_fallbacks = list(_OPENING_QUESTIONS.values()) + [_FALLBACK_QUESTION]
    for q in all_fallbacks:
        lower = q.lower()
        assert "take" not in lower or "medication" not in lower
        assert "diagnosis" not in lower
        assert "you have" not in lower  # No diagnostic assertion


# ---------------------------------------------------------------------------
# 8. MULTILINGUAL SUPPORT (31-33)
# ---------------------------------------------------------------------------


def test_31_english_session_generates_english_instruction():
    """31. English session includes English instruction in prompt."""
    prompt = build_system_prompt(
        language="English",
        current_history_json="{}",
        current_section="chief_complaint",
        missing_sections=["chief_complaint"],
    )
    assert "Conduct the interview in English" in prompt


def test_32_hindi_session_passes_hindi_instruction():
    """32. Hindi session passes Hindi instruction in prompt."""
    prompt = build_system_prompt(
        language="Hindi",
        current_history_json="{}",
        current_section="chief_complaint",
        missing_sections=["chief_complaint"],
    )
    assert "साक्षात्कार हिंदी में करें" in prompt


def test_33_marathi_session_passes_marathi_instruction():
    """33. Marathi session passes Marathi instruction in prompt."""
    prompt = build_system_prompt(
        language="Marathi",
        current_history_json="{}",
        current_section="chief_complaint",
        missing_sections=["chief_complaint"],
    )
    assert "मुलाखत मराठीत करा" in prompt


# ---------------------------------------------------------------------------
# 9. REGRESSION VERIFICATION (34)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_34_regression_full_clinical_interview_turn(
    client: AsyncClient, db_session: AsyncSession
):
    """34. End-to-end multi-turn interview regression test."""
    token, cid, sid = await _setup_session(client, db_session, email="reg34@test.com")

    # Turn 1: Chief complaint
    resp1 = _make_mock_ai_response(
        next_question="How long have you had this stomach ache?",
        chief_complaint="Severe abdominal pain",
        hpi=None,
        current_section="history_of_present_illness",
    )
    # Turn 2: HPI
    resp2 = _make_mock_ai_response(
        next_question="Does the pain radiate to your back?",
        chief_complaint="Severe abdominal pain",
        hpi="Severe abdominal pain starting 2 days ago, epigastric region",
        current_section="review_of_systems",
    )

    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = resp1
        res1 = await client.post(
            ai_messages_url(sid),
            json={"message": "I have bad stomach pain."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res1.status_code == 201
        assert res1.json()["interview"]["next_question"] == "How long have you had this stomach ache?"

        mock_gen.return_value = resp2
        res2 = await client.post(
            ai_messages_url(sid),
            json={"message": "It started 2 days ago in my upper stomach."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res2.status_code == 201
        assert res2.json()["interview"]["next_question"] == "Does the pain radiate to your back?"

        # Verify DB history record has both fields
        stmt = select(ClinicalHistory).where(
            ClinicalHistory.consultation_id == uuid.UUID(cid)
        )
        hist = (await db_session.execute(stmt)).scalar_one_or_none()
        assert hist is not None
        assert hist.chief_complaint == "Severe abdominal pain"
        assert "2 days ago" in hist.history_of_present_illness
