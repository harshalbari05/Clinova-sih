"""Pydantic schemas package."""

from app.schemas.alert import AlertListResponse, AlertResponse
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

__all__ = [
    "AlertListResponse",
    "AlertResponse",
    "CurrentUserResponse",
    "HospitalRegisterRequest",
    "HospitalSummaryResponse",
    "LoginRequest",
    "LogoutResponse",
    "PatientProfileResponse",
    "PatientRegisterRequest",
    "TokenResponse",
    "UserSummaryResponse",
]
