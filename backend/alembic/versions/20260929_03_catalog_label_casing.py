"""Standardize catalog labels and consolidate casing-only duplicates.

Revision ID: 20260929_03
Revises: 20260929_02
"""

import sqlalchemy as sa

from alembic import op

revision = "20260929_03"
down_revision = "20260929_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    for catalog_name, join_name, field in (
        ("allergens", "patient_allergies", "allergen_id"),
        ("conditions", "patient_conditions", "condition_id"),
    ):
        catalog = sa.Table(catalog_name, sa.MetaData(), autoload_with=connection)
        associations = sa.Table(join_name, sa.MetaData(), autoload_with=connection)
        catalog.c.id.type = sa.Uuid()
        associations.c.patient_id.type = sa.Uuid()
        associations.c[field].type = sa.Uuid()
        groups = {}
        for row in connection.execute(sa.select(catalog)).mappings():
            name = " ".join(
                word.upper() if word.upper() in {"COPD", "GERD"} else word.title()
                for word in row["name"].split(" ")
            )
            groups.setdefault(name, []).append(row)
        for name, rows in groups.items():
            # Prefer an already-canonical ID, otherwise choose deterministically.
            rows.sort(key=lambda row: (row["name"] != name, str(row["id"])))
            survivor = rows[0]["id"]
            for duplicate in rows[1:]:
                patient_ids = connection.scalars(
                    sa.select(associations.c.patient_id).where(
                        associations.c[field] == duplicate["id"]
                    )
                ).all()
                for patient_id in patient_ids:
                    exists = connection.scalar(
                        sa.select(associations.c.patient_id).where(
                            associations.c.patient_id == patient_id,
                            associations.c[field] == survivor,
                        )
                    )
                    if exists is None:
                        connection.execute(
                            associations.insert().values(patient_id=patient_id, **{field: survivor})
                        )
                connection.execute(
                    associations.delete().where(associations.c[field] == duplicate["id"])
                )
                connection.execute(catalog.delete().where(catalog.c.id == duplicate["id"]))
            connection.execute(catalog.update().where(catalog.c.id == survivor).values(name=name))


def downgrade() -> None:
    # Casing cleanup does not change the schema. Original spelling/casing and
    # merged duplicate IDs cannot be recovered, so retain the cleaned data.
    pass
