"""Test Rose des Vents endpoints."""
HEADERS = {"X-VLBH-Token": "test-token-12345"}


def test_rose_des_vents_reference(client):
    """GET /rose-des-vents/reference returns direction table."""
    r = client.get("/rose-des-vents/reference", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "directions" in data


def test_create_rose_des_vents(client):
    body = {
        "therapy_session_id": "00000000-0000-0000-0000-000000000010",
        "patient_id": "00000000-0000-0000-0000-000000000020",
        "primary": {
            "direction": "N",
            "deviation_degrees": 15.5,
        },
    }
    r = client.post("/rose-des-vents", json=body, headers=HEADERS)
    assert r.status_code == 201


def test_list_rose_des_vents(client):
    r = client.get("/rose-des-vents", headers=HEADERS)
    assert r.status_code == 200