import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import UUID_TYPE, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.hospital import Hospital
    from app.models.user import User


class HospitalUser(Base, TimestampMixin):
    """Associates a User with a Hospital facility and grants hospital-specific roles."""

    __tablename__ = "hospital_users"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "hospital_id", name="uq_hospital_users_user_hospital"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="hospital_staff",
    )  # e.g., hospital_admin, hospital_staff, doctor

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="hospital_users",
    )
    hospital: Mapped["Hospital"] = relationship(
        "Hospital",
        back_populates="hospital_users",
    )
