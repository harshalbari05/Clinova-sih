import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import JSONB_TYPE, UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.medical_document import MedicalDocument


class ExtractedData(Base, TimestampMixin):
    """OCR and AI-extracted clinical information structured as JSONB."""

    __tablename__ = "extracted_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("medical_documents.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    raw_ocr_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    extracted_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB_TYPE,
        nullable=True,
    )
    extraction_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )  # pending, completed, failed
    extracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    document: Mapped["MedicalDocument"] = relationship(
        "MedicalDocument",
        back_populates="extracted_data",
    )
