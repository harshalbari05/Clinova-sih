import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.allergy import Allergy
    from app.models.consent import Consent
    from app.models.consultation import Consultation
    from app.models.medical_document import MedicalDocument
    from app.models.medication import Medication
    from app.models.user import User


class Patient(Base, TimestampMixin):
    """Patient demographic profile corresponding 1-to-1 with a User identity."""

    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    gender: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    abha_id: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=True,
    )
    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    emergency_contact: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="patient",
    )
    consultations: Mapped[list["Consultation"]] = relationship(
        "Consultation",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    medical_documents: Mapped[list["MedicalDocument"]] = relationship(
        "MedicalDocument",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    medications: Mapped[list["Medication"]] = relationship(
        "Medication",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    allergies: Mapped[list["Allergy"]] = relationship(
        "Allergy",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    consents: Mapped[list["Consent"]] = relationship(
        "Consent",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
