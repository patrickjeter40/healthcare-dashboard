"""Exercise the actual Alembic revisions against populated legacy tables."""

import importlib.util
import os
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def load_revision(name):
    path = Path(__file__).parents[1] / "alembic" / "versions" / name
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_upgrade_preserves_legacy_and_deleted_selections_and_downgrade():
    engine = sa.create_engine("sqlite://")

    @sa.event.listens_for(engine, "connect")
    def configure(connection, _record):
        connection.create_function("btrim", 1, lambda value: value.strip(" "), deterministic=True)
        connection.execute("PRAGMA foreign_keys=ON")

    @sa.event.listens_for(sa.Table, "column_reflect")
    def reflect_uuid(_inspector, _table, column):
        if column["name"] == "id" or column["name"].endswith("_id"):
            column["type"] = sa.Uuid()

    initial = load_revision("20260928_01_patient_schema.py")
    revision = load_revision("20260929_02_reference_catalogs.py")
    with engine.begin() as connection:
        operations = Operations(MigrationContext.configure(connection))
        initial.op = operations
        revision.op = operations
        initial.upgrade()
        metadata = sa.MetaData()
        metadata.reflect(connection)
        patients = metadata.tables["patients"]
        active, deleted = uuid4(), uuid4()
        connection.execute(
            patients.insert(),
            [
                {
                    "id": identifier,
                    "first_name": "Fictional",
                    "last_name": "Migration",
                    "date_of_birth": date(1980, 1, 1),
                    "status": "active",
                    "deleted_at": deleted_at,
                }
                for identifier, deleted_at in (
                    (active, None),
                    (deleted, datetime.now(timezone.utc)),
                )
            ],
        )
        expected = {}
        for table, field in (
            ("patient_allergies", "allergen"),
            ("patient_conditions", "condition"),
        ):
            names = (
                ["Penicillin", "penicillin", "Penicilin"]
                if field == "allergen"
                else ["Asthma", "asthma", "Legacy condition"]
            )
            pairs = [
                (active, names[0]),
                (deleted, names[0]),
                (active, names[1]),
                (deleted, names[2]),
            ]
            expected[table] = set(pairs)
            connection.execute(
                metadata.tables[table].insert(),
                [
                    {"id": uuid4(), "patient_id": patient_id, field: name}
                    for patient_id, name in pairs
                ],
            )
        revision.upgrade()
        metadata = sa.MetaData()
        metadata.reflect(connection)
        for table, catalog, field in (
            ("patient_allergies", "allergens", "allergen"),
            ("patient_conditions", "conditions", "condition"),
        ):
            join = metadata.tables[table]
            reference = metadata.tables[catalog]
            actual = connection.execute(
                sa.select(join.c.patient_id, reference.c.name).join(
                    reference, join.c[f"{field}_id"] == reference.c.id
                )
            ).all()
            assert set(actual) == expected[table]
            assert connection.scalar(sa.select(sa.func.count()).select_from(reference)) == 3
            assert list(join.c.keys()) == ["patient_id", f"{field}_id"]
            assert set(join.primary_key.columns.keys()) == {"patient_id", f"{field}_id"}
        revision.downgrade()
        metadata = sa.MetaData()
        metadata.reflect(connection)
        for table, field in (
            ("patient_allergies", "allergen"),
            ("patient_conditions", "condition"),
        ):
            legacy = metadata.tables[table]
            assert (
                set(connection.execute(sa.select(legacy.c.patient_id, legacy.c[field])).all())
                == expected[table]
            )
    sa.event.remove(sa.Table, "column_reflect", reflect_uuid)
    engine.dispose()


@pytest.mark.parametrize(
    "catalog_name,join_name,field,canonical",
    [
        ("allergens", "patient_allergies", "allergen_id", "Penicillin"),
        ("conditions", "patient_conditions", "condition_id", "Asthma"),
    ],
)
def test_casing_cleanup_preserves_active_and_deleted_selections(
    client, catalog_name, join_name, field, canonical
):
    from app.database import get_db
    from app.main import app
    from app.models import Allergen, Condition

    model = Allergen if catalog_name == "allergens" else Condition
    payload = {
        "first_name": "Fictional",
        "last_name": "Casing",
        "date_of_birth": "1980-01-01",
        "status": "active",
    }
    active = client.post("/patients", json=payload).json()["id"]
    deleted = client.post("/patients", json=payload).json()["id"]
    client.delete(f"/patients/{deleted}")
    from uuid import UUID

    with next(app.dependency_overrides[get_db]()) as db:
        # This regression exercises the pre-04 schema where casing duplicates were legal.
        for table_name in ("allergens", "conditions"):
            db.execute(sa.text(f"DROP INDEX uq_{table_name}_normalized_name"))
        survivor = db.scalar(sa.select(model).where(model.name == canonical))
        survivor_id = survivor.id
        duplicate = model(name=canonical.lower())
        mixed = model(name=canonical.upper())
        legacy = model(name="legacy label")
        db.add_all([duplicate, mixed, legacy])
        db.flush()
        join = sa.Table(join_name, sa.MetaData(), autoload_with=db.connection())
        join.c.patient_id.type = sa.Uuid()
        join.c[field].type = sa.Uuid()
        db.execute(
            join.insert(),
            [
                {"patient_id": UUID(active), field: survivor.id},
                {"patient_id": UUID(active), field: duplicate.id},
                {"patient_id": UUID(deleted), field: mixed.id},
            ],
        )
        db.commit()
        revision = load_revision("20260929_03_catalog_label_casing.py")
        revision.op = Operations(MigrationContext.configure(db.connection()))
        revision.upgrade()
        db.commit()
        selections = set(db.execute(sa.select(join.c.patient_id, join.c[field])).all())
        assert selections == {(UUID(active), survivor_id), (UUID(deleted), survivor_id)}
        db.expire_all()
        assert db.get(model, survivor_id).name == canonical
        names = list(db.scalars(sa.select(model.name)))
        assert "Legacy Label" in names
        assert canonical.lower() not in names
        assert canonical.upper() not in names
        if model is Condition:
            assert "COPD" in names and "GERD" in names
        revision.downgrade()
        db.commit()
    response = client.get(f"/patients/{active}")
    assert response.status_code == 200
    attribute = "allergies" if catalog_name == "allergens" else "conditions"
    assert response.json()[attribute] == [{"id": str(survivor_id), "name": canonical}]
    references = client.get(f"/{catalog_name}").json()
    assert next(item for item in references if item["id"] == str(survivor_id))["name"] == canonical


@pytest.mark.skipif(os.environ.get("TEST_POSTGRES_MIGRATIONS") != "1", reason="Requires PostgreSQL")
def test_postgres_catalog_integrity_upgrade_and_downgrade():
    from app.database import Base, engine

    # Everything, including the temporary schema, rolls back after the test.
    # Search path isolates these revisions from the application tables.
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            schema = f"migration_test_{uuid4().hex}"
            connection.exec_driver_sql(f"CREATE SCHEMA {schema}")
            connection.exec_driver_sql(f"SET LOCAL search_path TO {schema}")
            operations = Operations(
                MigrationContext.configure(connection, opts={"target_metadata": Base.metadata})
            )
            for filename in (
                "20260928_01_patient_schema.py",
                "20260929_02_reference_catalogs.py",
                "20260929_03_catalog_label_casing.py",
            ):
                revision = load_revision(filename)
                revision.op = operations
                revision.upgrade()
            metadata = sa.MetaData()
            metadata.reflect(connection)
            patient_id = uuid4()
            connection.execute(
                metadata.tables["patients"]
                .insert()
                .values(
                    id=patient_id,
                    first_name="Fictional",
                    last_name="Integrity",
                    date_of_birth=date(1980, 1, 1),
                    status="active",
                    deleted_at=datetime.now(timezone.utc),
                )
            )
            references = []
            for catalog_name, join_name, field, name in (
                ("allergens", "patient_allergies", "allergen_id", "Penicillin"),
                ("conditions", "patient_conditions", "condition_id", "Asthma"),
            ):
                identifier = uuid4()
                connection.execute(
                    metadata.tables[catalog_name].insert().values(id=identifier, name=f" {name} ")
                )
                connection.execute(
                    metadata.tables[join_name]
                    .insert()
                    .values(patient_id=patient_id, **{field: identifier})
                )
                references.append((catalog_name, join_name, field, name, identifier))
            revision = load_revision("20260929_04_catalog_name_integrity.py")
            revision.op = operations
            revision.upgrade()
            for catalog_name, join_name, field, name, identifier in references:
                catalog = metadata.tables[catalog_name]
                join = metadata.tables[join_name]
                assert (
                    connection.scalar(sa.select(catalog.c.name).where(catalog.c.id == identifier))
                    == name
                )
                assert (
                    connection.scalar(
                        sa.select(join.c[field]).where(join.c.patient_id == patient_id)
                    )
                    == identifier
                )
                for invalid in (name.lower(), " Unique Padded Label "):
                    with pytest.raises(sa.exc.IntegrityError), connection.begin_nested():
                        connection.execute(catalog.insert().values(id=uuid4(), name=invalid))
                inspector = sa.inspect(connection)
                assert any(
                    index["name"] == f"uq_{catalog_name}_normalized_name"
                    for index in inspector.get_indexes(catalog_name)
                )
                assert any(
                    check["name"] == f"ck_{catalog_name}_name_trimmed"
                    for check in inspector.get_check_constraints(catalog_name)
                )
            revision.downgrade()
            for catalog_name, _join, _field, name, identifier in references:
                catalog = metadata.tables[catalog_name]
                assert (
                    connection.scalar(sa.select(catalog.c.name).where(catalog.c.id == identifier))
                    == name
                )
                connection.execute(catalog.insert().values(id=uuid4(), name=name.lower()))
                connection.execute(
                    catalog.insert().values(id=uuid4(), name=" Unique Padded Label ")
                )
        finally:
            transaction.rollback()


@pytest.mark.skipif(os.environ.get("TEST_POSTGRES_MIGRATIONS") != "1", reason="Requires PostgreSQL")
def test_postgres_address_lookup_migration_roundtrip():
    from app.database import Base, engine

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            schema = f"migration_test_{uuid4().hex}"
            connection.exec_driver_sql(f"CREATE SCHEMA {schema}")
            connection.exec_driver_sql(f"SET LOCAL search_path TO {schema}")
            operations = Operations(
                MigrationContext.configure(connection, opts={"target_metadata": Base.metadata})
            )
            for filename in (
                "20260928_01_patient_schema.py",
                "20260929_02_reference_catalogs.py",
                "20260929_03_catalog_label_casing.py",
                "20260929_04_catalog_name_integrity.py",
            ):
                revision = load_revision(filename)
                revision.op = operations
                revision.upgrade()
            identifiers = [uuid4(), uuid4(), uuid4()]
            for index, identifier in enumerate(identifiers):
                connection.execute(
                    sa.text(
                        "INSERT INTO patients (id, first_name, last_name, date_of_birth, "
                        "status, blood_type, city, deleted_at) "
                        "VALUES (:id, 'Test', 'Address', '1980-01-01', "
                        ":status, :blood, :city, :deleted)"
                    ),
                    {
                        "id": identifier,
                        "status": ("active", "inactive", "discharged")[index],
                        "blood": "AB-" if index < 2 else None,
                        "city": "Seattle" if index < 2 else None,
                        "deleted": datetime.now(timezone.utc) if index == 1 else None,
                    },
                )
            revision = load_revision("20260929_05_patient_address_lookups.py")
            revision.op = operations
            revision.upgrade()
            assert connection.scalar(sa.text("SELECT count(*) FROM addresses")) == 2
            assert connection.scalar(sa.text("SELECT count(*) FROM patient_statuses")) == 3
            assert connection.scalar(sa.text("SELECT count(*) FROM blood_types")) == 8
            assert (
                connection.scalar(
                    sa.text("SELECT city FROM addresses WHERE patient_id=:id"),
                    {"id": identifiers[1]},
                )
                == "Seattle"
            )
            assert "city" not in {
                column["name"] for column in sa.inspect(connection).get_columns("patients")
            }
            with pytest.raises(sa.exc.IntegrityError), connection.begin_nested():
                connection.execute(sa.text("UPDATE patients SET blood_type='X+'"))
            with pytest.raises(sa.exc.IntegrityError), connection.begin_nested():
                connection.execute(
                    sa.text(
                        "INSERT INTO addresses (id,patient_id,city) "
                        "VALUES (:id,:patient,'Duplicate')"
                    ),
                    {"id": uuid4(), "patient": identifiers[0]},
                )
            surrogate = load_revision("20260929_06_lookup_surrogate_keys.py")
            surrogate.op = operations
            surrogate.upgrade()
            for table, count in (("patient_statuses", 3), ("blood_types", 8)):
                populated = connection.scalar(
                    sa.text(
                        f"SELECT count(*) FROM {table} "
                        "WHERE id IS NOT NULL AND created_at IS NOT NULL"
                    )
                )
                assert populated == count
                with pytest.raises(sa.exc.IntegrityError), connection.begin_nested():
                    connection.execute(sa.text(f"UPDATE {table} SET code='A+'"))
            mapped = (
                connection.execute(
                    sa.text(
                        "SELECT p.id, s.code AS status, b.code AS blood FROM patients p "
                        "JOIN patient_statuses s ON p.status_id=s.id "
                        "LEFT JOIN blood_types b ON p.blood_type_id=b.id"
                    )
                )
                .mappings()
                .all()
            )
            by_patient = {row["id"]: row for row in mapped}
            for index, identifier in enumerate(identifiers):
                assert (
                    by_patient[identifier]["status"] == ("active", "inactive", "discharged")[index]
                )
                assert by_patient[identifier]["blood"] == ("AB-" if index < 2 else None)
            with pytest.raises(sa.exc.IntegrityError), connection.begin_nested():
                connection.execute(sa.text("UPDATE patients SET status_id=:id"), {"id": uuid4()})
            surrogate.downgrade()
            revision.downgrade()
            rows = (
                connection.execute(sa.text("SELECT id, city, blood_type, status FROM patients"))
                .mappings()
                .all()
            )
            by_id = {row["id"]: row for row in rows}
            for index, identifier in enumerate(identifiers):
                assert by_id[identifier]["city"] == ("Seattle" if index < 2 else None)
                assert by_id[identifier]["blood_type"] == ("AB-" if index < 2 else None)
                assert by_id[identifier]["status"] == ("active", "inactive", "discharged")[index]
        finally:
            transaction.rollback()
