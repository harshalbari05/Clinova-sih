"""Demo Seed Script for Clinova SIH End-to-End Demonstration (Step 10D).

Provides safe, reproducible, and idempotent seeding and cleanup of synthetic
demonstration records for the unbroken patient-to-physician workflow.

Usage:
    # Seed demo data (idempotent; creates records if missing)
    python scripts/demo_seed.py

    # Cleanly remove all demo data
    python scripts/demo_seed.py --reset

    # Reset and immediately re-seed fresh demo data
    python scripts/demo_seed.py --reset --seed
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.session import async_session_factory, engine
from app.models.ai_message import AIMessage
from app.models.ai_session import AISession
from app.models.alert import Alert
from app.models.consent import Consent
from app.models.consultation import Consultation
from app.models.hospital import Hospital
from app.models.hospital_user import HospitalUser
from app.models.patient import Patient
from app.models.summary import Summary
from app.models.timeline_event import TimelineEvent
from app.models.user import User
from app.services.auth_service import hash_password

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("clinova.demo_seed")

# Deterministic Demo Identifiers
DEMO_HOSPITAL_REG = "REG-DEMO-001"
DEMO_HOSPITAL_EMAIL = "opd@demohospital.org"
DEMO_DOCTOR_EMAIL = "doctor@demohospital.org"
DEMO_PATIENT_A_EMAIL = "rohan.patil@example.com"
DEMO_PATIENT_A_ABHA = "91-4521-8890-1234"
DEMO_PATIENT_B_EMAIL = "ananya.d@example.com"
DEMO_PATIENT_B_ABHA = "91-6789-1122-3344"

DEMO_EMAILS = [DEMO_DOCTOR_EMAIL, DEMO_PATIENT_A_EMAIL, DEMO_PATIENT_B_EMAIL]


async def reset_demo_data(session: AsyncSession) -> None:
    """Cleanly and safely delete all synthetic demo accounts and associated records."""
    logger.info("Purging synthetic demo data...")

    # 1. Find users by demo email
    stmt = select(User).where(User.email.in_(DEMO_EMAILS))
    users = list((await session.execute(stmt)).scalars().all())
    user_ids = [u.id for u in users]

    if user_ids:
        # Cascade or explicit deletion of users
        await session.execute(delete(User).where(User.id.in_(user_ids)))
        logger.info("Deleted %d demo user accounts (and cascaded patient profiles/consultations).", len(user_ids))

    # 2. Find and delete demo hospital
    hosp_stmt = select(Hospital).where(
        (Hospital.registration_number == DEMO_HOSPITAL_REG) | (Hospital.email == DEMO_HOSPITAL_EMAIL)
    )
    hospitals = list((await session.execute(hosp_stmt)).scalars().all())
    hosp_ids = [h.id for h in hospitals]

    if hosp_ids:
        await session.execute(delete(Hospital).where(Hospital.id.in_(hosp_ids)))
        logger.info("Deleted %d demo hospital record(s).", len(hosp_ids))

    await session.commit()
    logger.info("Demo data reset completed successfully.")


async def seed_demo_data(session: AsyncSession) -> dict[str, Any]:
    """Seed comprehensive end-to-end demo records for SIH presentation."""
    logger.info("Beginning Clinova demo seeding...")

    now = datetime.now(timezone.utc)
    today = date.today()

    # -------------------------------------------------------------
    # 1. Hospital Facility & Attending Physician Account
    # -------------------------------------------------------------
    hosp_stmt = select(Hospital).where(Hospital.registration_number == DEMO_HOSPITAL_REG)
    hospital = (await session.execute(hosp_stmt)).scalar_one_or_none()

    if not hospital:
        hospital = Hospital(
            name="Demo General Hospital",
            registration_number=DEMO_HOSPITAL_REG,
            phone="+91 22 2555 0100",
            email=DEMO_HOSPITAL_EMAIL,
            address="123 Healthcare Boulevard, Nariman Point",
            city="Mumbai",
            state="Maharashtra",
            pincode="400021",
        )
        session.add(hospital)
        await session.flush()
        logger.info("Created Demo Hospital: %s (ID: %s)", hospital.name, hospital.id)

    # Doctor User
    doc_stmt = select(User).where(User.email == DEMO_DOCTOR_EMAIL)
    doc_user = (await session.execute(doc_stmt)).scalar_one_or_none()

    if not doc_user:
        doc_user = User(
            email=DEMO_DOCTOR_EMAIL,
            phone="+91 98200 11223",
            password_hash=hash_password("HospitalPass123!"),
            role="hospital_admin",
            is_active=True,
        )
        session.add(doc_user)
        await session.flush()

        hosp_user = HospitalUser(
            user_id=doc_user.id,
            hospital_id=hospital.id,
            role="hospital_admin",
        )
        session.add(hosp_user)
        await session.flush()
        logger.info("Created Attending Physician: %s", doc_user.email)

    # -------------------------------------------------------------
    # 2. Patient A: Rohan Patil (Standard Complete Flow)
    # -------------------------------------------------------------
    pat_a_stmt = select(User).where(User.email == DEMO_PATIENT_A_EMAIL)
    user_a = (await session.execute(pat_a_stmt)).scalar_one_or_none()

    if not user_a:
        user_a = User(
            email=DEMO_PATIENT_A_EMAIL,
            phone="9876543210",
            password_hash=hash_password("PatientPass123!"),
            role="patient",
            is_active=True,
        )
        session.add(user_a)
        await session.flush()

        patient_a = Patient(
            user_id=user_a.id,
            full_name="Rohan Patil",
            date_of_birth=date(1990, 5, 14),
            gender="Male",
            phone="9876543210",
            abha_id=DEMO_PATIENT_A_ABHA,
            address="Flat 402, Green Meadows, Andheri East, Mumbai",
            emergency_contact="+919876543211",
        )
        session.add(patient_a)
        await session.flush()
    else:
        patient_a = (await session.execute(select(Patient).where(Patient.user_id == user_a.id))).scalar_one()

    # Consultation A
    con_a_stmt = select(Consultation).where(
        Consultation.patient_id == patient_a.id,
        Consultation.hospital_id == hospital.id,
    )
    con_a = (await session.execute(con_a_stmt)).scalars().first()

    if not con_a:
        con_a = Consultation(
            patient_id=patient_a.id,
            hospital_id=hospital.id,
            status="in_progress",
            chief_complaint="Persistent dry cough and mild evening fever for 5 days",
            started_at=now - timedelta(minutes=45),
        )
        session.add(con_a)
        await session.flush()

        # Consent Record
        consent_a = Consent(
            patient_id=patient_a.id,
            consultation_id=con_a.id,
            consent_type="clinical_intake",
            granted=True,
            version="v1.0",
            timestamp=now - timedelta(minutes=40),
        )
        session.add(consent_a)

        # AI Session & Conversational Turns
        ai_session_a = AISession(
            consultation_id=con_a.id,
            language="English",
            status="completed",
            started_at=now - timedelta(minutes=35),
            completed_at=now - timedelta(minutes=20),
        )
        session.add(ai_session_a)
        await session.flush()

        messages_a = [
            (
                "patient",
                "Hello, I have been having a persistent dry cough and slight fever every evening for 5 days.",
            ),
            (
                "ai",
                "I understand you're experiencing a dry cough and mild fever. Are you having any chest pain, shortness of breath, or coughing up blood?",
            ),
            (
                "patient",
                "No chest pain and no blood. Breathing is slightly uncomfortable only when coughing, but no severe shortness of breath.",
            ),
            (
                "ai",
                "Thank you for clarifying. Are you currently taking any regular medications or do you have any allergies?",
            ),
            (
                "patient",
                "I take Cetirizine 10mg when seasonal allergies act up. I have a known dust and pollen allergy. No other regular medications.",
            ),
            (
                "ai",
                "Understood. I have recorded your symptoms, allergy history, and medications. Your intake summary will now be synthesized for the attending physician.",
            ),
        ]
        for idx, (snd, txt) in enumerate(messages_a):
            msg = AIMessage(
                ai_session_id=ai_session_a.id,
                sender=snd,
                message=txt,
                message_type="text",
                created_at=now - timedelta(minutes=34 - idx * 2),
            )
            session.add(msg)

        # Timeline Events for Patient A
        ev1 = TimelineEvent(
            patient_id=patient_a.id,
            consultation_id=con_a.id,
            event_type="SYMPTOM",
            title="Dry Cough & Evening Fever",
            description="5-day history of non-productive dry cough and low-grade evening fever",
            event_date=today - timedelta(days=5),
            date_precision="EXACT",
            source_type="AI_INTERVIEW",
            source_id=str(ai_session_a.id),
            evidence="Patient reports persistent dry cough and slight fever every evening for 5 days.",
            verification_status="SOURCE_CONFIRMED",
            metadata_={"severity": "mild-to-moderate", "duration_days": 5},
        )
        ev2 = TimelineEvent(
            patient_id=patient_a.id,
            consultation_id=con_a.id,
            event_type="MEDICATION",
            title="Cetirizine 10mg PRN",
            description="Antihistamine taken as needed for seasonal allergic rhinitis",
            event_date=today - timedelta(days=180),
            date_precision="MONTH",
            source_type="PATIENT_HISTORY",
            evidence="Patient reported taking Cetirizine 10mg for seasonal allergies.",
            verification_status="SOURCE_CONFIRMED",
            metadata_={"dosage": "10mg", "route": "oral", "frequency": "PRN"},
        )
        ev3 = TimelineEvent(
            patient_id=patient_a.id,
            consultation_id=con_a.id,
            event_type="ALLERGY",
            title="Dust & Pollen Hypersensitivity",
            description="Seasonal allergic rhinitis with nasal congestion and ocular itching",
            event_date=date(2022, 3, 1),
            date_precision="YEAR",
            source_type="PATIENT_HISTORY",
            evidence="Known history of seasonal dust and pollen allergy since 2022.",
            verification_status="SOURCE_CONFIRMED",
            metadata_={"allergen": "Dust / Pollen", "reaction": "Rhinitis"},
        )
        session.add_all([ev1, ev2, ev3])

        # Clinical Summary for Patient A (Draft status, ready for physician workspace review & editing)
        summary_a = Summary(
            consultation_id=con_a.id,
            summary_text=(
                "34-year-old male presents with a 5-day history of persistent non-productive cough and "
                "intermittent low-grade evening fever. Patient explicitly denies hemoptysis, chest pain, "
                "or resting dyspnea. Known medical history of seasonal dust and pollen hypersensitivity, "
                "managed with Cetirizine 10mg PRN. Chest auscultation and vitals assessment recommended."
            ),
            ai_draft_text=(
                "34-year-old male presents with a 5-day history of persistent non-productive cough and "
                "intermittent low-grade evening fever. Patient explicitly denies hemoptysis, chest pain, "
                "or resting dyspnea. Known medical history of seasonal dust and pollen hypersensitivity, "
                "managed with Cetirizine 10mg PRN. Chest auscultation and vitals assessment recommended."
            ),
            structured_summary={
                "chief_complaint": "Persistent dry cough and mild evening fever for 5 days",
                "patient_reported_symptoms": [
                    {"symptom": "Dry non-productive cough", "duration": "5 days"},
                    {"symptom": "Low-grade evening fever", "duration": "5 days"},
                ],
                "past_medical_history": ["Seasonal allergic rhinitis (documented 2022)"],
                "current_medications": [{"name": "Cetirizine", "dosage": "10mg", "frequency": "PRN"}],
                "allergies": [{"allergen": "Dust & Pollen", "severity": "Mild"}],
                "red_flags": [],
                "recommendations": [
                    "Perform bilateral chest auscultation",
                    "Record oxygen saturation and baseline temperature",
                    "Consider routine CBC if febrile episodes continue past 7 days",
                ],
            },
            generated_by="AI",
            version=1,
            status="draft",
        )
        session.add(summary_a)
        logger.info("Seeded Consultation A: Rohan Patil (Encounter: #%s)", str(con_a.id)[:8].upper())

    # -------------------------------------------------------------
    # 3. Patient B: Ananya Deshmukh (Emergency Red-Flag Scenario)
    # -------------------------------------------------------------
    pat_b_stmt = select(User).where(User.email == DEMO_PATIENT_B_EMAIL)
    user_b = (await session.execute(pat_b_stmt)).scalar_one_or_none()

    if not user_b:
        user_b = User(
            email=DEMO_PATIENT_B_EMAIL,
            phone="9812345678",
            password_hash=hash_password("PatientPass123!"),
            role="patient",
            is_active=True,
        )
        session.add(user_b)
        await session.flush()

        patient_b = Patient(
            user_id=user_b.id,
            full_name="Ananya Deshmukh",
            date_of_birth=date(1968, 11, 20),
            gender="Female",
            phone="9812345678",
            abha_id=DEMO_PATIENT_B_ABHA,
            address="B-12 Hilltop Residency, Bandra West, Mumbai",
            emergency_contact="+919812345679",
        )
        session.add(patient_b)
        await session.flush()
    else:
        patient_b = (await session.execute(select(Patient).where(Patient.user_id == user_b.id))).scalar_one()

    # Consultation B
    con_b_stmt = select(Consultation).where(
        Consultation.patient_id == patient_b.id,
        Consultation.hospital_id == hospital.id,
    )
    con_b = (await session.execute(con_b_stmt)).scalars().first()

    if not con_b:
        con_b = Consultation(
            patient_id=patient_b.id,
            hospital_id=hospital.id,
            status="in_progress",
            chief_complaint="Acute severe retrosternal chest pain radiating to left shoulder and arm with diaphoresis",
            started_at=now - timedelta(minutes=25),
        )
        session.add(con_b)
        await session.flush()

        consent_b = Consent(
            patient_id=patient_b.id,
            consultation_id=con_b.id,
            consent_type="clinical_intake",
            granted=True,
            version="v1.0",
            timestamp=now - timedelta(minutes=24),
        )
        session.add(consent_b)

        # AI Session for Patient B
        ai_session_b = AISession(
            consultation_id=con_b.id,
            language="English",
            status="completed",
            started_at=now - timedelta(minutes=20),
            completed_at=now - timedelta(minutes=10),
        )
        session.add(ai_session_b)
        await session.flush()

        messages_b = [
            (
                "patient",
                "I suddenly started having intense chest pressure and tightness about an hour ago. It feels like a heavy weight on my chest.",
            ),
            (
                "ai",
                "This requires immediate attention. Is the chest pain spreading anywhere, such as your left arm, neck, or jaw? Are you feeling breathless or sweating?",
            ),
            (
                "patient",
                "Yes, the tightness is radiating down my left arm and up to my jaw. I am breaking out in a cold sweat and feel quite dizzy.",
            ),
            (
                "ai",
                "ATTENTION: Your symptoms indicate a high-priority emergency situation. Please notify OPD nursing staff immediately while I alert the attending physician.",
            ),
        ]
        for idx, (snd, txt) in enumerate(messages_b):
            msg = AIMessage(
                ai_session_id=ai_session_b.id,
                sender=snd,
                message=txt,
                message_type="text",
                created_at=now - timedelta(minutes=19 - idx * 2),
            )
            session.add(msg)

        # Active Red-Flag Alert
        alert_b = Alert(
            consultation_id=con_b.id,
            patient_id=patient_b.id,
            alert_type="CARDIAC_RED_FLAG",
            severity="critical",
            message=(
                "CRITICAL RED-FLAG ALERT: Acute retrosternal crushing chest pain radiating to left arm "
                "and jaw with diaphoresis and dizziness. High risk of Acute Coronary Syndrome (ACS). "
                "Immediate 12-lead ECG, telemetry, and STAT physician review mandatory."
            ),
            source="AI_TRIAGE",
            status="active",
        )
        session.add(alert_b)

        # Timeline Event
        ev_b1 = TimelineEvent(
            patient_id=patient_b.id,
            consultation_id=con_b.id,
            event_type="SYMPTOM",
            title="Acute Retrosternal Chest Pain (Radiation to Arm)",
            description="Acute severe crushing chest pressure radiating to left arm and jaw with diaphoresis",
            event_date=today,
            date_precision="EXACT",
            source_type="AI_INTERVIEW",
            source_id=str(ai_session_b.id),
            evidence="Patient reports sudden intense chest pressure radiating to left arm with cold sweat.",
            verification_status="SOURCE_CONFIRMED",
            metadata_={"urgency": "EMERGENCY", "red_flag": True},
        )
        ev_b2 = TimelineEvent(
            patient_id=patient_b.id,
            consultation_id=con_b.id,
            event_type="DIAGNOSIS_DOCUMENTED",
            title="Essential Hypertension",
            description="Managed hypertension on regular calcium-channel blocker",
            event_date=date(2021, 6, 15),
            date_precision="MONTH",
            source_type="PATIENT_HISTORY",
            evidence="Known hypertensive on Amlodipine 5mg OD since 2021.",
            verification_status="SOURCE_CONFIRMED",
            metadata_={"condition": "Hypertension", "icd10": "I10"},
        )
        session.add_all([ev_b1, ev_b2])

        # Summary for Patient B
        summary_b = Summary(
            consultation_id=con_b.id,
            summary_text=(
                "58-year-old female presents with acute onset (1 hour) of severe retrosternal squeezing chest "
                "pressure radiating to left arm and jaw, accompanied by cold diaphoresis and dizziness. "
                "Known history of hypertension on Amlodipine 5mg. Critical Red-Flag triggered: Acute Coronary "
                "Syndrome cannot be ruled out. Immediate 12-lead ECG, telemetry, IV access, and physician evaluation indicated."
            ),
            ai_draft_text=(
                "58-year-old female presents with acute onset (1 hour) of severe retrosternal squeezing chest "
                "pressure radiating to left arm and jaw, accompanied by cold diaphoresis and dizziness. "
                "Known history of hypertension on Amlodipine 5mg. Critical Red-Flag triggered: Acute Coronary "
                "Syndrome cannot be ruled out. Immediate 12-lead ECG, telemetry, IV access, and physician evaluation indicated."
            ),
            structured_summary={
                "chief_complaint": "Acute severe retrosternal chest pain radiating to left arm with diaphoresis",
                "patient_reported_symptoms": [
                    {"symptom": "Squeezing retrosternal chest pain", "duration": "1 hour"},
                    {"symptom": "Radiation to left arm and jaw", "duration": "1 hour"},
                    {"symptom": "Cold diaphoresis", "duration": "1 hour"},
                    {"symptom": "Dizziness", "duration": "1 hour"},
                ],
                "past_medical_history": ["Essential hypertension (2021)"],
                "current_medications": [{"name": "Amlodipine", "dosage": "5mg", "frequency": "OD"}],
                "allergies": [],
                "red_flags": [
                    "Acute squeezing retrosternal chest pain",
                    "Radiation to left upper extremity and jaw",
                    "Cold diaphoresis and lightheadedness",
                ],
                "recommendations": [
                    "STAT 12-lead ECG within 10 minutes",
                    "Continuous telemetry and continuous SpO2 monitoring",
                    "Obtain venous access and send STAT troponin and cardiac enzymes",
                    "Urgent bedside attending physician assessment",
                ],
            },
            generated_by="AI",
            version=1,
            status="draft",
        )
        session.add(summary_b)
        logger.info("Seeded Consultation B (Red Flag): Ananya Deshmukh (Encounter: #%s)", str(con_b.id)[:8].upper())

    await session.commit()
    logger.info("All demo records committed successfully!")

    return {
        "hospital_id": str(hospital.id),
        "hospital_name": hospital.name,
        "doctor_email": DEMO_DOCTOR_EMAIL,
        "doctor_password": "HospitalPass123!",
        "patient_a_email": DEMO_PATIENT_A_EMAIL,
        "patient_a_password": "PatientPass123!",
        "patient_a_ref": str(con_a.id)[:8].upper(),
        "patient_b_email": DEMO_PATIENT_B_EMAIL,
        "patient_b_password": "PatientPass123!",
        "patient_b_ref": str(con_b.id)[:8].upper(),
    }


def print_summary(data: dict[str, Any]) -> None:
    """Print high-visibility credentials and demonstration guidance."""
    print("\n" + "=" * 70)
    print("CLINOVA SIH DEMONSTRATION SEED COMPLETE")
    print("=" * 70)
    print(f"Hospital Facility : {data['hospital_name']} ({data['hospital_id'][:8]}...)")
    print("-" * 70)
    print("ATTENDING PHYSICIAN / HOSPITAL PORTAL (http://localhost:5174):")
    print(f"  Username/Email : {data['doctor_email']}")
    print(f"  Password       : {data['doctor_password']}")
    print("-" * 70)
    print("PATIENT A (STANDARD CASE - ROHAN PATIL):")
    print(f"  Portal URL     : http://localhost:5173")
    print(f"  Login Email    : {data['patient_a_email']}")
    print(f"  Password       : {data['patient_a_password']}")
    print(f"  Case Reference : #{data['patient_a_ref']}")
    print(f"  Symptoms       : Dry cough and mild evening fever (Routine / Green)")
    print("-" * 70)
    print("PATIENT B (EMERGENCY RED-FLAG CASE - ANANYA DESHMUKH):")
    print(f"  Portal URL     : http://localhost:5173")
    print(f"  Login Email    : {data['patient_b_email']}")
    print(f"  Password       : {data['patient_b_password']}")
    print(f"  Case Reference : #{data['patient_b_ref']}")
    print(f"  Symptoms       : Acute crushing chest pain radiating to left arm (EMERGENCY / RED)")
    print("=" * 70 + "\n")


async def ensure_schema() -> None:
    """Ensure all required tables and columns exist in PostgreSQL."""
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE hospital_users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;"))
        await conn.execute(text("ALTER TABLE patients ALTER COLUMN emergency_contact TYPE VARCHAR(255);"))
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Clinova SIH Demo Data Seeding & Cleanup Tool")
    parser.add_argument("--reset", action="store_true", help="Delete existing synthetic demo records")
    parser.add_argument("--seed", action="store_true", help="Explicitly re-seed demo records (default behavior)")
    args = parser.parse_args()

    await ensure_schema()

    async with async_session_factory() as session:
        if args.reset:
            await reset_demo_data(session)
            if not args.seed:
                return

        # Seed data (default when --reset is not passed, or when both --reset and --seed are passed)
        data = await seed_demo_data(session)
        print_summary(data)


if __name__ == "__main__":
    asyncio.run(main())
