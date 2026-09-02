import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient


class Allergy(Base, TimestampMixin):
    """Patient allergy and adverse reaction records."""

    __tablename__ = "allergies"

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
    allergen: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    reaction: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    severity: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )  # mild, moderate, severe
    source: Mapped[str] = mapped_column(
        String(50),
        default="patient",
        nullable=False,
    )  # patient, document, AI, doctor

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="allergies",
    )
