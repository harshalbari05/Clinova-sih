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

from app.schemas.summary import (
    StructuredSummary,
    SummaryConfirmRequest,
    SummaryEditRequest,
    SummaryGenerateRequest,
    SummaryRejectRequest,
    SummaryResponse,
    SummaryStatus,
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
    "StructuredSummary",
    "SummaryConfirmRequest",
    "SummaryEditRequest",
    "SummaryGenerateRequest",
    "SummaryRejectRequest",
    "SummaryResponse",
    "SummaryStatus",
    "TokenResponse",
    "UserSummaryResponse",
]
