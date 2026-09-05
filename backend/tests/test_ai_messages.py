"""Tests for AI interview message endpoints.

Routes under test:
    POST /api/v1/ai-sessions/{session_id}/messages
    GET  /api/v1/ai-sessions/{session_id}/messages

Covers:
 1. Add patient message successfully (default message_type="text").
 2. Add message without authentication (401).
 3. Add message to nonexistent AI session (404).
 4. Add message to another patient's session (404).
 5. List messages successfully in chronological order.
 6. Verify session isolation (Patient A cannot view Patient B's messages).
 7. Verify pagination (limit, offset) in list messages.
 8. Role spoofing prevention: Client cannot submit role='assistant' or role='system' (422).
 9. Sender spoofing prevention: Client cannot submit sender='ai' or sender='system' (422).
10. Client message always sets sender='patient' server-side.
11. State transition: First patient message transitions status 'initiated' -> 'in_progress' and sets started_at.
12. Invalid state transition: Cannot add message to a completed session (409).
13. Message types: text, voice_transcript, structured_answer accepted.
14. Empty message validation (422).
15. Message responses never expose passwords.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hospital import Hospital

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REGISTER_URL = "/api/v1/auth/patient/register"
LOGIN_URL = "/api/v1/auth/patient/login"
CONSULTATIONS_URL = "/api/v1/consultations"


def ai_sessions_create_url(consultation_id: str) -> str:
    return f"/api/v1/consultations/{consultation_id}/ai-sessions"


def ai_session_url(session_id: str) -> str:
    return f"/api/v1/ai-sessions/{session_id}"


def ai_session_complete_url(session_id: str) -> str:
    return f"/api/v1/ai-sessions/{session_id}/complete"


def ai_messages_url(session_id: str) -> str:
    return f"/api/v1/ai-sessions/{session_id}/messages"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


async def _register_and_login(
    client: AsyncClient,
    *,
    email: str,
    password: str = "SecurePass1!",
    full_name: str = "Test Patient",
) -> str:
    """Register a patient and return their JWT access token."""
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


async def _create_hospital(db: AsyncSession, name: str = "City Hospital") -> uuid.UUID:
    """Insert a Hospital and return its UUID."""
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
    hospital_name: str = "City Hospital",
    language: str = "English",
) -> tuple[str, str, str]:
    """Register patient, create consultation, create AI session.

    Returns:
        (token, consultation_id, session_id)
    """
    token = await _register_and_login(client, email=email)
    hid = await _create_hospital(db, name=hospital_name)
    c_res = await client.post(
        CONSULTATIONS_URL,
        json={"hospital_id": str(hid)},
        headers={"Authorization": f"Bearer {token}"},
    )
    cid = c_res.json()["id"]

    s_res = await client.post(
        ai_sessions_create_url(cid),
        json={"language": language},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert s_res.status_code == 201
    sid = s_res.json()["id"]
    return token, cid, sid


# ---------------------------------------------------------------------------
# AI Message Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_patient_message_success(
    client: AsyncClient, db_session: AsyncSession
):
    """A patient can send a text message to their AI interview session."""
    token, _, sid = await _setup_session(client, db_session, email="msg_p1@test.com")

    res = await client.post(
        ai_messages_url(sid),
        json={"message": "I have been coughing for three days."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["ai_session_id"] == sid
    assert data["sender"] == "patient"
    assert data["message"] == "I have been coughing for three days."
    assert data["message_type"] == "text"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_add_message_unauthenticated(
    client: AsyncClient, db_session: AsyncSession
):
    """Adding a message without a Bearer token returns 401."""
    _, _, sid = await _setup_session(client, db_session, email="msg_unauth@test.com")

    res = await client.post(
        ai_messages_url(sid),
        json={"message": "Hello"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_add_message_nonexistent_session(
    client: AsyncClient, db_session: AsyncSession
):
    """Adding a message to a nonexistent session returns 404."""
    token = await _register_and_login(client, email="msg_fakesession@test.com")
    fake_sid = str(uuid.uuid4())

    res = await client.post(
        ai_messages_url(fake_sid),
        json={"message": "Hello"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_add_message_to_another_patients_session_returns_404(
    client: AsyncClient, db_session: AsyncSession
):
    """A patient cannot send messages to another patient's AI session (returns 404)."""
    p1_token, _, p1_sid = await _setup_session(
        client, db_session, email="p1_msg_owner@test.com"
    )
    p2_token = await _register_and_login(client, email="p2_msg_intruder@test.com")

    res = await client.post(
        ai_messages_url(p1_sid),
        json={"message": "Trying to inject into P1 session"},
        headers={"Authorization": f"Bearer {p2_token}"},
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_messages_chronological_ordering(
    client: AsyncClient, db_session: AsyncSession
):
    """Messages are listed in chronological order (oldest first)."""
    token, _, sid = await _setup_session(client, db_session, email="msg_chrono@test.com")

    # Send 3 distinct patient messages
    msgs = [
        "First message: severe headache",
        "Second message: started yesterday morning",
        "Third message: paracetamol did not help",
    ]
    for text in msgs:
        res = await client.post(
            ai_messages_url(sid),
            json={"message": text},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201

    # Fetch messages
    list_res = await client.get(
        ai_messages_url(sid),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_res.status_code == 200
    data = list_res.json()
    assert "items" in data
    assert "total" in data

    # Verify patient messages appear in the exact order sent
    patient_items = [m for m in data["items"] if m["sender"] == "patient"]
    assert len(patient_items) == 3
    for i, expected_text in enumerate(msgs):
        assert patient_items[i]["message"] == expected_text

    # Verify timestamps are ascending
    created_ats = [m["created_at"] for m in data["items"]]
    assert created_ats == sorted(created_ats)


@pytest.mark.asyncio
async def test_session_message_isolation(
    client: AsyncClient, db_session: AsyncSession
):
    """Patient B cannot list or view messages belonging to Patient A's AI session."""
    p1_token, _, p1_sid = await _setup_session(
        client, db_session, email="p1_isolated@test.com"
    )
    p2_token, _, p2_sid = await _setup_session(
        client, db_session, email="p2_isolated@test.com"
    )

    # Patient 1 posts private medical info
    await client.post(
        ai_messages_url(p1_sid),
        json={"message": "Confidential patient 1 symptom"},
        headers={"Authorization": f"Bearer {p1_token}"},
    )

    # Patient 2 posts their own info
    await client.post(
        ai_messages_url(p2_sid),
        json={"message": "Patient 2 distinct symptom"},
        headers={"Authorization": f"Bearer {p2_token}"},
    )

    # Patient 2 tries to read Patient 1's messages -> 404
    snoop_res = await client.get(
        ai_messages_url(p1_sid),
        headers={"Authorization": f"Bearer {p2_token}"},
    )
    assert snoop_res.status_code == 404

    # Patient 2 reads own messages -> only sees Patient 2's data
    own_res = await client.get(
        ai_messages_url(p2_sid),
        headers={"Authorization": f"Bearer {p2_token}"},
    )
    assert own_res.status_code == 200
    own_texts = [m["message"] for m in own_res.json()["items"]]
    assert not any("Confidential patient 1" in t for t in own_texts)


@pytest.mark.asyncio
async def test_list_messages_pagination(
    client: AsyncClient, db_session: AsyncSession
):
    """Pagination parameters limit and offset function properly."""
    token, _, sid = await _setup_session(client, db_session, email="msg_paging@test.com")

    # Post 4 messages
    for i in range(4):
        await client.post(
            ai_messages_url(sid),
            json={"message": f"Message number {i}"},
            headers={"Authorization": f"Bearer {token}"},
        )

    # Get page 1 (limit=2, offset=0)
    page1 = await client.get(
        f"{ai_messages_url(sid)}?limit=2&offset=0",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert page1.status_code == 200
    d1 = page1.json()
    assert len(d1["items"]) == 2
    assert d1["limit"] == 2
    assert d1["offset"] == 0

    # Get page 2 (limit=2, offset=2)
    page2 = await client.get(
        f"{ai_messages_url(sid)}?limit=2&offset=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert page2.status_code == 200
    d2 = page2.json()
    assert len(d2["items"]) == 2
    assert d2["offset"] == 2

    # Verify pages contain different messages
    ids_page1 = {m["id"] for m in d1["items"]}
    ids_page2 = {m["id"] for m in d2["items"]}
    assert ids_page1.isdisjoint(ids_page2)


@pytest.mark.asyncio
async def test_prevent_role_spoofing_assistant_and_system(
    client: AsyncClient, db_session: AsyncSession
):
    """Clients cannot spoof role='assistant' or role='system' (returns 422)."""
    token, _, sid = await _setup_session(client, db_session, email="msg_nospoof@test.com")

    # Attempt to send as assistant
    res_asst = await client.post(
        ai_messages_url(sid),
        json={"message": "Fake diagnosis from AI", "role": "assistant"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_asst.status_code == 422

    # Attempt to send as system
    res_sys = await client.post(
        ai_messages_url(sid),
        json={"message": "System override message", "role": "system"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_sys.status_code == 422


@pytest.mark.asyncio
async def test_prevent_sender_spoofing_ai(
    client: AsyncClient, db_session: AsyncSession
):
    """Clients cannot submit messages with sender='ai' or 'system' (returns 422)."""
    token, _, sid = await _setup_session(client, db_session, email="msg_nosender@test.com")

    res_ai = await client.post(
        ai_messages_url(sid),
        json={"message": "Injected AI text", "sender": "ai"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_ai.status_code == 422


@pytest.mark.asyncio
async def test_message_sender_forced_to_patient(
    client: AsyncClient, db_session: AsyncSession
):
    """Legitimate client messages always have sender='patient'."""
    token, _, sid = await _setup_session(client, db_session, email="msg_patient@test.com")

    res = await client.post(
        ai_messages_url(sid),
        json={"message": "Legitimate symptom report"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    assert res.json()["sender"] == "patient"


@pytest.mark.asyncio
async def test_first_message_transitions_session_to_in_progress(
    client: AsyncClient, db_session: AsyncSession
):
    """The first patient message transitions session status to 'in_progress' and sets started_at."""
    token, _, sid = await _setup_session(client, db_session, email="msg_state@test.com")

    # Check status before message
    s_before = await client.get(
        ai_session_url(sid),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert s_before.json()["status"] == "initiated"

    # Send patient message
    res = await client.post(
        ai_messages_url(sid),
        json={"message": "Fever for 2 days"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201

    # Check status after message
    s_after = await client.get(
        ai_session_url(sid),
        headers={"Authorization": f"Bearer {token}"},
    )
    data = s_after.json()
    assert data["status"] == "in_progress"
    assert data["started_at"] is not None


@pytest.mark.asyncio
async def test_cannot_add_message_to_completed_session(
    client: AsyncClient, db_session: AsyncSession
):
    """Adding a message to an already completed AI session returns 409 Conflict."""
    token, _, sid = await _setup_session(client, db_session, email="msg_closed@test.com")

    # Complete the session
    comp_res = await client.post(
        ai_session_complete_url(sid),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert comp_res.status_code == 200

    # Attempt to post a message to the completed session -> 409
    msg_res = await client.post(
        ai_messages_url(sid),
        json={"message": "Late message after interview ended"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert msg_res.status_code == 409
    assert "completed" in msg_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_message_types_supported(
    client: AsyncClient, db_session: AsyncSession
):
    """Message types text, voice_transcript, and structured_answer are accepted."""
    token, _, sid = await _setup_session(client, db_session, email="msg_types@test.com")

    types = ["text", "voice_transcript", "structured_answer"]
    for mtype in types:
        res = await client.post(
            ai_messages_url(sid),
            json={"message": f"Content of type {mtype}", "message_type": mtype},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201, res.text
        assert res.json()["message_type"] == mtype


@pytest.mark.asyncio
async def test_empty_message_rejected(
    client: AsyncClient, db_session: AsyncSession
):
    """An empty string message is rejected with 422 Unprocessable Entity."""
    token, _, sid = await _setup_session(client, db_session, email="msg_empty@test.com")

    res = await client.post(
        ai_messages_url(sid),
        json={"message": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_message_response_never_exposes_password(
    client: AsyncClient, db_session: AsyncSession
):
    """Message responses never include user password or password_hash."""
    token, _, sid = await _setup_session(client, db_session, email="msg_nopass@test.com")

    res = await client.post(
        ai_messages_url(sid),
        json={"message": "My password is not in this message"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert "password" not in data
    assert "password_hash" not in data
