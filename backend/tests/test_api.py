from uuid import uuid4

from fastapi.testclient import TestClient


def patient_data(first_name: str = "Avery", last_name: str = "Test") -> dict:
    return {
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": "1980-04-12",
        "email": "avery@example.com",
        "status": "active",
        "blood_type": "A+",
        "allergies": ["penicillin"],
        "conditions": ["asthma"],
    }


def create_patient(client: TestClient, **changes: object) -> dict:
    response = client.post("/patients", json={**patient_data(), **changes})
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
        client.post("/patients", json={**patient_data(), "date_of_birth": "2999-01-01"}).status_code
        == 422
    )
    assert (
        client.post("/patients", json={**patient_data(), "email": "not-an-email"}).status_code
        == 422
    )
    assert client.get(f"/patients/{uuid4()}").status_code == 404


def test_create_update_and_soft_delete_patient(client: TestClient) -> None:
    patient = create_patient(client)
    assert patient["age"] > 0
    assert patient["allergies"] == ["penicillin"]
    updated = client.put(
        f"/patients/{patient['id']}",
        json={**patient_data("Avery", "Updated"), "allergies": ["latex"]},
    )
    assert updated.status_code == 200
    assert updated.json()["last_name"] == "Updated"
    assert updated.json()["allergies"] == ["latex"]

    assert client.delete(f"/patients/{patient['id']}").status_code == 204
    assert client.get("/patients").json()["total"] == 0
    assert client.get(f"/patients/{patient['id']}").status_code == 404
    assert client.put(f"/patients/{patient['id']}", json=patient_data()).status_code == 404


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
    assert "penicillin" in first.json()["summary"]
    assert "No recent clinical notes" in first.json()["summary"]
