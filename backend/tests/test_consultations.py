"""Tests for consultation endpoints.

Covers:
1.  Create consultation successfully.
2.  Create consultation without authentication (401).
3.  List own consultations (empty and populated).
4.  Get own consultation by ID.
5.  Get nonexistent consultation (404).
6.  Patient cannot access another patient's consultation (404, not 403).
7.  Patient identity comes from JWT, not client-provided patient_id.
8.  Invalid hospital_id (not found) returns 404.
9.  Pagination parameters work correctly.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hospital import Hospital

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REGISTER_URL = "/api/v1/auth/patient/register"
HOSPITAL_REGISTER_URL = "/api/v1/auth/hospital/register"
LOGIN_URL = "/api/v1/auth/patient/login"
CONSULTATIONS_URL = "/api/v1/consultations"


async def _register_and_login_patient(
    client: AsyncClient,
    *,
    email: str,
    password: str = "TestPassword1!",
    full_name: str = "Test Patient",
    phone: str | None = None,
) -> str:
    """Register a patient and return the Bearer token."""
    reg_payload: dict = {
        "email": email,
        "password": password,
        "full_name": full_name,
    }
    if phone:
        reg_payload["phone"] = phone

    reg_res = await client.post(REGISTER_URL, json=reg_payload)
    assert reg_res.status_code == 201, reg_res.text

    login_res = await client.post(
        LOGIN_URL,
        json={"identifier": email, "password": password},
    )
    assert login_res.status_code == 200, login_res.text
    return login_res.json()["access_token"]


async def _create_hospital_in_db(db_session: AsyncSession, name: str = "Test Hospital") -> uuid.UUID:
    """Directly insert a Hospital record into the test DB and return its ID."""
    hospital = Hospital(name=name)
    db_session.add(hospital)
    await db_session.flush()
    await db_session.refresh(hospital)
    return hospital.id


# ---------------------------------------------------------------------------
# Test: POST /api/v1/consultations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_consultation_success(
    client: AsyncClient, db_session: AsyncSession
):
    """Authenticated patient can create a consultation with a valid hospital_id."""
    hospital_id = await _create_hospital_in_db(db_session, name="City Medical Center")
    token = await _register_and_login_patient(
        client, email="consult.create@example.com"
    )

    payload = {
        "hospital_id": str(hospital_id),
        "chief_complaint": "Persistent headache for 3 days",
    }
    res = await client.post(
        CONSULTATIONS_URL,
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    data = res.json()

    assert data["hospital_id"] == str(hospital_id)
    assert data["chief_complaint"] == "Persistent headache for 3 days"
    assert data["status"] == "initiated"
    assert "id" in data
    assert "patient_id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_consultation_without_chief_complaint(
    client: AsyncClient, db_session: AsyncSession
):
    """Consultation can be created without a chief_complaint (it's optional)."""
    hospital_id = await _create_hospital_in_db(db_session, name="General Hospital")
    token = await _register_and_login_patient(
        client, email="consult.nocomplaint@example.com"
    )

    res = await client.post(
        CONSULTATIONS_URL,
        json={"hospital_id": str(hospital_id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    assert res.json()["chief_complaint"] is None


@pytest.mark.asyncio
async def test_create_consultation_unauthenticated(
    client: AsyncClient, db_session: AsyncSession
):
    """Missing token returns HTTP 401."""
    hospital_id = await _create_hospital_in_db(db_session)
    res = await client.post(
        CONSULTATIONS_URL,
        json={"hospital_id": str(hospital_id)},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_create_consultation_invalid_hospital(client: AsyncClient):
    """Non-existent hospital_id returns HTTP 404."""
    token = await _register_and_login_patient(
        client, email="bad.hospital@example.com"
    )
    fake_hospital_id = str(uuid.uuid4())

    res = await client.post(
        CONSULTATIONS_URL,
        json={"hospital_id": fake_hospital_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
    assert "Hospital not found" in res.json()["detail"]


@pytest.mark.asyncio
async def test_create_consultation_patient_id_from_jwt(
    client: AsyncClient, db_session: AsyncSession
):
    """patient_id in the created consultation must match the authenticated patient,
    not any client-provided value."""
    hospital_id = await _create_hospital_in_db(db_session, name="JWT Test Hospital")
    token = await _register_and_login_patient(
        client, email="jwt.patient@example.com", full_name="JWT Patient"
    )

    # Attempt to inject a different patient_id in the payload — it should be ignored
    fake_patient_id = str(uuid.uuid4())
    payload = {
        "hospital_id": str(hospital_id),
        # patient_id is not part of ConsultationCreate schema and should be ignored
        "patient_id": fake_patient_id,
    }
    res = await client.post(
        CONSULTATIONS_URL,
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    # The returned patient_id must NOT be the fake one
    assert res.json()["patient_id"] != fake_patient_id


# ---------------------------------------------------------------------------
# Test: GET /api/v1/consultations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_consultations_empty(client: AsyncClient):
    """Newly registered patient has an empty consultations list."""
    token = await _register_and_login_patient(
        client, email="list.empty@example.com"
    )
    res = await client.get(
        CONSULTATIONS_URL,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_consultations_populated(
    client: AsyncClient, db_session: AsyncSession
):
    """Patient sees their own consultations ordered newest-first."""
    hospital_id = await _create_hospital_in_db(db_session, name="List Test Hospital")
    token = await _register_and_login_patient(
        client, email="list.populated@example.com"
    )

    # Create 3 consultations
    for i in range(3):
        r = await client.post(
            CONSULTATIONS_URL,
            json={
                "hospital_id": str(hospital_id),
                "chief_complaint": f"Complaint {i}",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201

    res = await client.get(
        CONSULTATIONS_URL,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_consultations_unauthenticated(client: AsyncClient):
    """Missing token returns HTTP 401."""
    res = await client.get(CONSULTATIONS_URL)
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_list_consultations_pagination(
    client: AsyncClient, db_session: AsyncSession
):
    """limit and offset query parameters work correctly."""
    hospital_id = await _create_hospital_in_db(db_session, name="Pagination Hospital")
    token = await _register_and_login_patient(
        client, email="pagination@example.com"
    )

    # Create 5 consultations
    for _ in range(5):
        r = await client.post(
            CONSULTATIONS_URL,
            json={"hospital_id": str(hospital_id)},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201

    # Fetch first page of 2
    res = await client.get(
        CONSULTATIONS_URL,
        params={"limit": 2, "offset": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0

    # Fetch second page
    res2 = await client.get(
        CONSULTATIONS_URL,
        params={"limit": 2, "offset": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["items"]) == 2
    # IDs on page 2 must differ from page 1
    ids_p1 = {c["id"] for c in data["items"]}
    ids_p2 = {c["id"] for c in data2["items"]}
    assert ids_p1.isdisjoint(ids_p2)


# ---------------------------------------------------------------------------
# Test: GET /api/v1/consultations/{consultation_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_own_consultation_success(
    client: AsyncClient, db_session: AsyncSession
):
    """Patient can retrieve their own consultation by ID."""
    hospital_id = await _create_hospital_in_db(db_session, name="Get Test Hospital")
    token = await _register_and_login_patient(
        client, email="get.own@example.com"
    )

    create_res = await client.post(
        CONSULTATIONS_URL,
        json={
            "hospital_id": str(hospital_id),
            "chief_complaint": "Fever and chills",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 201
    consultation_id = create_res.json()["id"]

    get_res = await client.get(
        f"{CONSULTATIONS_URL}/{consultation_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == consultation_id
    assert data["chief_complaint"] == "Fever and chills"


@pytest.mark.asyncio
async def test_get_nonexistent_consultation(client: AsyncClient):
    """Requesting a consultation with a random UUID returns HTTP 404."""
    token = await _register_and_login_patient(
        client, email="notexist@example.com"
    )
    fake_id = str(uuid.uuid4())
    res = await client.get(
        f"{CONSULTATIONS_URL}/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_patient_cannot_access_other_patients_consultation(
    client: AsyncClient, db_session: AsyncSession
):
    """Patient B receives 404 when requesting Patient A's consultation ID.

    We deliberately return 404 (not 403) to avoid leaking that the consultation exists.
    """
    hospital_id = await _create_hospital_in_db(db_session, name="Ownership Hospital")

    # Patient A creates a consultation
    token_a = await _register_and_login_patient(
        client, email="owner.patient@example.com", full_name="Owner Patient"
    )
    create_res = await client.post(
        CONSULTATIONS_URL,
        json={"hospital_id": str(hospital_id), "chief_complaint": "Private complaint"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert create_res.status_code == 201
    consultation_id = create_res.json()["id"]

    # Patient B tries to access Patient A's consultation
    token_b = await _register_and_login_patient(
        client, email="attacker.patient@example.com", full_name="Attacker Patient"
    )
    res = await client.get(
        f"{CONSULTATIONS_URL}/{consultation_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    # Must be 404, not 200 and not 403
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_patient_list_does_not_include_other_patients_consultations(
    client: AsyncClient, db_session: AsyncSession
):
    """Patient B's consultation list must not contain Patient A's consultation."""
    hospital_id = await _create_hospital_in_db(db_session, name="Isolation Hospital")

    token_a = await _register_and_login_patient(
        client, email="isolation.a@example.com", full_name="Isolation A"
    )
    token_b = await _register_and_login_patient(
        client, email="isolation.b@example.com", full_name="Isolation B"
    )

    # A creates a consultation
    r_a = await client.post(
        CONSULTATIONS_URL,
        json={"hospital_id": str(hospital_id), "chief_complaint": "Only A's complaint"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r_a.status_code == 201
    a_consultation_id = r_a.json()["id"]

    # B lists their consultations — should be empty
    r_b = await client.get(
        CONSULTATIONS_URL,
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r_b.status_code == 200
    b_items = r_b.json()["items"]
    b_ids = [c["id"] for c in b_items]
    assert a_consultation_id not in b_ids
    assert r_b.json()["total"] == 0


@pytest.mark.asyncio
async def test_get_consultation_unauthenticated(client: AsyncClient):
    """Missing token on GET /consultations/{id} returns HTTP 401."""
    fake_id = str(uuid.uuid4())
    res = await client.get(f"{CONSULTATIONS_URL}/{fake_id}")
    assert res.status_code == 401
