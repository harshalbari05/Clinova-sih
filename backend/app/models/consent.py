import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.consultation import Consultation
    from app.models.patient import Patient


class Consent(Base, TimestampMixin):
    """Patient consent tracking for clinical history taking, AI processing, and document sharing."""

    __tablename__ = "consents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        primary_key=True,
        default=uuid.uuid4,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    consultation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE,
        ForeignKey("consultations.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    consent_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # clinical_history, document_processing, AI_processing, health_record_sharing, ABDM
    granted: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    version: Mapped[str] = mapped_column(
        String(50),
        default="v1.0",
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="consents",
    )
    consultation: Mapped["Consultation | None"] = relationship(
        "Consultation",
        back_populates="consents",
    )
