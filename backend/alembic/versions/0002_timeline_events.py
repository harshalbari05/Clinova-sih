"""Create timeline_events table for Step 8: Medical Timeline

Revision ID: 0002_timeline_events
Revises: 0001_initial_schema
Create Date: 2026-09-06 09:38:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_timeline_events"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "timeline_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("consultation_id", sa.UUID(), nullable=True),
        sa.Column("medical_document_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column(
            "date_precision",
            sa.String(length=50),
            nullable=False,
            server_default="EXACT",
        ),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column(
            "verification_status",
            sa.String(length=50),
            nullable=False,
            server_default="SOURCE_CONFIRMED",
        ),
        sa.Column(
            "metadata_",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"], ["patients.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["consultation_id"], ["consultations.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["medical_document_id"],
            ["medical_documents.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_timeline_events_patient_id"),
        "timeline_events",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_timeline_events_consultation_id"),
        "timeline_events",
        ["consultation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_timeline_events_medical_document_id"),
        "timeline_events",
        ["medical_document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_timeline_events_event_type"),
        "timeline_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_timeline_events_event_date"),
        "timeline_events",
        ["event_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_timeline_events_source_type"),
        "timeline_events",
        ["source_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_timeline_events_source_type"), table_name="timeline_events"
    )
    op.drop_index(
        op.f("ix_timeline_events_event_date"), table_name="timeline_events"
    )
    op.drop_index(
        op.f("ix_timeline_events_event_type"), table_name="timeline_events"
    )
    op.drop_index(
        op.f("ix_timeline_events_medical_document_id"),
        table_name="timeline_events",
    )
    op.drop_index(
        op.f("ix_timeline_events_consultation_id"),
        table_name="timeline_events",
    )
    op.drop_index(
        op.f("ix_timeline_events_patient_id"), table_name="timeline_events"
    )
    op.drop_table("timeline_events")
