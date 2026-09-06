"""Comprehensive test suite for Step 9: AI Clinical Summary + Physician Review.

Test Scenarios:
1. Context Assembler combines multi-source records (history, interview, docs, alerts, timeline).
2. AI draft summary generation succeeds with valid JSON and structured response.
3. AI provider failure gracefully triggers deterministic grounded fallback without crashing.
4. GET /api/v1/consultations/{id}/summary auto-generates draft if none exists.
5. Patient can view own consultation summary (read-only).
6. Patient cannot view another patient's consultation summary (returns safe 404).
7. Patient is forbidden from editing draft summary (returns 403).
8. Patient is forbidden from confirming draft summary (returns 403).
9. Patient is forbidden from rejecting draft summary (returns 403).
10. Hospital clinician can edit draft summary (increments version, preserves ai_draft_text, logs audit).
11. Hospital clinician can confirm summary (status='confirmed', reviewed_by/reviewed_at set, updates consultation, upgrades timeline events, logs audit).
12. Hospital clinician can reject summary (status='rejected', rejection reason recorded, logs audit).
13. Cannot edit or confirm a rejected summary without new draft.
14. Cross-hospital clinician access returns safe 404.
15. Force rebuild refreshes unconfirmed draft.
16. Provenance and evidence preservation across sections (PATIENT_REPORTED, DOCUMENT_EXTRACTED).
17. Clinical non-diagnostic safety disclaimer and absence of synthetic diagnoses/prescriptions.
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas import AIErrorKind, AIProviderError, AIResponse
from app.models.ai_message import AIMessage
from app.models.ai_session import AISession
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.clinical_history import ClinicalHistory
from app.models.consultation import Consultation
from app.models.extracted_data import ExtractedData
from app.models.hospital import Hospital
from app.models.hospital_user import HospitalUser
from app.models.medical_document import MedicalDocument
from app.models.patient import Patient
from app.models.summary import Summary
from app.models.timeline_event import TimelineEvent
from app.models.user import User
from app.schemas.summary import SummaryStatus
from app.schemas.timeline import TimelineVerificationStatus
from app.services.auth_service import create_access_token
from app.summary.context_assembler import context_assembler
from app.summary.generator import clinical_summary_generator
from app.summary.service import clinical_summary_service

# ---------------------------------------------------------------------------
# Helpers & Fixtures
# ---------------------------------------------------------------------------


async def _create_test_hospital(db: AsyncSession, name: str = "Apollo Hospital") -> Hospital:
    hospital = Hospital(
        id=uuid.uuid4(),
        name=name,
        registration_number=f"REG_{uuid.uuid4().hex[:6]}",
        address="100 Medical Blvd",
        city="Bengaluru",
        state="Karnataka",
        pincode="560001",
    )
    db.add(hospital)
    await db.flush()
    return hospital


async def _create_test_patient(
    db: AsyncSession, email: str = "patient@test.org"
) -> tuple[User, Patient, str]:
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
        full_name="Ananya Sharma",
        gender="female",
        date_of_birth=date(1990, 5, 15),
    )
    db.add(patient)
    await db.flush()

    token = create_access_token(data={"sub": str(user.id), "role": "patient"})
    return user, patient, token


async def _create_test_hospital_user(
    db: AsyncSession, hospital_id: uuid.UUID, role: str = "doctor", email: str = "doctor@test.org"
) -> tuple[User, HospitalUser, str]:
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

    token = create_access_token(data={"sub": str(user.id), "role": "hospital"})
    return user, h_user, token


async def _create_test_consultation(
    db: AsyncSession, patient_id: uuid.UUID, hospital_id: uuid.UUID, chief_complaint: str = "Fever and sore throat"
) -> Consultation:
    consultation = Consultation(
        id=uuid.uuid4(),
        patient_id=patient_id,
        hospital_id=hospital_id,
        status="initiated",
        chief_complaint=chief_complaint,
        started_at=datetime.now(timezone.utc),
    )
    db.add(consultation)
    await db.flush()
    return consultation


# ---------------------------------------------------------------------------
# Unit & Service Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_context_assembler_aggregates_all_sources(db_session: AsyncSession):
    """1. Context assembler collects clinical history, interview turns, docs, alerts, and timeline."""
    hosp = await _create_test_hospital(db_session)
    _user, patient, _ = await _create_test_patient(db_session)
    consultation = await _create_test_consultation(
        db_session, patient.id, hosp.id, chief_complaint="Severe throat pain"
    )

    # Add Clinical History
    ch = ClinicalHistory(
        consultation_id=consultation.id,
        chief_complaint="Severe throat pain for 3 days",
        history_of_present_illness="Patient reports painful swallowing.",
        past_medical_history="Mild asthma",
        drug_history="Salbutamol inhaler PRN",
        allergy_history="Penicillin",
    )
    db_session.add(ch)

    # Add AI Interview Session + Message
    session = AISession(
        consultation_id=consultation.id,
    )
    db_session.add(session)
    await db_session.flush()

    msg1 = AIMessage(ai_session_id=session.id, sender="patient", message="It hurts badly when I swallow.")
    msg2 = AIMessage(ai_session_id=session.id, sender="ai", message="How long has it hurt?")
    db_session.add_all([msg1, msg2])

    # Add Alert
    alert = Alert(
        consultation_id=consultation.id,
        patient_id=patient.id,
        alert_type="RESPIRATORY_DISTRESS",
        severity="high",
        message="Difficulty breathing noted.",
        status="active",
    )
    db_session.add(alert)

    # Add Document + Extracted Data
    doc = MedicalDocument(
        patient_id=patient.id,
        consultation_id=consultation.id,
        file_name="lab_report.pdf",
        document_type="Lab Report",
        file_url="/mock/path.pdf",
    )
    db_session.add(doc)
    await db_session.flush()

    ext = ExtractedData(
        document_id=doc.id,
        extracted_json={
            "medications": [{"name_as_written": "Paracetamol 500mg", "dose_as_written": "500mg"}],
            "laboratory_results": [{"test_name": "WBC Count", "result_value": "12000", "unit": "/mcL", "abnormal_flag": "high"}],
        },
        extraction_status="completed",
    )
    db_session.add(ext)

    # Add Timeline Event
    t_event = TimelineEvent(
        patient_id=patient.id,
        consultation_id=consultation.id,
        event_type="SURGERY",
        title="Appendectomy",
        event_date=date(2018, 6, 12),
        source_type="CLINICAL_HISTORY",
        verification_status="UNVERIFIED",
    )
    db_session.add(t_event)
    await db_session.commit()

    # Assemble context
    context = await context_assembler.assemble_context(db_session, consultation.id)

    assert context["patient"]["name"] == "Ananya Sharma"
    assert context["consultation"]["chief_complaint"] == "Severe throat pain"
    assert context["clinical_history"]["past_medical_history"] == "Mild asthma"
    assert len(context["alerts"]) == 1
    assert context["alerts"][0]["alert_type"] == "RESPIRATORY_DISTRESS"
    assert len(context["documents"]) == 1
    assert context["documents"][0]["extractions"]["medications"][0]["name_as_written"] == "Paracetamol 500mg"
    assert len(context["timeline_highlights"]) >= 1


@pytest.mark.asyncio
async def test_ai_draft_summary_generation_success(db_session: AsyncSession):
    """2. AI generation parses structured JSON and generates prose summary."""
    hosp = await _create_test_hospital(db_session)
    user, patient, _ = await _create_test_patient(db_session)
    consultation = await _create_test_consultation(db_session, patient.id, hosp.id)
    await db_session.commit()

    mock_ai_json = {
        "chief_complaint": "Fever and sore throat",
        "history_of_present_illness": "Patient has had sore throat for 2 days.",
        "patient_reported_symptoms": [
            {"item": "Throat pain", "source_type": "PATIENT_REPORTED", "evidence": "hurts to swallow"}
        ],
        "past_medical_history": [],
        "past_surgical_history": [],
        "current_medications": [],
        "allergies": [],
        "family_and_social_history": [],
        "relevant_investigations": [],
        "triage_and_red_flags": [],
        "timeline_highlights": [],
        "unreported_or_unclear_areas": ["Allergy status unclear"],
        "disclaimer": "AI-generated clinical draft for physician review only. Not a medical diagnosis or treatment plan.",
    }

    with patch("app.summary.generator.task_router.generate", return_value=AIResponse(
        text=f"```json\n{json.dumps(mock_ai_json)}\n```",
        provider="gemini",
        model="gemini-2.0-flash",
    )):
        summary = await clinical_summary_service.get_or_generate_summary(
            db_session, consultation.id, user
        )

    assert summary.id is not None
    assert summary.status == SummaryStatus.DRAFT.value
    assert summary.version == 1
    assert "CLINICAL SUMMARY DRAFT FOR PHYSICIAN REVIEW" in summary.summary_text
    assert summary.ai_draft_text == summary.summary_text
    assert summary.structured_summary["chief_complaint"] == "Fever and sore throat"

    # Verify audit log
    audit_stmt = select(AuditLog).where(AuditLog.action == "summary_generated")
    audit = (await db_session.execute(audit_stmt)).scalar_one_or_none()
    assert audit is not None
    assert audit.entity_id == str(consultation.id)


@pytest.mark.asyncio
async def test_ai_failure_deterministic_fallback(db_session: AsyncSession):
    """3. AI provider failure gracefully produces a safe deterministic summary."""
    hosp = await _create_test_hospital(db_session)
    user, patient, _ = await _create_test_patient(db_session)
    consultation = await _create_test_consultation(
        db_session, patient.id, hosp.id, chief_complaint="Persistent dry cough"
    )
    await db_session.commit()

    with patch("app.summary.generator.task_router.generate", side_effect=AIProviderError(
        kind=AIErrorKind.PROVIDER_UNAVAILABLE,
        provider="gemini",
        message="Service unreachable",
    )):
        summary = await clinical_summary_service.get_or_generate_summary(
            db_session, consultation.id, user
        )

    assert summary.id is not None
    assert summary.status == SummaryStatus.DRAFT.value
    assert "Persistent dry cough" in summary.summary_text
    assert summary.structured_summary is not None
    assert summary.structured_summary["chief_complaint"] == "Persistent dry cough"


# ---------------------------------------------------------------------------
# API Endpoints & Role Authorization Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patient_can_view_own_summary(client: AsyncClient, db_session: AsyncSession):
    """4 & 5. Patient can get summary for their consultation, auto-generating draft."""
    hosp = await _create_test_hospital(db_session)
    _user, patient, patient_token = await _create_test_patient(db_session)
    consultation = await _create_test_consultation(db_session, patient.id, hosp.id)
    await db_session.commit()

    res = await client.get(
        f"/api/v1/consultations/{consultation.id}/summary",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["consultation_id"] == str(consultation.id)
    assert data["status"] == "draft"
    assert data["version"] == 1
    assert "summary_text" in data


@pytest.mark.asyncio
async def test_patient_cannot_view_other_patient_summary(client: AsyncClient, db_session: AsyncSession):
    """6. Accessing another patient's consultation summary returns safe 404."""
    hosp = await _create_test_hospital(db_session)
    _user1, patient1, _ = await _create_test_patient(db_session, email="patient1@test.org")
    _user2, _patient2, token2 = await _create_test_patient(db_session, email="patient2@test.org")
    consultation1 = await _create_test_consultation(db_session, patient1.id, hosp.id)
    await db_session.commit()

    res = await client.get(
        f"/api/v1/consultations/{consultation1.id}/summary",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Consultation summary not found."


@pytest.mark.asyncio
async def test_patient_forbidden_from_editing_summary(client: AsyncClient, db_session: AsyncSession):
    """7. Patient attempting to edit summary receives 403 Forbidden."""
    hosp = await _create_test_hospital(db_session)
    _user, patient, patient_token = await _create_test_patient(db_session)
    consultation = await _create_test_consultation(db_session, patient.id, hosp.id)
    await db_session.commit()

    res = await client.put(
        f"/api/v1/consultations/{consultation.id}/summary",
        json={"summary_text": "Patient self-diagnosis: Viral Pharyngitis"},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert res.status_code == 403
    assert "Only authorized hospital clinicians" in res.json()["detail"]


@pytest.mark.asyncio
async def test_patient_forbidden_from_confirming_summary(client: AsyncClient, db_session: AsyncSession):
    """8. Patient attempting to confirm summary receives 403 Forbidden."""
    hosp = await _create_test_hospital(db_session)
    _user, patient, patient_token = await _create_test_patient(db_session)
    consultation = await _create_test_consultation(db_session, patient.id, hosp.id)
    await db_session.commit()

    res = await client.post(
        f"/api/v1/consultations/{consultation.id}/summary/confirm",
        json={},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert res.status_code == 403
    assert "Only authorized hospital clinicians" in res.json()["detail"]


@pytest.mark.asyncio
async def test_patient_forbidden_from_rejecting_summary(client: AsyncClient, db_session: AsyncSession):
    """9. Patient attempting to reject summary receives 403 Forbidden."""
    hosp = await _create_test_hospital(db_session)
    _user, patient, patient_token = await _create_test_patient(db_session)
    consultation = await _create_test_consultation(db_session, patient.id, hosp.id)
    await db_session.commit()

    res = await client.post(
        f"/api/v1/consultations/{consultation.id}/summary/reject",
        json={"reason": "Patient dislikes this draft"},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert res.status_code == 403
    assert "Only authorized hospital clinicians" in res.json()["detail"]


@pytest.mark.asyncio
async def test_clinician_can_edit_summary(client: AsyncClient, db_session: AsyncSession):
    """10. Authorized clinician edits summary, incrementing version and preserving ai_draft_text."""
    hosp = await _create_test_hospital(db_session)
    _p_user, patient, _ = await _create_test_patient(db_session)
    _doc_user, _h_user, doc_token = await _create_test_hospital_user(db_session, hosp.id, role="doctor")
    consultation = await _create_test_consultation(db_session, patient.id, hosp.id)
    await db_session.commit()

    # Pre-generate draft
    await client.get(
        f"/api/v1/consultations/{consultation.id}/summary",
        headers={"Authorization": f"Bearer {doc_token}"},
    )

    # Clinician edit
    edit_payload = {
        "summary_text": "Updated clinical impression by Dr. Rao.",
        "clinician_notes": "Exudative pharyngitis on examination.",
    }
    edit_res = await client.put(
        f"/api/v1/consultations/{consultation.id}/summary",
        json=edit_payload,
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert edit_res.status_code == 200
    data = edit_res.json()
    assert data["version"] == 2
    assert data["summary_text"] == "Updated clinical impression by Dr. Rao."
    assert data["clinician_notes"] == "Exudative pharyngitis on examination."
    assert data["ai_draft_text"] is not None
    assert data["ai_draft_text"] != data["summary_text"]

    # Verify audit log
    audit_stmt = select(AuditLog).where(AuditLog.action == "summary_edited")
    audit = (await db_session.execute(audit_stmt)).scalar_one_or_none()
    assert audit is not None


@pytest.mark.asyncio
async def test_clinician_can_confirm_summary(client: AsyncClient, db_session: AsyncSession):
    """11. Clinician confirms summary, promoting consultation and upgrading timeline events."""
    hosp = await _create_test_hospital(db_session)
    _p_user, patient, _ = await _create_test_patient(db_session)
    doc_user, _h_user, doc_token = await _create_test_hospital_user(db_session, hosp.id, role="doctor")
    consultation = await _create_test_consultation(db_session, patient.id, hosp.id)

    # Add unverified timeline event
    t_event = TimelineEvent(
        patient_id=patient.id,
        consultation_id=consultation.id,
        event_type="SYMPTOM",
        title="High fever",
        event_date=date.today(),
        source_type="PATIENT_REPORTED",
        verification_status="UNVERIFIED",
    )
    db_session.add(t_event)
    await db_session.commit()

    # Generate draft
    await client.get(
        f"/api/v1/consultations/{consultation.id}/summary",
        headers={"Authorization": f"Bearer {doc_token}"},
    )

    # Confirm summary
    confirm_res = await client.post(
        f"/api/v1/consultations/{consultation.id}/summary/confirm",
        json={"clinician_notes": "Reviewed and verified clinical facts.", "confirm_timeline_events": True},
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert confirm_res.status_code == 200
    data = confirm_res.json()
    assert data["status"] == "confirmed"
    assert data["reviewed_by_id"] == str(doc_user.id)
    assert data["reviewed_at"] is not None
    assert data["clinician_notes"] == "Reviewed and verified clinical facts."

    # Check consultation status promoted to reviewed
    await db_session.refresh(consultation)
    assert consultation.status == "reviewed"

    # Check timeline event promoted to CLINICIAN_VERIFIED
    await db_session.refresh(t_event)
    assert t_event.verification_status == TimelineVerificationStatus.CLINICIAN_VERIFIED.value

    # Check audit log
    audit_stmt = select(AuditLog).where(AuditLog.action == "summary_confirmed")
    audit = (await db_session.execute(audit_stmt)).scalar_one_or_none()
    assert audit is not None


@pytest.mark.asyncio
async def test_clinician_can_reject_summary(client: AsyncClient, db_session: AsyncSession):
    """12. Clinician rejects summary with reason."""
    hosp = await _create_test_hospital(db_session)
    _p_user, patient, _ = await _create_test_patient(db_session)
    doc_user, _h_user, doc_token = await _create_test_hospital_user(db_session, hosp.id, role="doctor")
    consultation = await _create_test_consultation(db_session, patient.id, hosp.id)
    await db_session.commit()

    # Generate draft
    await client.get(
        f"/api/v1/consultations/{consultation.id}/summary",
        headers={"Authorization": f"Bearer {doc_token}"},
    )

    # Reject draft
    reject_res = await client.post(
        f"/api/v1/consultations/{consultation.id}/summary/reject",
        json={"reason": "Inaccurate extraction of history and symptoms."},
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert reject_res.status_code == 200
    data = reject_res.json()
    assert data["status"] == "rejected"
    assert data["reviewed_by_id"] == str(doc_user.id)
    assert data["rejection_reason"] == "Inaccurate extraction of history and symptoms."

    # Check audit log
    audit_stmt = select(AuditLog).where(AuditLog.action == "summary_rejected")
    audit = (await db_session.execute(audit_stmt)).scalar_one_or_none()
    assert audit is not None


@pytest.mark.asyncio
async def test_cannot_edit_or_confirm_rejected_summary(client: AsyncClient, db_session: AsyncSession):
    """13. Attempting to edit or confirm a rejected summary returns 400 Bad Request."""
    hosp = await _create_test_hospital(db_session)
    _p_user, patient, _ = await _create_test_patient(db_session)
    _doc_user, _h_user, doc_token = await _create_test_hospital_user(db_session, hosp.id, role="doctor")
    consultation = await _create_test_consultation(db_session, patient.id, hosp.id)
    await db_session.commit()

    # Create rejected summary
    summary = Summary(
        consultation_id=consultation.id,
        summary_text="Rejected draft",
        status=SummaryStatus.REJECTED.value,
        rejection_reason="Discarded by clinician",
    )
    db_session.add(summary)
    await db_session.commit()

    # Try edit
    edit_res = await client.put(
        f"/api/v1/consultations/{consultation.id}/summary",
        json={"summary_text": "Trying to edit rejected"},
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert edit_res.status_code == 400
    assert "Cannot edit a rejected summary" in edit_res.json()["detail"]

    # Try confirm
    confirm_res = await client.post(
        f"/api/v1/consultations/{consultation.id}/summary/confirm",
        json={},
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert confirm_res.status_code == 400
    assert "Cannot confirm a rejected summary" in confirm_res.json()["detail"]


@pytest.mark.asyncio
async def test_cross_hospital_access_returns_404(client: AsyncClient, db_session: AsyncSession):
    """14. Clinician from Hospital B accessing consultation from Hospital A gets safe 404."""
    hosp_a = await _create_test_hospital(db_session, name="Hospital A")
    hosp_b = await _create_test_hospital(db_session, name="Hospital B")
    _p_user, patient, _ = await _create_test_patient(db_session)
    _doc_b_user, _h_b_user, doc_b_token = await _create_test_hospital_user(
        db_session, hosp_b.id, role="doctor", email="doctor_b@hospitalb.org"
    )
    consultation_a = await _create_test_consultation(db_session, patient.id, hosp_a.id)
    await db_session.commit()

    res = await client.get(
        f"/api/v1/consultations/{consultation_a.id}/summary",
        headers={"Authorization": f"Bearer {doc_b_token}"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Consultation summary not found."


@pytest.mark.asyncio
async def test_force_rebuild_summary(client: AsyncClient, db_session: AsyncSession):
    """15. Force rebuild refreshes unconfirmed draft."""
    hosp = await _create_test_hospital(db_session)
    _p_user, patient, _ = await _create_test_patient(db_session)
    _doc_user, _h_user, doc_token = await _create_test_hospital_user(db_session, hosp.id, role="doctor")
    consultation = await _create_test_consultation(db_session, patient.id, hosp.id)
    await db_session.commit()

    # Initial draft
    res1 = await client.get(
        f"/api/v1/consultations/{consultation.id}/summary",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert res1.status_code == 200
    v1 = res1.json()["version"]

    # Force rebuild
    res2 = await client.post(
        f"/api/v1/consultations/{consultation.id}/summary/generate",
        json={"force_rebuild": True},
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert res2.status_code == 200
    assert res2.json()["version"] == v1 + 1


@pytest.mark.asyncio
async def test_non_diagnostic_disclaimer_present(db_session: AsyncSession):
    """16 & 17. Non-diagnostic safety disclaimer is always enforced in structured summary."""
    hosp = await _create_test_hospital(db_session)
    _user, patient, _ = await _create_test_patient(db_session)
    consultation = await _create_test_consultation(db_session, patient.id, hosp.id)
    await db_session.commit()

    context = await context_assembler.assemble_context(db_session, consultation.id)
    summary_text, structured = await clinical_summary_generator.generate_summary(context)

    assert "AI-generated clinical draft for physician review only" in structured["disclaimer"]
    assert "Not a medical diagnosis or treatment plan" in structured["disclaimer"]
    assert "Note: AI-generated clinical draft for physician review only" in summary_text


@pytest.mark.asyncio
async def test_rejection_validation_short_reason(client: AsyncClient, db_session: AsyncSession):
    """18. Rejecting summary with empty or too short reason returns HTTP 422 Unprocessable Entity."""
    hosp = await _create_test_hospital(db_session)
    _p_user, patient, _ = await _create_test_patient(db_session)
    _doc_user, _h_user, doc_token = await _create_test_hospital_user(db_session, hosp.id, role="doctor")
    consultation = await _create_test_consultation(db_session, patient.id, hosp.id)
    await db_session.commit()

    # Pre-generate draft
    await client.get(
        f"/api/v1/consultations/{consultation.id}/summary",
        headers={"Authorization": f"Bearer {doc_token}"},
    )

    # Reject with invalid short reason
    res = await client.post(
        f"/api/v1/consultations/{consultation.id}/summary/reject",
        json={"reason": "No"},
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_fresh_draft_generation_after_rejection(client: AsyncClient, db_session: AsyncSession):
    """19. Clinician can generate a fresh draft after a summary is rejected."""
    hosp = await _create_test_hospital(db_session)
    _p_user, patient, _ = await _create_test_patient(db_session)
    _doc_user, _h_user, doc_token = await _create_test_hospital_user(db_session, hosp.id, role="doctor")
    consultation = await _create_test_consultation(db_session, patient.id, hosp.id)
    await db_session.commit()

    # Draft 1
    await client.get(
        f"/api/v1/consultations/{consultation.id}/summary",
        headers={"Authorization": f"Bearer {doc_token}"},
    )

    # Reject
    await client.post(
        f"/api/v1/consultations/{consultation.id}/summary/reject",
        json={"reason": "Clinical facts were outdated."},
        headers={"Authorization": f"Bearer {doc_token}"},
    )

    # Generate fresh draft
    res = await client.post(
        f"/api/v1/consultations/{consultation.id}/summary/generate",
        json={"force_rebuild": True},
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "draft"
    assert data["version"] == 2
    assert data["rejection_reason"] is None
