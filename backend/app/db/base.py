from datetime import datetime

from sqlalchemy import JSON, DateTime, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy Declarative Base for Clinova data persistence layer."""


# Cross-dialect portable types for seamless PostgreSQL production and SQLite testing
JSONB_TYPE = JSONB().with_variant(JSON, "sqlite")
UUID_TYPE = PG_UUID(as_uuid=True).with_variant(Uuid(as_uuid=True), "sqlite")


class TimestampMixin:
    """Reusable mixin providing standardized created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
