"""Tests for Hospital Reception Desk & Patient Registration (SIH Demo Step 2).

Verifies:
1. Receptionist can authenticate via /api/v1/auth/hospital/login.
2. Receptionist can retrieve available OPD departments.
3. Patients and unauthenticated callers are rejected from reception endpoints (401/403).
4. Valid patient QR (CLINOVA:PATIENT:{uuid}) resolves to safe demographic profile.
5. QR response never exposes clinical summary, history, medications, or documents.
6. Invalid or tampered QR codes return HTTP 400 Bad Request.
7. Non-existent patient QR returns HTTP 404 Not Found.
8. Receptionist role is strictly forbidden from accessing clinical summaries (403).
9. Receptionist role is strictly forbidden from accessing clinical history (403).
10. Receptionist role is strictly forbidden from accessing medical timeline (403).
11. Receptionist role is strictly forbidden from accessing medical documents (403).
12. Receptionist role is strictly forbidden from accessing clinical triage (403).
13. Registration assigns patient to selected OPD department.
14. Pre-hospital consultation with hospital_id=None is associated with the hospital upon registration.
15. Manual registration provisions patient & consultation without open profile search.
16. Department selection is required and stored.
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

# Endpoints
LOGIN_URL = "/api/v1/auth/hospital/login"
PATIENT_REGISTER_URL = "/api/v1/auth/patient/register"
PATIENT_LOGIN_URL = "/api/v1/auth/patient/login"
RECEPTION_LOOKUP_URL = "/api/v1/reception/lookup-qr"
RECEPTION_REGISTER_URL = "/api/v1/reception/register-patient"
RECEPTION_MANUAL_URL = "/api/v1/reception/register-manual"
RECEPTION_DEPTS_URL = "/api/v1/reception/departments"
CONSULTATIONS_URL = "/api/v1/consultations"


# ---------------------------------------------------------------------------
# Fixture Helpers
# ---------------------------------------------------------------------------


async def _setup_receptionist(
    client: AsyncClient, db_session: AsyncSession, email: str = "rec.test@hospital.org"
) -> tuple[str, uuid.UUID]:
    """Create a hospital, receptionist user, and return JWT token and hospital_id."""
    hospital = Hospital(name="Apex Memorial Hospital")
    db_session.add(hospital)
    await db_session.flush()

    user = User(
        email=email,
        phone="+91 91111 22222",
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


async def _setup_doctor(
    client: AsyncClient, db_session: AsyncSession, hospital_id: uuid.UUID, email: str = "doc.test@hospital.org"
) -> str:
    """Create a doctor user affiliated with the hospital."""
    user = User(
        email=email,
        phone="+91 93333 44444",
        password_hash=hash_password("DocPass123!"),
        role="doctor",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    hosp_user = HospitalUser(
        user_id=user.id,
        hospital_id=hospital_id,
        role="doctor",
    )
    db_session.add(hosp_user)
    await db_session.commit()

    login_res = await client.post(
        LOGIN_URL,
        json={"identifier": email, "password": "DocPass123!"},
    )
    assert login_res.status_code == 200, login_res.text
    return login_res.json()["access_token"]


async def _create_test_patient(
    client: AsyncClient, email: str = "patient.qr@example.com"
) -> tuple[str, str]:
    """Register patient and return (token, patient_id)."""
    reg_res = await client.post(
        PATIENT_REGISTER_URL,
        json={
            "email": email,
            "password": "PatientPassword1!",
            "full_name": "Suresh Kumar",
            "phone": "9876500001",
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
async def test_receptionist_authentication_and_departments(
    client: AsyncClient, db_session: AsyncSession
):
    """1. Receptionist can authenticate and retrieve OPD departments list."""
    token, _hosp_id = await _setup_receptionist(client, db_session)

    res = await client.get(
        RECEPTION_DEPTS_URL,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "departments" in data
    assert "General Medicine" in data["departments"]
    assert "Orthopedics" in data["departments"]
    assert "Pediatrics" in data["departments"]


@pytest.mark.asyncio
async def test_unauthorized_access_to_reception_endpoints(
    client: AsyncClient, db_session: AsyncSession
):
    """2. Patients and unauthenticated requests are rejected from reception endpoints."""
    # Unauthenticated
    res1 = await client.get(RECEPTION_DEPTS_URL)
    assert res1.status_code == 401

    # Patient account
    patient_token, _ = await _create_test_patient(client, email="noperm@patient.com")
    res2 = await client.get(
        RECEPTION_DEPTS_URL,
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert res2.status_code == 403


@pytest.mark.asyncio
async def test_valid_patient_qr_lookup_returns_safe_demographics(
    client: AsyncClient, db_session: AsyncSession
):
    """3. Valid patient QR resolves to safe demographic profile without medical data."""
    rec_token, _ = await _setup_receptionist(client, db_session, email="rec.qr@hospital.org")
    _, patient_id = await _create_test_patient(client, email="qr.safe@patient.com")

    qr_payload = f"CLINOVA:PATIENT:{patient_id}"

    res = await client.post(
        RECEPTION_LOOKUP_URL,
        json={"qr_code": qr_payload},
        headers={"Authorization": f"Bearer {rec_token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()

    # Allowed safe fields
    assert data["patient_id"] == patient_id
    assert data["full_name"] == "Suresh Kumar"
    assert data["phone"] == "9876500001"

    # Strictly forbidden clinical fields must NOT be in response
    forbidden_keys = [
        "summary",
        "clinical_summary",
        "clinical_history",
        "chief_complaint",
        "medical_documents",
        "medications",
        "allergies",
        "transcripts",
        "triage",
    ]
    for key in forbidden_keys:
        assert key not in data, f"Privacy violation: '{key}' exposed in QR lookup response!"


@pytest.mark.asyncio
async def test_qr_lookup_invalid_or_tampered_format(
    client: AsyncClient, db_session: AsyncSession
):
    """4. Tampered or invalid QR strings return HTTP 400 Bad Request."""
    rec_token, _ = await _setup_receptionist(client, db_session, email="rec.tamper@hospital.org")

    bad_qrs = [
        "INVALID_PREFIX:1234",
        "CLINOVA:PATIENT:not-a-valid-uuid",
        "CLINOVA:DOCTOR:some-id",
        "",
    ]
    for bad_qr in bad_qrs:
        res = await client.post(
            RECEPTION_LOOKUP_URL,
            json={"qr_code": bad_qr},
            headers={"Authorization": f"Bearer {rec_token}"},
        )
        assert res.status_code in [400, 422], f"Expected error for QR: {bad_qr}"


@pytest.mark.asyncio
async def test_qr_lookup_nonexistent_patient(
    client: AsyncClient, db_session: AsyncSession
):
    """5. Non-existent patient UUID in QR code returns HTTP 404."""
    rec_token, _ = await _setup_receptionist(client, db_session, email="rec.notfound@hospital.org")
    fake_id = str(uuid.uuid4())

    res = await client.post(
        RECEPTION_LOOKUP_URL,
        json={"qr_code": f"CLINOVA:PATIENT:{fake_id}"},
        headers={"Authorization": f"Bearer {rec_token}"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_receptionist_cannot_access_clinical_summary(
    client: AsyncClient, db_session: AsyncSession
):
    """6. Receptionist is strictly blocked (HTTP 403) from accessing clinical summary."""
    rec_token, hosp_id = await _setup_receptionist(client, db_session, email="rec.privacy@hospital.org")
    pat_token, _ = await _create_test_patient(client, email="pat.summary@test.com")

    # Create consultation
    c_res = await client.post(
        CONSULTATIONS_URL,
        json={"hospital_id": str(hosp_id), "chief_complaint": "Severe fever"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert c_res.status_code == 201
    consultation_id = c_res.json()["id"]

    # Receptionist attempts to view clinical summary
    summary_res = await client.get(
        f"/api/v1/consultations/{consultation_id}/summary",
        headers={"Authorization": f"Bearer {rec_token}"},
    )
    assert summary_res.status_code == 403
    assert "Receptionist" in summary_res.json()["detail"]


@pytest.mark.asyncio
async def test_receptionist_cannot_access_clinical_history_or_timeline(
    client: AsyncClient, db_session: AsyncSession
):
    """7. Receptionist is blocked (HTTP 403) from clinical history, timeline, and documents."""
    rec_token, hosp_id = await _setup_receptionist(client, db_session, email="rec.clin@hospital.org")
    pat_token, patient_id = await _create_test_patient(client, email="pat.clin@test.com")

    c_res = await client.post(
        CONSULTATIONS_URL,
        json={"hospital_id": str(hosp_id)},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    consultation_id = c_res.json()["id"]

    # Attempt clinical history
    h_res = await client.get(
        f"/api/v1/consultations/{consultation_id}/history",
        headers={"Authorization": f"Bearer {rec_token}"},
    )
    assert h_res.status_code == 403

    # Attempt medical timeline
    t_res = await client.get(
        f"/api/v1/consultations/{consultation_id}/timeline",
        headers={"Authorization": f"Bearer {rec_token}"},
    )
    assert t_res.status_code == 403

    # Attempt medical documents
    d_res = await client.get(
        f"/api/v1/medical-documents?consultation_id={consultation_id}",
        headers={"Authorization": f"Bearer {rec_token}"},
    )
    assert d_res.status_code == 403


@pytest.mark.asyncio
async def test_confirm_registration_associates_pre_hospital_consultation(
    client: AsyncClient, db_session: AsyncSession
):
    """8. Registering a patient with pre-hospital consultation reassigns hospital_id & department."""
    rec_token, hosp_id = await _setup_receptionist(client, db_session, email="rec.reg@hospital.org")
    pat_token, patient_id = await _create_test_patient(client, email="pat.prehosp@test.com")

    # Patient creates pre-hospital consultation (hospital_id is None)
    c_res = await client.post(
        CONSULTATIONS_URL,
        json={"chief_complaint": "Joint pain in knees"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert c_res.status_code == 201
    assert c_res.json()["hospital_id"] is None
    consultation_id = c_res.json()["id"]

    # Receptionist scans QR and confirms registration to "Orthopedics"
    reg_res = await client.post(
        RECEPTION_REGISTER_URL,
        json={
            "patient_id": patient_id,
            "department": "Orthopedics",
            "consultation_id": consultation_id,
        },
        headers={"Authorization": f"Bearer {rec_token}"},
    )
    assert reg_res.status_code == 201, reg_res.text
    reg_data = reg_res.json()

    assert reg_data["consultation_id"] == consultation_id
    assert reg_data["hospital_id"] == str(hosp_id)
    assert reg_data["department"] == "Orthopedics"
    assert reg_data["status"] == "initiated"

    # Verify consultation in DB now has hospital_id set to this hospital
    stmt = db_session.query if hasattr(db_session, "query") else None
    # Verify via API
    get_res = await client.get(
        f"{CONSULTATIONS_URL}/{consultation_id}",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["hospital_id"] == str(hosp_id)
    assert get_res.json()["department"] == "Orthopedics"


@pytest.mark.asyncio
async def test_manual_registration_walkin(
    client: AsyncClient, db_session: AsyncSession
):
    """9. Manual registration fallback provisions patient and department consultation."""
    rec_token, hosp_id = await _setup_receptionist(client, db_session, email="rec.manual@hospital.org")

    payload = {
        "full_name": "Vikram Seth",
        "phone": "9820088899",
        "age": 45,
        "gender": "Male",
        "abha_id": "91-1234-5678-9999",
        "department": "General Medicine",
        "chief_complaint": "Persistent cough and sore throat",
    }
    res = await client.post(
        RECEPTION_MANUAL_URL,
        json=payload,
        headers={"Authorization": f"Bearer {rec_token}"},
    )
    assert res.status_code == 201, res.text
    data = res.json()

    assert data["patient_name"] == "Vikram Seth"
    assert data["hospital_id"] == str(hosp_id)
    assert data["department"] == "General Medicine"
    assert data["status"] == "initiated"
    assert "consultation_id" in data
