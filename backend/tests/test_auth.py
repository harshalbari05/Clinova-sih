from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth_service import create_access_token


@pytest.mark.asyncio
async def test_patient_registration_success(client: AsyncClient, db_session: AsyncSession):
    """Verify successful patient registration creates user and patient profile without exposing secrets."""
    payload = {
        "email": "patient.test@example.com",
        "phone": "+919876543210",
        "password": "SecurePassword123!",
        "full_name": "Ramesh Kumar",
        "date_of_birth": "1988-04-12",
        "gender": "male",
        "abha_id": "14-1111-2222-3333",
        "address": "42 Market Street, Bangalore",
        "emergency_contact": "Sita Kumar (+919876543219)",
    }
    response = await client.post("/api/v1/auth/patient/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["account_type"] == "patient"
    assert data["user"]["email"] == "patient.test@example.com"
    assert data["user"]["phone"] == "+919876543210"
    assert data["user"]["role"] == "patient"
    assert data["user"]["is_active"] is True
    assert data["patient"]["full_name"] == "Ramesh Kumar"
    assert data["patient"]["abha_id"] == "14-1111-2222-3333"

    # Verify passwords/hashes never returned
    assert "password" not in data
    assert "password_hash" not in data["user"]
    assert "password" not in data["user"]

    # Verify password is encrypted in database
    stmt = select(User).where(User.email == "patient.test@example.com")
    db_user = (await db_session.execute(stmt)).scalar_one()
    assert db_user.password_hash is not None
    assert db_user.password_hash != "SecurePassword123!"
    assert db_user.password_hash.startswith("$2b$")


@pytest.mark.asyncio
async def test_patient_registration_duplicate_email(client: AsyncClient):
    """Verify duplicate email registration is rejected with HTTP 400."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "Original User",
    }
    res1 = await client.post("/api/v1/auth/patient/register", json=payload)
    assert res1.status_code == 201

    duplicate_payload = {
        "email": "duplicate@example.com",
        "phone": "+919999999999",
        "password": "Password123!",
        "full_name": "Another User",
    }
    res2 = await client.post("/api/v1/auth/patient/register", json=duplicate_payload)
    assert res2.status_code == 400
    assert "email address already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_patient_registration_duplicate_phone(client: AsyncClient):
    """Verify duplicate phone registration is rejected with HTTP 400."""
    payload1 = {
        "email": "user1@example.com",
        "phone": "+919888877777",
        "password": "Password123!",
        "full_name": "User One",
    }
    res1 = await client.post("/api/v1/auth/patient/register", json=payload1)
    assert res1.status_code == 201

    payload2 = {
        "email": "user2@example.com",
        "phone": "+919888877777",
        "password": "Password123!",
        "full_name": "User Two",
    }
    res2 = await client.post("/api/v1/auth/patient/register", json=payload2)
    assert res2.status_code == 400
    assert "phone number already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_patient_registration_duplicate_abha_id(client: AsyncClient):
    """Verify duplicate ABHA ID is rejected with HTTP 400."""
    payload1 = {
        "email": "abha1@example.com",
        "password": "Password123!",
        "full_name": "ABHA One",
        "abha_id": "99-9999-9999-9999",
    }
    res1 = await client.post("/api/v1/auth/patient/register", json=payload1)
    assert res1.status_code == 201

    payload2 = {
        "email": "abha2@example.com",
        "password": "Password123!",
        "full_name": "ABHA Two",
        "abha_id": "99-9999-9999-9999",
    }
    res2 = await client.post("/api/v1/auth/patient/register", json=payload2)
    assert res2.status_code == 400
    assert "ABHA ID already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_patient_login_success(client: AsyncClient):
    """Verify patient login using email and phone identifiers returns signed JWT."""
    # Register
    reg_payload = {
        "email": "login.test@example.com",
        "phone": "+919123456780",
        "password": "ValidLoginPassword1!",
        "full_name": "Vijay Verma",
    }
    reg_res = await client.post("/api/v1/auth/patient/register", json=reg_payload)
    assert reg_res.status_code == 201

    # Login with email
    email_login = await client.post(
        "/api/v1/auth/patient/login",
        json={"identifier": "login.test@example.com", "password": "ValidLoginPassword1!"},
    )
    assert email_login.status_code == 200
    email_data = email_login.json()
    assert "access_token" in email_data
    assert email_data["token_type"] == "bearer"
    assert email_data["account_type"] == "patient"
    assert email_data["user"]["email"] == "login.test@example.com"
    assert email_data["patient"]["full_name"] == "Vijay Verma"

    # Login with phone
    phone_login = await client.post(
        "/api/v1/auth/patient/login",
        json={"identifier": "+919123456780", "password": "ValidLoginPassword1!"},
    )
    assert phone_login.status_code == 200
    phone_data = phone_login.json()
    assert "access_token" in phone_data
    assert phone_data["user"]["phone"] == "+919123456780"


@pytest.mark.asyncio
async def test_patient_login_invalid_password(client: AsyncClient):
    """Verify invalid password returns HTTP 401."""
    reg_payload = {
        "email": "invalid.pw@example.com",
        "password": "CorrectPassword123!",
        "full_name": "Test User",
    }
    await client.post("/api/v1/auth/patient/register", json=reg_payload)

    login_res = await client.post(
        "/api/v1/auth/patient/login",
        json={"identifier": "invalid.pw@example.com", "password": "IncorrectPassword!"},
    )
    assert login_res.status_code == 401
    assert login_res.json()["detail"] == "Invalid credentials."


@pytest.mark.asyncio
async def test_patient_login_inactive_user(client: AsyncClient, db_session: AsyncSession):
    """Verify inactive user cannot log in (HTTP 403)."""
    reg_payload = {
        "email": "inactive.patient@example.com",
        "password": "Password123!",
        "full_name": "Inactive User",
    }
    await client.post("/api/v1/auth/patient/register", json=reg_payload)

    # Deactivate user in DB
    stmt = select(User).where(User.email == "inactive.patient@example.com")
    user = (await db_session.execute(stmt)).scalar_one()
    user.is_active = False
    await db_session.commit()

    login_res = await client.post(
        "/api/v1/auth/patient/login",
        json={"identifier": "inactive.patient@example.com", "password": "Password123!"},
    )
    assert login_res.status_code == 403
    assert "inactive" in login_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_hospital_registration_success(client: AsyncClient):
    """Verify hospital facility and hospital_admin user registration."""
    payload = {
        "hospital_name": "Metro Healthcare Center",
        "registration_number": "HOSP-REG-2026-999",
        "hospital_phone": "+912288776655",
        "hospital_email": "contact@metrocare.in",
        "address": "88 Healthcare Blvd",
        "city": "Pune",
        "state": "Maharashtra",
        "pincode": "411001",
        "admin_email": "admin@metrocare.in",
        "admin_password": "AdminPassword2026!",
        "admin_phone": "+919811223344",
        "admin_name": "Dr. Anjali Patil",
    }
    res = await client.post("/api/v1/auth/hospital/register", json=payload)
    assert res.status_code == 201
    data = res.json()

    assert data["account_type"] == "hospital"
    assert data["hospital_role"] == "hospital_admin"
    assert data["user"]["email"] == "admin@metrocare.in"
    assert data["user"]["role"] == "hospital_admin"
    assert data["hospital"]["name"] == "Metro Healthcare Center"
    assert data["hospital"]["registration_number"] == "HOSP-REG-2026-999"
    assert data["hospital"]["city"] == "Pune"


@pytest.mark.asyncio
async def test_hospital_registration_duplicate(client: AsyncClient):
    """Verify duplicate hospital registration number or admin email is rejected."""
    payload = {
        "hospital_name": "First Hospital",
        "registration_number": "UNIQUE-HOSP-01",
        "admin_email": "admin.first@hospital.org",
        "admin_password": "Password123!",
    }
    res1 = await client.post("/api/v1/auth/hospital/register", json=payload)
    assert res1.status_code == 201

    # Duplicate registration number
    dup_reg = {
        "hospital_name": "Second Hospital",
        "registration_number": "UNIQUE-HOSP-01",
        "admin_email": "admin.second@hospital.org",
        "admin_password": "Password123!",
    }
    res2 = await client.post("/api/v1/auth/hospital/register", json=dup_reg)
    assert res2.status_code == 400
    assert "registration number already exists" in res2.json()["detail"]

    # Duplicate admin email
    dup_email = {
        "hospital_name": "Third Hospital",
        "registration_number": "UNIQUE-HOSP-02",
        "admin_email": "admin.first@hospital.org",
        "admin_password": "Password123!",
    }
    res3 = await client.post("/api/v1/auth/hospital/register", json=dup_email)
    assert res3.status_code == 400
    assert "email address already exists" in res3.json()["detail"]


@pytest.mark.asyncio
async def test_hospital_login_success(client: AsyncClient):
    """Verify hospital admin login produces valid JWT token with hospital context."""
    hosp_payload = {
        "hospital_name": "Apex Multispecialty Hospital",
        "registration_number": "APEX-001",
        "admin_email": "director@apex.org",
        "admin_password": "DirectorSecure1!",
    }
    await client.post("/api/v1/auth/hospital/register", json=hosp_payload)

    login_res = await client.post(
        "/api/v1/auth/hospital/login",
        json={"identifier": "director@apex.org", "password": "DirectorSecure1!"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["account_type"] == "hospital"
    assert data["hospital_role"] == "hospital_admin"
    assert data["hospital"]["name"] == "Apex Multispecialty Hospital"


@pytest.mark.asyncio
async def test_hospital_login_invalid_credentials(client: AsyncClient):
    """Verify invalid credentials on hospital login return HTTP 401."""
    hosp_payload = {
        "hospital_name": "Test Clinic",
        "admin_email": "clinic@test.org",
        "admin_password": "CorrectPassword1!",
    }
    await client.post("/api/v1/auth/hospital/register", json=hosp_payload)

    res = await client.post(
        "/api/v1/auth/hospital/login",
        json={"identifier": "clinic@test.org", "password": "WrongPassword!"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials."


@pytest.mark.asyncio
async def test_current_user_patient_context(client: AsyncClient):
    """Verify GET /api/v1/auth/me returns patient context with valid Bearer token."""
    reg_payload = {
        "email": "me.patient@example.com",
        "password": "Password123!",
        "full_name": "Kiran Rao",
    }
    await client.post("/api/v1/auth/patient/register", json=reg_payload)

    login_res = await client.post(
        "/api/v1/auth/patient/login",
        json={"identifier": "me.patient@example.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]

    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["account_type"] == "patient"
    assert data["user"]["email"] == "me.patient@example.com"
    assert data["patient"]["full_name"] == "Kiran Rao"


@pytest.mark.asyncio
async def test_current_user_hospital_context(client: AsyncClient):
    """Verify GET /api/v1/auth/me returns hospital context for hospital admin."""
    hosp_payload = {
        "hospital_name": "Surya Hospital",
        "admin_email": "admin@suryahospital.org",
        "admin_password": "SuryaPassword1!",
    }
    await client.post("/api/v1/auth/hospital/register", json=hosp_payload)

    login_res = await client.post(
        "/api/v1/auth/hospital/login",
        json={"identifier": "admin@suryahospital.org", "password": "SuryaPassword1!"},
    )
    token = login_res.json()["access_token"]

    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["account_type"] == "hospital"
    assert data["hospital_role"] == "hospital_admin"
    assert data["hospital"]["name"] == "Surya Hospital"


@pytest.mark.asyncio
async def test_current_user_unauthorized_cases(client: AsyncClient, db_session: AsyncSession):
    """Verify GET /api/v1/auth/me handles missing, invalid, and expired tokens."""
    # 1. Missing token
    res_no_token = await client.get("/api/v1/auth/me")
    assert res_no_token.status_code == 401

    # 2. Invalid token string
    res_invalid_token = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.jwt.token"},
    )
    assert res_invalid_token.status_code == 401

    # 3. Expired token
    reg_payload = {
        "email": "expired.user@example.com",
        "password": "Password123!",
        "full_name": "Expired Token User",
    }
    await client.post("/api/v1/auth/patient/register", json=reg_payload)

    stmt = select(User).where(User.email == "expired.user@example.com")
    user = (await db_session.execute(stmt)).scalar_one()

    # Create expired token
    expired_token = create_access_token(
        {"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(seconds=-60),
    )

    res_expired = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res_expired.status_code == 401
    assert "expired" in res_expired.json()["detail"].lower()


@pytest.mark.asyncio
async def test_logout_endpoint(client: AsyncClient):
    """Verify POST /api/v1/auth/logout returns success message."""
    res = await client.post("/api/v1/auth/logout")
    assert res.status_code == 200
    assert "logged out" in res.json()["message"].lower()
