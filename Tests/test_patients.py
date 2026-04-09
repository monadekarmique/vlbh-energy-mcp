"""Test patient CRUD endpoints."""
HEADERS = {"X-VLBH-Token": "test-token-12345"}


def test_create_patient(client):
    body = {
        "first_name": "Marie",
        "last_name": "Dupont",
        "email": "marie@example.com",
        "date_of_birth": "1985-03-15",
    }
    r = client.post("/patients", json=body, headers=HEADERS)
    assert r.status_code == 201
    data = r.json()
    assert data["first_name"] == "Marie"
    assert "id" in data


def test_list_patients(client):
    r = client.get("/patients", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "patients" in data
    assert "total" in data


def test_create_patient_no_auth(client):
    body = {"first_name": "Test", "last_name": "NoAuth"}
    r = client.post("/patients", json=body)
    assert r.status_code == 422 or r.status_code == 401