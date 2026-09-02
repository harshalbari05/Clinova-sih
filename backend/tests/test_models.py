import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AIMessage,
    AISession,
    Alert,
    Allergy,
    AuditLog,
    ClinicalHistory,
    Consent,
    Consultation,
    ExtractedData,
    Hospital,
    HospitalUser,
    MedicalDocument,
    Medication,
    Patient,
    Summary,
    User,
)


@pytest.mark.asyncio
async def test_database_connection(db_session: AsyncSession):
    """Verify asynchronous database execution and session lifecycle."""
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_user_creation(db_session: AsyncSession):
    """Verify user model creation, fields, and queries."""
    user = User(
        email="patient@example.com",
        phone="+919876543210",
        password_hash="hashed_secret_pw",
        role="patient",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.email == "patient@example.com"
    assert user.phone == "+919876543210"
    assert user.role == "patient"
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None

    # Query back
    stmt = select(User).where(User.email == "patient@example.com")
    db_user = (await db_session.execute(stmt)).scalar_one_or_none()
    assert db_user is not None
    assert db_user.id == user.id


@pytest.mark.asyncio
async def test_patient_creation(db_session: AsyncSession):
    """Verify patient profile linked 1-to-1 to a user."""
    user = User(
        email="john.doe@example.com",
        role="patient",
    )
    db_session.add(user)
    await db_session.flush()

    patient = Patient(
        user_id=user.id,
        full_name="John Doe",
        date_of_birth=date(1990, 5, 15),
        gender="male",
        phone="+919876543211",
        abha_id="14-1234-5678-9012",
        address="123 Health Ave, Mumbai, MH",
        emergency_contact="Jane Doe (+919876543212)",
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)

    assert patient.id is not None
    assert patient.user_id == user.id
    assert patient.full_name == "John Doe"
    assert patient.abha_id == "14-1234-5678-9012"
    assert patient.date_of_birth == date(1990, 5, 15)


@pytest.mark.asyncio
async def test_hospital_creation(db_session: AsyncSession):
    """Verify hospital facility record creation."""
    hospital = Hospital(
        name="City Care Multispecialty Hospital",
        registration_number="HOSP-MH-2026-001",
        phone="+912223456789",
        email="info@citycare.org",
        address="45 Medical Enclave",
        city="Mumbai",
        state="Maharashtra",
        pincode="400001",
    )
    db_session.add(hospital)
    await db_session.commit()
    await db_session.refresh(hospital)

    assert hospital.id is not None
    assert hospital.registration_number == "HOSP-MH-2026-001"
    assert hospital.city == "Mumbai"


@pytest.mark.asyncio
async def test_hospital_user_association(db_session: AsyncSession):
    """Verify associating a staff or doctor user with a hospital facility."""
    staff_user = User(email="dr.sharma@citycare.org", role="doctor")
    hospital = Hospital(name="Apollo Metro Hospital", registration_number="HOSP-002")
    db_session.add_all([staff_user, hospital])
    await db_session.flush()

    hospital_user = HospitalUser(
        user_id=staff_user.id,
        hospital_id=hospital.id,
        role="doctor",
    )
    db_session.add(hospital_user)
    await db_session.commit()
    await db_session.refresh(hospital_user)

    assert hospital_user.id is not None
    assert hospital_user.user_id == staff_user.id
    assert hospital_user.hospital_id == hospital.id
    assert hospital_user.role == "doctor"


@pytest.mark.asyncio
async def test_consultation_creation(db_session: AsyncSession):
    """Verify consultation entity linking patient and hospital."""
    user = User(email="patient2@example.com", role="patient")
    hospital = Hospital(name="General Hospital", registration_number="HOSP-003")
    db_session.add_all([user, hospital])
    await db_session.flush()

    patient = Patient(user_id=user.id, full_name="Aarav Patel")
    db_session.add(patient)
    await db_session.flush()

    consultation = Consultation(
        patient_id=patient.id,
        hospital_id=hospital.id,
        status="initiated",
        chief_complaint="Severe headache and fever for 3 days",
        started_at=datetime.now(timezone.utc),
    )
    db_session.add(consultation)
    await db_session.commit()
    await db_session.refresh(consultation)

    assert consultation.id is not None
    assert consultation.patient_id == patient.id
    assert consultation.hospital_id == hospital.id
    assert consultation.status == "initiated"
    assert consultation.chief_complaint == "Severe headache and fever for 3 days"


@pytest.mark.asyncio
async def test_clinical_history_creation(db_session: AsyncSession):
    """Verify progressive clinical history taking linked 1-to-1 to a consultation."""
    user = User(email="patient3@example.com", role="patient")
    hospital = Hospital(name="District Hospital", registration_number="HOSP-004")
    db_session.add_all([user, hospital])
    await db_session.flush()

    patient = Patient(user_id=user.id, full_name="Priya Sharma")
    db_session.add(patient)
    await db_session.flush()

    consultation = Consultation(
        patient_id=patient.id,
        hospital_id=hospital.id,
        status="in_progress",
    )
    db_session.add(consultation)
    await db_session.flush()

    history = ClinicalHistory(
        consultation_id=consultation.id,
        chief_complaint="Chest tightness upon exertion",
        history_of_present_illness="Symptoms started 2 weeks ago, worsens after walking",
        past_medical_history="Hypertension diagnosed in 2020",
        past_surgical_history="Appendectomy (2015)",
        drug_history="Amlodipine 5mg OD",
        allergy_history="Penicillin causes rash",
        family_history="Father had CAD at age 55",
        personal_history="Non-smoker, vegetarian",
        review_of_systems="Cardiovascular: Positive for mild dyspnea on exertion",
    )
    db_session.add(history)
    await db_session.commit()
    await db_session.refresh(history)

    assert history.id is not None
    assert history.consultation_id == consultation.id
    assert history.allergy_history == "Penicillin causes rash"


@pytest.mark.asyncio
async def test_ai_session_and_messages(db_session: AsyncSession):
    """Verify AI history-taking session and conversation turns with cascading."""
    user = User(email="patient4@example.com", role="patient")
    hospital = Hospital(name="Global Clinic", registration_number="HOSP-005")
    db_session.add_all([user, hospital])
    await db_session.flush()

    patient = Patient(user_id=user.id, full_name="Rohan Gupta")
    db_session.add(patient)
    await db_session.flush()

    consultation = Consultation(patient_id=patient.id, hospital_id=hospital.id)
    db_session.add(consultation)
    await db_session.flush()

    ai_session = AISession(
        consultation_id=consultation.id,
        language="Hindi",
        status="in_progress",
        started_at=datetime.now(timezone.utc),
    )
    db_session.add(ai_session)
    await db_session.flush()

    msg1 = AIMessage(
        ai_session_id=ai_session.id,
        sender="ai",
        message="नमस्ते, आपको क्या तकलीफ हो रही है?",
        message_type="text",
    )
    msg2 = AIMessage(
        ai_session_id=ai_session.id,
        sender="patient",
        message="मुझे पिछले दो दिनों से बहुत तेज़ बुखार और सरदर्द है।",
        message_type="voice_transcript",
    )
    db_session.add_all([msg1, msg2])
    await db_session.commit()

    # Query back AI messages
    stmt = select(AIMessage).where(AIMessage.ai_session_id == ai_session.id)
    messages = (await db_session.execute(stmt)).scalars().all()
    assert len(messages) == 2
    assert messages[0].sender == "ai"
    assert messages[1].message_type == "voice_transcript"

    # Test cascade delete
    await db_session.delete(ai_session)
    await db_session.commit()

    remaining_msgs = (await db_session.execute(stmt)).scalars().all()
    assert len(remaining_msgs) == 0


@pytest.mark.asyncio
async def test_medical_document_and_extracted_data(db_session: AsyncSession):
    """Verify document storage metadata and JSONB extracted clinical payload."""
    user = User(email="patient5@example.com", role="patient")
    hospital = Hospital(name="Apex Diagnostic Center", registration_number="HOSP-006")
    db_session.add_all([user, hospital])
    await db_session.flush()

    patient = Patient(user_id=user.id, full_name="Sunita Rao")
    db_session.add(patient)
    await db_session.flush()

    doc = MedicalDocument(
        patient_id=patient.id,
        file_name="blood_test_cbc_2026.pdf",
        file_url="/storage/patients/p5/docs/blood_test_cbc_2026.pdf",
        document_type="lab_report",
        document_date=date(2026, 8, 20),
        mime_type="application/pdf",
        ocr_status="completed",
    )
    db_session.add(doc)
    await db_session.flush()

    extracted = ExtractedData(
        document_id=doc.id,
        raw_ocr_text="Complete Blood Count Hemoglobin: 11.2 g/dL Platelets: 210,000",
        extracted_json={
            "lab_name": "Apex Diagnostics",
            "test_type": "CBC",
            "values": {
                "hemoglobin": {"val": 11.2, "unit": "g/dL", "status": "low"},
                "platelets": {"val": 210000, "unit": "/mcL", "status": "normal"},
            },
        },
        extraction_status="completed",
        extracted_at=datetime.now(timezone.utc),
    )
    db_session.add(extracted)
    await db_session.commit()
    await db_session.refresh(extracted)

    assert extracted.id is not None
    assert extracted.document_id == doc.id
    assert extracted.extracted_json["values"]["hemoglobin"]["val"] == 11.2


@pytest.mark.asyncio
async def test_medications_and_allergies(db_session: AsyncSession):
    """Verify medication and allergy tracking."""
    user = User(email="patient6@example.com", role="patient")
    db_session.add(user)
    await db_session.flush()

    patient = Patient(user_id=user.id, full_name="Vikram Singh")
    db_session.add(patient)
    await db_session.flush()

    med = Medication(
        patient_id=patient.id,
        name="Metformin",
        dosage="500mg",
        frequency="Twice daily",
        route="Oral",
        duration="Ongoing",
        source="doctor",
    )
    allergy = Allergy(
        patient_id=patient.id,
        allergen="Sulfa drugs",
        reaction="Severe urticaria and facial edema",
        severity="severe",
        source="patient",
    )
    db_session.add_all([med, allergy])
    await db_session.commit()

    # Query
    med_stmt = select(Medication).where(Medication.patient_id == patient.id)
    allergy_stmt = select(Allergy).where(Allergy.patient_id == patient.id)

    db_med = (await db_session.execute(med_stmt)).scalar_one()
    db_allergy = (await db_session.execute(allergy_stmt)).scalar_one()

    assert db_med.name == "Metformin"
    assert db_allergy.severity == "severe"


@pytest.mark.asyncio
async def test_ai_summary_creation(db_session: AsyncSession):
    """Verify AI structured clinical summary creation and versioning."""
    user = User(email="patient7@example.com", role="patient")
    hospital = Hospital(name="Lifeline Medical", registration_number="HOSP-007")
    db_session.add_all([user, hospital])
    await db_session.flush()

    patient = Patient(user_id=user.id, full_name="Kavita Nair")
    db_session.add(patient)
    await db_session.flush()

    consultation = Consultation(patient_id=patient.id, hospital_id=hospital.id)
    db_session.add(consultation)
    await db_session.flush()

    summary = Summary(
        consultation_id=consultation.id,
        summary_text="Patient presents with acute pharyngitis and low grade pyrexia.",
        structured_summary={
            "chief_complaint": "Sore throat",
            "duration": "2 days",
            "red_flags": [],
            "suggested_differential": ["Viral Pharyngitis", "Strep Throat"],
        },
        generated_by="Clinova AI v1.0",
        version=1,
        status="draft",
    )
    db_session.add(summary)
    await db_session.commit()
    await db_session.refresh(summary)

    assert summary.id is not None
    assert summary.version == 1
    assert summary.status == "draft"
    assert summary.structured_summary["chief_complaint"] == "Sore throat"


@pytest.mark.asyncio
async def test_alert_creation(db_session: AsyncSession):
    """Verify clinical red flag decision-support alerts."""
    user = User(email="patient8@example.com", role="patient")
    hospital = Hospital(name="Emergency Care Hospital", registration_number="HOSP-008")
    db_session.add_all([user, hospital])
    await db_session.flush()

    patient = Patient(user_id=user.id, full_name="Meera Iyer")
    db_session.add(patient)
    await db_session.flush()

    consultation = Consultation(patient_id=patient.id, hospital_id=hospital.id)
    db_session.add(consultation)
    await db_session.flush()

    alert = Alert(
        consultation_id=consultation.id,
        patient_id=patient.id,
        alert_type="cardiovascular_red_flag",
        severity="critical",
        message="Patient reports sudden crushing substernal chest pain radiating to left jaw with diaphoresis.",
        source="AI History Engine",
        status="active",
    )
    db_session.add(alert)
    await db_session.commit()
    await db_session.refresh(alert)

    assert alert.id is not None
    assert alert.severity == "critical"
    assert alert.status == "active"


@pytest.mark.asyncio
async def test_consent_creation_and_revocation(db_session: AsyncSession):
    """Verify consent tracking and timestamped revocation."""
    user = User(email="patient9@example.com", role="patient")
    db_session.add(user)
    await db_session.flush()

    patient = Patient(user_id=user.id, full_name="Ananya Joshi")
    db_session.add(patient)
    await db_session.flush()

    consent = Consent(
        patient_id=patient.id,
        consent_type="AI_processing",
        granted=True,
        version="v1.0",
    )
    db_session.add(consent)
    await db_session.commit()
    await db_session.refresh(consent)

    assert consent.id is not None
    assert consent.granted is True
    assert consent.revoked_at is None

    # Revoke consent
    consent.granted = False
    consent.revoked_at = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(consent)

    assert consent.granted is False
    assert consent.revoked_at is not None


@pytest.mark.asyncio
async def test_audit_log_creation(db_session: AsyncSession):
    """Verify audit log records with structured JSON metadata."""
    user = User(email="admin@citycare.org", role="hospital_admin")
    db_session.add(user)
    await db_session.flush()

    log_entry = AuditLog(
        user_id=user.id,
        action="consultation_viewed",
        entity_type="consultation",
        entity_id=str(uuid.uuid4()),
        metadata_json={
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "action_context": "Emergency triage review",
        },
    )
    db_session.add(log_entry)
    await db_session.commit()
    await db_session.refresh(log_entry)

    assert log_entry.id is not None
    assert log_entry.action == "consultation_viewed"
    assert log_entry.metadata_json["action_context"] == "Emergency triage review"
