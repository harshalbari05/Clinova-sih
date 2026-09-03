import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.models.hospital import Hospital
from app.models.hospital_user import HospitalUser
from app.models.patient import Patient
from app.models.user import User
from app.services.auth_service import decode_access_token

security = HTTPBearer(auto_error=False)

DatabaseDep = Annotated[AsyncSession, Depends(get_async_db)]
AuthHeaderDep = Annotated[HTTPAuthorizationCredentials | None, Depends(security)]


async def get_current_user(
    credentials: AuthHeaderDep,
    db: DatabaseDep,
) -> User:
    """Extract, decode, and validate the JWT Bearer token to return the active User."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_current_patient(
    user: CurrentUserDep,
    db: DatabaseDep,
) -> tuple[User, Patient]:
    """Dependency ensuring the authenticated user has an active patient profile."""
    stmt = select(Patient).where(Patient.user_id == user.id)
    patient = (await db.execute(stmt)).scalar_one_or_none()

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have an associated patient profile.",
        )

    return user, patient


CurrentPatientDep = Annotated[tuple[User, Patient], Depends(get_current_patient)]


async def get_current_hospital_user(
    user: CurrentUserDep,
    db: DatabaseDep,
) -> tuple[User, HospitalUser, Hospital]:
    """Dependency ensuring the authenticated user is associated with a hospital facility."""
    stmt = (
        select(HospitalUser, Hospital)
        .join(Hospital, HospitalUser.hospital_id == Hospital.id)
        .where(HospitalUser.user_id == user.id)
    )
    result = (await db.execute(stmt)).first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with any hospital facility.",
        )

    hospital_user, hospital = result
    return user, hospital_user, hospital


CurrentHospitalUserDep = Annotated[
    tuple[User, HospitalUser, Hospital], Depends(get_current_hospital_user)
]

__all__ = [
    "AsyncGenerator",
    "AsyncSession",
    "AuthHeaderDep",
    "CurrentHospitalUserDep",
    "CurrentPatientDep",
    "CurrentUserDep",
    "DatabaseDep",
    "get_async_db",
    "get_current_hospital_user",
    "get_current_patient",
    "get_current_user",
]
