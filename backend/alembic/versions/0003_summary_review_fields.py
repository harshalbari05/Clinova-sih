"""Add physician review and auditability fields to summaries table for Step 9

Revision ID: 0003_summary_review_fields
Revises: 0002_timeline_events
Create Date: 2026-09-06 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_summary_review_fields"
down_revision: str | None = "0002_timeline_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("summaries", sa.Column("reviewed_by_id", sa.UUID(), nullable=True))
    op.add_column(
        "summaries",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("summaries", sa.Column("clinician_notes", sa.Text(), nullable=True))
    op.add_column("summaries", sa.Column("rejection_reason", sa.Text(), nullable=True))
    op.add_column("summaries", sa.Column("ai_draft_text", sa.Text(), nullable=True))

    op.create_foreign_key(
        "fk_summaries_reviewed_by_id_users",
        "summaries",
        "users",
        ["reviewed_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_summaries_reviewed_by_id"),
        "summaries",
        ["reviewed_by_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_summaries_reviewed_by_id"), table_name="summaries")
    op.drop_constraint(
        "fk_summaries_reviewed_by_id_users", "summaries", type_="foreignkey"
    )
    op.drop_column("summaries", "ai_draft_text")
    op.drop_column("summaries", "rejection_reason")
    op.drop_column("summaries", "clinician_notes")
    op.drop_column("summaries", "reviewed_at")
    op.drop_column("summaries", "reviewed_by_id")
