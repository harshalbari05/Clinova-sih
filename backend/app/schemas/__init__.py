"""Pydantic schemas package."""

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
