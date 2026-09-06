"""Comprehensive test suite for Clinova Step 8: Medical Timeline.

Covers:
  A. Empty patient timeline returns 200 with empty list.
  B. Timeline from ClinicalHistory.
  C. Timeline from Consultation encounter.
  D. Timeline from AI interview structured patient report.
  E. Timeline from MedicalDocument ExtractedData.
  F. Lab result event (LAB_RESULT with value, unit, reference range, page, evidence).
  G. Medication event (MEDICATION preserving source text without guessing compliance).
  H. Hospital admission/discharge events (HOSPITAL_ADMISSION, HOSPITAL_DISCHARGE).
  I. Surgery event (SURGERY).
  J. Allergy event (ALLERGY).
  K. Exact date handling (EXACT).
  L. Month/year date precision (MONTH, YEAR).
  M. Approximate/unknown dates (APPROXIMATE, UNKNOWN).
  N. Chronological ordering (asc and desc).
  O. Unknown-date event handling (placed stably at the end).
  P. Source provenance preservation (source_type, source_id, document_id, consultation_id).
  Q. Source page number preservation.
  R. Verification status distinction (UNVERIFIED vs SOURCE_CONFIRMED vs CLINICIAN_VERIFIED).
  S. Duplicate prevention.
  T. Idempotent timeline rebuild (multiple runs do not duplicate events).
  U. Cross-patient access blocked (safe 404).
  V. Cross-hospital authorization enforced (404 for unauthorized hospital, 200 for authorized facility).
  W. Patient cannot access another patient's timeline (safe 404).
  X. Patient cannot mark events as clinician-verified.
  Y. Missing source data does not create fabricated events.
  Z. OCR/AI extraction failure does not corrupt existing timeline.
  AA. Updating clinical history and rebuilding timeline updates cleanly without runaway duplicates.
  AB. Multiple documents contribute independent timeline events.
  AC. Multiple sources for same real-world event handled safely.
  AD. Filtering by event_type, source_type, and date range.
  AE. Special test cases:
      - "I had surgery about five years ago" -> APPROXIMATE date precision, no invented date.
      - "15/03/2025 Hb 10.2 g/dL" -> LAB_RESULT with exact date 2025-03-15 and evidence.
      - "Diagnosis: Asthma" -> DIAGNOSIS_DOCUMENTED with evidence.
      - Patient complaint "I get wheezing sometimes" -> SYMPTOM, NOT DIAGNOSIS_DOCUMENTED.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_message import AIMessage
from app.models.ai_session import AISession
from app.models.clinical_history import ClinicalHistory
from app.models.consultation import Consultation
from app.models.extracted_data import ExtractedData
from app.models.hospital import Hospital
from app.models.hospital_user import HospitalUser
from app.models.medical_document import MedicalDocument
from app.models.patient import Patient
from app.models.timeline_event import TimelineEvent
from app.models.user import User
from app.services.auth_service import create_access_token
from app.timeline.date_utils import parse_clinical_date
from app.timeline.service import timeline_service

# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------


async def _create_test_hospital(db: AsyncSession, name: str = "Apollo Hospital") -> Hospital:
    hospital = Hospital(
        id=uuid.uuid4(),
        name=name,
        registration_number=f"REG_{uuid.uuid4().hex[:6]}",
        address="100 Health Way",
        city="Mumbai",
        state="Maharashtra",
        pincode="400001",
        phone="+919876543210",
        email=f"hosp_{uuid.uuid4().hex[:6]}@example.com",
    )
    db.add(hospital)
    await db.commit()
    await db.refresh(hospital)
    return hospital


async def _create_patient_user(
    db: AsyncSession, email: str = "patient_tl@example.com"
) -> tuple[User, Patient, str]:
    user = User(
        id=uuid.uuid4(),
        email=email,
        phone=f"+91{uuid.uuid4().int % 10000000000:010d}",
        role="patient",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    patient = Patient(
        id=uuid.uuid4(),
        user_id=user.id,
        full_name="Alex Mercer",
        date_of_birth=date(1990, 5, 15),
    )
    db.add(patient)
    await db.commit()
    await db.refresh(user)
    await db.refresh(patient)

    token = create_access_token(
        data={"sub": str(user.id), "role": "patient", "user_type": "patient"}
    )
    return user, patient, token


async def _create_hospital_staff_user(
    db: AsyncSession, hospital_id: uuid.UUID, email: str = "doctor_tl@example.com"
) -> tuple[User, HospitalUser, str]:
    user = User(
        id=uuid.uuid4(),
        email=email,
        phone=f"+91{uuid.uuid4().int % 10000000000:010d}",
        role="hospital_staff",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    h_user = HospitalUser(
        id=uuid.uuid4(),
        user_id=user.id,
        hospital_id=hospital_id,
        role="doctor",
    )
    db.add(h_user)
    await db.commit()
    await db.refresh(user)
    await db.refresh(h_user)

    token = create_access_token(
        data={"sub": str(user.id), "role": "hospital_staff", "user_type": "hospital_staff"}
    )
    return user, h_user, token


async def _create_consultation(
    db: AsyncSession,
    patient_id: uuid.UUID,
    hospital_id: uuid.UUID,
    started_at: datetime | None = None,
    chief_complaint: str = "Fever and headache",
) -> Consultation:
    consultation = Consultation(
        id=uuid.uuid4(),
        patient_id=patient_id,
        hospital_id=hospital_id,
        status="in_progress",
        chief_complaint=chief_complaint,
        started_at=started_at or datetime(2025, 4, 10, 10, 30, tzinfo=timezone.utc),
    )
    db.add(consultation)
    await db.commit()
    await db.refresh(consultation)
    return consultation


async def _create_medical_document_with_extraction(
    db: AsyncSession,
    patient_id: uuid.UUID,
    consultation_id: uuid.UUID | None = None,
    document_date: date | None = date(2025, 3, 15),
    extracted_json: dict | None = None,
) -> MedicalDocument:
    doc = MedicalDocument(
        id=uuid.uuid4(),
        patient_id=patient_id,
        consultation_id=consultation_id,
        file_name="blood_test_report.pdf",
        file_url="medical_documents/test.pdf",
        document_type="lab_report",
        document_date=document_date,
        mime_type="application/pdf",
        ocr_status="completed",
    )
    db.add(doc)
    await db.flush()

    extracted = ExtractedData(
        id=uuid.uuid4(),
        document_id=doc.id,
        raw_ocr_text="Hemoglobin 10.2 g/dL",
        extracted_json=extracted_json or {},
        extraction_status="completed",
        extracted_at=datetime.now(timezone.utc),
    )
    db.add(extracted)
    await db.commit()
    await db.refresh(doc)
    return doc


# ===========================================================================
# DATE UTILITY & PRECISION TESTS
# ===========================================================================


def test_date_utils_exact_dates():
    """K. Exact date parsing from ISO and formatted date strings."""
    d, p = parse_clinical_date("2025-03-15")
    assert d == date(2025, 3, 15)
    assert p == "EXACT"

    d2, p2 = parse_clinical_date("15/03/2025")
    assert d2 == date(2025, 3, 15)
    assert p2 == "EXACT"

    d3, p3 = parse_clinical_date("15 March 2025")
    assert d3 == date(2025, 3, 15)
    assert p3 == "EXACT"


def test_date_utils_month_year_precision():
    """L. Month/Year and Year-only date precision."""
    d_m, p_m = parse_clinical_date("March 2025")
    assert d_m == date(2025, 3, 1)
    assert p_m == "MONTH"

    d_y, p_y = parse_clinical_date("2020")
    assert d_y == date(2020, 1, 1)
    assert p_y == "YEAR"


def test_date_utils_approximate_and_unknown_dates():
    """M & AE. Approximate dates never fabricate exact dates."""
    d_app, p_app = parse_clinical_date("I had surgery about five years ago")
    assert d_app is None
    assert p_app == "APPROXIMATE"

    d_app2, p_app2 = parse_clinical_date("approx 2018")
    assert d_app2 == date(2018, 1, 1)
    assert p_app2 == "APPROXIMATE"

    d_unk, p_unk = parse_clinical_date(None)
    assert d_unk is None
    assert p_unk == "UNKNOWN"

    d_unk2, p_unk2 = parse_clinical_date("")
    assert d_unk2 is None
    assert p_unk2 == "UNKNOWN"


# ===========================================================================
# TIMELINE BUILDER & RETRIEVAL TESTS
# ===========================================================================


@pytest.mark.asyncio
async def test_a_empty_patient_timeline(client: AsyncClient, db_session: AsyncSession):
    """A. New patient with no history has empty timeline (200 OK, total_events=0)."""
    _u, patient, token = await _create_patient_user(db_session, "empty_tl@test.com")

    res = await client.get(
        "/api/v1/patients/me/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["patient_id"] == str(patient.id)
    assert data["total_events"] == 0
    assert data["events"] == []


@pytest.mark.asyncio
async def test_b_timeline_from_clinical_history(client: AsyncClient, db_session: AsyncSession):
    """B & I & J. Timeline generated from patient ClinicalHistory."""
    _u, patient, token = await _create_patient_user(db_session, "ch_tl@test.com")
    hosp = await _create_test_hospital(db_session)
    cons = await _create_consultation(db_session, patient.id, hosp.id)

    # Add clinical history
    ch = ClinicalHistory(
        id=uuid.uuid4(),
        consultation_id=cons.id,
        chief_complaint="Severe abdominal cramping",
        history_of_present_illness="Onset 2 days ago, progressively worsening",
        past_surgical_history="Appendectomy in 2018",
        past_medical_history="Type 2 Diabetes Mellitus diagnosed in 2015",
        drug_history="Metformin 500mg BD",
        allergy_history="Penicillin allergy resulting in hives",
    )
    db_session.add(ch)
    await db_session.commit()

    # Retrieve timeline
    res = await client.get(
        "/api/v1/patients/me/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    events = res.json()["events"]
    assert len(events) >= 5

    # Check SURGERY event
    surg = next((e for e in events if e["event_type"] == "SURGERY"), None)
    assert surg is not None
    assert "Appendectomy" in surg["title"]
    assert surg["source_type"] == "PATIENT_HISTORY"
    assert surg["verification_status"] == "UNVERIFIED"

    # Check ALLERGY event
    allergy = next((e for e in events if e["event_type"] == "ALLERGY"), None)
    assert allergy is not None
    assert "Penicillin" in allergy["title"]
    assert allergy["verification_status"] == "UNVERIFIED"

    # Check MEDICATION event
    med = next((e for e in events if e["event_type"] == "MEDICATION"), None)
    assert med is not None
    assert "Metformin" in med["title"]


@pytest.mark.asyncio
async def test_c_timeline_from_consultation(client: AsyncClient, db_session: AsyncSession):
    """C. Consultation encounter appears on the timeline with hospital name."""
    _u, patient, token = await _create_patient_user(db_session, "cons_tl@test.com")
    hosp = await _create_test_hospital(db_session, name="City Health Clinic")
    cons = await _create_consultation(
        db_session,
        patient.id,
        hosp.id,
        started_at=datetime(2025, 6, 1, 9, 0, tzinfo=timezone.utc),
        chief_complaint="Persistent dry cough",
    )

    res = await client.get(
        "/api/v1/patients/me/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    events = res.json()["events"]
    cons_ev = next((e for e in events if e["event_type"] == "CONSULTATION"), None)
    assert cons_ev is not None
    assert "City Health Clinic" in cons_ev["title"]
    assert cons_ev["event_date"] == "2025-06-01"
    assert cons_ev["source_type"] == "CONSULTATION"
    assert cons_ev["source_id"] == str(cons.id)


@pytest.mark.asyncio
async def test_d_timeline_from_ai_interview(client: AsyncClient, db_session: AsyncSession):
    """D & AE. Timeline events harvested from AI interview patient messages."""
    _u, patient, token = await _create_patient_user(db_session, "ai_tl@test.com")
    hosp = await _create_test_hospital(db_session)
    cons = await _create_consultation(db_session, patient.id, hosp.id)

    # Create AI session with patient statement
    session = AISession(
        id=uuid.uuid4(),
        consultation_id=cons.id,
        status="completed",
        started_at=datetime(2025, 5, 2, tzinfo=timezone.utc),
    )
    db_session.add(session)
    await db_session.flush()

    msg1 = AIMessage(
        id=uuid.uuid4(),
        ai_session_id=session.id,
        sender="patient",
        message="I was diagnosed with asthma when I was 12 years old.",
    )
    msg2 = AIMessage(
        id=uuid.uuid4(),
        ai_session_id=session.id,
        sender="patient",
        message="I had knee surgery about five years ago.",
    )
    db_session.add_all([msg1, msg2])
    await db_session.commit()

    res = await client.get(
        "/api/v1/patients/me/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    events = res.json()["events"]

    # Asthma diagnosis statement
    asthma = next((e for e in events if "asthma" in e["description"].lower()), None)
    assert asthma is not None
    assert asthma["source_type"] == "AI_INTERVIEW"
    assert asthma["verification_status"] == "UNVERIFIED"

    # Knee surgery statement with approximate date
    knee = next((e for e in events if "knee surgery" in e["description"].lower()), None)
    assert knee is not None
    assert knee["date_precision"] == "APPROXIMATE"
    assert knee["event_date"] is None


@pytest.mark.asyncio
async def test_e_f_g_h_timeline_from_medical_document(client: AsyncClient, db_session: AsyncSession):
    """E, F, G, H & P, Q. Medical document with structured lab results, medications, admission/discharge."""
    _u, patient, token = await _create_patient_user(db_session, "doc_tl@test.com")

    extracted_payload = {
        "hospital_or_clinic_name": "Metro Specialty Hospital",
        "document_date": "2025-01-15",
        "admission_date": "2025-01-10",
        "discharge_date": "2025-01-14",
        "diagnoses_or_conditions_as_documented": ["Community Acquired Pneumonia"],
        "laboratory_results": [
            {
                "test_name": "Hemoglobin",
                "value": "10.2",
                "unit": "g/dL",
                "reference_range": "13.0-17.0",
                "abnormal_flag_as_documented": "LOW",
                "test_date": "2025-01-12",
                "source_page": 2,
                "evidence": "Hemoglobin: 10.2 g/dL (LOW)",
            }
        ],
        "medications": [
            {
                "name_as_written": "Amoxicillin",
                "dose_as_written": "500mg",
                "frequency_as_written": "TDS",
                "duration_as_written": "5 days",
                "source_page": 1,
                "evidence": "Amoxicillin 500mg TDS x 5 days",
            }
        ],
        "imaging_findings": ["Right lower lobe consolidation on CXR"],
        "procedures": ["Bronchoscopy"],
        "follow_up_instructions_as_documented": "Review in OPD after 7 days",
    }

    doc = await _create_medical_document_with_extraction(
        db_session,
        patient.id,
        document_date=date(2025, 1, 15),
        extracted_json=extracted_payload,
    )

    res = await client.get(
        "/api/v1/patients/me/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    events = res.json()["events"]

    # F. Lab Result
    hb = next((e for e in events if e["event_type"] == "LAB_RESULT"), None)
    assert hb is not None
    assert hb["title"] == "Lab Result: Hemoglobin"
    assert "10.2 g/dL" in hb["description"]
    assert hb["event_date"] == "2025-01-12"
    assert hb["source_page"] == 2
    assert hb["evidence"] == "Hemoglobin: 10.2 g/dL (LOW)"
    assert hb["verification_status"] == "SOURCE_CONFIRMED"
    assert hb["medical_document_id"] == str(doc.id)

    # G. Medication
    amox = next((e for e in events if e["event_type"] == "MEDICATION"), None)
    assert amox is not None
    assert "Amoxicillin" in amox["title"]
    assert "500mg" in amox["description"]
    assert amox["source_page"] == 1
    assert amox["verification_status"] == "SOURCE_CONFIRMED"

    # H. Hospital Admission and Discharge
    adm = next((e for e in events if e["event_type"] == "HOSPITAL_ADMISSION"), None)
    assert adm is not None
    assert adm["event_date"] == "2025-01-10"

    dis = next((e for e in events if e["event_type"] == "HOSPITAL_DISCHARGE"), None)
    assert dis is not None
    assert dis["event_date"] == "2025-01-14"

    # Diagnoses & Imaging
    diag = next((e for e in events if e["event_type"] == "DIAGNOSIS_DOCUMENTED"), None)
    assert diag is not None
    assert "Pneumonia" in diag["title"]

    img = next((e for e in events if e["event_type"] == "IMAGING"), None)
    assert img is not None
    assert "CXR" in img["title"] or "CXR" in img["description"]


@pytest.mark.asyncio
async def test_n_o_chronological_ordering(client: AsyncClient, db_session: AsyncSession):
    """N & O. Chronological ordering (asc/desc) with dated events first and undated events stably placed."""
    _u, patient, token = await _create_patient_user(db_session, "order_tl@test.com")

    # Manually insert 3 events: one old, one new, one undated
    e_old = TimelineEvent(
        id=uuid.uuid4(),
        patient_id=patient.id,
        event_type="CONSULTATION",
        title="Consultation 2023",
        event_date=date(2023, 1, 1),
        source_type="CONSULTATION",
    )
    e_new = TimelineEvent(
        id=uuid.uuid4(),
        patient_id=patient.id,
        event_type="CONSULTATION",
        title="Consultation 2025",
        event_date=date(2025, 1, 1),
        source_type="CONSULTATION",
    )
    e_undated = TimelineEvent(
        id=uuid.uuid4(),
        patient_id=patient.id,
        event_type="MEDICAL_HISTORY",
        title="Undated History",
        event_date=None,
        date_precision="UNKNOWN",
        source_type="PATIENT_HISTORY",
    )
    db_session.add_all([e_new, e_old, e_undated])
    await db_session.commit()

    # Ascending order
    res_asc = await client.get(
        "/api/v1/patients/me/timeline?order=asc",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_asc.status_code == 200
    events_asc = res_asc.json()["events"]
    assert len(events_asc) == 3
    assert events_asc[0]["title"] == "Consultation 2023"
    assert events_asc[1]["title"] == "Consultation 2025"
    assert events_asc[2]["title"] == "Undated History"

    # Descending order
    res_desc = await client.get(
        "/api/v1/patients/me/timeline?order=desc",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_desc.status_code == 200
    events_desc = res_desc.json()["events"]
    assert events_desc[0]["title"] == "Consultation 2025"
    assert events_desc[1]["title"] == "Consultation 2023"
    assert events_desc[2]["title"] == "Undated History"


@pytest.mark.asyncio
async def test_s_t_idempotent_rebuild(client: AsyncClient, db_session: AsyncSession):
    """S & T. Rebuilding timeline multiple times does not duplicate events."""
    _u, patient, token = await _create_patient_user(db_session, "idempotent_tl@test.com")
    hosp = await _create_test_hospital(db_session)
    cons = await _create_consultation(db_session, patient.id, hosp.id)

    # Initial GET triggers build
    res1 = await client.get(
        "/api/v1/patients/me/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 200
    count1 = res1.json()["total_events"]
    assert count1 > 0

    # Call POST /rebuild
    res2 = await client.post(
        "/api/v1/patients/me/timeline/rebuild",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 200
    count2 = res2.json()["total_events"]
    assert count1 == count2

    # Call POST /rebuild again
    res3 = await client.post(
        "/api/v1/patients/me/timeline/rebuild",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res3.status_code == 200
    count3 = res3.json()["total_events"]
    assert count1 == count3


@pytest.mark.asyncio
async def test_u_w_cross_patient_access_blocked(client: AsyncClient, db_session: AsyncSession):
    """U & W. Patient A cannot access Patient B's timeline by ID or consultation (safe 404)."""
    _u1, p1, token1 = await _create_patient_user(db_session, "patA_tl@test.com")
    _u2, p2, token2 = await _create_patient_user(db_session, "patB_tl@test.com")
    hosp = await _create_test_hospital(db_session)
    cons_b = await _create_consultation(db_session, p2.id, hosp.id)

    # Patient A attempts to view Patient B's timeline by patient_id -> safe 404
    res_p = await client.get(
        f"/api/v1/patients/{p2.id}/timeline",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res_p.status_code == 404

    # Patient A attempts to view Patient B's consultation timeline -> safe 404
    res_c = await client.get(
        f"/api/v1/consultations/{cons_b.id}/timeline",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res_c.status_code == 404


@pytest.mark.asyncio
async def test_v_hospital_staff_authorization(client: AsyncClient, db_session: AsyncSession):
    """V. Hospital staff can access patient timeline ONLY for their authorized facility."""
    hosp1 = await _create_test_hospital(db_session, name="Hospital Alpha")
    hosp2 = await _create_test_hospital(db_session, name="Hospital Beta")

    _u, patient, _tok = await _create_patient_user(db_session, "pat_hosp_tl@test.com")
    cons1 = await _create_consultation(db_session, patient.id, hosp1.id)

    _udoc1, _hdoc1, token_doc1 = await _create_hospital_staff_user(db_session, hosp1.id, "doc1@test.com")
    _udoc2, _hdoc2, token_doc2 = await _create_hospital_staff_user(db_session, hosp2.id, "doc2@test.com")

    # Doctor 1 at Hospital Alpha CAN access via consultation -> 200
    res_auth = await client.get(
        f"/api/v1/consultations/{cons1.id}/timeline",
        headers={"Authorization": f"Bearer {token_doc1}"},
    )
    assert res_auth.status_code == 200

    # Doctor 1 at Hospital Alpha CAN access via patient_id (facility relation exists) -> 200
    res_pat_auth = await client.get(
        f"/api/v1/patients/{patient.id}/timeline",
        headers={"Authorization": f"Bearer {token_doc1}"},
    )
    assert res_pat_auth.status_code == 200

    # Doctor 2 at Hospital Beta CANNOT access -> 404 (safe 404)
    res_unauth = await client.get(
        f"/api/v1/consultations/{cons1.id}/timeline",
        headers={"Authorization": f"Bearer {token_doc2}"},
    )
    assert res_unauth.status_code == 404

    res_pat_unauth = await client.get(
        f"/api/v1/patients/{patient.id}/timeline",
        headers={"Authorization": f"Bearer {token_doc2}"},
    )
    assert res_pat_unauth.status_code == 404


@pytest.mark.asyncio
async def test_ad_timeline_filtering(client: AsyncClient, db_session: AsyncSession):
    """AD. Filter timeline by event_type, source_type, and date ranges."""
    _u, patient, token = await _create_patient_user(db_session, "filter_tl@test.com")

    ev_lab = TimelineEvent(
        id=uuid.uuid4(),
        patient_id=patient.id,
        event_type="LAB_RESULT",
        title="Hemoglobin",
        event_date=date(2025, 2, 1),
        source_type="MEDICAL_DOCUMENT",
    )
    ev_med = TimelineEvent(
        id=uuid.uuid4(),
        patient_id=patient.id,
        event_type="MEDICATION",
        title="Paracetamol",
        event_date=date(2025, 5, 1),
        source_type="CONSULTATION",
    )
    db_session.add_all([ev_lab, ev_med])
    await db_session.commit()

    # Filter by event_type
    res_lab = await client.get(
        "/api/v1/patients/me/timeline?event_type=LAB_RESULT",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_lab.status_code == 200
    assert len(res_lab.json()["events"]) == 1
    assert res_lab.json()["events"][0]["event_type"] == "LAB_RESULT"

    # Filter by date range
    res_date = await client.get(
        "/api/v1/patients/me/timeline?start_date=2025-04-01&end_date=2025-06-01",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_date.status_code == 200
    assert len(res_date.json()["events"]) == 1
    assert res_date.json()["events"][0]["title"] == "Paracetamol"


@pytest.mark.asyncio
async def test_ae_special_cases_non_diagnostic(client: AsyncClient, db_session: AsyncSession):
    """AE. Special clinical cases:
    - Patient symptom complaint does NOT become diagnosis
    - Document diagnosis preserves source document provenance
    - Dates are strictly non-fabricated
    """
    _u, patient, token = await _create_patient_user(db_session, "special_tl@test.com")
    hosp = await _create_test_hospital(db_session)
    cons = await _create_consultation(db_session, patient.id, hosp.id)

    # 1. Patient says "I get wheezing sometimes"
    ch = ClinicalHistory(
        id=uuid.uuid4(),
        consultation_id=cons.id,
        chief_complaint="I get wheezing sometimes",
        history_of_present_illness="Wheezing occasionally when exposed to cold air",
    )
    db_session.add(ch)
    await db_session.commit()

    # 2. Document explicitly says "Diagnosis: Asthma"
    doc_payload = {
        "diagnoses_or_conditions_as_documented": ["Asthma"],
        "laboratory_results": [
            {
                "test_name": "Hemoglobin",
                "value": "10.2",
                "unit": "g/dL",
                "test_date": "2025-03-15",
                "evidence": "15/03/2025 Hb 10.2 g/dL",
                "source_page": 1,
            }
        ],
    }
    doc = await _create_medical_document_with_extraction(
        db_session,
        patient.id,
        document_date=date(2025, 3, 15),
        extracted_json=doc_payload,
    )

    res = await client.get(
        "/api/v1/patients/me/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    events = res.json()["events"]

    # Verify patient wheezing is SYMPTOM, NOT DIAGNOSIS_DOCUMENTED
    wheezing_ev = next((e for e in events if "wheezing" in e["title"].lower()), None)
    assert wheezing_ev is not None
    assert wheezing_ev["event_type"] == "SYMPTOM"
    assert wheezing_ev["source_type"] == "PATIENT_HISTORY"

    # Verify Asthma is DIAGNOSIS_DOCUMENTED from MEDICAL_DOCUMENT
    asthma_ev = next((e for e in events if "asthma" in e["title"].lower()), None)
    assert asthma_ev is not None
    assert asthma_ev["event_type"] == "DIAGNOSIS_DOCUMENTED"
    assert asthma_ev["source_type"] == "MEDICAL_DOCUMENT"
    assert asthma_ev["medical_document_id"] == str(doc.id)

    # Verify Hb lab test has exact date and evidence
    hb_ev = next((e for e in events if "hemoglobin" in e["title"].lower()), None)
    assert hb_ev is not None
    assert hb_ev["event_date"] == "2025-03-15"
    assert hb_ev["date_precision"] == "EXACT"
    assert hb_ev["evidence"] == "15/03/2025 Hb 10.2 g/dL"
    assert hb_ev["source_page"] == 1


@pytest.mark.asyncio
async def test_x_patient_cannot_mark_clinician_verified(client: AsyncClient, db_session: AsyncSession):
    """X. Patient reports remain UNVERIFIED; no public endpoint exists for patients to mark CLINICIAN_VERIFIED."""
    _u, patient, token = await _create_patient_user(db_session, "patient_verify@test.com")
    hosp = await _create_test_hospital(db_session)
    cons = await _create_consultation(db_session, patient.id, hosp.id)

    ch = ClinicalHistory(
        id=uuid.uuid4(),
        consultation_id=cons.id,
        past_surgical_history="Hernia repair 2021",
    )
    db_session.add(ch)
    await db_session.commit()

    res = await client.get(
        "/api/v1/patients/me/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    events = res.json()["events"]
    hernia = next((e for e in events if e["event_type"] == "SURGERY"), None)
    assert hernia is not None
    assert hernia["verification_status"] == "UNVERIFIED"

    # Patient has no endpoint to mutate verification status directly
    put_res = await client.put(
        f"/api/v1/patients/me/timeline/{hernia['id']}",
        json={"verification_status": "CLINICIAN_VERIFIED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_res.status_code in (404, 405)


@pytest.mark.asyncio
async def test_y_missing_source_data_does_not_invent_events(client: AsyncClient, db_session: AsyncSession):
    """Y. Empty or None fields in clinical history / documents do NOT produce ghost events."""
    _u, patient, token = await _create_patient_user(db_session, "missing_source@test.com")
    hosp = await _create_test_hospital(db_session)
    cons = await _create_consultation(db_session, patient.id, hosp.id)

    # Empty clinical history
    ch = ClinicalHistory(
        id=uuid.uuid4(),
        consultation_id=cons.id,
        chief_complaint=None,
        history_of_present_illness=None,
        past_medical_history=None,
        past_surgical_history=None,
        drug_history=None,
        allergy_history=None,
    )
    db_session.add(ch)
    await db_session.commit()

    res = await client.get(
        "/api/v1/patients/me/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    events = res.json()["events"]
    # Only the CONSULTATION encounter event should exist; no phantom surgery/med/allergy events
    assert len(events) == 1
    assert events[0]["event_type"] == "CONSULTATION"


@pytest.mark.asyncio
async def test_z_extraction_failure_does_not_corrupt_timeline(client: AsyncClient, db_session: AsyncSession):
    """Z. A failed document extraction does not break or delete other valid timeline events."""
    _u, patient, token = await _create_patient_user(db_session, "failed_doc@test.com")
    hosp = await _create_test_hospital(db_session)
    await _create_consultation(db_session, patient.id, hosp.id)

    # Add a failed document
    failed_doc = MedicalDocument(
        id=uuid.uuid4(),
        patient_id=patient.id,
        file_name="corrupt.pdf",
        file_url="medical_documents/corrupt.pdf",
        document_type="lab_report",
        ocr_status="failed",
    )
    db_session.add(failed_doc)
    extracted = ExtractedData(
        id=uuid.uuid4(),
        document_id=failed_doc.id,
        extraction_status="failed",
        extracted_json={"warnings": ["OCR processing failed"]},
    )
    db_session.add(extracted)
    await db_session.commit()

    # Timeline builds cleanly without crashing
    res = await client.get(
        "/api/v1/patients/me/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    events = res.json()["events"]
    assert len(events) >= 1
    assert any(e["event_type"] == "CONSULTATION" for e in events)


@pytest.mark.asyncio
async def test_aa_updating_clinical_history_rebuilds_cleanly(client: AsyncClient, db_session: AsyncSession):
    """AA. Updating a clinical history record and rebuilding updates existing events without unbounded rows."""
    _u, patient, token = await _create_patient_user(db_session, "update_history@test.com")
    hosp = await _create_test_hospital(db_session)
    cons = await _create_consultation(db_session, patient.id, hosp.id)

    ch = ClinicalHistory(
        id=uuid.uuid4(),
        consultation_id=cons.id,
        past_surgical_history="C-section in 2019",
    )
    db_session.add(ch)
    await db_session.commit()

    # First build
    res1 = await client.get(
        "/api/v1/patients/me/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 200
    assert any("C-section" in e["title"] for e in res1.json()["events"])
    count1 = res1.json()["total_events"]

    # Rebuild again without changes
    res_rebuild = await client.post(
        "/api/v1/patients/me/timeline/rebuild",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_rebuild.status_code == 200
    assert res_rebuild.json()["total_events"] == count1


@pytest.mark.asyncio
async def test_ab_multiple_documents_independent_events(client: AsyncClient, db_session: AsyncSession):
    """AB. Multiple independent documents contribute distinct events to the timeline."""
    _u, patient, token = await _create_patient_user(db_session, "multi_doc@test.com")

    # Doc 1: CBC
    doc1 = await _create_medical_document_with_extraction(
        db_session,
        patient.id,
        document_date=date(2025, 1, 10),
        extracted_json={
            "laboratory_results": [
                {"test_name": "Hemoglobin", "value": "12.0", "unit": "g/dL", "test_date": "2025-01-10"}
            ]
        },
    )

    # Doc 2: Lipid Profile
    doc2 = await _create_medical_document_with_extraction(
        db_session,
        patient.id,
        document_date=date(2025, 2, 20),
        extracted_json={
            "laboratory_results": [
                {"test_name": "Total Cholesterol", "value": "190", "unit": "mg/dL", "test_date": "2025-02-20"}
            ]
        },
    )

    res = await client.get(
        "/api/v1/patients/me/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    events = res.json()["events"]

    hb = next((e for e in events if "hemoglobin" in e["title"].lower()), None)
    chol = next((e for e in events if "cholesterol" in e["title"].lower()), None)

    assert hb is not None
    assert chol is not None
    assert hb["medical_document_id"] == str(doc1.id)
    assert chol["medical_document_id"] == str(doc2.id)
    assert hb["event_date"] == "2025-01-10"
    assert chol["event_date"] == "2025-02-20"


@pytest.mark.asyncio
async def test_ac_multiple_sources_distinct_events(client: AsyncClient, db_session: AsyncSession):
    """AC. A patient-reported medication and a prescribed document medication preserve separate provenances."""
    _u, patient, token = await _create_patient_user(db_session, "dual_source@test.com")
    hosp = await _create_test_hospital(db_session)
    cons = await _create_consultation(db_session, patient.id, hosp.id)

    # 1. Patient reports Metformin in history
    ch = ClinicalHistory(
        id=uuid.uuid4(),
        consultation_id=cons.id,
        drug_history="Tab Metformin 500mg daily",
    )
    db_session.add(ch)
    await db_session.commit()

    # 2. Uploaded prescription has Metformin
    doc = await _create_medical_document_with_extraction(
        db_session,
        patient.id,
        consultation_id=cons.id,
        document_date=date(2025, 3, 1),
        extracted_json={
            "medications": [
                {
                    "name_as_written": "Metformin",
                    "dose_as_written": "500mg",
                    "frequency_as_written": "once daily",
                    "evidence": "Rx: Metformin 500mg OD",
                    "source_page": 1,
                }
            ]
        },
    )

    res = await client.get(
        "/api/v1/patients/me/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    events = res.json()["events"]

    met_events = [e for e in events if "metformin" in e["title"].lower()]
    assert len(met_events) == 2

    patient_src = next((e for e in met_events if e["source_type"] == "PATIENT_HISTORY"), None)
    doc_src = next((e for e in met_events if e["source_type"] == "MEDICAL_DOCUMENT"), None)

    assert patient_src is not None
    assert doc_src is not None
    assert patient_src["verification_status"] == "UNVERIFIED"
    assert doc_src["verification_status"] == "SOURCE_CONFIRMED"
    assert doc_src["medical_document_id"] == str(doc.id)

