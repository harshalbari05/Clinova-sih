"""Hospital reception desk API endpoints.

Routes:
    POST /api/v1/reception/lookup-qr        — Resolve Clinova QR to safe demographic profile.
    POST /api/v1/reception/register-patient — Confirm QR registration & assign OPD department.
    POST /api/v1/reception/register-manual  — Manual patient registration fallback.
    GET  /api/v1/reception/departments      — List available hospital OPD departments.

Security:
    - Requires authenticated hospital user (receptionist, hospital_admin, hospital_staff, doctor).
    - Patients and unauthenticated requests are rejected.
    - Zero clinical history or AI summary data is ever exposed via these endpoints.
"""

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentHospitalUserDep, DatabaseDep
from app.schemas.reception import (
    AdvanceQueueRequest,
    AdvanceQueueResponse,
    ConfirmRegistrationRequest,
    DepartmentQueueResponse,
    DepartmentsListResponse,
    ManualRegistrationRequest,
    QRLookupRequest,
    RegistrationResponse,
    SafePatientLookupResponse,
)
from app.services import reception_service

router = APIRouter()


@router.post(
    "/lookup-qr",
    response_model=SafePatientLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Lookup Patient by QR Code",
    description=(
        "Resolves a Clinova patient QR code string (e.g. 'CLINOVA:PATIENT:{uuid}') "
        "to a safe, non-clinical patient demographic profile. "
        "Only authorized hospital reception staff may call this endpoint."
    ),
)
async def lookup_patient_qr(
    payload: QRLookupRequest,
    current_hospital_user: CurrentHospitalUserDep,
    db: DatabaseDep,
) -> SafePatientLookupResponse:
    """Resolve patient registration from QR code safely."""
    _user, hospital_user, _hospital = current_hospital_user
    return await reception_service.lookup_patient_by_qr(
        db=db,
        hospital_user=hospital_user,
        qr_code=payload.qr_code,
    )


@router.post(
    "/register-patient",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirm Registration & Assign Department",
    description=(
        "Confirms registration of a scanned patient for a hospital visit and assigns "
        "them to an OPD department. If the patient has a pre-hospital intake consultation, "
        "it is associated with this hospital and department."
    ),
)
async def confirm_registration(
    payload: ConfirmRegistrationRequest,
    current_hospital_user: CurrentHospitalUserDep,
    db: DatabaseDep,
) -> RegistrationResponse:
    """Confirm patient registration for an OPD department."""
    _user, hospital_user, hospital = current_hospital_user
    return await reception_service.register_patient(
        db=db,
        hospital_user=hospital_user,
        hospital=hospital,
        payload=payload,
    )


@router.post(
    "/register-manual",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Manual Walk-in Registration Fallback",
    description=(
        "Registers a walk-in patient when the QR code cannot be scanned. "
        "Captures minimum required demographic details and provisions a consultation "
        "for the assigned hospital department without an open profile search."
    ),
)
async def register_manual(
    payload: ManualRegistrationRequest,
    current_hospital_user: CurrentHospitalUserDep,
    db: DatabaseDep,
) -> RegistrationResponse:
    """Manually register a walk-in patient."""
    _user, hospital_user, hospital = current_hospital_user
    return await reception_service.register_manual_patient(
        db=db,
        hospital_user=hospital_user,
        hospital=hospital,
        payload=payload,
    )


@router.get(
    "/departments",
    response_model=DepartmentsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List OPD Departments",
    description="Returns list of available OPD departments for patient assignment.",
)
async def get_departments(
    current_hospital_user: CurrentHospitalUserDep,
) -> DepartmentsListResponse:
    """Retrieve available OPD departments."""
    _user, hospital_user, _hospital = current_hospital_user
    reception_service._assert_reception_authorized(hospital_user)
    return await reception_service.get_available_departments()


@router.get(
    "/queue",
    response_model=DepartmentQueueResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Department Queue",
    description="Returns the operational queue and now-serving token for an OPD department.",
)
async def get_department_queue(
    current_hospital_user: CurrentHospitalUserDep,
    db: DatabaseDep,
    department: str = Query(default="General Medicine", description="OPD Department name"),
) -> DepartmentQueueResponse:
    """Retrieve the operational OPD queue for a specific hospital department."""
    _user, hospital_user, hospital = current_hospital_user
    return await reception_service.get_department_queue(
        db=db,
        hospital_user=hospital_user,
        hospital=hospital,
        department=department,
    )


@router.post(
    "/queue/advance",
    response_model=AdvanceQueueResponse,
    status_code=status.HTTP_200_OK,
    summary="Advance Department Queue",
    description="Advances the department queue: completes current in_progress and calls next waiting patient.",
)
async def advance_department_queue(
    payload: AdvanceQueueRequest,
    current_hospital_user: CurrentHospitalUserDep,
    db: DatabaseDep,
) -> AdvanceQueueResponse:
    """Advance the department queue to the next patient."""
    _user, hospital_user, hospital = current_hospital_user
    return await reception_service.advance_department_queue(
        db=db,
        hospital_user=hospital_user,
        hospital=hospital,
        department=payload.department,
    )

