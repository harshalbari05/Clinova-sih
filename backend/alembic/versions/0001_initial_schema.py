"""Initial Clinova PostgreSQL Database Schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-02 16:47:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column(
            "role", sa.String(length=50), nullable=False, server_default="patient"
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_phone"), "users", ["phone"], unique=True)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    # 2. patients
    op.create_table(
        "patients",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(length=50), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("abha_id", sa.String(length=100), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("emergency_contact", sa.String(length=255), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_patients_user_id"), "patients", ["user_id"], unique=True)
    op.create_index(op.f("ix_patients_abha_id"), "patients", ["abha_id"], unique=True)

    # 3. hospitals
    op.create_table(
        "hospitals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("registration_number", sa.String(length=100), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("pincode", sa.String(length=20), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_hospitals_registration_number"),
        "hospitals",
        ["registration_number"],
        unique=True,
    )
    op.create_index(op.f("ix_hospitals_email"), "hospitals", ["email"], unique=False)
    op.create_index(op.f("ix_hospitals_city"), "hospitals", ["city"], unique=False)

    # 4. hospital_users
    op.create_table(
        "hospital_users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("hospital_id", sa.UUID(), nullable=False),
        sa.Column(
            "role",
            sa.String(length=50),
            nullable=False,
            server_default="hospital_staff",
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
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "hospital_id", name="uq_hospital_users_user_hospital"
        ),
    )
    op.create_index(
        op.f("ix_hospital_users_hospital_id"),
        "hospital_users",
        ["hospital_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_hospital_users_user_id"), "hospital_users", ["user_id"], unique=False
    )

    # 5. consultations
    op.create_table(
        "consultations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("hospital_id", sa.UUID(), nullable=False),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="initiated"
        ),
        sa.Column("chief_complaint", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_consultations_hospital_id"),
        "consultations",
        ["hospital_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_consultations_patient_id"),
        "consultations",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_consultations_status"), "consultations", ["status"], unique=False
    )

    # 6. clinical_histories
    op.create_table(
        "clinical_histories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("consultation_id", sa.UUID(), nullable=False),
        sa.Column("chief_complaint", sa.Text(), nullable=True),
        sa.Column("history_of_present_illness", sa.Text(), nullable=True),
        sa.Column("past_medical_history", sa.Text(), nullable=True),
        sa.Column("past_surgical_history", sa.Text(), nullable=True),
        sa.Column("drug_history", sa.Text(), nullable=True),
        sa.Column("allergy_history", sa.Text(), nullable=True),
        sa.Column("family_history", sa.Text(), nullable=True),
        sa.Column("personal_history", sa.Text(), nullable=True),
        sa.Column("review_of_systems", sa.Text(), nullable=True),
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
            ["consultation_id"], ["consultations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_clinical_histories_consultation_id"),
        "clinical_histories",
        ["consultation_id"],
        unique=True,
    )

    # 7. ai_sessions
    op.create_table(
        "ai_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("consultation_id", sa.UUID(), nullable=False),
        sa.Column(
            "language", sa.String(length=50), nullable=False, server_default="English"
        ),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="initiated"
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
            ["consultation_id"], ["consultations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ai_sessions_consultation_id"),
        "ai_sessions",
        ["consultation_id"],
        unique=False,
    )

    # 8. ai_messages
    op.create_table(
        "ai_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ai_session_id", sa.UUID(), nullable=False),
        sa.Column("sender", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "message_type", sa.String(length=50), nullable=False, server_default="text"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["ai_session_id"], ["ai_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ai_messages_ai_session_id"),
        "ai_messages",
        ["ai_session_id"],
        unique=False,
    )

    # 9. medical_documents
    op.create_table(
        "medical_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("consultation_id", sa.UUID(), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column(
            "ocr_status", sa.String(length=50), nullable=False, server_default="pending"
        ),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
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
            ["consultation_id"], ["consultations.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_medical_documents_consultation_id"),
        "medical_documents",
        ["consultation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_medical_documents_patient_id"),
        "medical_documents",
        ["patient_id"],
        unique=False,
    )

    # 10. extracted_data
    op.create_table(
        "extracted_data",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("raw_ocr_text", sa.Text(), nullable=True),
        sa.Column(
            "extracted_json",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=True,
        ),
        sa.Column(
            "extraction_status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=True),
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
            ["document_id"], ["medical_documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_extracted_data_document_id"),
        "extracted_data",
        ["document_id"],
        unique=True,
    )

    # 11. medications
    op.create_table(
        "medications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("consultation_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("dosage", sa.String(length=100), nullable=True),
        sa.Column("frequency", sa.String(length=100), nullable=True),
        sa.Column("route", sa.String(length=100), nullable=True),
        sa.Column("duration", sa.String(length=100), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "source", sa.String(length=50), nullable=False, server_default="patient"
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
            ["consultation_id"], ["consultations.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_medications_consultation_id"),
        "medications",
        ["consultation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_medications_patient_id"), "medications", ["patient_id"], unique=False
    )

    # 12. allergies
    op.create_table(
        "allergies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("allergen", sa.String(length=255), nullable=False),
        sa.Column("reaction", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=50), nullable=True),
        sa.Column(
            "source", sa.String(length=50), nullable=False, server_default="patient"
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
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_allergies_patient_id"), "allergies", ["patient_id"], unique=False
    )

    # 13. summaries
    op.create_table(
        "summaries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("consultation_id", sa.UUID(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column(
            "structured_summary",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=True,
        ),
        sa.Column(
            "generated_by", sa.String(length=100), nullable=False, server_default="AI"
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="draft"
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
            ["consultation_id"], ["consultations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_summaries_consultation_id"),
        "summaries",
        ["consultation_id"],
        unique=False,
    )

    # 14. alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("consultation_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("alert_type", sa.String(length=100), nullable=False),
        sa.Column(
            "severity", sa.String(length=50), nullable=False, server_default="medium"
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="AI"),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="active"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["consultation_id"], ["consultations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_alerts_consultation_id"), "alerts", ["consultation_id"], unique=False
    )
    op.create_index(
        op.f("ix_alerts_patient_id"), "alerts", ["patient_id"], unique=False
    )
    op.create_index(op.f("ix_alerts_severity"), "alerts", ["severity"], unique=False)
    op.create_index(op.f("ix_alerts_status"), "alerts", ["status"], unique=False)

    # 15. consents
    op.create_table(
        "consents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("consultation_id", sa.UUID(), nullable=True),
        sa.Column("consent_type", sa.String(length=100), nullable=False),
        sa.Column(
            "granted", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "version", sa.String(length=50), nullable=False, server_default="v1.0"
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
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
            ["consultation_id"], ["consultations.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_consents_consultation_id"),
        "consents",
        ["consultation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_consents_patient_id"), "consents", ["patient_id"], unique=False
    )

    # 16. audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("consents")
    op.drop_table("alerts")
    op.drop_table("summaries")
    op.drop_table("allergies")
    op.drop_table("medications")
    op.drop_table("extracted_data")
    op.drop_table("medical_documents")
    op.drop_table("ai_messages")
    op.drop_table("ai_sessions")
    op.drop_table("clinical_histories")
    op.drop_table("consultations")
    op.drop_table("hospital_users")
    op.drop_table("hospitals")
    op.drop_table("patients")
    op.drop_table("users")
