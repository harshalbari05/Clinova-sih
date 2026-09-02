import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.ai_message import AIMessage
    from app.models.consultation import Consultation


class AISession(Base, TimestampMixin):
    """AI clinical history-taking session associated with a consultation."""

    __tablename__ = "ai_sessions"

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
    language: Mapped[str] = mapped_column(
        String(50),
        default="English",
        nullable=False,
    )  # e.g., English, Hindi, Marathi
    status: Mapped[str] = mapped_column(
        String(50),
        default="initiated",
        nullable=False,
    )  # initiated, in_progress, completed, failed
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    consultation: Mapped["Consultation"] = relationship(
        "Consultation",
        back_populates="ai_sessions",
    )
    messages: Mapped[list["AIMessage"]] = relationship(
        "AIMessage",
        back_populates="ai_session",
        cascade="all, delete-orphan",
    )
