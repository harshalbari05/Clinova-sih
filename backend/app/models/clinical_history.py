import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.consultation import Consultation


class ClinicalHistory(Base, TimestampMixin):
    """Clinical history record captured during history taking, linked 1-to-1 with a consultation."""

    __tablename__ = "clinical_histories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        primary_key=True,
        default=uuid.uuid4,
    )
    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("consultations.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    chief_complaint: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    history_of_present_illness: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    past_medical_history: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    past_surgical_history: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    drug_history: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    allergy_history: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    family_history: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    personal_history: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    review_of_systems: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    consultation: Mapped["Consultation"] = relationship(
        "Consultation",
        back_populates="clinical_history",
    )
