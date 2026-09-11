"""Triage and Red-Flag Alert API endpoints.

Routes:
    GET /api/v1/consultations/{consultation_id}/triage  — Retrieve latest triage result
    GET /api/v1/consultations/{consultation_id}/alerts  — List clinical alerts for consultation

Security:
    - Patients may only access triage and alerts for consultations they own (404 otherwise).
    - Hospital staff may only access consultations affiliated with their facility (404 otherwise).
    - No existence information is leaked for unauthorized consultations.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUserDep, DatabaseDep
from app.models.ai_message import AIMessage
from app.models.ai_session import AISession
from app.models.clinical_history import ClinicalHistory
from app.models.consultation import Consultation
from app.models.hospital_user import HospitalUser
from app.models.patient import Patient
from app.schemas.alert import AlertListResponse, AlertResponse
from app.triage.schemas import TriageResult
from app.triage.service import triage_service

router = APIRouter()


async def _authorize_consultation_access(
    db: DatabaseDep,
    user: CurrentUserDep,
    consultation_id: uuid.UUID,
) -> Consultation:
    """Validate consultation exists and caller is authorized to view it.

    Patients:
        Must own the consultation (consultation.patient_id == patient.id).
        Returns 404 if not found or owned by another patient.

    Hospital Staff:
        Must belong to the hospital facility managing the consultation
        (consultation.hospital_id == hospital_user.hospital_id).
        Returns 404 if not found or belonging to another facility.

    Raises:
        HTTPException(404): If consultation not found or caller unauthorized.
        HTTPException(403): If user has no patient profile and no hospital role.
    """
    stmt = select(Consultation).where(Consultation.id == consultation_id)
    consultation = (await db.execute(stmt)).scalar_one_or_none()

    if consultation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found",
        )

    # Check patient context
    patient_stmt = select(Patient).where(Patient.user_id == user.id)
    patient = (await db.execute(patient_stmt)).scalar_one_or_none()

    if patient is not None:
        if consultation.patient_id != patient.id:
            # Safe 404: Do not leak existence of other patients' consultations
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found",
            )
        return consultation

    # Check hospital staff context
    hospital_user_stmt = select(HospitalUser).where(HospitalUser.user_id == user.id)
    hospital_user = (await db.execute(hospital_user_stmt)).scalar_one_or_none()

    if hospital_user is not None:
        if hospital_user.role == "receptionist":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Receptionist role is not authorized to access clinical triage data.",
            )
        if consultation.hospital_id != hospital_user.hospital_id:
            # Safe 404: Do not leak cross-facility data
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found",
            )
        return consultation

    # User is neither patient nor hospital staff
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have permission to access clinical data.",
    )


@router.get(
    "/consultations/{consultation_id}/triage",
    response_model=TriageResult,
    status_code=status.HTTP_200_OK,
    summary="Get Triage Result",
    description=(
        "Returns the latest structured red-flag triage assessment for the consultation. "
        "Evaluates reported symptoms, chief complaint, and clinical history. "
        "Enforces strict ownership access control (404 for unauthorized)."
    ),
)
async def get_consultation_triage(
    consultation_id: uuid.UUID,
    user: CurrentUserDep,
    db: DatabaseDep,
) -> TriageResult:
    """Retrieve red-flag triage findings for the consultation."""
    consultation = await _authorize_consultation_access(db, user, consultation_id)

    # Fetch existing clinical history
    hist_stmt = select(ClinicalHistory).where(
        ClinicalHistory.consultation_id == consultation_id
    )
    history = (await db.execute(hist_stmt)).scalar_one_or_none()

    # Gather all patient statements: chief complaint + patient messages in AI sessions
    patient_statements: list[str] = []
    if consultation.chief_complaint:
        patient_statements.append(consultation.chief_complaint)

    msg_stmt = (
        select(AIMessage.message)
        .join(AISession, AIMessage.ai_session_id == AISession.id)
        .where(
            AISession.consultation_id == consultation_id,
            AIMessage.sender == "patient",
        )
        .order_by(AIMessage.created_at.asc())
    )
    session_msgs = list((await db.execute(msg_stmt)).scalars().all())
    patient_statements.extend(session_msgs)

    text = "\n".join(patient_statements) if patient_statements else ""
    return await triage_service.evaluate_triage(
        db=db,
        consultation=consultation,
        patient_text=text,
        history=history,
        use_ai_assistance=False,  # Read endpoint uses fast authoritative deterministic evaluation
    )


@router.get(
    "/consultations/{consultation_id}/alerts",
    response_model=AlertListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Consultation Alerts",
    description=(
        "Returns all active and historical red-flag alerts generated for this consultation. "
        "Ordered newest first. Enforces strict ownership access control."
    ),
)
async def list_consultation_alerts(
    consultation_id: uuid.UUID,
    user: CurrentUserDep,
    db: DatabaseDep,
) -> AlertListResponse:
    """Retrieve all red-flag alerts associated with a consultation."""
    await _authorize_consultation_access(db, user, consultation_id)
    alerts = await triage_service.get_consultation_alerts(db, consultation_id)
    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in alerts],
        total=len(alerts),
    )
