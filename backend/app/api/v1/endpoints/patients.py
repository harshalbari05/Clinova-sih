"""Patient profile API endpoints.

Routes:
    GET  /api/v1/patients/me  — Return authenticated patient's profile.
    PUT  /api/v1/patients/me  — Partially update authenticated patient's profile.

Authentication:
    Both endpoints require a valid Bearer JWT.
    Identity comes exclusively from the JWT — no client-supplied patient_id is accepted.
"""

from fastapi import APIRouter, status

from app.api.deps import CurrentPatientDep, DatabaseDep
from app.schemas.auth import PatientProfileResponse
from app.schemas.patient import ActiveVisitResponse, PatientProfileUpdate
from app.services import patient_service, reception_service

router = APIRouter()


@router.get(
    "/me",
    response_model=PatientProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Patient Profile",
    description=(
        "Returns the currently authenticated patient's demographic profile. "
        "Requires a valid Bearer JWT issued to a patient account."
    ),
)
async def get_my_profile(
    current_patient: CurrentPatientDep,
) -> PatientProfileResponse:
    """Return the authenticated patient's profile (already loaded by dependency)."""
    _user, patient = current_patient
    return PatientProfileResponse.model_validate(patient)


@router.put(
    "/me",
    response_model=PatientProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Patient Profile",
    description=(
        "Partially updates the authenticated patient's demographic profile. "
        "Only provided fields are updated. "
        "Immutable fields (id, user_id, created_at) are never accepted. "
        "Returns the updated profile."
    ),
)
async def update_my_profile(
    update_data: PatientProfileUpdate,
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
) -> PatientProfileResponse:
    """Partially update the authenticated patient's profile."""
    _user, patient = current_patient
    updated = await patient_service.update_patient_profile(db, patient, update_data)
    return PatientProfileResponse.model_validate(updated)


@router.get(
    "/me/active-visit",
    response_model=ActiveVisitResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Active Hospital Visit & Token",
    description=(
        "Returns the authenticated patient's active hospital visit, department token, "
        "now-serving status, and people ahead. Zero clinical data of other patients is exposed."
    ),
)
async def get_my_active_visit(
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
) -> ActiveVisitResponse:
    """Retrieve active hospital visit and department token for the caller."""
    _user, patient = current_patient
    return await reception_service.get_patient_active_visit(db, patient)

