import json
import logging
from typing import Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("clinova.config")


class Settings(BaseSettings):
    # Application Configuration
    PROJECT_NAME: str = "Clinova API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    ENABLE_API_DOCS: bool | None = None

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def docs_enabled(self) -> bool:
        """API documentation (/docs, /redoc) is enabled unless in production without explicit opt-in."""
        if self.ENABLE_API_DOCS is not None:
            return self.ENABLE_API_DOCS
        return not self.is_production

    # CORS Configuration (Configurable development/production origins)
    BACKEND_CORS_ORIGINS: list[str] | str = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        origins: list[str] = []
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    origins = [str(item) for item in json.loads(v_str)]
                except Exception:
                    origins = [i.strip() for i in v_str.split(",") if i.strip()]
            else:
                origins = [i.strip() for i in v_str.split(",") if i.strip()]
        elif isinstance(v, list):
            origins = [str(item).strip() for item in v if str(item).strip()]

        # Strip trailing slashes so browser origin headers match exactly
        return [o.rstrip("/") for o in origins if o]

    # Database Configuration (PostgreSQL Async)
    DATABASE_URL: str | None = None
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "clinova"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    @property
    def async_database_uri(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            # Adapt standard cloud URLs (postgres://, postgresql://) to asyncpg driver
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # JWT & Security Configuration
    JWT_SECRET_KEY: str | None = None
    JWT_ALGORITHM: str = "HS256"
    SECRET_KEY: str = "temporary_dev_secret_key_change_in_production_32bytes"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @property
    def jwt_secret(self) -> str:
        """Resolve active JWT secret key with fallback to legacy SECRET_KEY."""
        return self.JWT_SECRET_KEY or self.SECRET_KEY

    @property
    def jwt_algorithm(self) -> str:
        """Resolve active JWT algorithm with fallback to legacy ALGORITHM."""
        return self.JWT_ALGORITHM or self.ALGORITHM

    # Medical Document Storage & OCR Configuration (Step 7)
    STORAGE_PROVIDER: str = "local"
    MEDICAL_DOCUMENT_MAX_SIZE_MB: int = 10
    MEDICAL_DOCUMENT_STORAGE_PATH: str = "./storage/medical_documents"
    DOCUMENT_PROCESSING_ENABLED: bool = True
    OCR_PROVIDER: str = "tesseract"
    OCR_DEFAULT_LANGUAGE: str = "eng"
    OCR_LANGUAGES: str = "eng,hin,mar"

    @model_validator(mode="after")
    def validate_production_security(self) -> Self:
        if self.is_production:
            if self.DEBUG:
                logger.warning("Disabling DEBUG mode because ENVIRONMENT is production.")
                self.DEBUG = False
            active_secret = self.JWT_SECRET_KEY or self.SECRET_KEY
            if not active_secret or active_secret == "temporary_dev_secret_key_change_in_production_32bytes":
                raise ValueError(
                    "CRITICAL SECURITY: In production environment, a secure JWT_SECRET_KEY "
                    "must be configured. The default development secret cannot be used."
                )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
