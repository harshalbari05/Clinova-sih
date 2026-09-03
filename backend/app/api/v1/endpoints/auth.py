from fastapi import APIRouter, status

from app.api.deps import CurrentUserDep, DatabaseDep
from app.core.config import settings
from app.schemas.auth import (
    CurrentUserResponse,
    HospitalRegisterRequest,
    HospitalSummaryResponse,
    LoginRequest,
    LogoutResponse,
    PatientProfileResponse,
    PatientRegisterRequest,
    TokenResponse,
    UserSummaryResponse,
)
from app.services import auth_service

router = APIRouter()


@router.post(
    "/patient/register",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Patient Registration",
    description="Registers a new patient with corresponding user account and demographic profile.",
)
async def register_patient(
    req: PatientRegisterRequest,
    db: DatabaseDep,
) -> CurrentUserResponse:
    user, patient = await auth_service.register_patient(db, req)
    return CurrentUserResponse(
        user=UserSummaryResponse.model_validate(user),
        account_type="patient",
        patient=PatientProfileResponse.model_validate(patient),
    )


@router.post(
    "/patient/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Patient Login",
    description="Authenticates a patient using email or phone and returns a signed JWT access token.",
)
async def login_patient(
    req: LoginRequest,
    db: DatabaseDep,
) -> TokenResponse:
    token, user, patient = await auth_service.login_patient(
        db, req.identifier, req.password
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserSummaryResponse.model_validate(user),
        account_type="patient",
        patient=PatientProfileResponse.model_validate(patient),
    )


@router.post(
    "/hospital/register",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Hospital Registration",
    description="Registers a new hospital facility and its initial hospital_admin user account.",
)
async def register_hospital(
    req: HospitalRegisterRequest,
    db: DatabaseDep,
) -> CurrentUserResponse:
    hospital, user, hospital_user = await auth_service.register_hospital(db, req)
    return CurrentUserResponse(
        user=UserSummaryResponse.model_validate(user),
        account_type="hospital",
        hospital=HospitalSummaryResponse.model_validate(hospital),
        hospital_role=hospital_user.role,
    )


@router.post(
    "/hospital/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Hospital User Login",
    description="Authenticates hospital staff or administrator and returns a signed JWT access token.",
)
async def login_hospital(
    req: LoginRequest,
    db: DatabaseDep,
) -> TokenResponse:
    token, user, hospital, role = await auth_service.login_hospital(
        db, req.identifier, req.password
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserSummaryResponse.model_validate(user),
        account_type="hospital",
        hospital=HospitalSummaryResponse.model_validate(hospital),
        hospital_role=role,
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Current User Context",
    description="Retrieves the currently authenticated user's profile and hospital/patient association.",
)
async def get_me(
    current_user: CurrentUserDep,
    db: DatabaseDep,
) -> CurrentUserResponse:
    return await auth_service.get_user_context(db, current_user)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout",
    description="Confirms user logout. Clients must discard their locally stored JWT access token.",
)
async def logout() -> LogoutResponse:
    return LogoutResponse(
        message="Successfully logged out. Please remove token from client storage."
    )
