"""Make consultation hospital_id nullable for pre-hospital patient intake

Revision ID: 0004_consultation_hospital_nullable
Revises: 0003_summary_review_fields
Create Date: 2026-09-11 19:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_consultation_hospital_nullable"
down_revision: str | None = "0003_summary_review_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "consultations",
        "hospital_id",
        existing_type=sa.UUID(),
        nullable=True,
    )
    op.add_column(
        "consultations",
        sa.Column("department", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "consultations",
        sa.Column("token_number", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("consultations", "token_number")
    op.drop_column("consultations", "department")
    op.alter_column(
        "consultations",
        "hospital_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
