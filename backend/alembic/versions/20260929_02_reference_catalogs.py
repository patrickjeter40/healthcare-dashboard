"""Preserve free-text selections as reference catalogs and composite-key associations.

Revision ID: 20260929_02
Revises: 20260928_01
"""

from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision = "20260929_02"
down_revision = "20260928_01"
branch_labels = None
depends_on = None

PAIRS = (
    ("allergens", "patient_allergies", "allergen"),
    ("conditions", "patient_conditions", "condition"),
)


def upgrade() -> None:
    connection = op.get_bind()
    for catalog_name, join_name, field in PAIRS:
        catalog = op.create_table(
            catalog_name,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.UniqueConstraint("name"),
            sa.CheckConstraint("length(btrim(name)) > 0", name="name_not_blank"),
        )
        legacy = sa.Table(join_name, sa.MetaData(), autoload_with=connection)
        legacy.c.patient_id.type = sa.Uuid()
        # Exact matches only: preserve case variants and misspellings without
        # guessing whether they represent the same clinical concept.
        rows = connection.execute(sa.select(legacy)).mappings().all()
        identifiers = {}
        for row in rows:
            name = row[field]
            if name not in identifiers:
                identifiers[name] = uuid4()
                connection.execute(
                    catalog.insert().values(
                        id=identifiers[name], name=name, created_at=row["created_at"]
                    )
                )
        # PostgreSQL transactional DDL protects the buffered selections.
        op.drop_table(join_name)
        associations = op.create_table(
            join_name,
            sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), primary_key=True),
            sa.Column(
                f"{field}_id", sa.Uuid(), sa.ForeignKey(f"{catalog_name}.id"), primary_key=True
            ),
            sa.PrimaryKeyConstraint("patient_id", f"{field}_id", name=f"pk_{join_name}"),
        )
        if rows:
            connection.execute(
                associations.insert(),
                [
                    {"patient_id": patient_id, f"{field}_id": catalog_id}
                    for patient_id, catalog_id in {
                        (row["patient_id"], identifiers[row[field]]) for row in rows
                    }
                ],
            )


def downgrade() -> None:
    connection = op.get_bind()
    for catalog_name, join_name, field in reversed(PAIRS):
        catalog = sa.Table(catalog_name, sa.MetaData(), autoload_with=connection)
        associations = sa.Table(join_name, sa.MetaData(), autoload_with=connection)
        catalog.c.id.type = sa.Uuid()
        associations.c.patient_id.type = sa.Uuid()
        associations.c[f"{field}_id"].type = sa.Uuid()
        rows = connection.execute(
            sa.select(associations.c.patient_id, catalog.c.name).join(
                catalog, associations.c[f"{field}_id"] == catalog.c.id
            )
        ).all()
        op.drop_table(join_name)
        legacy = op.create_table(
            join_name,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False),
            sa.Column(field, sa.String(120), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.UniqueConstraint("patient_id", field, name=f"uq_{join_name}_patient_{field}"),
            sa.CheckConstraint(f"length(btrim({field})) > 0", name=f"{field}_not_blank"),
        )
        if rows:
            connection.execute(
                legacy.insert(),
                [{"id": uuid4(), "patient_id": row.patient_id, field: row.name} for row in rows],
            )
        op.create_index(f"ix_{join_name}_patient_id", join_name, ["patient_id"])
        op.drop_table(catalog_name)
