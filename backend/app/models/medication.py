import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.consultation import Consultation
    from app.models.patient import Patient


class Medication(Base, TimestampMixin):
    """Patient medication record, sourced from patient report, document OCR, AI, or physician."""

    __tablename__ = "medications"

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
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    dosage: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    frequency: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    route: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    duration: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    source: Mapped[str] = mapped_column(
        String(50),
        default="patient",
        nullable=False,
    )  # patient, document, AI, doctor

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="medications",
    )
    consultation: Mapped["Consultation | None"] = relationship(
        "Consultation",
        back_populates="medications",
    )
