"""Enforce trimmed, case-insensitively unique catalog names.

Revision ID: 20260929_04
Revises: 20260929_03
"""

import sqlalchemy as sa

from alembic import op

revision = "20260929_04"
down_revision = "20260929_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table_name in ("allergens", "conditions"):
        # The previous revision merged casing-only duplicates. Any new normalized
        # duplicates introduced by direct SQL cause this migration to roll back
        # rather than guessing which reference ID to remove.
        op.create_index(
            f"uq_{table_name}_normalized_name",
            table_name,
            [sa.text("lower(btrim(name))")],
            unique=True,
        )
        catalog = sa.table(table_name, sa.column("name", sa.String(120)))
        op.execute(catalog.update().values(name=sa.func.btrim(catalog.c.name)))
        op.create_check_constraint(
            op.f(f"ck_{table_name}_name_trimmed"), table_name, "name = btrim(name)"
        )


def downgrade() -> None:
    for table_name in ("conditions", "allergens"):
        op.drop_constraint(op.f(f"ck_{table_name}_name_trimmed"), table_name, type_="check")
        op.drop_index(f"uq_{table_name}_normalized_name", table_name=table_name)
    # Trimming is retained; IDs and patient associations were never changed.
