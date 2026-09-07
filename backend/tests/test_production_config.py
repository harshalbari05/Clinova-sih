"""Tests for production environment configuration and security hardening."""

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_application


def test_cors_origin_sanitization():
    """Verify CORS origin assembler strips trailing slashes and handles CSV and JSON."""
    # Test comma-separated with trailing slashes and whitespace
    s1 = Settings(
        BACKEND_CORS_ORIGINS="https://patient.clinova.health/, https://hospital.clinova.health"
    )
    assert s1.BACKEND_CORS_ORIGINS == [
        "https://patient.clinova.health",
        "https://hospital.clinova.health",
    ]

    # Test JSON array with trailing slash
    s2 = Settings(
        BACKEND_CORS_ORIGINS='["https://app.clinova.health/"]'
    )
    assert s2.BACKEND_CORS_ORIGINS == ["https://app.clinova.health"]


def test_cloud_database_url_adaptation():
    """Verify standard cloud database URLs are adapted to postgresql+asyncpg."""
    # postgres:// standard URL (Supabase/Heroku)
    s1 = Settings(
        DATABASE_URL="postgres://user:pass@db.example.com:5432/clinovadb"
    )
    assert s1.async_database_uri == "postgresql+asyncpg://user:pass@db.example.com:5432/clinovadb"

    # postgresql:// standard URL (Neon/AWS RDS)
    s2 = Settings(
        DATABASE_URL="postgresql://user:pass@db.example.com:5432/clinovadb"
    )
    assert s2.async_database_uri == "postgresql+asyncpg://user:pass@db.example.com:5432/clinovadb"

    # Already asyncpg URL
    s3 = Settings(
        DATABASE_URL="postgresql+asyncpg://user:pass@db.example.com:5432/clinovadb"
    )
    assert s3.async_database_uri == "postgresql+asyncpg://user:pass@db.example.com:5432/clinovadb"


def test_production_rejects_insecure_secret():
    """Verify that ENVIRONMENT=production raises error if default dev secret is used."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY=None,
            SECRET_KEY="temporary_dev_secret_key_change_in_production_32bytes",
        )
    assert "CRITICAL SECURITY" in str(exc_info.value)


def test_production_allows_secure_secret():
    """Verify that ENVIRONMENT=production succeeds with secure secret configured."""
    s = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a" * 32,
    )
    assert s.is_production is True
    assert s.DEBUG is False
    assert s.docs_enabled is False


def test_production_docs_opt_in():
    """Verify that API docs can be explicitly opted-in during staging/prod if needed."""
    s = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a" * 32,
        ENABLE_API_DOCS=True,
    )
    assert s.docs_enabled is True


@pytest.mark.asyncio
async def test_production_error_masking():
    """Verify unhandled exceptions return generic message in production."""
    from fastapi import APIRouter
    from app.core import config as cfg_module

    # Temporarily set environment to production with a secure key
    orig_env = cfg_module.settings.ENVIRONMENT
    orig_debug = cfg_module.settings.DEBUG
    orig_key = cfg_module.settings.JWT_SECRET_KEY

    try:
        cfg_module.settings.ENVIRONMENT = "production"
        cfg_module.settings.DEBUG = False
        cfg_module.settings.JWT_SECRET_KEY = "a" * 32

        app = create_application()

        # Add a route that raises an unhandled exception
        test_router = APIRouter()

        @test_router.get("/test-crash")
        async def crash():
            raise RuntimeError("Sensitive internal database connection string: postgres://secret:1234@internal")

        app.include_router(test_router)

        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            response = await client.get("/test-crash")
            assert response.status_code == 500
            data = response.json()
            # Must NOT leak the secret or traceback
            assert "postgres://secret:1234@internal" not in data["detail"]
            assert data["detail"] == "Internal server error. Please contact system administration."
    finally:
        cfg_module.settings.ENVIRONMENT = orig_env
        cfg_module.settings.DEBUG = orig_debug
        cfg_module.settings.JWT_SECRET_KEY = orig_key
