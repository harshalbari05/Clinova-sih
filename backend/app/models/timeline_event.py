"""TimelineEvent SQLAlchemy database model for Clinova Step 8: Medical Timeline.

Represents a single, normalized, source-backed clinical occurrence in a patient's
medical history. Preserves exact provenance, supporting evidence, and date precision
without making diagnostic deductions.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import JSONB_TYPE, UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.consultation import Consultation
    from app.models.medical_document import MedicalDocument
    from app.models.patient import Patient


class TimelineEvent(Base, TimestampMixin):
    """Normalized, source-backed timeline event for a patient."""

    __tablename__ = "timeline_events"

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
    medical_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE,
        ForeignKey("medical_documents.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    # Event classification
    event_type: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )  # e.g., CONSULTATION, SYMPTOM, DIAGNOSIS_DOCUMENTED, LAB_TEST, LAB_RESULT,
    # IMAGING, PROCEDURE, SURGERY, HOSPITAL_ADMISSION, HOSPITAL_DISCHARGE,
    # MEDICATION, ALLERGY, MEDICAL_HISTORY, FOLLOW_UP, OTHER

    # Human-readable summary
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Date handling with strict precision
    event_date: Mapped[date | None] = mapped_column(
        Date,
        index=True,
        nullable=True,
    )
    date_precision: Mapped[str] = mapped_column(
        String(50),
        default="EXACT",
        nullable=False,
    )  # EXACT, MONTH, YEAR, APPROXIMATE, UNKNOWN

    # Provenance & source tracking
    source_type: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )  # PATIENT_HISTORY, AI_INTERVIEW, MEDICAL_DOCUMENT, OCR_EXTRACTION, CONSULTATION, CLINICIAN_ENTERED
    source_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    evidence: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    source_page: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Clinical verification status (ready for Step 9 physician review)
    verification_status: Mapped[str] = mapped_column(
        String(50),
        default="SOURCE_CONFIRMED",
        nullable=False,
    )  # UNVERIFIED, SOURCE_CONFIRMED, CLINICIAN_VERIFIED

    # Optional metadata (e.g., test units, reference ranges, abnormal flags)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB_TYPE,
        nullable=True,
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="timeline_events",
    )
    consultation: Mapped["Consultation | None"] = relationship(
        "Consultation",
        back_populates="timeline_events",
    )
    medical_document: Mapped["MedicalDocument | None"] = relationship(
        "MedicalDocument",
        back_populates="timeline_events",
    )
