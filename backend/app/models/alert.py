import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.consultation import Consultation
    from app.models.patient import Patient


class Alert(Base, TimestampMixin):
    """Red flag alert detected during history taking for physician decision support."""

    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        primary_key=True,
        default=uuid.uuid4,
    )
    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("consultations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    alert_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(50),
        default="medium",
        index=True,
        nullable=False,
    )  # low, medium, high, critical
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        String(50),
        default="AI",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        index=True,
        nullable=False,
    )  # active, acknowledged, resolved
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    consultation: Mapped["Consultation"] = relationship(
        "Consultation",
        back_populates="alerts",
    )
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="alerts",
    )
