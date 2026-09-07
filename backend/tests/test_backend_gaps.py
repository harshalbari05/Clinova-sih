"""Comprehensive test suite for Step 10A.1 backend gaps:
1. Hospital-Scoped Consultation Queue (GET /api/v1/consultations)
2. Public Hospital Directory (GET /api/v1/hospitals)
3. Explicit Consultation Consent Endpoint (POST /api/v1/consultations/{id}/consent)
4. End-to-End Integration Flow

All tests run against isolated async SQLite in-memory database.
"""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import create_access_token
from app.models.audit_log import AuditLog
from app.models.consent import Consent
from app.models.consultation import Consultation
from app.models.hospital import Hospital
from app.models.hospital_user import HospitalUser
from app.models.patient import Patient
from app.models.user import User

# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

PATIENT_REGISTER_URL = "/api/v1/auth/patient/register"
PATIENT_LOGIN_URL = "/api/v1/auth/patient/login"
HOSPITAL_REGISTER_URL = "/api/v1/auth/hospital/register"
HOSPITAL_LOGIN_URL = "/api/v1/auth/hospital/login"
CONSULTATIONS_URL = "/api/v1/consultations"
HOSPITALS_URL = "/api/v1/hospitals"


async def _create_hospital(
    db: AsyncSession,
    name: str = "Apollo Hospital",
    city: str = "Bengaluru",
    state: str = "Karnataka",
    registration_number: str | None = None,
) -> Hospital:
    """Insert a hospital facility directly into the database."""
    hospital = Hospital(
        id=uuid.uuid4(),
        name=name,
        city=city,
        state=state,
        registration_number=registration_number or f"REG-{uuid.uuid4().hex[:8].upper()}",
    )
    db.add(hospital)
    await db.flush()
    await db.refresh(hospital)
    return hospital


async def _create_patient_user(
    db: AsyncSession,
    email: str = "patient@example.com",
    full_name: str = "Test Patient",
) -> tuple[User, Patient, str]:
    """Create a patient user + profile in DB and return (user, patient, jwt_token)."""
    user = User(
        id=uuid.uuid4(),
        email=email,
        role="patient",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    patient = Patient(
        id=uuid.uuid4(),
        user_id=user.id,
        full_name=full_name,
    )
    db.add(patient)
    await db.flush()
    await db.refresh(user)
    await db.refresh(patient)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return user, patient, token


async def _create_hospital_user(
    db: AsyncSession,
    hospital_id: uuid.UUID,
    role: str = "doctor",
    email: str = "staff@hospital.org",
) -> tuple[User, HospitalUser, str]:
    """Create a hospital staff member in DB and return (user, hospital_user, jwt_token)."""
    user = User(
        id=uuid.uuid4(),
        email=email,
        role="hospital",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    h_user = HospitalUser(
        id=uuid.uuid4(),
        user_id=user.id,
        hospital_id=hospital_id,
        role=role,
    )
    db.add(h_user)
    await db.flush()
    await db.refresh(user)
    await db.refresh(h_user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return user, h_user, token


async def _create_consultation(
    db: AsyncSession,
    patient_id: uuid.UUID,
    hospital_id: uuid.UUID,
    chief_complaint: str = "General Consultation",
    status: str = "initiated",
    created_at: datetime | None = None,
) -> Consultation:
    """Insert a consultation directly into DB."""
    consultation = Consultation(
        id=uuid.uuid4(),
        patient_id=patient_id,
        hospital_id=hospital_id,
        status=status,
        chief_complaint=chief_complaint,
        created_at=created_at or datetime.now(timezone.utc),
    )
    db.add(consultation)
    await db.flush()
    await db.refresh(consultation)
    return consultation


# ===========================================================================
# 1. Hospital-Scoped Consultation Queue (GET /api/v1/consultations)
# ===========================================================================


@pytest.mark.asyncio
async def test_patient_list_own_consultations_only_desc(
    client: AsyncClient, db_session: AsyncSession
):
    """Patient receives only their own consultations ordered by created_at DESC (newest first)."""
    hosp = await _create_hospital(db_session, name="City Hospital")
    _user1, patient1, token1 = await _create_patient_user(
        db_session, email="p1@example.com"
    )
    _user2, patient2, _token2 = await _create_patient_user(
        db_session, email="p2@example.com"
    )

    # Patient 1 creates 2 consultations with different timestamps
    c1 = await _create_consultation(
        db_session,
        patient_id=patient1.id,
        hospital_id=hosp.id,
        chief_complaint="Complaint 1 (Older)",
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    c2 = await _create_consultation(
        db_session,
        patient_id=patient1.id,
        hospital_id=hosp.id,
        chief_complaint="Complaint 2 (Newer)",
        created_at=datetime(2026, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
    )

    # Patient 2 creates a consultation
    await _create_consultation(
        db_session,
        patient_id=patient2.id,
        hospital_id=hosp.id,
        chief_complaint="Patient 2 Complaint",
    )

    # Patient 1 lists consultations
    res = await client.get(
        CONSULTATIONS_URL,
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2
    # Check descending order: c2 (newer) first, c1 (older) second
    assert data["items"][0]["id"] == str(c2.id)
    assert data["items"][1]["id"] == str(c1.id)
    # Verify no Patient 2 data leaked
    item_ids = [item["id"] for item in data["items"]]
    assert str(c1.id) in item_ids
    assert str(c2.id) in item_ids


@pytest.mark.asyncio
async def test_doctor_list_hospital_queue_fifo_asc(
    client: AsyncClient, db_session: AsyncSession
):
    """Doctor receives consultations for their affiliated hospital in FIFO queue order (created_at ASC)."""
    hosp = await _create_hospital(db_session, name="Metro General")
    _doc_u, _doc_h, doc_token = await _create_hospital_user(
        db_session, hospital_id=hosp.id, role="doctor", email="doctor@metro.org"
    )

    _p1_u, p1, _ = await _create_patient_user(db_session, email="p1@metro.org")
    _p2_u, p2, _ = await _create_patient_user(db_session, email="p2@metro.org")

    # c1 created first (older), c2 created second (newer)
    c1 = await _create_consultation(
        db_session,
        patient_id=p1.id,
        hospital_id=hosp.id,
        chief_complaint="First in line",
        created_at=datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
    )
    c2 = await _create_consultation(
        db_session,
        patient_id=p2.id,
        hospital_id=hosp.id,
        chief_complaint="Second in line",
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )

    res = await client.get(
        CONSULTATIONS_URL,
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2
    # FIFO: First in line (c1) must be first in response, c2 second
    assert data["items"][0]["id"] == str(c1.id)
    assert data["items"][1]["id"] == str(c2.id)


@pytest.mark.asyncio
async def test_hospital_admin_list_hospital_queue(
    client: AsyncClient, db_session: AsyncSession
):
    """Hospital admin receives facility consultations in FIFO order."""
    hosp = await _create_hospital(db_session, name="Apollo Clinic")
    _adm_u, _adm_h, adm_token = await _create_hospital_user(
        db_session, hospital_id=hosp.id, role="hospital_admin", email="admin@apollo.org"
    )
    _p_u, p, _ = await _create_patient_user(db_session, email="p@apollo.org")

    c = await _create_consultation(
        db_session,
        patient_id=p.id,
        hospital_id=hosp.id,
        chief_complaint="Admin check",
    )

    res = await client.get(
        CONSULTATIONS_URL,
        headers={"Authorization": f"Bearer {adm_token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == str(c.id)


@pytest.mark.asyncio
async def test_cross_hospital_isolation(
    client: AsyncClient, db_session: AsyncSession
):
    """Doctor from Hospital A cannot see consultations from Hospital B and vice versa."""
    hosp_a = await _create_hospital(db_session, name="Hospital Alpha")
    hosp_b = await _create_hospital(db_session, name="Hospital Beta")

    _doc_a_u, _doc_a_h, doc_a_token = await _create_hospital_user(
        db_session, hospital_id=hosp_a.id, role="doctor", email="doc_a@alpha.org"
    )
    _doc_b_u, _doc_b_h, doc_b_token = await _create_hospital_user(
        db_session, hospital_id=hosp_b.id, role="doctor", email="doc_b@beta.org"
    )

    _p_u, p, _ = await _create_patient_user(db_session, email="patient_iso@example.com")

    # Consultation at Hospital A
    c_a = await _create_consultation(
        db_session,
        patient_id=p.id,
        hospital_id=hosp_a.id,
        chief_complaint="Complaint Alpha",
    )
    # Consultation at Hospital B
    c_b = await _create_consultation(
        db_session,
        patient_id=p.id,
        hospital_id=hosp_b.id,
        chief_complaint="Complaint Beta",
    )

    # Doctor A queue
    res_a = await client.get(
        CONSULTATIONS_URL,
        headers={"Authorization": f"Bearer {doc_a_token}"},
    )
    assert res_a.status_code == 200
    items_a = res_a.json()["items"]
    assert len(items_a) == 1
    assert items_a[0]["id"] == str(c_a.id)

    # Doctor B queue
    res_b = await client.get(
        CONSULTATIONS_URL,
        headers={"Authorization": f"Bearer {doc_b_token}"},
    )
    assert res_b.status_code == 200
    items_b = res_b.json()["items"]
    assert len(items_b) == 1
    assert items_b[0]["id"] == str(c_b.id)


@pytest.mark.asyncio
async def test_hospital_queue_status_filter(
    client: AsyncClient, db_session: AsyncSession
):
    """Status filter parameter correctly narrows the queue to matching status."""
    hosp = await _create_hospital(db_session, name="Status Filter Hospital")
    _doc_u, _doc_h, doc_token = await _create_hospital_user(
        db_session, hospital_id=hosp.id, role="doctor", email="filter_doc@test.org"
    )
    _p_u, p, _ = await _create_patient_user(db_session, email="p_filter@test.org")

    c_init = await _create_consultation(
        db_session,
        patient_id=p.id,
        hospital_id=hosp.id,
        chief_complaint="Initiated consultation",
        status="initiated",
    )
    _c_rev = await _create_consultation(
        db_session,
        patient_id=p.id,
        hospital_id=hosp.id,
        chief_complaint="Reviewed consultation",
        status="reviewed",
    )

    # Filter for 'initiated'
    res_init = await client.get(
        f"{CONSULTATIONS_URL}?status=initiated",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert res_init.status_code == 200
    data_init = res_init.json()
    assert data_init["total"] == 1
    assert data_init["items"][0]["id"] == str(c_init.id)
    assert data_init["items"][0]["status"] == "initiated"

    # Filter for 'reviewed'
    res_rev = await client.get(
        f"{CONSULTATIONS_URL}?status=reviewed",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert res_rev.status_code == 200
    data_rev = res_rev.json()
    assert data_rev["total"] == 1
    assert data_rev["items"][0]["status"] == "reviewed"


@pytest.mark.asyncio
async def test_hospital_queue_query_param_override_defense(
    client: AsyncClient, db_session: AsyncSession
):
    """Doctor cannot pass arbitrary hospital_id or patient_id query params to breach facility scope."""
    hosp_a = await _create_hospital(db_session, name="Facility A")
    hosp_b = await _create_hospital(db_session, name="Facility B")

    _doc_u, _doc_h, doc_token = await _create_hospital_user(
        db_session, hospital_id=hosp_a.id, role="doctor", email="defense_doc@test.org"
    )
    _p_u, p, _ = await _create_patient_user(db_session, email="p_defense@test.org")

    await _create_consultation(
        db_session,
        patient_id=p.id,
        hospital_id=hosp_b.id,
        chief_complaint="Belongs to Hospital B",
    )

    # Doctor tries to query Facility B via malicious query parameter injection
    res = await client.get(
        f"{CONSULTATIONS_URL}?hospital_id={hosp_b.id}&patient_id={p.id}",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    # Should still strictly return Hospital A queue (which is empty)
    assert data["total"] == 0
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_hospital_queue_empty(
    client: AsyncClient, db_session: AsyncSession
):
    """Empty consultation queue returns 200 OK with empty items list and total=0."""
    hosp = await _create_hospital(db_session, name="Empty Queue Hospital")
    _doc_u, _doc_h, doc_token = await _create_hospital_user(
        db_session, hospital_id=hosp.id, role="doctor", email="empty_queue@test.org"
    )

    res = await client.get(
        CONSULTATIONS_URL,
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_consultation_list_unauthenticated(client: AsyncClient):
    """Unauthenticated call to GET /api/v1/consultations returns 401."""
    res = await client.get(CONSULTATIONS_URL)
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_consultation_list_unaffiliated_user(
    client: AsyncClient, db_session: AsyncSession
):
    """User with neither a patient nor hospital profile returns 403 Forbidden."""
    orphan_user = User(
        id=uuid.uuid4(),
        email="orphan@example.com",
        role="unknown_role",
        is_active=True,
    )
    db_session.add(orphan_user)
    await db_session.flush()

    token = create_access_token({"sub": str(orphan_user.id), "role": "unknown_role"})

    res = await client.get(
        CONSULTATIONS_URL,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert "permission" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_single_consultation_doctor_access(
    client: AsyncClient, db_session: AsyncSession
):
    """Doctor can retrieve a single consultation from their own hospital, but 404 for other hospital."""
    hosp_a = await _create_hospital(db_session, name="Hospital One")
    hosp_b = await _create_hospital(db_session, name="Hospital Two")

    _doc_u, _doc_h, doc_token = await _create_hospital_user(
        db_session, hospital_id=hosp_a.id, role="doctor", email="doc_get@one.org"
    )
    _p_u, p, _ = await _create_patient_user(db_session, email="p_get@one.org")

    c_own = await _create_consultation(
        db_session,
        patient_id=p.id,
        hospital_id=hosp_a.id,
        chief_complaint="Accessible consultation",
    )
    c_other = await _create_consultation(
        db_session,
        patient_id=p.id,
        hospital_id=hosp_b.id,
        chief_complaint="Inaccessible consultation",
    )

    # Accessible
    res_own = await client.get(
        f"{CONSULTATIONS_URL}/{c_own.id}",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert res_own.status_code == 200
    assert res_own.json()["id"] == str(c_own.id)

    # Safe 404 for consultation at another hospital
    res_other = await client.get(
        f"{CONSULTATIONS_URL}/{c_other.id}",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert res_other.status_code == 404
    assert res_other.json()["detail"] == "Consultation not found."


# ===========================================================================
# 2. Public Hospital Directory (GET /api/v1/hospitals)
# ===========================================================================


@pytest.mark.asyncio
async def test_list_hospitals_public_access_no_auth(
    client: AsyncClient, db_session: AsyncSession
):
    """Public hospital directory can be accessed without any authorization header."""
    await _create_hospital(db_session, name="Public Hospital")

    res = await client.get(HOSPITALS_URL)
    assert res.status_code == 200, res.text
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_hospitals_alphabetical_order(
    client: AsyncClient, db_session: AsyncSession
):
    """Hospitals are returned sorted alphabetically ascending by name."""
    await _create_hospital(db_session, name="Zeta Multispecialty")
    await _create_hospital(db_session, name="Alpha Healthcare")
    await _create_hospital(db_session, name="Beta Clinic")

    res = await client.get(HOSPITALS_URL)
    assert res.status_code == 200
    data = res.json()
    names = [h["name"] for h in data]
    assert names == ["Alpha Healthcare", "Beta Clinic", "Zeta Multispecialty"]


@pytest.mark.asyncio
async def test_list_hospitals_safe_fields_only(
    client: AsyncClient, db_session: AsyncSession
):
    """Directory items contain only safe public fields (id, name, city, state) and no sensitive data."""
    hosp = Hospital(
        id=uuid.uuid4(),
        name="Security Test Hospital",
        registration_number="CONFIDENTIAL-REG-999",
        phone="+919876543210",
        email="internal-admin@hospital.org",
        address="123 Restricted Campus Lane",
        city="Mumbai",
        state="Maharashtra",
        pincode="400001",
    )
    db_session.add(hosp)
    await db_session.flush()

    res = await client.get(HOSPITALS_URL)
    assert res.status_code == 200
    data = res.json()
    entry = next(h for h in data if h["id"] == str(hosp.id))

    # Safe fields must be present
    assert entry["id"] == str(hosp.id)
    assert entry["name"] == "Security Test Hospital"
    assert entry["city"] == "Mumbai"
    assert entry["state"] == "Maharashtra"

    # Sensitive fields must NOT exist in the response schema
    assert "registration_number" not in entry
    assert "phone" not in entry
    assert "email" not in entry
    assert "address" not in entry
    assert "pincode" not in entry
    assert "created_at" not in entry
    assert "updated_at" not in entry


@pytest.mark.asyncio
async def test_list_hospitals_empty_db(client: AsyncClient):
    """When no hospitals exist, returns 200 OK with empty list."""
    res = await client.get(HOSPITALS_URL)
    assert res.status_code == 200
    assert res.json() == []


# ===========================================================================
# 3. Explicit Consultation Consent Endpoint (POST /api/v1/consultations/{id}/consent)
# ===========================================================================


@pytest.mark.asyncio
async def test_record_consent_success(
    client: AsyncClient, db_session: AsyncSession
):
    """Patient records informed consent successfully for own consultation."""
    hosp = await _create_hospital(db_session, name="Consent Hospital")
    _p_u, patient, token = await _create_patient_user(
        db_session, email="patient_consent@test.org"
    )
    c = await _create_consultation(
        db_session,
        patient_id=patient.id,
        hospital_id=hosp.id,
        chief_complaint="Fever and Cough",
    )

    payload = {
        "consent_given": True,
        "consent_type": "clinical_intake",
    }
    res = await client.post(
        f"{CONSULTATIONS_URL}/{c.id}/consent",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    data = res.json()

    assert data["patient_id"] == str(patient.id)
    assert data["consultation_id"] == str(c.id)
    assert data["consent_type"] == "clinical_intake"
    assert data["granted"] is True
    assert data["version"] == "v1.0"
    assert "timestamp" in data
    assert data["revoked_at"] is None


@pytest.mark.asyncio
async def test_record_consent_server_timestamp_authoritative(
    client: AsyncClient, db_session: AsyncSession
):
    """Server generates authoritative timestamp and ignores any forged client timestamps."""
    hosp = await _create_hospital(db_session, name="Timestamp Hospital")
    _p_u, patient, token = await _create_patient_user(
        db_session, email="timestamp_patient@test.org"
    )
    c = await _create_consultation(
        db_session,
        patient_id=patient.id,
        hospital_id=hosp.id,
        chief_complaint="Chest congestion",
    )

    before_time = datetime.now(timezone.utc)

    # Client passes extra/bogus client timestamp
    payload = {
        "consent_given": True,
        "consent_type": "clinical_intake",
        "timestamp": "1999-01-01T00:00:00Z",
    }
    res = await client.post(
        f"{CONSULTATIONS_URL}/{c.id}/consent",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()

    # Server timestamp must be close to now, definitely not 1999
    ts = datetime.fromisoformat(data["timestamp"])
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    assert ts.year >= 2026
    assert abs((ts - before_time).total_seconds()) < 10


@pytest.mark.asyncio
async def test_record_consent_cross_patient_denied(
    client: AsyncClient, db_session: AsyncSession
):
    """Patient cannot record consent for another patient's consultation (returns safe 404)."""
    hosp = await _create_hospital(db_session, name="Cross Patient Hospital")
    _p1_u, patient1, _token1 = await _create_patient_user(
        db_session, email="p1_consent@test.org"
    )
    _p2_u, _patient2, token2 = await _create_patient_user(
        db_session, email="p2_consent@test.org"
    )

    c1 = await _create_consultation(
        db_session,
        patient_id=patient1.id,
        hospital_id=hosp.id,
        chief_complaint="Patient 1 issue",
    )

    # Patient 2 tries to record consent for Patient 1's consultation
    payload = {"consent_given": True, "consent_type": "clinical_intake"}
    res = await client.post(
        f"{CONSULTATIONS_URL}/{c1.id}/consent",
        json=payload,
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Consultation not found."


@pytest.mark.asyncio
async def test_record_consent_hospital_user_forbidden(
    client: AsyncClient, db_session: AsyncSession
):
    """Hospital user cannot call the consent recording endpoint (403 Forbidden)."""
    hosp = await _create_hospital(db_session, name="Staff Consent Hospital")
    _p_u, patient, _ = await _create_patient_user(
        db_session, email="staff_patient@test.org"
    )
    _doc_u, _doc_h, doc_token = await _create_hospital_user(
        db_session, hospital_id=hosp.id, role="doctor", email="staff_doctor@test.org"
    )

    c = await _create_consultation(
        db_session,
        patient_id=patient.id,
        hospital_id=hosp.id,
        chief_complaint="Doctor tries to consent",
    )

    payload = {"consent_given": True, "consent_type": "clinical_intake"}
    res = await client.post(
        f"{CONSULTATIONS_URL}/{c.id}/consent",
        json=payload,
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_record_consent_unauthenticated(
    client: AsyncClient, db_session: AsyncSession
):
    """Unauthenticated call to record consent returns 401."""
    random_id = uuid.uuid4()
    res = await client.post(
        f"{CONSULTATIONS_URL}/{random_id}/consent",
        json={"consent_given": True, "consent_type": "clinical_intake"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_record_consent_idempotency(
    client: AsyncClient, db_session: AsyncSession
):
    """Submitting consent multiple times updates the existing record without duplicates."""
    hosp = await _create_hospital(db_session, name="Idempotent Hospital")
    _p_u, patient, token = await _create_patient_user(
        db_session, email="idempotent_patient@test.org"
    )
    c = await _create_consultation(
        db_session,
        patient_id=patient.id,
        hospital_id=hosp.id,
        chief_complaint="Idempotent test",
    )

    payload = {"consent_given": True, "consent_type": "clinical_intake"}

    # First submission
    res1 = await client.post(
        f"{CONSULTATIONS_URL}/{c.id}/consent",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 201
    consent_id1 = res1.json()["id"]

    # Second submission (e.g. user taps submit again or updates status)
    payload2 = {"consent_given": False, "consent_type": "clinical_intake"}
    res2 = await client.post(
        f"{CONSULTATIONS_URL}/{c.id}/consent",
        json=payload2,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 201
    consent_id2 = res2.json()["id"]

    # ID must be the same (updated existing record)
    assert consent_id1 == consent_id2
    assert res2.json()["granted"] is False

    # Verify exactly 1 consent row exists in database for this consultation
    stmt = select(Consent).where(Consent.consultation_id == c.id)
    records = (await db_session.execute(stmt)).scalars().all()
    assert len(records) == 1
    assert records[0].granted is False


@pytest.mark.asyncio
async def test_record_consent_creates_audit_log(
    client: AsyncClient, db_session: AsyncSession
):
    """Recording consent writes an audit log entry."""
    hosp = await _create_hospital(db_session, name="Audit Hospital")
    user, patient, token = await _create_patient_user(
        db_session, email="audit_patient@test.org"
    )
    c = await _create_consultation(
        db_session,
        patient_id=patient.id,
        hospital_id=hosp.id,
        chief_complaint="Audit log verification",
    )

    payload = {"consent_given": True, "consent_type": "clinical_intake"}
    res = await client.post(
        f"{CONSULTATIONS_URL}/{c.id}/consent",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201

    # Verify AuditLog row
    stmt = select(AuditLog).where(
        AuditLog.entity_id == str(c.id),
        AuditLog.action == "consultation_consent_recorded",
    )
    audit = (await db_session.execute(stmt)).scalar_one_or_none()
    assert audit is not None
    assert audit.user_id == user.id
    assert audit.entity_type == "consultation"
    assert audit.metadata_json["granted"] is True
    assert audit.metadata_json["consent_type"] == "clinical_intake"


@pytest.mark.asyncio
async def test_record_consent_nonexistent_consultation(
    client: AsyncClient, db_session: AsyncSession
):
    """Recording consent for a non-existent consultation returns 404."""
    _p_u, _patient, token = await _create_patient_user(
        db_session, email="nonexistent_consult@test.org"
    )
    non_existent_id = uuid.uuid4()

    res = await client.post(
        f"{CONSULTATIONS_URL}/{non_existent_id}/consent",
        json={"consent_given": True, "consent_type": "clinical_intake"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Consultation not found."


# ===========================================================================
# 4. End-to-End Integration Flow
# ===========================================================================


@pytest.mark.asyncio
async def test_e2e_patient_registration_to_doctor_queue(
    client: AsyncClient, db_session: AsyncSession
):
    """Complete end-to-end integration test:
    1. Unauthenticated user lists public hospital directory and selects Hospital A.
    2. Patient registers and logs in.
    3. Patient creates a consultation targeting Hospital A.
    4. Patient records informed consent for that consultation.
    5. Doctor at Hospital A logs in and retrieves OPD queue -> sees new consultation.
    6. Doctor at Hospital B logs in and retrieves OPD queue -> queue is empty (cross-hospital isolation).
    """
    # 1. Hospital Directory
    hosp_a = await _create_hospital(db_session, name="Apollo Hospitals Greams Road", city="Chennai")
    hosp_b = await _create_hospital(db_session, name="Manipal Hospital HAL Airport", city="Bengaluru")

    dir_res = await client.get(HOSPITALS_URL)
    assert dir_res.status_code == 200
    dir_hospitals = dir_res.json()
    assert len(dir_hospitals) == 2
    selected_hospital_id = str(hosp_a.id)

    # 2. Patient registers and logs in
    reg_payload = {
        "email": "e2e.patient@example.com",
        "password": "SecurePassword2026!",
        "full_name": "Ramesh Kumar",
        "phone": "+919876500001",
    }
    reg_res = await client.post(PATIENT_REGISTER_URL, json=reg_payload)
    assert reg_res.status_code == 201

    login_res = await client.post(
        PATIENT_LOGIN_URL,
        json={"identifier": "e2e.patient@example.com", "password": "SecurePassword2026!"},
    )
    assert login_res.status_code == 200
    patient_token = login_res.json()["access_token"]

    # 3. Patient creates consultation targeting Hospital A
    consult_payload = {
        "hospital_id": selected_hospital_id,
        "chief_complaint": "Persistent high fever and severe joint pain for 4 days",
    }
    create_res = await client.post(
        CONSULTATIONS_URL,
        json=consult_payload,
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert create_res.status_code == 201
    consultation = create_res.json()
    consultation_id = consultation["id"]
    assert consultation["hospital_id"] == selected_hospital_id
    assert consultation["status"] == "initiated"

    # 4. Patient records informed consent
    consent_payload = {
        "consent_given": True,
        "consent_type": "clinical_intake",
    }
    consent_res = await client.post(
        f"{CONSULTATIONS_URL}/{consultation_id}/consent",
        json=consent_payload,
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert consent_res.status_code == 201
    consent_data = consent_res.json()
    assert consent_data["granted"] is True
    assert consent_data["consultation_id"] == consultation_id

    # 5. Doctor at Hospital A logs in and retrieves OPD queue
    _doc_a_u, _doc_a_h, doc_a_token = await _create_hospital_user(
        db_session, hospital_id=hosp_a.id, role="doctor", email="dr.sharma@apollo.org"
    )
    queue_a_res = await client.get(
        CONSULTATIONS_URL,
        headers={"Authorization": f"Bearer {doc_a_token}"},
    )
    assert queue_a_res.status_code == 200
    queue_a_data = queue_a_res.json()
    assert queue_a_data["total"] == 1
    assert queue_a_data["items"][0]["id"] == consultation_id
    assert queue_a_data["items"][0]["chief_complaint"] == "Persistent high fever and severe joint pain for 4 days"

    # 6. Doctor at Hospital B logs in and retrieves OPD queue (cross-hospital isolation)
    _doc_b_u, _doc_b_h, doc_b_token = await _create_hospital_user(
        db_session, hospital_id=hosp_b.id, role="doctor", email="dr.patel@manipal.org"
    )
    queue_b_res = await client.get(
        CONSULTATIONS_URL,
        headers={"Authorization": f"Bearer {doc_b_token}"},
    )
    assert queue_b_res.status_code == 200
    queue_b_data = queue_b_res.json()
    assert queue_b_data["total"] == 0
    assert queue_b_data["items"] == []
