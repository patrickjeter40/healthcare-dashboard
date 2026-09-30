from datetime import date, datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models import (
    Allergen,
    Condition,
    Patient,
    PatientAllergy,
    PatientCondition,
    PatientStatusLookup,
)
from app.seed import seed_catalogs


def reference(client: TestClient, path: str, name: str) -> dict:
    return next(item for item in client.get(path).json() if item["name"] == name)


def patient_data(client: TestClient, first_name: str = "Avery", last_name: str = "Test") -> dict:
    return {
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": "1980-04-12",
        "email": "avery@example.com",
        "status": "active",
        "blood_type": "A+",
        "allergy_ids": [reference(client, "/allergens", "Penicillin")["id"]],
        "condition_ids": [reference(client, "/conditions", "Asthma")["id"]],
    }


def create_patient(client: TestClient, **changes: object) -> dict:
    response = client.post("/patients", json={**patient_data(client), **changes})
    assert response.status_code == 201, response.text
    return response.json()


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_search_filter_sort_and_pagination(client: TestClient) -> None:
    create_patient(client, first_name="Zoe", last_name="Baker", status="active")
    create_patient(client, first_name="Amy", last_name="Carter", status="inactive")
    create_patient(client, first_name="Ana", last_name="Adams", status="active")

    page = client.get(
        "/patients", params={"page": 1, "page_size": 1, "sort_by": "name", "sort_order": "asc"}
    )
    assert page.status_code == 200
    assert page.json()["total"] == 3
    assert page.json()["page_size"] == 1
    assert page.json()["items"][0]["last_name"] == "Adams"

    searched = client.get("/patients", params={"search": "Carter", "status": "inactive"})
    assert searched.json()["total"] == 1
    assert searched.json()["items"][0]["first_name"] == "Amy"
    assert client.get("/patients", params={"page_size": 101}).status_code == 422


def test_patient_validation_and_missing_record(client: TestClient) -> None:
    assert (
        client.post(
            "/patients", json={**patient_data(client), "date_of_birth": "2999-01-01"}
        ).status_code
        == 422
    )
    assert (
        client.post("/patients", json={**patient_data(client), "email": "not-an-email"}).status_code
        == 422
    )
    assert client.get(f"/patients/{uuid4()}").status_code == 404


def test_create_update_and_soft_delete_patient(client: TestClient) -> None:
    patient = create_patient(client)
    assert patient["age"] > 0
    assert patient["allergies"] == [reference(client, "/allergens", "Penicillin")]
    updated = client.put(
        f"/patients/{patient['id']}",
        json={
            **patient_data(client, "Avery", "Updated"),
            "allergy_ids": [reference(client, "/allergens", "Latex")["id"]],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["last_name"] == "Updated"
    assert updated.json()["allergies"] == [reference(client, "/allergens", "Latex")]

    assert client.delete(f"/patients/{patient['id']}").status_code == 204
    assert client.get("/patients").json()["total"] == 0
    assert client.get(f"/patients/{patient['id']}").status_code == 404
    assert client.put(f"/patients/{patient['id']}", json=patient_data(client)).status_code == 404


def test_note_ownership_soft_delete_and_summary(client: TestClient) -> None:
    first = create_patient(client)
    second = create_patient(client, first_name="Jordan", email="jordan@example.com")
    path = f"/patients/{first['id']}"
    created = client.post(f"{path}/notes", json={"content": "  Symptoms improving.  "})
    assert created.status_code == 201
    note = created.json()
    assert note["content"] == "Symptoms improving."
    assert len(client.get(f"{path}/notes").json()) == 1
    assert "Symptoms improving." in client.get(f"{path}/summary").json()["summary"]

    wrong_patient = client.delete(f"/patients/{second['id']}/notes/{note['id']}")
    assert wrong_patient.status_code == 404
    assert client.delete(f"{path}/notes/{note['id']}").status_code == 204
    assert client.get(f"{path}/notes").json() == []
    assert "Symptoms improving." not in client.get(f"{path}/summary").json()["summary"]
    assert client.delete(f"{path}/notes/{note['id']}").status_code == 404


def test_notes_require_active_patient_and_valid_content(client: TestClient) -> None:
    patient = create_patient(client)
    path = f"/patients/{patient['id']}"
    assert client.post(f"{path}/notes", json={"content": "   "}).status_code == 422
    assert client.post(f"{path}/notes", json={"content": "x" * 5001}).status_code == 422
    assert client.delete(path).status_code == 204
    assert client.get(f"{path}/notes").status_code == 404
    assert client.post(f"{path}/notes", json={"content": "test"}).status_code == 404
    assert client.get(f"{path}/summary").status_code == 404


def test_summary_without_notes_is_deterministic(client: TestClient) -> None:
    patient = create_patient(client)
    path = f"/patients/{patient['id']}/summary"
    first = client.get(path)
    second = client.get(path)
    assert first.status_code == 200
    assert first.json() == second.json()
    assert "Avery Test" in first.json()["summary"]
    assert "Penicillin" in first.json()["summary"]
    assert "No recent clinical notes" in first.json()["summary"]


@pytest.mark.parametrize(
    "path,name", [("/allergens", "Penicillin"), ("/conditions", "Hypertension")]
)
def test_reference_catalog(client: TestClient, path: str, name: str) -> None:
    response = client.get(path)
    assert response.status_code == 200
    values = response.json()
    assert 10 <= len(values) <= 20
    assert [item["name"] for item in values] == sorted(
        (item["name"] for item in values), key=str.casefold
    )
    assert name in [item["name"] for item in values]
    for item in values:
        assert set(item) == {"id", "name"}
        UUID(item["id"])
    assert client.post(path, json={"name": "New"}).status_code == 405


@pytest.mark.parametrize("field", ["allergy_ids", "condition_ids"])
def test_invalid_reference_is_atomic(client: TestClient, field: str) -> None:
    patient = create_patient(client)
    payload = {**patient_data(client), "last_name": "Must not persist", field: [str(uuid4())]}
    response = client.post("/patients", json=payload)
    assert response.status_code == 422
    assert field in response.text and "Unknown" in response.text
    assert client.get("/patients").json()["total"] == 1
    response = client.put(f"/patients/{patient['id']}", json=payload)
    assert response.status_code == 422
    assert client.get(f"/patients/{patient['id']}").json() == patient


@pytest.mark.parametrize("field", ["allergy_ids", "condition_ids"])
def test_duplicate_ids_rejected(client: TestClient, field: str) -> None:
    payload = patient_data(client)
    payload[field] *= 2
    assert client.post("/patients", json=payload).status_code == 422


def test_replacement_detail_and_deleted_relationships(client: TestClient) -> None:
    patient = create_patient(client)
    path = f"/patients/{patient['id']}"
    latex = reference(client, "/allergens", "Latex")
    penicillin = reference(client, "/allergens", "Penicillin")
    hypertension = reference(client, "/conditions", "Hypertension")
    payload = {
        **patient_data(client),
        "allergy_ids": [penicillin["id"], latex["id"]],
        "condition_ids": [hypertension["id"]],
    }
    for _ in range(2):
        response = client.put(path, json=payload)
        assert response.status_code == 200
        assert response.json()["allergies"] == [latex, penicillin]
        assert response.json()["conditions"] == [hypertension]
    assert client.get(path).json() == response.json()
    assert "Hypertension" in client.get(f"{path}/summary").json()["summary"]
    assert client.delete(path).status_code == 204
    assert client.put(path, json=payload).status_code == 404
    with next(app.dependency_overrides[get_db]()) as db:
        assert db.get(Patient, UUID(patient["id"])).deleted_at is not None
        assert db.scalar(select(func.count()).select_from(PatientAllergy)) == 2
        assert db.scalar(select(func.count()).select_from(PatientCondition)) == 1
    other = create_patient(client)
    assert (
        client.put(
            f"/patients/{other['id']}",
            json={**patient_data(client), "allergy_ids": [], "condition_ids": []},
        ).json()["allergies"]
        == []
    )
    assert client.get(f"/patients/{other['id']}").json()["conditions"] == []


@pytest.mark.parametrize(
    "model,field,path,name",
    [
        (PatientAllergy, "allergen_id", "/allergens", "Penicillin"),
        (PatientCondition, "condition_id", "/conditions", "Asthma"),
    ],
)
def test_database_association_constraints(client: TestClient, model, field, path, name) -> None:
    patient = create_patient(client)
    identifier = UUID(reference(client, path, name)["id"])
    with next(app.dependency_overrides[get_db]()) as db:
        db.add(model(patient_id=UUID(patient["id"]), **{field: identifier}))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        db.add(model(patient_id=UUID(patient["id"]), **{field: uuid4()}))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_catalog_seed_idempotent_and_unique(client: TestClient) -> None:
    before = [client.get(path).json() for path in ("/allergens", "/conditions")]
    with next(app.dependency_overrides[get_db]()) as db:
        seed_catalogs(db)
        seed_catalogs(db)
        db.commit()
        for model, name in ((Allergen, "Penicillin"), (Condition, "Asthma")):
            db.add(model(name=name))
            with pytest.raises(IntegrityError):
                db.commit()
            db.rollback()
    assert before == [client.get(path).json() for path in ("/allergens", "/conditions")]


def test_free_text_no_longer_accepted(client: TestClient) -> None:
    assert (
        client.post("/patients", json={**patient_data(client), "allergies": ["custom"]}).status_code
        == 422
    )


@pytest.mark.parametrize("model,existing", [(Allergen, "Penicillin"), (Condition, "Asthma")])
@pytest.mark.parametrize("variant", ["case", "leading_space", "trailing_space", "unique_padded"])
def test_catalog_normalized_names_enforced(
    client: TestClient, model, existing: str, variant: str
) -> None:
    names = {
        "case": existing.lower(),
        "leading_space": " " + existing,
        "trailing_space": existing + " ",
        "unique_padded": " New Catalog Value ",
    }
    with next(app.dependency_overrides[get_db]()) as db:
        db.add(model(name=names[variant]))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        # Constraints protect updates as well as new catalog entries.
        value = model(name="Distinct Catalog Value")
        db.add(value)
        db.commit()
        value.name = names[variant]
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        assert value.name == "Distinct Catalog Value"


@pytest.mark.parametrize("timestamp", ["invalid", "2024-01-01T12:00:00", "2999-01-01T00:00:00Z"])
def test_note_timestamp_validation(client: TestClient, timestamp: str) -> None:
    patient = create_patient(client)
    path = f"/patients/{patient['id']}/notes"
    response = client.post(path, json={"content": "Fictional follow-up", "recorded_at": timestamp})
    assert response.status_code == 422
    assert "recorded_at" in response.text
    assert client.get(path).json() == []


def test_note_supplied_timestamp_and_order(client: TestClient) -> None:
    patient = create_patient(client)
    path = f"/patients/{patient['id']}"
    first = client.post(
        f"{path}/notes",
        json={"content": "Earlier fictional visit", "recorded_at": "2024-01-02T10:30:00+05:30"},
    )
    assert first.status_code == 201
    assert datetime.fromisoformat(first.json()["recorded_at"]) == datetime(
        2024, 1, 2, 5, tzinfo=timezone.utc
    )
    second = client.post(
        f"{path}/notes",
        json={"content": "Later fictional visit", "recorded_at": "2024-01-03T12:15:00Z"},
    )
    assert second.status_code == 201
    notes = client.get(f"{path}/notes").json()
    assert [note["id"] for note in notes] == [second.json()["id"], first.json()["id"]]
    summary = client.get(f"{path}/summary").json()["summary"]
    assert "January 2, 2024" in summary and "Earlier fictional visit" in summary
    assert "January 3, 2024" in summary and "Later fictional visit" in summary


def test_summary_explicit_unknown_blood_type(client: TestClient) -> None:
    patient = create_patient(client, blood_type=None)
    summary = client.get(f"/patients/{patient['id']}/summary").json()["summary"]
    assert "blood type is not recorded" in summary


def test_directory_over_100_patients_uses_bounded_queries(client: TestClient) -> None:
    with next(app.dependency_overrides[get_db]()) as db:
        db.add_all(
            [
                Patient(
                    first_name=f"Sample{index:03d}",
                    last_name="Directory",
                    date_of_birth=date(1980, 1, 1),
                    status=db.scalar(
                        select(PatientStatusLookup).where(
                            PatientStatusLookup.code == ("active" if index % 2 == 0 else "inactive")
                        )
                    ),
                )
                for index in range(125)
            ]
        )
        db.commit()
        engine = db.get_bind()
    statements = []

    def count_queries(_connection, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", count_queries)
    try:
        first = client.get(
            "/patients", params={"page_size": 20, "sort_by": "name", "sort_order": "asc"}
        )
        assert first.status_code == 200
        assert first.json()["total"] == 125
        assert len(first.json()["items"]) == 20
        assert first.json()["items"][0]["first_name"] == "Sample000"
        # Count plus one patient query and two batched association queries; no N+1.
        assert len(statements) <= 4
    finally:
        event.remove(engine, "before_cursor_execute", count_queries)
    last = client.get(
        "/patients", params={"page": 7, "page_size": 20, "sort_by": "name", "sort_order": "asc"}
    )
    assert len(last.json()["items"]) == 5
    assert last.json()["items"][-1]["first_name"] == "Sample124"
    assert client.get("/patients", params={"status": "active"}).json()["total"] == 63
    assert client.get("/patients", params={"search": "Sample124"}).json()["total"] == 1


def test_patient_seed_minimum_and_restart_idempotence(client: TestClient, monkeypatch) -> None:
    from app import seed as seed_module

    with next(app.dependency_overrides[get_db]()) as db:
        factory = sessionmaker(bind=db.get_bind(), autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(seed_module, "SessionLocal", factory)
    assert seed_module.seed() == 40
    assert seed_module.seed() == 0
    page = client.get("/patients", params={"page_size": 100}).json()
    assert page["total"] == 40
    assert all(patient["email"].endswith("@example.com") for patient in page["items"])
    first = page["items"][0]["id"]
    client.delete(f"/patients/{first}")
    assert seed_module.seed() == 0
    assert client.get("/patients").json()["total"] == 39


def test_address_lifecycle_and_lookup_foreign_keys(client):
    from app.models import Address

    patient = create_patient(client, city="Seattle", address_line_1="123 Example Street")
    identifier = UUID(patient["id"])
    with next(app.dependency_overrides[get_db]()) as db:
        address_id = db.scalar(select(Address.id).where(Address.patient_id == identifier))
        assert address_id is not None
        assert "city" not in Patient.__table__.columns
        assert (
            list(Patient.__table__.c.status_id.foreign_keys)[0].target_fullname
            == "patient_statuses.id"
        )
        assert (
            list(Patient.__table__.c.blood_type_id.foreign_keys)[0].target_fullname
            == "blood_types.id"
        )
        for field, invalid in (("status_id", uuid4()), ("blood_type_id", uuid4())):
            with pytest.raises(IntegrityError), db.begin_nested():
                db.execute(
                    Patient.__table__.update()
                    .where(Patient.id == identifier)
                    .values(**{field: invalid})
                )
    response = client.put(
        f"/patients/{identifier}", json={**patient_data(client), "city": "Portland"}
    )
    assert response.status_code == 200
    assert response.json()["city"] == "Portland"
    with next(app.dependency_overrides[get_db]()) as db:
        assert db.scalar(select(Address.id).where(Address.patient_id == identifier)) == address_id
    assert client.delete(f"/patients/{identifier}").status_code == 204
    with next(app.dependency_overrides[get_db]()) as db:
        assert db.scalar(select(Address.id).where(Address.patient_id == identifier)) == address_id
    other = create_patient(client, postal_code="12345", blood_type=None)
    response = client.put(
        f"/patients/{other['id']}", json={**patient_data(client), "blood_type": None}
    )
    assert response.status_code == 200
    assert response.json()["postal_code"] is None
    with next(app.dependency_overrides[get_db]()) as db:
        assert db.scalar(select(Address.id).where(Address.patient_id == UUID(other["id"]))) is None


def test_readiness_checks_database_without_changing_liveness(client):
    from sqlalchemy.exc import OperationalError

    assert client.get("/ready").json() == {"status": "ok"}
    original = app.dependency_overrides[get_db]

    class UnavailableDatabase:
        def execute(self, _statement):
            raise OperationalError("SELECT 1", {}, RuntimeError("private connection details"))

    def unavailable_database():
        yield UnavailableDatabase()

    app.dependency_overrides[get_db] = unavailable_database
    try:
        response = client.get("/ready")
        assert response.status_code == 503
        assert response.json() == {"detail": "Database unavailable"}
        assert client.get("/health").json() == {"status": "ok"}
    finally:
        app.dependency_overrides[get_db] = original


def test_conflict_rolls_back_and_session_remains_usable(client):
    from app.services.errors import ConflictError
    from app.services.transactions import commit_or_conflict

    with next(app.dependency_overrides[get_db]()) as db:
        db.add(Allergen(name="Penicillin"))
        with pytest.raises(ConflictError):
            commit_or_conflict(db)
        assert (
            db.scalar(
                select(func.count()).select_from(Allergen).where(Allergen.name == "Penicillin")
            )
            == 1
        )
        db.add(Allergen(name="Test Reference After Rollback"))
        commit_or_conflict(db)
    assert reference(client, "/allergens", "Test Reference After Rollback")


def test_api_conflict_response_does_not_leak_database_errors(client, monkeypatch):
    from app.services import patients as patient_service
    from app.services.errors import ConflictError

    def conflict(_data, _db):
        raise ConflictError("Data conflicts with an existing record")

    monkeypatch.setattr(patient_service, "create_patient", conflict)
    response = client.post("/patients", json=patient_data(client))
    assert response.status_code == 409
    assert response.json() == {"detail": "Data conflicts with an existing record"}


def test_lookup_ids_metadata_seed_and_status_sort(client):
    from app.models import BloodTypeLookup

    with next(app.dependency_overrides[get_db]()) as db:
        before = {}
        for model, expected in ((PatientStatusLookup, 3), (BloodTypeLookup, 8)):
            values = list(db.scalars(select(model)))
            assert len(values) == expected
            assert all(isinstance(item.id, UUID) and item.created_at is not None for item in values)
            before[model] = {item.code: item.id for item in values}
        seed_catalogs(db)
        db.commit()
        for model in before:
            assert {item.code: item.id for item in db.scalars(select(model))} == before[model]
    for code in ("inactive", "active", "discharged"):
        create_patient(client, status=code)
    for order in ("asc", "desc"):
        response = client.get("/patients", params={"sort_by": "status", "sort_order": order})
        assert response.status_code == 200
        assert [item["status"] for item in response.json()["items"]] == sorted(
            ["inactive", "active", "discharged"], reverse=order == "desc"
        )
