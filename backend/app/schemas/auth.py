import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

# ==========================================
# Requests
# ==========================================


class PatientRegisterRequest(BaseModel):
    """Payload for patient registration."""

    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=50)
    abha_id: str | None = Field(default=None, max_length=100)
    address: str | None = None
    emergency_contact: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_contact_present(self) -> "PatientRegisterRequest":
        if not self.email and not self.phone:
            raise ValueError("Either email or phone number must be provided.")
        return self


class HospitalRegisterRequest(BaseModel):
    """Payload for hospital facility and administrator registration."""

    hospital_name: str = Field(min_length=1, max_length=255)
    registration_number: str | None = Field(default=None, max_length=100)
    hospital_phone: str | None = Field(default=None, max_length=50)
    hospital_email: EmailStr | None = None
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    pincode: str | None = Field(default=None, max_length=20)

    # Admin User details
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=128)
    admin_phone: str | None = Field(default=None, max_length=50)
    admin_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    """Generic login request using email or phone identifier."""

    identifier: str = Field(
        min_length=1,
        max_length=255,
        description="User email address or registered phone number",
    )
    password: str = Field(min_length=1, max_length=128)


# ==========================================
# Responses (Safe - Never exposing password hash)
# ==========================================


class UserSummaryResponse(BaseModel):
    """Public user identity information."""

    id: uuid.UUID
    email: str | None = None
    phone: str | None = None
    role: str
    is_active: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PatientProfileResponse(BaseModel):
    """Patient demographic and medical identity profile."""

    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    date_of_birth: date | None = None
    gender: str | None = None
    phone: str | None = None
    abha_id: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class HospitalSummaryResponse(BaseModel):
    """Hospital facility information."""

    id: uuid.UUID
    name: str
    registration_number: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Authentication token response with context."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummaryResponse
    account_type: str  # "patient" or "hospital"
    patient: PatientProfileResponse | None = None
    hospital: HospitalSummaryResponse | None = None
    hospital_role: str | None = None


class CurrentUserResponse(BaseModel):
    """Detailed profile of the currently authenticated session."""

    user: UserSummaryResponse
    account_type: str  # "patient" or "hospital"
    patient: PatientProfileResponse | None = None
    hospital: HospitalSummaryResponse | None = None
    hospital_role: str | None = None


class LogoutResponse(BaseModel):
    """Stateless logout confirmation."""

    message: str = "Successfully logged out. Token should be removed from client storage."
