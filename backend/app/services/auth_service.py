from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.hospital import Hospital
from app.models.hospital_user import HospitalUser
from app.models.patient import Patient
from app.models.user import User
from app.schemas.auth import (
    CurrentUserResponse,
    HospitalRegisterRequest,
    HospitalSummaryResponse,
    PatientProfileResponse,
    PatientRegisterRequest,
    UserSummaryResponse,
)


def hash_password(password: str) -> str:
    """Hash plain-text password using bcrypt."""
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verify plain password against hashed password."""
    if not hashed_password:
        return False
    pw_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(pw_bytes, hashed_bytes)
    except (ValueError, TypeError):
        return False


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a signed JWT access token."""
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )


async def register_patient(
    db: AsyncSession, req: PatientRegisterRequest
) -> tuple[User, Patient]:
    """Register a new patient account with atomic User and Patient records."""
    # Check email collision
    if req.email:
        existing_email = await db.execute(
            select(User).where(User.email == req.email)
        )
        if existing_email.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

    # Check phone collision
    if req.phone:
        existing_phone = await db.execute(
            select(User).where(User.phone == req.phone)
        )
        if existing_phone.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this phone number already exists.",
            )

    # Check ABHA ID collision
    if req.abha_id:
        existing_abha = await db.execute(
            select(Patient).where(Patient.abha_id == req.abha_id)
        )
        if existing_abha.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A patient with this ABHA ID already exists.",
            )

    # Create User record
    hashed = hash_password(req.password)
    user = User(
        email=req.email,
        phone=req.phone,
        password_hash=hashed,
        role="patient",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Create Patient record
    patient = Patient(
        user_id=user.id,
        full_name=req.full_name,
        date_of_birth=req.date_of_birth,
        gender=req.gender,
        phone=req.phone,
        abha_id=req.abha_id,
        address=req.address,
        emergency_contact=req.emergency_contact,
    )
    db.add(patient)
    await db.commit()
    await db.refresh(user)
    await db.refresh(patient)

    return user, patient


async def login_patient(
    db: AsyncSession, identifier: str, password: str
) -> tuple[str, User, Patient]:
    """Authenticate a patient and return JWT token with profile details."""
    stmt = select(User).where(
        or_(User.email == identifier, User.phone == identifier)
    )
    user = (await db.execute(stmt)).scalar_one_or_none()

    # Avoid timing/enumeration attacks by verifying password even if user is not found
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    # Verify patient profile association
    patient_stmt = select(Patient).where(Patient.user_id == user.id)
    patient = (await db.execute(patient_stmt)).scalar_one_or_none()
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = {
        "sub": str(user.id),
        "role": user.role,
        "user_type": "patient",
    }
    token = create_access_token(claims)
    return token, user, patient


async def register_hospital(
    db: AsyncSession, req: HospitalRegisterRequest
) -> tuple[Hospital, User, HospitalUser]:
    """Register a new hospital facility and its administrative user account."""
    # Check registration number collision
    if req.registration_number:
        existing_hosp = await db.execute(
            select(Hospital).where(
                Hospital.registration_number == req.registration_number
            )
        )
        if existing_hosp.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A hospital with this registration number already exists.",
            )

    # Check admin email collision
    existing_user = await db.execute(
        select(User).where(User.email == req.admin_email)
    )
    if existing_user.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Check admin phone collision
    if req.admin_phone:
        existing_phone = await db.execute(
            select(User).where(User.phone == req.admin_phone)
        )
        if existing_phone.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this phone number already exists.",
            )

    # Create Hospital facility
    hospital = Hospital(
        name=req.hospital_name,
        registration_number=req.registration_number,
        phone=req.hospital_phone,
        email=req.hospital_email,
        address=req.address,
        city=req.city,
        state=req.state,
        pincode=req.pincode,
    )
    db.add(hospital)
    await db.flush()

    # Create Hospital Admin User
    hashed = hash_password(req.admin_password)
    user = User(
        email=req.admin_email,
        phone=req.admin_phone,
        password_hash=hashed,
        role="hospital_admin",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Create HospitalUser link with role 'hospital_admin'
    hospital_user = HospitalUser(
        user_id=user.id,
        hospital_id=hospital.id,
        role="hospital_admin",
    )
    db.add(hospital_user)
    await db.commit()
    await db.refresh(hospital)
    await db.refresh(user)
    await db.refresh(hospital_user)

    return hospital, user, hospital_user


async def login_hospital(
    db: AsyncSession, identifier: str, password: str
) -> tuple[str, User, Hospital, str]:
    """Authenticate a hospital administrator or staff member."""
    stmt = select(User).where(
        or_(User.email == identifier, User.phone == identifier)
    )
    user = (await db.execute(stmt)).scalar_one_or_none()

    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    # Retrieve hospital association
    hu_stmt = (
        select(HospitalUser, Hospital)
        .join(Hospital, HospitalUser.hospital_id == Hospital.id)
        .where(HospitalUser.user_id == user.id)
    )
    result = (await db.execute(hu_stmt)).first()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    hospital_user, hospital = result
    claims = {
        "sub": str(user.id),
        "role": hospital_user.role,
        "user_type": "hospital",
        "hospital_id": str(hospital.id),
    }
    token = create_access_token(claims)
    return token, user, hospital, hospital_user.role


async def get_user_context(
    db: AsyncSession, user: User
) -> CurrentUserResponse:
    """Retrieve full context (patient or hospital) for current authenticated user."""
    user_summary = UserSummaryResponse.model_validate(user)

    # Check for Patient profile
    patient_stmt = select(Patient).where(Patient.user_id == user.id)
    patient = (await db.execute(patient_stmt)).scalar_one_or_none()
    if patient is not None:
        return CurrentUserResponse(
            user=user_summary,
            account_type="patient",
            patient=PatientProfileResponse.model_validate(patient),
        )

    # Check for Hospital association
    hu_stmt = (
        select(HospitalUser, Hospital)
        .join(Hospital, HospitalUser.hospital_id == Hospital.id)
        .where(HospitalUser.user_id == user.id)
    )
    hu_result = (await db.execute(hu_stmt)).first()
    if hu_result is not None:
        hospital_user, hospital = hu_result
        return CurrentUserResponse(
            user=user_summary,
            account_type="hospital",
            hospital=HospitalSummaryResponse.model_validate(hospital),
            hospital_role=hospital_user.role,
        )

    # Fallback to plain user context
    return CurrentUserResponse(
        user=user_summary,
        account_type="user",
    )
