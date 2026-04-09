"""Test tore sessions CRUD endpoints."""
HEADERS = {"X-VLBH-Token": "test-token-12345"}


def test_create_tore_session(client):
    body = {
        "therapy_session_id": "00000000-0000-0000-0000-000000000010",
        "patient_id": "00000000-0000-0000-0000-000000000020",
        "before": {
            "tore_intensite": 5000,
            "tore_coherence": 45,
            "stockage_rendement": 60.0,
        },
    }
    r = client.post("/tore-sessions", json=body, headers=HEADERS)
    assert r.status_code == 201


def test_create_tore_session_with_after(client):
    body = {
        "therapy_session_id": "00000000-0000-0000-0000-000000000010",
        "patient_id": "00000000-0000-0000-0000-000000000020",
        "before": {"stockage_rendement": 60.0},
        "after": {"stockage_rendement": 78.5},
    }
    r = client.post("/tore-sessions", json=body, headers=HEADERS)
    assert r.status_code == 201

def test_list_tore_sessions(client):
    r = client.get("/tore-sessions", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "sessions" in data
    assert "total" in data


def test_tore_session_invalid_coherence(client):
    """tore_coherence must be 0-100."""
    body = {
        "therapy_session_id": "00000000-0000-0000-0000-000000000010",
        "patient_id": "00000000-0000-0000-0000-000000000020",
        "before": {"tore_coherence": 999},
    }
    r = client.post("/tore-sessions", json=body, headers=HEADERS)
    assert r.status_code == 422