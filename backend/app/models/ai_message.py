import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import UUID_TYPE, Base

if TYPE_CHECKING:
    from app.models.ai_session import AISession


class AIMessage(Base):
    """Stores conversation turns between the patient and the AI history-taking engine."""

    __tablename__ = "ai_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        primary_key=True,
        default=uuid.uuid4,
    )
    ai_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("ai_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sender: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # ai, patient, system
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    message_type: Mapped[str] = mapped_column(
        String(50),
        default="text",
        nullable=False,
    )  # text, voice_transcript, structured_answer
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    ai_session: Mapped["AISession"] = relationship(
        "AISession",
        back_populates="messages",
    )
