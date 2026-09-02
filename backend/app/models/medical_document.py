import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.consultation import Consultation
    from app.models.extracted_data import ExtractedData
    from app.models.patient import Patient


class MedicalDocument(Base, TimestampMixin):
    """References patient-uploaded medical records, reports, prescriptions, and scans."""

    __tablename__ = "medical_documents"

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
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # prescription, lab_report, discharge_summary, medical_report, other
    document_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    mime_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    ocr_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )  # pending, processing, completed, failed
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="medical_documents",
    )
    consultation: Mapped["Consultation | None"] = relationship(
        "Consultation",
        back_populates="medical_documents",
    )
    extracted_data: Mapped["ExtractedData | None"] = relationship(
        "ExtractedData",
        back_populates="document",
        uselist=False,
        cascade="all, delete-orphan",
    )
