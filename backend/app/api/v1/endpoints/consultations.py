"""Consultation API endpoints.

Routes:
    POST /api/v1/consultations                    — Create a new consultation (Patient only).
    GET  /api/v1/consultations                    — List consultations (Patient: own; Hospital: facility queue).
    GET  /api/v1/consultations/{consultation_id}  — Get a single consultation by ID.
    POST /api/v1/consultations/{consultation_id}/consent — Record explicit patient consent for consultation.

Security:
    - Creating consultation and recording consent requires an authenticated patient account.
    - Listing consultations dynamically checks user context:
        * Patients see only their own consultations (newest-first).
        * Hospital users see only their facility's consultations (OPD queue FIFO, oldest-first).
        * Cross-facility and cross-patient isolation enforced server-side.
"""

import uuid

from fastapi import APIRouter, Body, Query, status

from app.api.deps import CurrentPatientDep, CurrentUserDep, DatabaseDep
from app.schemas.consent import ConsentRecordRequest, ConsentResponse
from app.schemas.consultation import (
    ConsultationCreate,
    ConsultationListResponse,
    ConsultationResponse,
)
from app.services import consultation_service

router = APIRouter()


@router.post(
    "",
    response_model=ConsultationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Consultation",
    description=(
        "Creates a new consultation for the authenticated patient at the specified hospital. "
        "The patient_id is derived from the Bearer JWT — it cannot be overridden by the client. "
        "Returns 404 if the hospital_id does not exist."
    ),
)
async def create_consultation(
    payload: ConsultationCreate,
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
) -> ConsultationResponse:
    """Create a consultation owned by the authenticated patient."""
    _user, patient = current_patient
    return await consultation_service.create_consultation(db, patient, payload)


@router.get(
    "",
    response_model=ConsultationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Consultations",
    description=(
        "Returns a paginated list of consultations based on caller role: "
        "- Patients receive their own consultations (newest-first). "
        "- Hospital staff (doctors, admins) receive consultations belonging to their affiliated hospital (oldest-first). "
        "Supports optional status filtering and pagination."
    ),
)
async def list_consultations(
    user: CurrentUserDep,
    db: DatabaseDep,
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter by consultation status (e.g., 'initiated', 'reviewed').",
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return."),
    offset: int = Query(default=0, ge=0, description="Records to skip."),
) -> ConsultationListResponse:
    """List consultations for the authenticated patient or hospital facility."""
    return await consultation_service.list_consultations(
        db,
        user,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{consultation_id}",
    response_model=ConsultationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Consultation",
    description=(
        "Returns a single consultation by ID. "
        "Patients can only access their own consultations. "
        "Hospital staff can only access consultations belonging to their hospital. "
        "Returns 404 if the consultation does not exist or caller is not authorized."
    ),
)
async def get_consultation(
    consultation_id: uuid.UUID,
    user: CurrentUserDep,
    db: DatabaseDep,
) -> ConsultationResponse:
    """Get a single consultation by ID, enforcing ownership or facility isolation."""
    return await consultation_service.get_consultation(db, user, consultation_id)


@router.post(
    "/{consultation_id}/consent",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Consultation Consent",
    description=(
        "Records explicit patient informed consent for clinical history intake and AI processing. "
        "Requires authenticated patient ownership of the consultation. "
        "Server-generates authoritative timestamp and updates existing consent record idempotently."
    ),
)
async def record_consultation_consent(
    consultation_id: uuid.UUID,
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
    payload: ConsentRecordRequest = Body(default_factory=ConsentRecordRequest),
) -> ConsentResponse:
    """Record informed consent for the consultation encounter."""
    _user, patient = current_patient
    return await consultation_service.record_consent(
        db=db,
        patient=patient,
        consultation_id=consultation_id,
        payload=payload,
    )
