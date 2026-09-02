import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.consultation import Consultation
    from app.models.hospital_user import HospitalUser


class Hospital(Base, TimestampMixin):
    """Hospital facility record."""

    __tablename__ = "hospitals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    registration_number: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        index=True,
        nullable=True,
    )
    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    city: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )
    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    pincode: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Relationships
    hospital_users: Mapped[list["HospitalUser"]] = relationship(
        "HospitalUser",
        back_populates="hospital",
        cascade="all, delete-orphan",
    )
    consultations: Mapped[list["Consultation"]] = relationship(
        "Consultation",
        back_populates="hospital",
        cascade="all, delete-orphan",
    )
