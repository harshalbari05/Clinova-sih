import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import JSONB_TYPE, UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.consultation import Consultation
    from app.models.user import User


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

    # Step 9: Physician Review and Auditability Fields
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    clinician_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    ai_draft_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    consultation: Mapped["Consultation"] = relationship(
        "Consultation",
        back_populates="summaries",
    )
    reviewed_by: Mapped["User | None"] = relationship(
        "User",
    )
