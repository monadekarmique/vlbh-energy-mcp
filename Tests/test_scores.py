"""Test scores endpoints."""
HEADERS = {"X-VLBH-Token": "test-token-12345"}


def test_create_scores(client):
    body = {
        "therapy_session_id": "00000000-0000-0000-0000-000000000010",
        "patient_id": "00000000-0000-0000-0000-000000000020",
        "patient_scores": {
            "sla": 85.0,
            "slsa": 120.0,
            "slpmo": 45.0,
            "slm": 5000,
        },
    }
    r = client.post("/scores", json=body, headers=HEADERS)
    assert r.status_code == 201


def test_list_scores(client):
    r = client.get("/scores", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "scores" in data
    assert "total" in data