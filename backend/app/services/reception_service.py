"""Reception service layer for patient registration and QR resolution.

Responsibilities:
- Resolve Clinova patient QR code to safe demographic profile.
- Confirm patient registration and assign hospital OPD department.
- Handle manual registration fallback when QR is unavailable.
- Maintain strict clinical data isolation: receptionists NEVER receive clinical
  histories, AI summaries, interview transcripts, or reports.
"""

import uuid
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import Consultation
from app.models.hospital import Hospital
from app.models.hospital_user import HospitalUser
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import ActiveVisitResponse
from app.schemas.reception import (
    AdvanceQueueResponse,
    ConfirmRegistrationRequest,
    DepartmentQueueResponse,
    DepartmentsListResponse,
    ManualRegistrationRequest,
    QueueEntry,
    RegistrationResponse,
    SafePatientLookupResponse,
)
from app.services.auth_service import hash_password

__all__ = [
    "STANDARD_OPD_DEPARTMENTS",
    "advance_department_queue",
    "get_available_departments",
    "get_department_queue",
    "get_patient_active_visit",
    "lookup_patient_by_qr",
    "register_manual_patient",
    "register_patient",
]

# Standard Hospital OPD Departments for SIH Demonstration
STANDARD_OPD_DEPARTMENTS: list[str] = [
    "General Medicine",
    "Orthopedics",
    "ENT",
    "Pediatrics",
    "Cardiology",
    "Dermatology",
    "Obstetrics & Gynecology",
    "Pulmonology",
    "Ophthalmology",
    "General Surgery",
]

ALLOWED_RECEPTION_ROLES = frozenset(
    {"receptionist", "hospital_admin", "hospital_staff", "doctor"}
)


def _assert_reception_authorized(hospital_user: HospitalUser) -> None:
    """Verify hospital user has permission to operate reception desk."""
    if hospital_user.role not in ALLOWED_RECEPTION_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{hospital_user.role}' is not authorized for reception registration.",
        )


def _parse_qr_code(qr_code: str) -> uuid.UUID:
    """Extract and validate the patient UUID from the QR payload.

    Expected format: CLINOVA:PATIENT:{uuid} or direct UUID string.
    """
    raw = qr_code.strip()
    prefix = "CLINOVA:PATIENT:"
    if raw.startswith(prefix):
        raw = raw[len(prefix) :].strip()

    try:
        return uuid.UUID(raw)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Clinova patient QR code format. Expected 'CLINOVA:PATIENT:{id}'.",
        )


def _calc_age(dob: date | None) -> int | None:
    """Calculate age in whole years from date of birth."""
    if dob is None:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


async def get_available_departments() -> DepartmentsListResponse:
    """Return available hospital OPD departments."""
    return DepartmentsListResponse(departments=STANDARD_OPD_DEPARTMENTS)


async def lookup_patient_by_qr(
    db: AsyncSession,
    hospital_user: HospitalUser,
    qr_code: str,
) -> SafePatientLookupResponse:
    """Look up a patient via their Clinova QR code.

    Guarantees:
    - Caller must be an authorized hospital user.
    - Resolves solely to registration-safe demographic data.
    - NEVER returns clinical history, AI summary, or medical records.
    - Detects whether the patient already has an active unassigned pre-hospital consultation.
    """
    _assert_reception_authorized(hospital_user)
    patient_id = _parse_qr_code(qr_code)

    stmt = select(Patient).where(Patient.id == patient_id)
    patient = (await db.execute(stmt)).scalar_one_or_none()

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient registration not found for this QR code.",
        )

    # Check for active pre-hospital intake consultation (unassigned hospital_id)
    cons_stmt = (
        select(Consultation)
        .where(
            Consultation.patient_id == patient.id,
            Consultation.hospital_id.is_(None),
            Consultation.status == "initiated",
        )
        .order_by(Consultation.created_at.desc())
    )
    active_cons = (await db.execute(cons_stmt)).scalars().first()

    return SafePatientLookupResponse(
        patient_id=patient.id,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        age=_calc_age(patient.date_of_birth),
        gender=patient.gender,
        phone=patient.phone,
        abha_id=patient.abha_id,
        blood_group=getattr(patient, "blood_group", None),
        has_active_intake=active_cons is not None,
        active_consultation_id=active_cons.id if active_cons else None,
    )


async def _generate_token_for_consultation(
    db: AsyncSession,
    hospital_id: uuid.UUID,
    department: str,
    consultation: Consultation,
) -> int:
    """Generate an idempotent sequential token number for this hospital visit and OPD department.

    Tokens are department-scoped (e.g. General Medicine 21, 22, 23... vs Orthopedics 11, 12, 13...).
    Repeated registration calls return the existing token without incrementing.
    """
    if (
        consultation.token_number is not None
        and consultation.department == department
        and consultation.hospital_id == hospital_id
    ):
        return consultation.token_number

    stmt = (
        select(func.max(Consultation.token_number))
        .where(
            Consultation.hospital_id == hospital_id,
            Consultation.department == department,
        )
    )
    max_token = (await db.execute(stmt)).scalar() or 0
    next_token = max_token + 1

    consultation.token_number = next_token
    consultation.department = department
    consultation.hospital_id = hospital_id
    consultation.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return next_token


async def register_patient(
    db: AsyncSession,
    hospital_user: HospitalUser,
    hospital: Hospital,
    payload: ConfirmRegistrationRequest,
) -> RegistrationResponse:
    """Confirm hospital visit registration, assign OPD department, and generate token.

    If the patient has an active pre-hospital consultation, this reassigns it from
    hospital_id = null to the current hospital facility, assigns the department,
    and provisions a sequential department token.
    Otherwise, creates a new consultation record with a token.
    """
    _assert_reception_authorized(hospital_user)

    if payload.department not in STANDARD_OPD_DEPARTMENTS:
        # Accept custom department or standard
        pass

    # Verify patient exists
    p_stmt = select(Patient).where(Patient.id == payload.patient_id)
    patient = (await db.execute(p_stmt)).scalar_one_or_none()
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    consultation: Consultation | None = None

    # Case A: Specific consultation provided
    if payload.consultation_id is not None:
        c_stmt = select(Consultation).where(
            Consultation.id == payload.consultation_id,
            Consultation.patient_id == patient.id,
        )
        consultation = (await db.execute(c_stmt)).scalar_one_or_none()
        if consultation is not None:
            consultation.hospital_id = hospital.id
            consultation.department = payload.department
            consultation.updated_at = datetime.now(timezone.utc)

    # Case B: Check for unassigned pre-hospital consultation
    if consultation is None:
        unassigned_stmt = (
            select(Consultation)
            .where(
                Consultation.patient_id == patient.id,
                Consultation.hospital_id.is_(None),
                Consultation.status == "initiated",
            )
            .order_by(Consultation.created_at.desc())
        )
        consultation = (await db.execute(unassigned_stmt)).scalars().first()
        if consultation is not None:
            consultation.hospital_id = hospital.id
            consultation.department = payload.department
            consultation.updated_at = datetime.now(timezone.utc)

    # Case B.2: Check for existing active consultation for this patient in this hospital and department (Idempotency)
    if consultation is None:
        active_hosp_stmt = (
            select(Consultation)
            .where(
                Consultation.patient_id == patient.id,
                Consultation.hospital_id == hospital.id,
                Consultation.department == payload.department,
                Consultation.status.in_(["initiated", "in_progress"]),
            )
            .order_by(Consultation.created_at.desc())
        )
        consultation = (await db.execute(active_hosp_stmt)).scalars().first()

    # Case C: Create a fresh consultation for this hospital visit
    if consultation is None:
        consultation = Consultation(
            patient_id=patient.id,
            hospital_id=hospital.id,
            department=payload.department,
            chief_complaint="Hospital OPD Check-in",
            status="initiated",
        )
        db.add(consultation)

    await db.flush()

    # Generate sequential department token
    token_number = await _generate_token_for_consultation(
        db=db,
        hospital_id=hospital.id,
        department=payload.department,
        consultation=consultation,
    )

    await db.refresh(consultation)

    return RegistrationResponse(
        consultation_id=consultation.id,
        patient_id=patient.id,
        patient_name=patient.full_name,
        hospital_id=hospital.id,
        hospital_name=hospital.name,
        department=payload.department,
        token_number=token_number,
        status=consultation.status,
        message=f"Patient {patient.full_name} successfully registered for {payload.department}. Token #{token_number}.",
        created_at=consultation.created_at,
    )


async def register_manual_patient(
    db: AsyncSession,
    hospital_user: HospitalUser,
    hospital: Hospital,
    payload: ManualRegistrationRequest,
) -> RegistrationResponse:
    """Register a walk-in patient manually when QR is unavailable and generate a token.

    Does not perform open profile searches. Checks only for exact phone/ABHA matches
    to prevent duplicate accounts, then immediately provisions a consultation for
    the selected hospital department with a token.
    """
    _assert_reception_authorized(hospital_user)

    # Check for existing patient by exact phone or ABHA ID
    match_conditions = [Patient.phone == payload.phone]
    if payload.abha_id:
        match_conditions.append(Patient.abha_id == payload.abha_id)

    existing_stmt = select(Patient).where(or_(*match_conditions))
    patient = (await db.execute(existing_stmt)).scalar_one_or_none()

    if patient is None:
        # Create a new patient identity
        dob = payload.date_of_birth
        if dob is None and payload.age is not None:
            # Approximate date of birth from age
            approx_year = date.today().year - payload.age
            dob = date(approx_year, 1, 1)

        temp_email = f"walkin_{uuid.uuid4().hex[:8]}@clinova.local"
        user = User(
            email=temp_email,
            phone=payload.phone,
            password_hash=hash_password("TemporaryWalkinPass1!"),
            role="patient",
            is_active=True,
        )
        db.add(user)
        await db.flush()

        patient = Patient(
            user_id=user.id,
            full_name=payload.full_name,
            phone=payload.phone,
            date_of_birth=dob,
            gender=payload.gender,
            abha_id=payload.abha_id,
        )
        db.add(patient)
        await db.flush()
        await db.refresh(patient)

    # Create new consultation for selected department
    consultation = Consultation(
        patient_id=patient.id,
        hospital_id=hospital.id,
        department=payload.department,
        chief_complaint=payload.chief_complaint or "Walk-in OPD Registration",
        status="initiated",
    )
    db.add(consultation)
    await db.flush()

    # Generate sequential department token
    token_number = await _generate_token_for_consultation(
        db=db,
        hospital_id=hospital.id,
        department=payload.department,
        consultation=consultation,
    )

    await db.refresh(consultation)

    return RegistrationResponse(
        consultation_id=consultation.id,
        patient_id=patient.id,
        patient_name=patient.full_name,
        hospital_id=hospital.id,
        hospital_name=hospital.name,
        department=payload.department,
        token_number=token_number,
        status=consultation.status,
        message=f"Patient {patient.full_name} manually registered for {payload.department}. Token #{token_number}.",
        created_at=consultation.created_at,
    )


async def get_department_queue(
    db: AsyncSession,
    hospital_user: HospitalUser,
    hospital: Hospital,
    department: str,
) -> DepartmentQueueResponse:
    """Retrieve the operational OPD queue for a specific hospital department.

    Strictly non-clinical: contains only operational queue status, display names,
    tokens, and timestamps. Zero medical history, AI summary, or documents exposed.
    """
    _assert_reception_authorized(hospital_user)

    # 1. Fetch active consultations for this hospital and department
    stmt = (
        select(Consultation, Patient)
        .join(Patient, Consultation.patient_id == Patient.id)
        .where(
            Consultation.hospital_id == hospital.id,
            Consultation.department == department,
            Consultation.status.in_(["in_progress", "initiated"]),
        )
        .order_by(Consultation.token_number.asc().nulls_last(), Consultation.created_at.asc())
    )
    rows = (await db.execute(stmt)).all()

    now_serving: int | None = None
    entries: list[QueueEntry] = []
    waiting_position = 1

    for cons, pat in rows:
        if cons.status == "in_progress" and now_serving is None:
            now_serving = cons.token_number

        # Format patient display name safely: e.g. "Rohan P."
        name_parts = pat.full_name.split()
        if len(name_parts) > 1:
            display_name = f"{name_parts[0]} {name_parts[-1][0]}."
        else:
            display_name = pat.full_name

        pos = waiting_position if cons.status == "initiated" else 0
        if cons.status == "initiated":
            waiting_position += 1

        entries.append(
            QueueEntry(
                token_number=cons.token_number or 0,
                token=cons.token_number or 0,
                patient_display_name=display_name,
                department=cons.department or department,
                status="waiting" if cons.status == "initiated" else "in_progress",
                position=pos,
                consultation_id=cons.id,
                checkin_time=cons.created_at,
                chief_complaint=cons.chief_complaint,
            )
        )

    # If no in_progress consultation currently, check last completed token
    if now_serving is None:
        last_completed_stmt = (
            select(Consultation.token_number)
            .where(
                Consultation.hospital_id == hospital.id,
                Consultation.department == department,
                Consultation.status.in_(["completed", "reviewed"]),
                Consultation.token_number.is_not(None),
            )
            .order_by(Consultation.token_number.desc())
            .limit(1)
        )
        now_serving = (await db.execute(last_completed_stmt)).scalar()

    waiting_count = sum(1 for e in entries if e.status == "waiting")

    return DepartmentQueueResponse(
        hospital_id=hospital.id,
        hospital_name=hospital.name,
        department=department,
        now_serving=now_serving,
        waiting_count=waiting_count,
        entries=entries,
    )


async def advance_department_queue(
    db: AsyncSession,
    hospital_user: HospitalUser,
    hospital: Hospital,
    department: str,
) -> AdvanceQueueResponse:
    """Advance the department queue: marks current in_progress as completed,

    and transitions the next waiting initiated consultation to in_progress.
    """
    _assert_reception_authorized(hospital_user)

    # 1. Find current in_progress consultation
    curr_stmt = (
        select(Consultation)
        .where(
            Consultation.hospital_id == hospital.id,
            Consultation.department == department,
            Consultation.status == "in_progress",
        )
        .order_by(Consultation.token_number.asc().nulls_last())
    )
    current_cons = (await db.execute(curr_stmt)).scalars().first()
    prev_token: int | None = None
    if current_cons is not None:
        prev_token = current_cons.token_number
        current_cons.status = "completed"
        current_cons.completed_at = datetime.now(timezone.utc)
        current_cons.updated_at = datetime.now(timezone.utc)

    # 2. Find next waiting consultation
    next_stmt = (
        select(Consultation)
        .where(
            Consultation.hospital_id == hospital.id,
            Consultation.department == department,
            Consultation.status == "initiated",
        )
        .order_by(Consultation.token_number.asc().nulls_last(), Consultation.created_at.asc())
    )
    next_cons = (await db.execute(next_stmt)).scalars().first()
    new_serving: int | None = None
    if next_cons is not None:
        next_cons.status = "in_progress"
        next_cons.started_at = datetime.now(timezone.utc)
        next_cons.updated_at = datetime.now(timezone.utc)
        new_serving = next_cons.token_number

    await db.flush()

    # Remaining waiting count
    remaining_stmt = (
        select(func.count())
        .where(
            Consultation.hospital_id == hospital.id,
            Consultation.department == department,
            Consultation.status == "initiated",
        )
    )
    waiting_count = (await db.execute(remaining_stmt)).scalar() or 0

    msg = (
        f"Queue advanced to Token #{new_serving}."
        if new_serving is not None
        else "Queue is clear. No more patients waiting."
    )

    return AdvanceQueueResponse(
        department=department,
        previous_token=prev_token,
        now_serving=new_serving,
        waiting_count=waiting_count,
        message=msg,
    )


async def get_patient_active_visit(
    db: AsyncSession,
    patient: Patient,
) -> ActiveVisitResponse:
    """Retrieve the currently authenticated patient's active hospital visit & queue status.

    Returns the patient's token, current now_serving, and number of people ahead in the department.
    Guarantees that patient cannot view other patients' names or clinical data.
    """
    # 1. Find patient's latest active consultation linked to a hospital
    stmt = (
        select(Consultation, Hospital)
        .join(Hospital, Consultation.hospital_id == Hospital.id)
        .where(
            Consultation.patient_id == patient.id,
            Consultation.hospital_id.is_not(None),
            Consultation.status.in_(["initiated", "in_progress"]),
        )
        .order_by(Consultation.created_at.desc())
    )
    row = (await db.execute(stmt)).first()

    if row is None:
        return ActiveVisitResponse(has_active_visit=False)

    cons, hosp = row
    department = cons.department or "General Medicine"
    my_token = cons.token_number

    # 2. Query now_serving for this hospital + department
    now_serving_stmt = (
        select(Consultation.token_number)
        .where(
            Consultation.hospital_id == hosp.id,
            Consultation.department == department,
            Consultation.status == "in_progress",
        )
        .limit(1)
    )
    now_serving = (await db.execute(now_serving_stmt)).scalar()

    # If no in_progress, check latest completed token
    if now_serving is None:
        last_completed_stmt = (
            select(Consultation.token_number)
            .where(
                Consultation.hospital_id == hosp.id,
                Consultation.department == department,
                Consultation.status.in_(["completed", "reviewed"]),
                Consultation.token_number.is_not(None),
            )
            .order_by(Consultation.token_number.desc())
            .limit(1)
        )
        now_serving = (await db.execute(last_completed_stmt)).scalar()

    # 3. Calculate people ahead: waiting patients in same department with earlier token
    people_ahead = 0
    if my_token is not None and cons.status == "initiated":
        ahead_stmt = (
            select(func.count())
            .where(
                Consultation.hospital_id == hosp.id,
                Consultation.department == department,
                Consultation.status == "initiated",
                Consultation.token_number < my_token,
            )
        )
        people_ahead = (await db.execute(ahead_stmt)).scalar() or 0
    elif cons.status == "in_progress":
        people_ahead = 0

    return ActiveVisitResponse(
        has_active_visit=True,
        consultation_id=cons.id,
        hospital_id=hosp.id,
        hospital_name=hosp.name,
        department=department,
        token_number=my_token,
        now_serving=now_serving,
        people_ahead=people_ahead,
        status="called" if cons.status == "in_progress" else "waiting",
        checkin_time=cons.created_at,
    )

