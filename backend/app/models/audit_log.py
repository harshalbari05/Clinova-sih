import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import JSONB_TYPE, UUID_TYPE, Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base):
    """Audit trail tracking security and data access actions across the platform."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    action: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )  # patient_login, consultation_created, document_uploaded, summary_confirmed, etc.
    entity_type: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    entity_id: Mapped[str | None] = mapped_column(
        String(255),
        index=True,
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB_TYPE,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="audit_logs",
    )
