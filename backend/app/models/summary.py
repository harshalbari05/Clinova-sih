import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import JSONB_TYPE, UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.consultation import Consultation


class Summary(Base, TimestampMixin):
    """Physician-ready summary generated from consultation history taking."""

    __tablename__ = "summaries"

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
    summary_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    structured_summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB_TYPE,
        nullable=True,
    )
    generated_by: Mapped[str] = mapped_column(
        String(100),
        default="AI",
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        nullable=False,
    )  # draft, confirmed, rejected

    # Relationships
    consultation: Mapped["Consultation"] = relationship(
        "Consultation",
        back_populates="summaries",
    )
