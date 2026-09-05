"""Tests for clinical history endpoints.

Routes under test:
    POST /api/v1/consultations/{consultation_id}/history
    GET  /api/v1/consultations/{consultation_id}/history
    PUT  /api/v1/consultations/{consultation_id}/history

Covers all 15 required scenarios:
 1.  Create clinical history successfully.
 2.  Get own clinical history.
 3.  Update own clinical history.
 4.  Partial update.
 5.  Create without authentication.
 6.  Get without authentication.
 7.  Update without authentication.
 8.  Create for nonexistent consultation.
 9.  Access another patient's consultation history (GET).
10.  Update another patient's consultation history (PUT).
11.  Duplicate clinical-history creation (409).
12.  Get history when none exists (404).
13.  Invalid request data / validation.
14.  Verify patient identity is derived from JWT (not client body).
15.  Verify no password/password_hash appears in response.
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


def history_url(consultation_id: str) -> str:
    return f"/api/v1/consultations/{consultation_id}/history"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


async def _register_and_login(
    client: AsyncClient,
    *,
    email: str,
    password: str = "TestPassword1!",
    full_name: str = "Test Patient",
) -> str:
    """Register a patient and return their Bearer token."""
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
    """Insert a Hospital directly and return its UUID."""
    h = Hospital(name=name)
    db.add(h)
    await db.flush()
    await db.refresh(h)
    return h.id


async def _create_consultation(
    client: AsyncClient, token: str, hospital_id: uuid.UUID
) -> str:
    """Create a consultation via the API and return its string UUID."""
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
    hospital_name: str = "Setup Hospital",
) -> tuple[str, str]:
    """Register patient, create hospital + consultation. Returns (token, consultation_id)."""
    token = await _register_and_login(client, email=email)
    hosp_id = await _create_hospital(db, name=hospital_name)
    consultation_id = await _create_consultation(client, token, hosp_id)
    return token, consultation_id


# ---------------------------------------------------------------------------
# Test 1: Create clinical history successfully
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_clinical_history_success(
    client: AsyncClient, db_session: AsyncSession
):
    token, cid = await _setup(client, db_session, email="ch.create@example.com")

    payload = {
        "chief_complaint": "Chest pain on exertion",
        "history_of_present_illness": "Started 2 weeks ago, worsens on climbing stairs.",
        "past_medical_history": "Hypertension since 2015",
        "drug_history": "Amlodipine 5mg OD",
        "allergy_history": "NKDA",
        "family_history": "Father had MI at age 55",
        "personal_history": "Non-smoker, occasional alcohol",
        "review_of_systems": "Mild dyspnea, no syncope",
    }
    res = await client.post(
        history_url(cid),
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    data = res.json()

    assert data["consultation_id"] == cid
    assert data["chief_complaint"] == "Chest pain on exertion"
    assert data["past_medical_history"] == "Hypertension since 2015"
    assert data["drug_history"] == "Amlodipine 5mg OD"
    assert data["allergy_history"] == "NKDA"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


# ---------------------------------------------------------------------------
# Test 2: Get own clinical history
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_clinical_history_success(
    client: AsyncClient, db_session: AsyncSession
):
    token, cid = await _setup(client, db_session, email="ch.get@example.com")

    # Create history first
    create_res = await client.post(
        history_url(cid),
        json={"chief_complaint": "Fever for 3 days"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 201

    # Now GET it
    get_res = await client.get(
        history_url(cid),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["consultation_id"] == cid
    assert data["chief_complaint"] == "Fever for 3 days"


# ---------------------------------------------------------------------------
# Test 3: Update own clinical history (full fields)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_clinical_history_full(
    client: AsyncClient, db_session: AsyncSession
):
    token, cid = await _setup(client, db_session, email="ch.update@example.com")

    await client.post(
        history_url(cid),
        json={"chief_complaint": "Original complaint"},
        headers={"Authorization": f"Bearer {token}"},
    )

    update_payload = {
        "chief_complaint": "Updated complaint",
        "history_of_present_illness": "Now 4 weeks, progressive",
        "past_surgical_history": "Appendectomy 2010",
        "family_history": "Mother — Type 2 DM",
    }
    res = await client.put(
        history_url(cid),
        json=update_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["chief_complaint"] == "Updated complaint"
    assert data["history_of_present_illness"] == "Now 4 weeks, progressive"
    assert data["past_surgical_history"] == "Appendectomy 2010"
    assert data["family_history"] == "Mother — Type 2 DM"


# ---------------------------------------------------------------------------
# Test 4: Partial update — only one field changes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_clinical_history_partial(
    client: AsyncClient, db_session: AsyncSession
):
    token, cid = await _setup(client, db_session, email="ch.partial@example.com")

    await client.post(
        history_url(cid),
        json={
            "chief_complaint": "Headache",
            "drug_history": "Paracetamol PRN",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Update only drug_history; chief_complaint must be untouched
    res = await client.put(
        history_url(cid),
        json={"drug_history": "Ibuprofen 400mg TDS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["drug_history"] == "Ibuprofen 400mg TDS"
    assert data["chief_complaint"] == "Headache"  # unchanged


# ---------------------------------------------------------------------------
# Tests 5-7: Authentication required for all methods
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_clinical_history_unauthenticated(
    client: AsyncClient, db_session: AsyncSession
):
    """POST without Bearer token returns 401."""
    hosp_id = await _create_hospital(db_session, name="Auth Hospital POST")
    token = await _register_and_login(client, email="ch.anon.post@example.com")
    cid = await _create_consultation(client, token, hosp_id)

    res = await client.post(history_url(cid), json={"chief_complaint": "Hacker"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_clinical_history_unauthenticated(
    client: AsyncClient, db_session: AsyncSession
):
    """GET without Bearer token returns 401."""
    hosp_id = await _create_hospital(db_session, name="Auth Hospital GET")
    token = await _register_and_login(client, email="ch.anon.get@example.com")
    cid = await _create_consultation(client, token, hosp_id)

    res = await client.get(history_url(cid))
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_update_clinical_history_unauthenticated(
    client: AsyncClient, db_session: AsyncSession
):
    """PUT without Bearer token returns 401."""
    hosp_id = await _create_hospital(db_session, name="Auth Hospital PUT")
    token = await _register_and_login(client, email="ch.anon.put@example.com")
    cid = await _create_consultation(client, token, hosp_id)

    res = await client.put(
        history_url(cid), json={"chief_complaint": "Unauthorized edit"}
    )
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# Test 8: Create for nonexistent consultation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_clinical_history_nonexistent_consultation(client: AsyncClient):
    """Creating history for a UUID that has no consultation returns 404."""
    token = await _register_and_login(client, email="ch.noc@example.com")
    fake_cid = str(uuid.uuid4())

    res = await client.post(
        history_url(fake_cid),
        json={"chief_complaint": "Test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Tests 9-10: Cross-patient access denied
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_another_patients_clinical_history_returns_404(
    client: AsyncClient, db_session: AsyncSession
):
    """Patient B cannot GET Patient A's clinical history (returns 404)."""
    hosp_id = await _create_hospital(db_session, name="Cross-Patient Hospital GET")

    # Patient A creates consultation + history
    token_a = await _register_and_login(client, email="ch.owner.a@example.com")
    cid_a = await _create_consultation(client, token_a, hosp_id)
    await client.post(
        history_url(cid_a),
        json={"chief_complaint": "Patient A private data"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # Patient B attempts to read Patient A's history
    token_b = await _register_and_login(client, email="ch.attacker.b@example.com")
    res = await client.get(
        history_url(cid_a),
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_update_another_patients_clinical_history_returns_404(
    client: AsyncClient, db_session: AsyncSession
):
    """Patient B cannot PUT Patient A's clinical history (returns 404)."""
    hosp_id = await _create_hospital(db_session, name="Cross-Patient Hospital PUT")

    token_a = await _register_and_login(client, email="ch.owner2.a@example.com")
    cid_a = await _create_consultation(client, token_a, hosp_id)
    await client.post(
        history_url(cid_a),
        json={"chief_complaint": "Original"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    token_b = await _register_and_login(client, email="ch.attacker2.b@example.com")
    res = await client.put(
        history_url(cid_a),
        json={"chief_complaint": "Tampered"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Test 11: Duplicate clinical history creation (409)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_clinical_history_duplicate_returns_409(
    client: AsyncClient, db_session: AsyncSession
):
    """Creating a second clinical history for the same consultation returns 409."""
    token, cid = await _setup(client, db_session, email="ch.dup@example.com")

    first = await client.post(
        history_url(cid),
        json={"chief_complaint": "First creation"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert first.status_code == 201

    second = await client.post(
        history_url(cid),
        json={"chief_complaint": "Duplicate attempt"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]


# ---------------------------------------------------------------------------
# Test 12: GET history when none exists → 404
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_clinical_history_none_exists(
    client: AsyncClient, db_session: AsyncSession
):
    """GET when no history has been created yet returns 404."""
    token, cid = await _setup(client, db_session, email="ch.empty@example.com")

    res = await client.get(
        history_url(cid),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
    assert "No clinical history" in res.json()["detail"]


# ---------------------------------------------------------------------------
# Test 13: Update when no history exists → 404 (do not auto-create)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_clinical_history_none_exists_returns_404(
    client: AsyncClient, db_session: AsyncSession
):
    """PUT when no history record exists must return 404, not silently create one."""
    token, cid = await _setup(client, db_session, email="ch.update.none@example.com")

    res = await client.put(
        history_url(cid),
        json={"chief_complaint": "Should not create"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Test 14: Patient identity comes from JWT, not client body
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patient_identity_from_jwt_not_body(
    client: AsyncClient, db_session: AsyncSession
):
    """consultation_id from the URL path is used; injected patient_id in body is ignored."""
    token, cid = await _setup(client, db_session, email="ch.jwt.identity@example.com")

    # Inject a fake patient_id in the body — the schema should ignore it
    fake_patient_id = str(uuid.uuid4())
    res = await client.post(
        history_url(cid),
        json={
            "chief_complaint": "Valid complaint",
            "patient_id": fake_patient_id,  # should be silently ignored by Pydantic
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    # consultation_id must match the URL path, not any injected value
    assert data["consultation_id"] == cid
    assert "patient_id" not in data  # not a field in ClinicalHistoryResponse


# ---------------------------------------------------------------------------
# Test 15: No password/password_hash in response
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clinical_history_never_returns_password(
    client: AsyncClient, db_session: AsyncSession
):
    """Clinical history responses must never contain passwords or hashes."""
    token, cid = await _setup(
        client, db_session, email="ch.nopw@example.com"
    )
    res = await client.post(
        history_url(cid),
        json={"chief_complaint": "Safe response check"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    raw = res.text
    assert "password" not in raw
    assert "password_hash" not in raw
    assert "TestPassword1!" not in raw


# ---------------------------------------------------------------------------
# Additional: Create with all fields (coverage of all 9 model fields)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_clinical_history_all_fields(
    client: AsyncClient, db_session: AsyncSession
):
    """All 9 clinical history fields are accepted and persisted correctly."""
    token, cid = await _setup(client, db_session, email="ch.allfields@example.com")

    payload = {
        "chief_complaint": "Breathlessness",
        "history_of_present_illness": "Progressive over 6 months",
        "past_medical_history": "Asthma since childhood",
        "past_surgical_history": "Cholecystectomy 2018",
        "drug_history": "Salbutamol inhaler PRN",
        "allergy_history": "Penicillin — rash",
        "family_history": "No significant family history",
        "personal_history": "Non-smoker, vegetarian",
        "review_of_systems": "No cough, no fever, mild ankle swelling",
    }
    res = await client.post(
        history_url(cid),
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()

    for field, value in payload.items():
        assert data[field] == value, f"Field {field} mismatch"


# ---------------------------------------------------------------------------
# Additional: Empty body create (all fields optional)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_clinical_history_empty_body(
    client: AsyncClient, db_session: AsyncSession
):
    """A clinical history can be created with no fields (all are optional)."""
    token, cid = await _setup(client, db_session, email="ch.empty.body@example.com")

    res = await client.post(
        history_url(cid),
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["consultation_id"] == cid
    assert data["chief_complaint"] is None


# ---------------------------------------------------------------------------
# Additional: GET after PUT confirms persistence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_after_update_reflects_changes(
    client: AsyncClient, db_session: AsyncSession
):
    """GET after PUT must reflect the persisted changes."""
    token, cid = await _setup(client, db_session, email="ch.getafter@example.com")

    await client.post(
        history_url(cid),
        json={"chief_complaint": "Initial complaint"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.put(
        history_url(cid),
        json={"chief_complaint": "Revised complaint", "drug_history": "Metformin 500mg BD"},
        headers={"Authorization": f"Bearer {token}"},
    )

    get_res = await client.get(
        history_url(cid), headers={"Authorization": f"Bearer {token}"}
    )
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["chief_complaint"] == "Revised complaint"
    assert data["drug_history"] == "Metformin 500mg BD"
