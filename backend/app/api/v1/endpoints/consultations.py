"""Consultation API endpoints.

Routes:
    POST /api/v1/consultations                    — Create a new consultation.
    GET  /api/v1/consultations                    — List authenticated patient's consultations.
    GET  /api/v1/consultations/{consultation_id}  — Get a single consultation by ID.

Security:
    All endpoints require a valid Bearer JWT for a patient account.
    patient_id is ALWAYS derived from the JWT — never from client-supplied data.
    A patient can only access their own consultations.
"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentPatientDep, DatabaseDep
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
    summary="List My Consultations",
    description=(
        "Returns a paginated list of consultations belonging to the authenticated patient, "
        "ordered newest-first. Supports optional limit and offset query parameters."
    ),
)
async def list_consultations(
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return."),
    offset: int = Query(default=0, ge=0, description="Records to skip."),
) -> ConsultationListResponse:
    """List all consultations owned by the authenticated patient."""
    _user, patient = current_patient
    return await consultation_service.list_consultations(db, patient, limit=limit, offset=offset)


@router.get(
    "/{consultation_id}",
    response_model=ConsultationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Consultation",
    description=(
        "Returns a single consultation by ID. "
        "Returns 404 if the consultation does not exist or belongs to another patient. "
        "No existence information is leaked for consultations of other patients."
    ),
)
async def get_consultation(
    consultation_id: uuid.UUID,
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
) -> ConsultationResponse:
    """Get a single consultation by ID, enforcing ownership."""
    _user, patient = current_patient
    return await consultation_service.get_consultation(db, patient, consultation_id)
