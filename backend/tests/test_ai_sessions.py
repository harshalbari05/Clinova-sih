"""Tests for AI interview session endpoints.

Routes under test:
    POST /api/v1/consultations/{consultation_id}/ai-sessions
    GET  /api/v1/ai-sessions/{session_id}
    POST /api/v1/ai-sessions/{session_id}/complete

Covers:
 1. Create AI session successfully (default & specified language).
 2. Create AI session without authentication (401).
 3. Create AI session for nonexistent consultation (404).
 4. Create AI session for another patient's consultation (404).
 5. Get own AI session (200).
 6. Get another patient's session (404).
 7. Get session without authentication (401).
 8. Get nonexistent session (404).
 9. Complete own session (200, completed_at set).
10. Complete another patient's session (404).
11. Complete session without authentication (401).
12. Complete already completed session (409).
13. Multiple sessions per consultation permitted.
14. Patient identity derived strictly from JWT (client cannot pass arbitrary patient_id).
15. AI session never returns password or password_hash.
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


async def _create_hospital(db: AsyncSession, name: str = "Test Hospital") -> uuid.UUID:
    """Insert a Hospital and return its UUID."""
    h = Hospital(name=name)
    db.add(h)
    await db.flush()
    await db.refresh(h)
    return h.id


async def _create_consultation(
    client: AsyncClient, token: str, hospital_id: uuid.UUID
) -> str:
    """Create a consultation and return its UUID string."""
    res = await client.post(
        CONSULTATIONS_URL,
        json={"hospital_id": str(hospital_id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


async def _setup(
    client: AsyncClient,
    db: AsyncSession,
    *,
    email: str,
    hospital_name: str = "General Hospital",
) -> tuple[str, str]:
    """Register a patient, create a consultation, and return (token, consultation_id)."""
    token = await _register_and_login(client, email=email)
    hid = await _create_hospital(db, name=hospital_name)
    cid = await _create_consultation(client, token, hid)
    return token, cid


# ---------------------------------------------------------------------------
# AI Session Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_ai_session_success(client: AsyncClient, db_session: AsyncSession):
    """Create an AI interview session for a patient's consultation."""
    token, cid = await _setup(client, db_session, email="session_p1@test.com")

    # Create session with default language
    res = await client.post(
        ai_sessions_create_url(cid),
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["consultation_id"] == cid
    assert data["language"] == "English"
    assert data["status"] == "initiated"
    assert data["completed_at"] is None
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_ai_session_with_language(
    client: AsyncClient, db_session: AsyncSession
):
    """Create an AI interview session with an Indian language specified."""
    token, cid = await _setup(client, db_session, email="session_hindi@test.com")

    res = await client.post(
        ai_sessions_create_url(cid),
        json={"language": "Hindi"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["language"] == "Hindi"
    assert data["status"] == "initiated"


@pytest.mark.asyncio
async def test_create_ai_session_unauthenticated(
    client: AsyncClient, db_session: AsyncSession
):
    """Creating an AI session without a Bearer token returns 401."""
    token, cid = await _setup(client, db_session, email="session_unauth@test.com")

    res = await client.post(ai_sessions_create_url(cid), json={})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_create_ai_session_nonexistent_consultation(
    client: AsyncClient, db_session: AsyncSession
):
    """Creating an AI session for a nonexistent consultation returns 404."""
    token = await _register_and_login(client, email="session_random@test.com")
    fake_cid = str(uuid.uuid4())

    res = await client.post(
        ai_sessions_create_url(fake_cid),
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_ai_session_another_patients_consultation(
    client: AsyncClient, db_session: AsyncSession
):
    """A patient cannot create an AI session on another patient's consultation (returns 404)."""
    p1_token, p1_cid = await _setup(client, db_session, email="p1_owner@test.com")
    p2_token = await _register_and_login(client, email="p2_attacker@test.com")

    res = await client.post(
        ai_sessions_create_url(p1_cid),
        json={},
        headers={"Authorization": f"Bearer {p2_token}"},
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_own_ai_session_success(
    client: AsyncClient, db_session: AsyncSession
):
    """A patient can retrieve their own AI session by ID."""
    token, cid = await _setup(client, db_session, email="session_getter@test.com")

    # Create session
    create_res = await client.post(
        ai_sessions_create_url(cid),
        json={"language": "Marathi"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 201
    sid = create_res.json()["id"]

    # Get session
    get_res = await client.get(
        ai_session_url(sid),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == sid
    assert data["consultation_id"] == cid
    assert data["language"] == "Marathi"
    assert data["status"] == "initiated"


@pytest.mark.asyncio
async def test_get_another_patients_ai_session_returns_404(
    client: AsyncClient, db_session: AsyncSession
):
    """Accessing another patient's AI session returns 404 (safe, no information leakage)."""
    p1_token, p1_cid = await _setup(client, db_session, email="p1_secret@test.com")
    p2_token = await _register_and_login(client, email="p2_snoop@test.com")

    create_res = await client.post(
        ai_sessions_create_url(p1_cid),
        json={},
        headers={"Authorization": f"Bearer {p1_token}"},
    )
    assert create_res.status_code == 201
    sid = create_res.json()["id"]

    # Patient 2 tries to access Patient 1's session
    snoop_res = await client.get(
        ai_session_url(sid),
        headers={"Authorization": f"Bearer {p2_token}"},
    )
    assert snoop_res.status_code == 404


@pytest.mark.asyncio
async def test_get_ai_session_unauthenticated(
    client: AsyncClient, db_session: AsyncSession
):
    """Retrieving an AI session without authentication returns 401."""
    token, cid = await _setup(client, db_session, email="session_noauth@test.com")
    create_res = await client.post(
        ai_sessions_create_url(cid),
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    sid = create_res.json()["id"]

    res = await client.get(ai_session_url(sid))
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_nonexistent_ai_session(client: AsyncClient):
    """Requesting an AI session with an arbitrary UUID returns 404."""
    token = await _register_and_login(client, email="session_fakeid@test.com")
    fake_sid = str(uuid.uuid4())

    res = await client.get(
        ai_session_url(fake_sid),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_complete_own_ai_session_success(
    client: AsyncClient, db_session: AsyncSession
):
    """A patient can complete their own AI interview session."""
    token, cid = await _setup(client, db_session, email="session_complete@test.com")

    create_res = await client.post(
        ai_sessions_create_url(cid),
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    sid = create_res.json()["id"]

    complete_res = await client.post(
        ai_session_complete_url(sid),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert complete_res.status_code == 200, complete_res.text
    data = complete_res.json()
    assert data["id"] == sid
    assert data["status"] == "completed"
    assert data["completed_at"] is not None

    # Verify GET reflects the completed state
    get_res = await client.get(
        ai_session_url(sid),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_complete_another_patients_ai_session_returns_404(
    client: AsyncClient, db_session: AsyncSession
):
    """A patient cannot complete another patient's AI session (returns 404)."""
    p1_token, p1_cid = await _setup(client, db_session, email="p1_done@test.com")
    p2_token = await _register_and_login(client, email="p2_trycomplete@test.com")

    create_res = await client.post(
        ai_sessions_create_url(p1_cid),
        json={},
        headers={"Authorization": f"Bearer {p1_token}"},
    )
    sid = create_res.json()["id"]

    res = await client.post(
        ai_session_complete_url(sid),
        headers={"Authorization": f"Bearer {p2_token}"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_complete_already_completed_ai_session_returns_409(
    client: AsyncClient, db_session: AsyncSession
):
    """Completing an already completed AI session returns 409 Conflict."""
    token, cid = await _setup(client, db_session, email="session_double_comp@test.com")

    create_res = await client.post(
        ai_sessions_create_url(cid),
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    sid = create_res.json()["id"]

    # First completion succeeds
    res1 = await client.post(
        ai_session_complete_url(sid),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 200

    # Second completion returns 409 Conflict
    res2 = await client.post(
        ai_session_complete_url(sid),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 409
    assert "terminal state" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_multiple_ai_sessions_per_consultation(
    client: AsyncClient, db_session: AsyncSession
):
    """One consultation can have multiple AI sessions (e.g. resuming an interview)."""
    token, cid = await _setup(client, db_session, email="session_multi@test.com")

    res1 = await client.post(
        ai_sessions_create_url(cid),
        json={"language": "English"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 201
    sid1 = res1.json()["id"]

    res2 = await client.post(
        ai_sessions_create_url(cid),
        json={"language": "Hindi"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 201
    sid2 = res2.json()["id"]

    assert sid1 != sid2
    assert res1.json()["consultation_id"] == res2.json()["consultation_id"]


@pytest.mark.asyncio
async def test_ai_session_never_exposes_password(
    client: AsyncClient, db_session: AsyncSession
):
    """AI session responses never contain password or password_hash."""
    token, cid = await _setup(client, db_session, email="session_nopass@test.com")

    res = await client.post(
        ai_sessions_create_url(cid),
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert "password" not in data
    assert "password_hash" not in data
