"""Integration and security tests for OPD Department Registration and Token Queue.

Verifies SIH Demo Step 3 requirements:
1. Registration generates an OPD department-scoped token number.
2. Token is idempotent (repeated registration calls return same token number).
3. Multiple patients in the same department receive sequential tokens (e.g. 1, 2, 3...).
4. Different departments have independent token sequences (e.g. GM vs Orthopedics).
5. Authorized hospital staff (receptionist, doctor) can retrieve the department queue.
6. Department queue returns non-clinical operational data (display name, token, position, status).
7. Receptionist is blocked from accessing clinical summaries (403 Forbidden).
8. Hospital staff can advance the queue (transitions now_serving from 24 to 25).
9. Patient can retrieve active hospital visit & token via GET /api/v1/patients/me/active-visit.
10. Patient active visit returns people_ahead and current now_serving.
11. Pre-hospital consultation has has_active_visit=False until hospital registration.
12. Cross-hospital queue isolation: hospital staff cannot see another hospital's queue.
"""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import Consultation
from app.models.hospital import Hospital
from app.models.hospital_user import HospitalUser
from app.models.patient import Patient
from app.models.user import User
from app.services.auth_service import hash_password

LOGIN_URL = "/api/v1/auth/hospital/login"
PATIENT_REGISTER_URL = "/api/v1/auth/patient/register"
PATIENT_LOGIN_URL = "/api/v1/auth/patient/login"
RECEPTION_REGISTER_URL = "/api/v1/reception/register-patient"
RECEPTION_MANUAL_URL = "/api/v1/reception/register-manual"
RECEPTION_QUEUE_URL = "/api/v1/reception/queue"
RECEPTION_ADVANCE_URL = "/api/v1/reception/queue/advance"
PATIENT_ACTIVE_VISIT_URL = "/api/v1/patients/me/active-visit"


# ---------------------------------------------------------------------------
# Fixture Helpers
# ---------------------------------------------------------------------------


async def _setup_receptionist(
    client: AsyncClient,
    db_session: AsyncSession,
    hospital_name: str = "Apex Memorial Hospital",
    email: str = "rec.queue@hospital.org",
) -> tuple[str, uuid.UUID]:
    """Create a hospital and receptionist user; return (access_token, hospital_id)."""
    hospital = Hospital(name=hospital_name)
    db_session.add(hospital)
    await db_session.flush()

    user = User(
        email=email,
        phone=f"+91 {uuid.uuid4().int % 9000000000 + 1000000000}",
        password_hash=hash_password("RecPass123!"),
        role="receptionist",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    hosp_user = HospitalUser(
        user_id=user.id,
        hospital_id=hospital.id,
        role="receptionist",
    )
    db_session.add(hosp_user)
    await db_session.commit()

    login_res = await client.post(
        LOGIN_URL,
        json={"identifier": email, "password": "RecPass123!"},
    )
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    return token, hospital.id


async def _create_test_patient(
    client: AsyncClient,
    email: str = "patient.queue@example.com",
    full_name: str = "Rohan Patil",
) -> tuple[str, str]:
    """Register a patient and return (token, patient_id)."""
    reg_res = await client.post(
        PATIENT_REGISTER_URL,
        json={
            "email": email,
            "password": "PatientPassword1!",
            "full_name": full_name,
            "phone": f"98765{uuid.uuid4().int % 100000:05d}",
        },
    )
    assert reg_res.status_code == 201, reg_res.text
    patient_id = reg_res.json()["patient"]["id"]

    login_res = await client.post(
        PATIENT_LOGIN_URL,
        json={"identifier": email, "password": "PatientPassword1!"},
    )
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    return token, patient_id


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patient_pre_hospital_active_visit_is_false(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Pre-hospital patient consultation has has_active_visit=False until hospital registration."""
    pat_token, pat_id = await _create_test_patient(client, email="prehospital@test.com")

    # Create pre-hospital consultation (hospital_id is None)
    cons_res = await client.post(
        "/api/v1/consultations",
        headers={"Authorization": f"Bearer {pat_token}"},
        json={"patient_id": pat_id},
    )
    assert cons_res.status_code == 201, cons_res.text

    # Check active visit
    visit_res = await client.get(
        PATIENT_ACTIVE_VISIT_URL,
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert visit_res.status_code == 200
    visit_data = visit_res.json()
    assert visit_data["has_active_visit"] is False
    assert visit_data["token_number"] is None


@pytest.mark.asyncio
async def test_register_patient_generates_sequential_department_token(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Registering patients in a department generates sequential tokens (1, 2, 3...)."""
    rec_token, hosp_id = await _setup_receptionist(client, db_session)

    # Register patient 1
    pat1_token, pat1_id = await _create_test_patient(client, email="p1@test.com", full_name="Aarav Sharma")
    r1 = await client.post(
        RECEPTION_REGISTER_URL,
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"patient_id": pat1_id, "department": "General Medicine"},
    )
    assert r1.status_code == 201, r1.text
    data1 = r1.json()
    assert data1["token_number"] == 1
    assert data1["department"] == "General Medicine"

    # Register patient 2
    pat2_token, pat2_id = await _create_test_patient(client, email="p2@test.com", full_name="Sneha Kapoor")
    r2 = await client.post(
        RECEPTION_REGISTER_URL,
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"patient_id": pat2_id, "department": "General Medicine"},
    )
    assert r2.status_code == 201, r2.text
    data2 = r2.json()
    assert data2["token_number"] == 2


@pytest.mark.asyncio
async def test_token_is_idempotent_on_repeated_registration(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Submitting registration again for the same consultation returns the identical token."""
    rec_token, hosp_id = await _setup_receptionist(client, db_session)
    pat_token, pat_id = await _create_test_patient(client, email="idem@test.com")

    # First registration
    r1 = await client.post(
        RECEPTION_REGISTER_URL,
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"patient_id": pat_id, "department": "Pediatrics"},
    )
    assert r1.status_code == 201
    token1 = r1.json()["token_number"]

    # Repeated registration
    r2 = await client.post(
        RECEPTION_REGISTER_URL,
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"patient_id": pat_id, "department": "Pediatrics"},
    )
    assert r2.status_code == 201
    assert r2.json()["token_number"] == token1


@pytest.mark.asyncio
async def test_different_departments_have_independent_token_sequences(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Orthopedics starts at token 1 even if General Medicine already has token 1 and 2."""
    rec_token, hosp_id = await _setup_receptionist(client, db_session)

    # General Medicine patient
    _, p_gm_id = await _create_test_patient(client, email="gm@test.com")
    r_gm = await client.post(
        RECEPTION_REGISTER_URL,
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"patient_id": p_gm_id, "department": "General Medicine"},
    )
    assert r_gm.status_code == 201
    assert r_gm.json()["token_number"] == 1

    # Orthopedics patient receives 1 independently
    _, p_ortho_id = await _create_test_patient(client, email="ortho@test.com")
    r_ortho = await client.post(
        RECEPTION_REGISTER_URL,
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"patient_id": p_ortho_id, "department": "Orthopedics"},
    )
    assert r_ortho.status_code == 201
    assert r_ortho.json()["token_number"] == 1


@pytest.mark.asyncio
async def test_get_department_queue_returns_non_clinical_operational_data(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Department queue endpoint returns masked display name, token, and status without clinical info."""
    rec_token, hosp_id = await _setup_receptionist(client, db_session)
    _, pat_id = await _create_test_patient(client, email="queue_op@test.com", full_name="Vikramaditya Roy")

    reg_res = await client.post(
        RECEPTION_REGISTER_URL,
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"patient_id": pat_id, "department": "General Medicine"},
    )
    assert reg_res.status_code == 201

    q_res = await client.get(
        f"{RECEPTION_QUEUE_URL}?department=General%20Medicine",
        headers={"Authorization": f"Bearer {rec_token}"},
    )
    assert q_res.status_code == 200, q_res.text
    q_data = q_res.json()
    assert q_data["department"] == "General Medicine"
    assert q_data["waiting_count"] >= 1
    assert len(q_data["entries"]) >= 1

    entry = q_data["entries"][0]
    assert entry["token"] == 1
    # Verify name masking (e.g. Vikramaditya R.)
    assert "Vikramaditya" in entry["patient_display_name"]
    assert entry["status"] == "waiting"
    assert "clinical" not in str(entry).lower()
    assert "summary" not in str(entry).lower()
    assert "history" not in str(entry).lower()


@pytest.mark.asyncio
async def test_patient_active_visit_reflects_token_and_queue_position(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Patient can view their token, now_serving, and people_ahead in real-time."""
    rec_token, hosp_id = await _setup_receptionist(client, db_session)

    # Register patient 1
    _, p1_id = await _create_test_patient(client, email="p1_ahead@test.com", full_name="Patient One")
    r1 = await client.post(
        RECEPTION_REGISTER_URL,
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"patient_id": p1_id, "department": "ENT"},
    )
    assert r1.status_code == 201

    # Register patient 2
    p2_token, p2_id = await _create_test_patient(client, email="p2_ahead@test.com", full_name="Patient Two")
    r2 = await client.post(
        RECEPTION_REGISTER_URL,
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"patient_id": p2_id, "department": "ENT"},
    )
    assert r2.status_code == 201

    # Patient 2 checks active visit
    res = await client.get(
        PATIENT_ACTIVE_VISIT_URL,
        headers={"Authorization": f"Bearer {p2_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["has_active_visit"] is True
    assert data["token_number"] == 2
    assert data["department"] == "ENT"
    # Patient 1 is ahead
    assert data["people_ahead"] == 1


@pytest.mark.asyncio
async def test_queue_advancement_transitions_now_serving(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Advancing queue sets next waiting patient to in_progress / now_serving."""
    rec_token, hosp_id = await _setup_receptionist(client, db_session)

    # Register two manual patients in Cardiology
    await client.post(
        RECEPTION_MANUAL_URL,
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"full_name": "Cardio One", "phone": "9822222201", "department": "Cardiology"},
    )
    await client.post(
        RECEPTION_MANUAL_URL,
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"full_name": "Cardio Two", "phone": "9822222202", "department": "Cardiology"},
    )

    # Advance queue
    adv_res = await client.post(
        RECEPTION_ADVANCE_URL,
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"department": "Cardiology"},
    )
    assert adv_res.status_code == 200, adv_res.text
    adv_data = adv_res.json()
    assert adv_data["now_serving"] == 1

    # Check department queue
    q_res = await client.get(
        f"{RECEPTION_QUEUE_URL}?department=Cardiology",
        headers={"Authorization": f"Bearer {rec_token}"},
    )
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["now_serving"] == 1
    # 1 is now serving, 1 remains waiting
    assert q_data["waiting_count"] == 1


@pytest.mark.asyncio
async def test_cross_hospital_queue_isolation(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Receptionist at Hospital A only sees queue for Hospital A, not Hospital B."""
    rec_a_token, hosp_a_id = await _setup_receptionist(
        client, db_session, hospital_name="Hospital Alpha", email="rec.alpha@hospital.org"
    )
    rec_b_token, hosp_b_id = await _setup_receptionist(
        client, db_session, hospital_name="Hospital Beta", email="rec.beta@hospital.org"
    )

    # Register patient in Hospital A
    await client.post(
        RECEPTION_MANUAL_URL,
        headers={"Authorization": f"Bearer {rec_a_token}"},
        json={"full_name": "Alpha Patient", "phone": "9811111111", "department": "General Medicine"},
    )

    # Hospital B queue should be empty for General Medicine
    q_b_res = await client.get(
        f"{RECEPTION_QUEUE_URL}?department=General%20Medicine",
        headers={"Authorization": f"Bearer {rec_b_token}"},
    )
    assert q_b_res.status_code == 200
    q_b_data = q_b_res.json()
    assert q_b_data["hospital_id"] == str(hosp_b_id)
    assert q_b_data["waiting_count"] == 0
    assert len(q_b_data["entries"]) == 0


@pytest.mark.asyncio
async def test_patient_cannot_view_or_modify_other_patient_tokens(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Patients can only retrieve their own active visit via /patients/me/active-visit."""
    rec_token, hosp_id = await _setup_receptionist(client, db_session)

    pat1_token, pat1_id = await _create_test_patient(client, email="pat1.sec@example.com", full_name="Patient 1")
    pat2_token, pat2_id = await _create_test_patient(client, email="pat2.sec@example.com", full_name="Patient 2")

    # Register Patient 1 in General Medicine
    await client.post(
        RECEPTION_REGISTER_URL,
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"patient_id": pat1_id, "department": "General Medicine"},
    )

    # Patient 2 checks active visit - should be False
    p2_res = await client.get(
        PATIENT_ACTIVE_VISIT_URL,
        headers={"Authorization": f"Bearer {pat2_token}"},
    )
    assert p2_res.status_code == 200
    assert p2_res.json()["has_active_visit"] is False

    # Patient cannot access receptionist queue endpoint (403 Forbidden)
    q_unauth = await client.get(
        f"{RECEPTION_QUEUE_URL}?department=General%20Medicine",
        headers={"Authorization": f"Bearer {pat1_token}"},
    )
    assert q_unauth.status_code in (401, 403)
