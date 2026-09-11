import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.ai_session import AISession
    from app.models.alert import Alert
    from app.models.clinical_history import ClinicalHistory
    from app.models.consent import Consent
    from app.models.hospital import Hospital
    from app.models.medical_document import MedicalDocument
    from app.models.medication import Medication
    from app.models.patient import Patient
    from app.models.summary import Summary
    from app.models.timeline_event import TimelineEvent


class Consultation(Base, TimestampMixin):
    """Central consultation entity linking patient, hospital, and clinical events."""

    __tablename__ = "consultations"

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
    hospital_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE,
        ForeignKey("hospitals.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        default="initiated",
    )  # initiated, in_progress, completed, reviewed, cancelled
    chief_complaint: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    token_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="consultations",
    )
    hospital: Mapped["Hospital | None"] = relationship(
        "Hospital",
        back_populates="consultations",
    )
    clinical_history: Mapped["ClinicalHistory | None"] = relationship(
        "ClinicalHistory",
        back_populates="consultation",
        uselist=False,
        cascade="all, delete-orphan",
    )
    ai_sessions: Mapped[list["AISession"]] = relationship(
        "AISession",
        back_populates="consultation",
        cascade="all, delete-orphan",
    )
    summaries: Mapped[list["Summary"]] = relationship(
        "Summary",
        back_populates="consultation",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="consultation",
        cascade="all, delete-orphan",
    )
    medical_documents: Mapped[list["MedicalDocument"]] = relationship(
        "MedicalDocument",
        back_populates="consultation",
    )
    medications: Mapped[list["Medication"]] = relationship(
        "Medication",
        back_populates="consultation",
    )
    consents: Mapped[list["Consent"]] = relationship(
        "Consent",
        back_populates="consultation",
    )
    timeline_events: Mapped[list["TimelineEvent"]] = relationship(
        "TimelineEvent",
        back_populates="consultation",
    )
