"""Clinical history API endpoints.

All routes are nested under /api/v1/consultations/{consultation_id}/history
to make the parent-child relationship explicit in the URL structure.

Routes:
    POST /api/v1/consultations/{consultation_id}/history  — Create clinical history.
    GET  /api/v1/consultations/{consultation_id}/history  — Get clinical history.
    PUT  /api/v1/consultations/{consultation_id}/history  — Update clinical history.

Security:
    - All endpoints require a valid Bearer JWT for a patient account.
    - consultation_id comes from the URL path (not the request body).
    - Patient ownership of the consultation is verified server-side before
      any clinical history is touched.
    - A patient cannot access or modify another patient's clinical history.
"""

import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentPatientDep, DatabaseDep
from app.schemas.clinical_history import (
    ClinicalHistoryCreate,
    ClinicalHistoryResponse,
    ClinicalHistoryUpdate,
)
from app.services import clinical_history_service

router = APIRouter()


@router.post(
    "",
    response_model=ClinicalHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Clinical History",
    description=(
        "Creates a clinical history record for the specified consultation. "
        "The consultation must belong to the authenticated patient. "
        "Returns HTTP 409 if a clinical history already exists for this consultation "
        "(one consultation supports exactly one clinical history record). "
        "All clinical content fields are optional at creation."
    ),
)
async def create_clinical_history(
    consultation_id: uuid.UUID,
    payload: ClinicalHistoryCreate,
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
) -> ClinicalHistoryResponse:
    """Create a clinical history for the authenticated patient's consultation."""
    _user, patient = current_patient
    return await clinical_history_service.create_clinical_history(
        db, patient, consultation_id, payload
    )


@router.get(
    "",
    response_model=ClinicalHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Clinical History",
    description=(
        "Returns the clinical history for the specified consultation. "
        "The consultation must belong to the authenticated patient. "
        "Returns HTTP 404 if no clinical history exists yet, or if the "
        "consultation does not belong to the authenticated patient."
    ),
)
async def get_clinical_history(
    consultation_id: uuid.UUID,
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
) -> ClinicalHistoryResponse:
    """Get the clinical history for the authenticated patient's consultation."""
    _user, patient = current_patient
    return await clinical_history_service.get_clinical_history(
        db, patient, consultation_id
    )


@router.put(
    "",
    response_model=ClinicalHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Clinical History",
    description=(
        "Partially updates the clinical history for the specified consultation. "
        "Only provided fields are updated; omitted fields retain their current values. "
        "The clinical history MUST already exist (create it first with POST). "
        "The consultation must belong to the authenticated patient. "
        "Returns HTTP 404 if no clinical history exists, or if the consultation "
        "does not belong to the authenticated patient."
    ),
)
async def update_clinical_history(
    consultation_id: uuid.UUID,
    payload: ClinicalHistoryUpdate,
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
) -> ClinicalHistoryResponse:
    """Partially update the clinical history for the authenticated patient's consultation."""
    _user, patient = current_patient
    return await clinical_history_service.update_clinical_history(
        db, patient, consultation_id, payload
    )
