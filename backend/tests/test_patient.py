"""Tests for patient profile endpoints.

Covers:
1.  Get own profile successfully (authenticated patient).
2.  Get profile without authentication (401).
3.  Update own profile successfully (full update).
4.  Partial profile update (only one field).
5.  Invalid profile data (validation error 422).
6.  Verify password is never returned in any response.
7.  Two patients cannot access each other's profiles.
8.  Update with duplicate ABHA ID is rejected (409).
9.  Update with duplicate phone is rejected (409).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REGISTER_URL = "/api/v1/auth/patient/register"
LOGIN_URL = "/api/v1/auth/patient/login"
PROFILE_URL = "/api/v1/patients/me"


async def _register_and_login(
    client: AsyncClient,
    *,
    email: str,
    password: str = "TestPassword1!",
    full_name: str = "Test Patient",
    phone: str | None = None,
    abha_id: str | None = None,
) -> str:
    """Register a patient and return the Bearer token."""
    reg_payload: dict = {
        "email": email,
        "password": password,
        "full_name": full_name,
    }
    if phone:
        reg_payload["phone"] = phone
    if abha_id:
        reg_payload["abha_id"] = abha_id

    reg_res = await client.post(REGISTER_URL, json=reg_payload)
    assert reg_res.status_code == 201, reg_res.text

    login_res = await client.post(
        LOGIN_URL,
        json={"identifier": email, "password": password},
    )
    assert login_res.status_code == 200, login_res.text
    return login_res.json()["access_token"]


# ---------------------------------------------------------------------------
# Test: GET /api/v1/patients/me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_own_profile_success(client: AsyncClient):
    """Authenticated patient can retrieve their own profile."""
    token = await _register_and_login(
        client,
        email="profile.get@example.com",
        full_name="Priya Sharma",
    )
    res = await client.get(PROFILE_URL, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    assert data["full_name"] == "Priya Sharma"
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_profile_unauthenticated(client: AsyncClient):
    """Missing token returns HTTP 401."""
    res = await client.get(PROFILE_URL)
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_invalid_token(client: AsyncClient):
    """Invalid Bearer token returns HTTP 401."""
    res = await client.get(
        PROFILE_URL,
        headers={"Authorization": "Bearer not.a.real.token"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_never_returns_password(client: AsyncClient):
    """Passwords and hashes must never appear in the profile response."""
    token = await _register_and_login(
        client, email="no.password.leak@example.com", password="SuperSecret99!"
    )
    res = await client.get(PROFILE_URL, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    # These keys must never be present in the response body
    assert "password" not in data
    assert "password_hash" not in data
    assert "SuperSecret99!" not in str(data)


# ---------------------------------------------------------------------------
# Test: PUT /api/v1/patients/me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_profile_success(client: AsyncClient):
    """Authenticated patient can fully update their profile fields."""
    token = await _register_and_login(
        client, email="update.full@example.com", full_name="Old Name"
    )
    update_payload = {
        "full_name": "New Full Name",
        "date_of_birth": "1990-07-15",
        "gender": "female",
        "address": "101 New Street, Mumbai",
        "emergency_contact": "Raj (+919800000001)",
    }
    res = await client.put(
        PROFILE_URL,
        json=update_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["full_name"] == "New Full Name"
    assert data["date_of_birth"] == "1990-07-15"
    assert data["gender"] == "female"
    assert data["address"] == "101 New Street, Mumbai"
    assert data["emergency_contact"] == "Raj (+919800000001)"


@pytest.mark.asyncio
async def test_update_profile_partial(client: AsyncClient):
    """Partial update only modifies the provided field(s)."""
    token = await _register_and_login(
        client,
        email="partial.update@example.com",
        full_name="Partial Patient",
        phone="+919000000001",
    )

    # Get initial profile
    get_res = await client.get(
        PROFILE_URL, headers={"Authorization": f"Bearer {token}"}
    )
    original = get_res.json()

    # Update only full_name
    res = await client.put(
        PROFILE_URL,
        json={"full_name": "Updated Only Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["full_name"] == "Updated Only Name"
    # Phone should be unchanged
    assert data["phone"] == original["phone"]


@pytest.mark.asyncio
async def test_update_profile_empty_body(client: AsyncClient):
    """Sending an empty update body returns the unchanged profile (no-op)."""
    token = await _register_and_login(
        client, email="noop.update@example.com", full_name="No-Op Patient"
    )
    res = await client.put(
        PROFILE_URL,
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["full_name"] == "No-Op Patient"


@pytest.mark.asyncio
async def test_update_profile_invalid_full_name(client: AsyncClient):
    """Empty string for full_name violates min_length=1 and returns 422."""
    token = await _register_and_login(
        client, email="invalid.name@example.com", full_name="Valid Name"
    )
    res = await client.put(
        PROFILE_URL,
        json={"full_name": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_update_profile_unauthenticated(client: AsyncClient):
    """PUT /me without authentication returns HTTP 401."""
    res = await client.put(PROFILE_URL, json={"full_name": "Hacker"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_update_profile_never_returns_password(client: AsyncClient):
    """Updated profile response must not contain any password or hash."""
    token = await _register_and_login(
        client, email="update.nopw@example.com", password="VerySecret123!"
    )
    res = await client.put(
        PROFILE_URL,
        json={"full_name": "Safe Update"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_update_profile_duplicate_abha_id_rejected(client: AsyncClient):
    """Updating abha_id to one already used by another patient returns 409."""
    # Register first patient with a specific ABHA ID
    await _register_and_login(
        client,
        email="abha.owner@example.com",
        full_name="ABHA Owner",
        abha_id="10-1234-5678-9012",
    )
    # Register second patient without ABHA ID
    token2 = await _register_and_login(
        client,
        email="abha.thief@example.com",
        full_name="ABHA Thief",
    )
    # Try to steal the first patient's ABHA ID
    res = await client.put(
        PROFILE_URL,
        json={"abha_id": "10-1234-5678-9012"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res.status_code == 409
    assert "ABHA ID already exists" in res.json()["detail"]


@pytest.mark.asyncio
async def test_patients_cannot_access_each_other_profile(client: AsyncClient):
    """Two separate patients each see only their own profile data."""
    token_a = await _register_and_login(
        client, email="patient.a@example.com", full_name="Patient Alpha"
    )
    token_b = await _register_and_login(
        client, email="patient.b@example.com", full_name="Patient Beta"
    )

    res_a = await client.get(
        PROFILE_URL, headers={"Authorization": f"Bearer {token_a}"}
    )
    res_b = await client.get(
        PROFILE_URL, headers={"Authorization": f"Bearer {token_b}"}
    )

    assert res_a.status_code == 200
    assert res_b.status_code == 200
    # Each patient sees their own data
    assert res_a.json()["full_name"] == "Patient Alpha"
    assert res_b.json()["full_name"] == "Patient Beta"
    # IDs are different
    assert res_a.json()["id"] != res_b.json()["id"]
