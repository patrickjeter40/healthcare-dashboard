"""Use UUID identities and creation metadata consistently across lookup tables."""

from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision = "20260929_06"
down_revision = "20260929_05"
branch_labels = None
depends_on = None

LOOKUPS = (("patient_statuses", "status", 20, False), ("blood_types", "blood_type", 3, True))


def upgrade():
    connection = op.get_bind()
    for table, field, _length, nullable in LOOKUPS:
        op.add_column(table, sa.Column("id", sa.Uuid(), nullable=True))
        op.add_column(
            table,
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        for code in connection.scalars(sa.text(f"SELECT code FROM {table}")).all():
            connection.execute(
                sa.text(f"UPDATE {table} SET id=:id WHERE code=:code"),
                {"id": uuid4(), "code": code},
            )
        op.drop_constraint(f"fk_patients_{field}_{table}", "patients", type_="foreignkey")
        op.drop_constraint(f"pk_{table}", table, type_="primary")
        op.create_unique_constraint(f"uq_{table}_code", table, ["code"])
        op.alter_column(table, "id", nullable=False)
        op.create_primary_key(f"pk_{table}", table, ["id"])
        op.add_column("patients", sa.Column(f"{field}_id", sa.Uuid(), nullable=True))
        connection.execute(
            sa.text(
                f"UPDATE patients SET {field}_id = {table}.id FROM {table} "
                f"WHERE patients.{field} = {table}.code"
            )
        )
        op.alter_column("patients", f"{field}_id", nullable=nullable)
        op.create_foreign_key(
            f"fk_patients_{field}_id_{table}", "patients", table, [f"{field}_id"], ["id"]
        )
        op.drop_column("patients", field)


def downgrade():
    connection = op.get_bind()
    for table, field, length, nullable in reversed(LOOKUPS):
        op.add_column("patients", sa.Column(field, sa.String(length), nullable=True))
        connection.execute(
            sa.text(
                f"UPDATE patients SET {field} = {table}.code FROM {table} "
                f"WHERE patients.{field}_id = {table}.id"
            )
        )
        op.alter_column("patients", field, nullable=nullable)
        op.drop_constraint(f"fk_patients_{field}_id_{table}", "patients", type_="foreignkey")
        op.drop_column("patients", f"{field}_id")
        op.drop_constraint(f"pk_{table}", table, type_="primary")
        op.drop_constraint(f"uq_{table}_code", table, type_="unique")
        op.create_primary_key(f"pk_{table}", table, ["code"])
        op.create_foreign_key(f"fk_patients_{field}_{table}", "patients", table, [field], ["code"])
        op.drop_column(table, "id")
        op.drop_column(table, "created_at")
