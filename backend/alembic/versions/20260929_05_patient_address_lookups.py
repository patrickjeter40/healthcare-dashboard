"""Separate patient addresses and introduce status/blood type lookups."""

from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision = "20260929_05"
down_revision = "20260929_04"
branch_labels = None
depends_on = None

ADDRESS_FIELDS = {
    "address_line_1": 200,
    "address_line_2": 200,
    "city": 100,
    "state": 100,
    "postal_code": 20,
}


def upgrade():
    statuses = op.create_table(
        "patient_statuses",
        sa.Column("code", sa.String(20), primary_key=True),
        sa.Column("name", sa.String(40), nullable=False, unique=True),
    )
    blood_types = op.create_table("blood_types", sa.Column("code", sa.String(3), primary_key=True))
    op.bulk_insert(
        statuses,
        [{"code": code, "name": code.title()} for code in ("active", "inactive", "discharged")],
    )
    op.bulk_insert(
        blood_types, [{"code": code} for code in ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")]
    )
    addresses = op.create_table(
        "addresses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False, unique=True
        ),
        *(sa.Column(field, sa.String(length)) for field, length in ADDRESS_FIELDS.items()),
    )
    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id, " + ", ".join(ADDRESS_FIELDS) + " FROM patients")
    ).mappings()
    for row in rows:
        values = {field: row[field] for field in ADDRESS_FIELDS}
        if any(value is not None for value in values.values()):
            connection.execute(
                addresses.insert().values(id=uuid4(), patient_id=row["id"], **values)
            )
    op.drop_constraint(op.f("ck_patients_status_allowed"), "patients", type_="check")
    op.drop_constraint(op.f("ck_patients_blood_type_allowed"), "patients", type_="check")
    op.create_foreign_key(
        "fk_patients_status_patient_statuses", "patients", "patient_statuses", ["status"], ["code"]
    )
    op.create_foreign_key(
        "fk_patients_blood_type_blood_types", "patients", "blood_types", ["blood_type"], ["code"]
    )
    for field in ADDRESS_FIELDS:
        op.drop_column("patients", field)


def downgrade():
    for field, length in ADDRESS_FIELDS.items():
        op.add_column("patients", sa.Column(field, sa.String(length)))
    op.execute(
        sa.text(
            "UPDATE patients SET "
            + ", ".join(f"{field} = addresses.{field}" for field in ADDRESS_FIELDS)
            + " FROM addresses WHERE patients.id = addresses.patient_id"
        )
    )
    op.drop_constraint("fk_patients_status_patient_statuses", "patients", type_="foreignkey")
    op.drop_constraint("fk_patients_blood_type_blood_types", "patients", type_="foreignkey")
    op.create_check_constraint(
        "status_allowed", "patients", "status IN ('active', 'inactive', 'discharged')"
    )
    op.create_check_constraint(
        "blood_type_allowed",
        "patients",
        "blood_type IS NULL OR blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')",
    )
    op.drop_table("addresses")
    op.drop_table("blood_types")
    op.drop_table("patient_statuses")
