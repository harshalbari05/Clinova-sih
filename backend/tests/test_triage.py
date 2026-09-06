"""Comprehensive automated test suite for Clinova Step 6: Red-Flag Detection & Triage.

Covers:
  A. No red flags (mild stomach pain -> NORMAL)
  B. Severe chest pain (crushing chest pain -> EMERGENCY_REVIEW)
  C. Chest pain + breathing difficulty (conjunction red-flag)
  D. Sudden one-sided weakness (neurological deficit)
  E. Sudden speech difficulty (neurological deficit)
  F. Heavy bleeding / vomiting blood (bleeding red-flag)
  G. Severe breathing difficulty (gasping/cannot catch breath)
  H. Fainting / loss of consciousness (altered consciousness)
  I. Allergic emergency (anaphylaxis with breathing distress)
  J. Self-harm statement indicating immediate intent (safety alert)
  K. Pregnancy-related urgent symptom (heavy bleeding during pregnancy)
  L. Vague/non-emergency symptoms (no over-triggering)
  M. Duplicate alert detection (updates existing active alert without creating duplicates)
  N. Cross-patient security (Patient A cannot access Patient B's triage/alerts -> 404)
  O. Hospital authorization (Hospital user cannot access another facility's consultation -> 404)
  P. AI provider failure resilience (all providers fail -> deterministic rules still run)
  Q. AI malformed response (malformed JSON -> handled gracefully)
  R. AI success integration (structured AI extraction merges cleanly)
  S. Ollama fallback routing (Ollama is last fallback)
  T. Interview engine integration (emergency response uses calm safety notice)
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.registry import clear_provider_cache
from app.ai.router import AITaskRouter
from app.ai.schemas import (
    AIErrorKind,
    AIProviderError,
    AIResponse,
)
from app.ai.tasks import AITaskType
from app.models.alert import Alert
from app.models.consultation import Consultation
from app.models.hospital import Hospital
from app.models.hospital_user import HospitalUser
from app.models.patient import Patient
from app.models.user import User
from app.services.auth_service import create_access_token
from app.triage.detector import DeterministicTriageDetector, default_detector
from app.triage.schemas import (
    TriageCategory,
    TriageUrgency,
)
from app.triage.service import (
    EMERGENCY_SAFETY_NOTICE,
    triage_service,
)

# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------

DUMMY_CONSULTATION_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DUMMY_PATIENT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture(autouse=True)
def reset_registry():
    clear_provider_cache()
    yield
    clear_provider_cache()


async def _create_test_hospital(db: AsyncSession, name: str = "City Hospital") -> Hospital:
    hospital = Hospital(
        id=uuid.uuid4(),
        name=name,
        registration_number=f"REG_{uuid.uuid4().hex[:6]}",
        address="123 Health Ave",
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


async def _create_patient_user(db: AsyncSession, email: str = "patient@example.com") -> tuple[User, Patient, str]:
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
        full_name="John Doe",
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
    db: AsyncSession, hospital_id: uuid.UUID, email: str = "doctor@example.com"
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
        data={
            "sub": str(user.id),
            "role": "hospital_staff",
            "user_type": "hospital",
            "hospital_id": str(hospital_id),
        }
    )
    return user, h_user, token


async def _create_consultation(
    db: AsyncSession, patient_id: uuid.UUID, hospital_id: uuid.UUID, chief_complaint: str = "General checkup"
) -> Consultation:
    consultation = Consultation(
        id=uuid.uuid4(),
        patient_id=patient_id,
        hospital_id=hospital_id,
        status="in_progress",
        chief_complaint=chief_complaint,
    )
    db.add(consultation)
    await db.commit()
    await db.refresh(consultation)
    return consultation


# ---------------------------------------------------------------------------
# Part 15: Scenarios A – L: Deterministic Rule Unit Tests
# ---------------------------------------------------------------------------


def test_scenario_a_no_red_flags_mild_stomach_pain():
    """A. No red flags: 'I have mild stomach pain since yesterday' -> NORMAL."""
    detector = DeterministicTriageDetector()
    res = detector.evaluate(
        consultation_id=DUMMY_CONSULTATION_ID,
        text="I have mild stomach pain since yesterday.",
    )
    assert res.has_red_flags is False
    assert res.urgency == TriageUrgency.NORMAL
    assert len(res.findings) == 0
    assert res.requires_immediate_attention is False


def test_scenario_b_severe_crushing_chest_pain():
    """B. Severe chest pain explicitly reported -> EMERGENCY_REVIEW."""
    detector = DeterministicTriageDetector()
    res = detector.evaluate(
        consultation_id=DUMMY_CONSULTATION_ID,
        text="I am experiencing severe crushing chest pain radiating to my left arm.",
    )
    assert res.has_red_flags is True
    assert res.urgency == TriageUrgency.EMERGENCY_REVIEW
    assert res.requires_immediate_attention is True
    codes = [f.code for f in res.findings]
    assert "CHEST_PAIN_CRUSHING" in codes


def test_scenario_c_chest_pain_with_breathing_difficulty():
    """C. Chest pain + shortness of breath -> EMERGENCY_REVIEW."""
    detector = DeterministicTriageDetector()
    res = detector.evaluate(
        consultation_id=DUMMY_CONSULTATION_ID,
        text="I have chest pain and severe shortness of breath.",
    )
    assert res.has_red_flags is True
    assert res.urgency == TriageUrgency.EMERGENCY_REVIEW
    codes = [f.code for f in res.findings]
    assert "CHEST_PAIN_WITH_DYSPNEA" in codes


def test_scenario_d_sudden_one_sided_weakness():
    """D. Sudden one-sided weakness -> Neurological red-flag."""
    detector = DeterministicTriageDetector()
    res = detector.evaluate(
        consultation_id=DUMMY_CONSULTATION_ID,
        text="All of a sudden, my left arm and leg became weak and my face is drooping on one side.",
    )
    assert res.has_red_flags is True
    assert res.urgency == TriageUrgency.EMERGENCY_REVIEW
    codes = [f.code for f in res.findings]
    assert "STROKE_ONE_SIDED_WEAKNESS" in codes


def test_scenario_e_sudden_speech_difficulty():
    """E. Sudden speech difficulty -> Neurological red-flag."""
    detector = DeterministicTriageDetector()
    res = detector.evaluate(
        consultation_id=DUMMY_CONSULTATION_ID,
        text="My family noticed I suddenly developed slurred speech and cannot speak properly.",
    )
    assert res.has_red_flags is True
    assert res.urgency == TriageUrgency.EMERGENCY_REVIEW
    codes = [f.code for f in res.findings]
    assert "STROKE_SPEECH_DIFFICULTY" in codes


def test_scenario_f_heavy_bleeding_and_hematemesis():
    """F. Heavy bleeding and vomiting blood -> Bleeding red-flag."""
    detector = DeterministicTriageDetector()
    res = detector.evaluate(
        consultation_id=DUMMY_CONSULTATION_ID,
        text="I have uncontrolled bleeding from an injury and I was throwing up blood.",
    )
    assert res.has_red_flags is True
    assert res.urgency == TriageUrgency.EMERGENCY_REVIEW
    codes = [f.code for f in res.findings]
    assert any("BLEEDING" in c for c in codes)


def test_scenario_g_severe_breathing_distress():
    """G. Severe breathing difficulty -> Respiratory red-flag."""
    detector = DeterministicTriageDetector()
    res = detector.evaluate(
        consultation_id=DUMMY_CONSULTATION_ID,
        text="I cannot catch my breath and I am gasping for air right now.",
    )
    assert res.has_red_flags is True
    assert res.urgency == TriageUrgency.EMERGENCY_REVIEW
    codes = [f.code for f in res.findings]
    assert "BREATHING_SEVERE_DISTRESS" in codes


def test_scenario_h_fainting_loss_of_consciousness():
    """H. Fainting/loss of consciousness -> Altered consciousness red-flag."""
    detector = DeterministicTriageDetector()
    res = detector.evaluate(
        consultation_id=DUMMY_CONSULTATION_ID,
        text="The patient collapsed and is unresponsive and difficult to wake.",
    )
    assert res.has_red_flags is True
    assert res.urgency == TriageUrgency.EMERGENCY_REVIEW
    codes = [f.code for f in res.findings]
    assert "ALTERED_CONSCIOUSNESS_UNRESPONSIVE" in codes


def test_scenario_i_allergic_emergency_anaphylaxis():
    """I. Allergic emergency -> Anaphylaxis red-flag when swelling + dyspnea co-occur."""
    detector = DeterministicTriageDetector()
    res = detector.evaluate(
        consultation_id=DUMMY_CONSULTATION_ID,
        text="I had an allergic reaction and my throat is closing up and I can't breathe.",
    )
    assert res.has_red_flags is True
    assert res.urgency == TriageUrgency.EMERGENCY_REVIEW
    codes = [f.code for f in res.findings]
    assert "ANAPHYLAXIS_AIRWAY_SWELLING" in codes


def test_scenario_j_self_harm_immediate_intent():
    """J. Self-harm statement indicating immediate intent -> Safety alert."""
    detector = DeterministicTriageDetector()
    res = detector.evaluate(
        consultation_id=DUMMY_CONSULTATION_ID,
        text="I want to kill myself and I am planning to end my life tonight.",
    )
    assert res.has_red_flags is True
    assert res.urgency == TriageUrgency.EMERGENCY_REVIEW
    codes = [f.code for f in res.findings]
    assert "SELF_HARM_INTENT" in codes


def test_scenario_k_pregnancy_related_urgency():
    """K. Pregnancy-related urgent symptom -> Pregnancy red-flag."""
    detector = DeterministicTriageDetector()
    res = detector.evaluate(
        consultation_id=DUMMY_CONSULTATION_ID,
        text="I am 5 months pregnant and experiencing heavy bleeding and severe abdominal pain.",
    )
    assert res.has_red_flags is True
    assert res.urgency == TriageUrgency.EMERGENCY_REVIEW
    codes = [f.code for f in res.findings]
    assert "PREGNANCY_BLEEDING_OR_SEVERE_PAIN" in codes


def test_scenario_l_vague_non_emergency_symptoms_no_false_positives():
    """L. Vague/chronic symptoms do NOT trigger emergency red flags."""
    detector = DeterministicTriageDetector()

    # Mild dyspnea on exertion only
    res1 = detector.evaluate(
        consultation_id=DUMMY_CONSULTATION_ID,
        text="I sometimes feel a little short of breath when climbing stairs.",
    )
    assert res1.urgency == TriageUrgency.NORMAL
    assert res1.has_red_flags is False

    # Slight chest discomfort after exercise
    res2 = detector.evaluate(
        consultation_id=DUMMY_CONSULTATION_ID,
        text="My chest feels slightly uncomfortable after heavy gym exercise.",
    )
    assert res2.urgency == TriageUrgency.NORMAL
    assert res2.has_red_flags is False

    # Explicit denial of symptoms
    res3 = detector.evaluate(
        consultation_id=DUMMY_CONSULTATION_ID,
        text="I have no chest pain and no shortness of breath, just a cough.",
    )
    assert res3.urgency == TriageUrgency.NORMAL
    assert res3.has_red_flags is False


# ---------------------------------------------------------------------------
# Part 15: Scenarios M – S: Service, Database & Fallback Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scenario_m_duplicate_alert_prevention(db_session: AsyncSession):
    """M. Duplicate detection: calling evaluate_triage twice updates existing active alert."""
    hosp = await _create_test_hospital(db_session)
    _user, patient, _ = await _create_patient_user(db_session)
    consultation = await _create_consultation(db_session, patient.id, hosp.id)

    # First turn: trigger red flag
    res1 = await triage_service.evaluate_triage(
        db=db_session,
        consultation=consultation,
        patient_text="I have severe crushing chest pain in my chest.",
        use_ai_assistance=False,
    )
    assert res1.has_red_flags is True

    # Check alert count
    alerts_stmt = select(Alert).where(Alert.consultation_id == consultation.id)
    alerts_1 = list((await db_session.execute(alerts_stmt)).scalars().all())
    assert len(alerts_1) == 1
    initial_alert_id = alerts_1[0].id
    initial_message = alerts_1[0].message

    # Second turn: same consultation, same red-flag finding
    res2 = await triage_service.evaluate_triage(
        db=db_session,
        consultation=consultation,
        patient_text="The crushing chest pain is still there.",
        use_ai_assistance=False,
    )
    assert res2.has_red_flags is True

    # Verify no duplicate alert row was created!
    alerts_2 = list((await db_session.execute(alerts_stmt)).scalars().all())
    assert len(alerts_2) == 1
    assert alerts_2[0].id == initial_alert_id
    assert alerts_2[0].status == "active"


@pytest.mark.asyncio
async def test_scenario_p_ai_provider_failure_resilience(db_session: AsyncSession):
    """P. When AI providers fail, deterministic engine runs successfully without crash."""
    hosp = await _create_test_hospital(db_session)
    _user, patient, _ = await _create_patient_user(db_session)
    consultation = await _create_consultation(db_session, patient.id, hosp.id)

    # Mock task router to raise provider unavailable error
    with patch("app.triage.service.task_router.generate", side_effect=AIProviderError(
        kind=AIErrorKind.PROVIDER_UNAVAILABLE,
        provider="gemini",
        message="Gemini API is down",
    )):
        res = await triage_service.evaluate_triage(
            db=db_session,
            consultation=consultation,
            patient_text="I have severe crushing chest pain.",
            use_ai_assistance=True,
        )

    # Deterministic result still succeeds completely
    assert res.has_red_flags is True
    assert res.urgency == TriageUrgency.EMERGENCY_REVIEW
    assert any(f.code == "CHEST_PAIN_CRUSHING" for f in res.findings)


@pytest.mark.asyncio
async def test_scenario_q_ai_malformed_response_safe_handling(db_session: AsyncSession):
    """Q. Malformed AI response does not crash application or corrupt state."""
    hosp = await _create_test_hospital(db_session)
    _user, patient, _ = await _create_patient_user(db_session)
    consultation = await _create_consultation(db_session, patient.id, hosp.id)

    # Mock router returning non-JSON garbage
    with patch("app.triage.service.task_router.generate", return_value=AIResponse(
        text="NOT A JSON {corrupted output...}",
        provider="groq",
        model="llama3",
    )):
        res = await triage_service.evaluate_triage(
            db=db_session,
            consultation=consultation,
            patient_text="I have a mild cough, no red flags.",
            use_ai_assistance=True,
        )

    # Handled smoothly without crash
    assert res.urgency == TriageUrgency.NORMAL
    assert res.has_red_flags is False


@pytest.mark.asyncio
async def test_scenario_r_ai_success_integration(db_session: AsyncSession):
    """R. Valid AI structured output is cleanly validated and integrated."""
    hosp = await _create_test_hospital(db_session)
    _user, patient, _ = await _create_patient_user(db_session)
    consultation = await _create_consultation(db_session, patient.id, hosp.id)

    ai_payload = json.dumps({
        "findings": [
            {
                "finding": "severe_chest_pain",
                "category": "cardiovascular_chest",
                "present": True,
                "evidence": "Patient feels crushing tightness in chest",
                "confidence": 0.95
            }
        ],
        "summary_notes": "Patient reported acute severe chest tightness."
    })

    with patch("app.triage.service.task_router.generate", return_value=AIResponse(
        text=ai_payload,
        provider="gemini",
        model="gemini-2.0-flash",
    )):
        res = await triage_service.evaluate_triage(
            db=db_session,
            consultation=consultation,
            patient_text="I feel a tightness in my chest.",
            use_ai_assistance=True,
        )

    assert res.has_red_flags is True
    assert res.source == "DETERMINISTIC_WITH_AI_EVALUATION"
    assert any(f.code == "SEVERE_CHEST_PAIN" for f in res.findings)


def test_scenario_s_ollama_fallback_routing_for_triage():
    """S. Verify Ollama remains the last fallback for AITaskType.TRIAGE."""
    router = AITaskRouter()
    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "gemini"
        mock_settings.AI_TRIAGE_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = ["groq", "openrouter", "ollama"]

        chain = router._build_provider_chain(AITaskType.TRIAGE)

    assert chain == ["gemini", "groq", "openrouter", "ollama"]
    assert chain[-1] == "ollama"


# ---------------------------------------------------------------------------
# Part 15: Scenarios N – O & Endpoints: API & Security Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scenario_n_cross_patient_security(client: AsyncClient, db_session: AsyncSession):
    """N. Patient A cannot access Patient B's triage or alerts (returns 404)."""
    hosp = await _create_test_hospital(db_session)
    _user_a, patient_a, token_a = await _create_patient_user(db_session, email="patient_a@example.com")
    _user_b, patient_b, token_b = await _create_patient_user(db_session, email="patient_b@example.com")

    # Create consultation owned by Patient B
    consultation_b = await _create_consultation(db_session, patient_b.id, hosp.id)

    # Patient A attempts to read Patient B's triage
    res_triage = await client.get(
        f"/api/v1/consultations/{consultation_b.id}/triage",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_triage.status_code == 404
    assert res_triage.json()["detail"] == "Consultation not found"

    # Patient A attempts to read Patient B's alerts
    res_alerts = await client.get(
        f"/api/v1/consultations/{consultation_b.id}/alerts",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_alerts.status_code == 404
    assert res_alerts.json()["detail"] == "Consultation not found"


@pytest.mark.asyncio
async def test_scenario_o_hospital_authorization(client: AsyncClient, db_session: AsyncSession):
    """O. Hospital staff from Facility A cannot access Facility B's consultation."""
    hosp_a = await _create_test_hospital(db_session, name="Hospital Alpha")
    hosp_b = await _create_test_hospital(db_session, name="Hospital Beta")

    _user_staff_a, _h_user_a, token_staff_a = await _create_hospital_staff_user(
        db_session, hosp_a.id, email="doctor_alpha@example.com"
    )
    _user_p, patient, _token_p = await _create_patient_user(db_session, email="patient_c@example.com")

    # Consultation registered at Hospital B
    consultation_b = await _create_consultation(db_session, patient.id, hosp_b.id)

    # Staff from Hospital A tries to access consultation belonging to Hospital B
    res = await client.get(
        f"/api/v1/consultations/{consultation_b.id}/alerts",
        headers={"Authorization": f"Bearer {token_staff_a}"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Consultation not found"


@pytest.mark.asyncio
async def test_patient_and_hospital_staff_access_own_alerts(client: AsyncClient, db_session: AsyncSession):
    """Verify both the owning patient and affiliated hospital staff can view consultation alerts."""
    hosp = await _create_test_hospital(db_session)
    _user_p, patient, token_p = await _create_patient_user(db_session)
    _user_s, _h_user, token_staff = await _create_hospital_staff_user(db_session, hosp.id)

    consultation = await _create_consultation(db_session, patient.id, hosp.id)

    # Insert an alert
    alert = Alert(
        id=uuid.uuid4(),
        consultation_id=consultation.id,
        patient_id=patient.id,
        alert_type="CHEST_PAIN_CRUSHING",
        severity="critical",
        message="Patient reported crushing chest pain.",
        source="AI_TRIAGE",
        status="active",
    )
    db_session.add(alert)
    await db_session.commit()

    # Patient reads own alerts
    res_p = await client.get(
        f"/api/v1/consultations/{consultation.id}/alerts",
        headers={"Authorization": f"Bearer {token_p}"},
    )
    assert res_p.status_code == 200
    data_p = res_p.json()
    assert data_p["total"] == 1
    assert data_p["items"][0]["alert_type"] == "CHEST_PAIN_CRUSHING"

    # Hospital staff reads alerts for consultation at their facility
    res_s = await client.get(
        f"/api/v1/consultations/{consultation.id}/alerts",
        headers={"Authorization": f"Bearer {token_staff}"},
    )
    assert res_s.status_code == 200
    assert res_s.json()["total"] == 1


# ---------------------------------------------------------------------------
# Part 15: Scenario T: AI Interview Flow Integration Test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scenario_t_interview_emergency_safety_notice_integration(
    client: AsyncClient, db_session: AsyncSession
):
    """T. Sending emergency symptom during interview triggers Alert creation and returns calm safety notice."""
    hosp = await _create_test_hospital(db_session)
    _user_p, patient, token_p = await _create_patient_user(db_session)
    consultation = await _create_consultation(db_session, patient.id, hosp.id)

    # 1. Start AI session
    sess_res = await client.post(
        f"/api/v1/consultations/{consultation.id}/ai-sessions",
        headers={"Authorization": f"Bearer {token_p}"},
        json={"language": "English"},
    )
    assert sess_res.status_code == 201, sess_res.text
    session_id = sess_res.json()["id"]

    # 2. Patient sends an explicit red-flag message
    with patch("app.ai.router.task_router.generate", return_value=AIResponse(
        text=json.dumps({
            "next_question": "Can you describe the pain more?",
            "current_section": "chief_complaint",
            "interview_complete": False,
        }),
        provider="gemini",
        model="gemini-2.0-flash",
    )):
        msg_res = await client.post(
            f"/api/v1/ai-sessions/{session_id}/messages",
            headers={"Authorization": f"Bearer {token_p}"},
            json={"message": "I am having severe crushing chest pain and cannot catch my breath!"},
        )

    assert msg_res.status_code == 201, msg_res.text
    resp_data = msg_res.json()

    # The AI response MUST prioritize the emergency safety notice!
    assert resp_data["ai_message"]["message"] == EMERGENCY_SAFETY_NOTICE
    assert "urgent medical attention" in resp_data["ai_message"]["message"]

    # Confirm Alert was created in database
    alerts_stmt = select(Alert).where(Alert.consultation_id == consultation.id)
    alerts = list((await db_session.execute(alerts_stmt)).scalars().all())
    assert len(alerts) >= 1
    assert any(a.severity == "critical" for a in alerts)
    assert any("CHEST_PAIN" in a.alert_type for a in alerts)
