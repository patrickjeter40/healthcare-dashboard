"""Create patients and related clinical tables.

Revision ID: 20260928_01
Revises:
"""

import sqlalchemy as sa

from alembic import op

revision = "20260928_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("email", sa.String(320)),
        sa.Column("phone", sa.String(40)),
        sa.Column("address_line_1", sa.String(200)),
        sa.Column("address_line_2", sa.String(200)),
        sa.Column("city", sa.String(100)),
        sa.Column("state", sa.String(100)),
        sa.Column("postal_code", sa.String(20)),
        sa.Column("blood_type", sa.String(3)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("last_visit_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("length(btrim(first_name)) > 0", name="first_name_not_blank"),
        sa.CheckConstraint("length(btrim(last_name)) > 0", name="last_name_not_blank"),
        sa.CheckConstraint("status IN ('active', 'inactive', 'discharged')", name="status_allowed"),
        sa.CheckConstraint(
            "blood_type IS NULL OR blood_type IN "
            "('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')",
            name="blood_type_allowed",
        ),
    )
    op.create_table(
        "patient_allergies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("allergen", sa.String(120), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("patient_id", "allergen", name="uq_patient_allergies_patient_allergen"),
        sa.CheckConstraint("length(btrim(allergen)) > 0", name="allergen_not_blank"),
    )
    op.create_index("ix_patient_allergies_patient_id", "patient_allergies", ["patient_id"])
    op.create_table(
        "patient_conditions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("condition", sa.String(120), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "patient_id", "condition", name="uq_patient_conditions_patient_condition"
        ),
        sa.CheckConstraint("length(btrim(condition)) > 0", name="condition_not_blank"),
    )
    op.create_index("ix_patient_conditions_patient_id", "patient_conditions", ["patient_id"])
    op.create_table(
        "patient_notes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("length(btrim(content)) > 0", name="content_not_blank"),
    )
    op.create_index("ix_patient_notes_patient_id", "patient_notes", ["patient_id"])
    op.create_index("ix_patient_notes_recorded_at", "patient_notes", ["recorded_at"])


def downgrade() -> None:
    op.drop_table("patient_notes")
    op.drop_table("patient_conditions")
    op.drop_table("patient_allergies")
    op.drop_table("patients")
