"""Test chromotherapy endpoints."""
HEADERS = {"X-VLBH-Token": "test-token-12345"}


def test_chromo_reference(client):
    """GET /chromo/reference returns full mapping table."""
    r = client.get("/chromo/reference", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "meridiens" in data
    assert "color_gels" in data
    assert "elements" in data
    assert len(data["meridiens"]) == 14
    assert len(data["color_gels"]) == 12
    assert len(data["elements"]) == 5
    # Check a known mapping
    poumon = next(m for m in data["meridiens"] if m["meridien"] == "poumon")
    assert poumon["element"] == "metal"
    assert poumon["color_tonify"] == "indigo"
    assert poumon["color_sedate"] == "orange"


def test_create_chromo_session(client):
    body = {
        "therapy_session_id": "00000000-0000-0000-0000-000000000010",
        "patient_id": "00000000-0000-0000-0000-000000000020",
        "prescriptions": [
            {
                "meridien": "poumon",
                "color_gel": "indigo",
                "action": "tonify",
                "duration_seconds": 180,
            }
        ],
        "protocol_source": "5_elements",
    }
    r = client.post("/chromo", json=body, headers=HEADERS)
    assert r.status_code == 201

def test_list_chromo_sessions(client):
    r = client.get("/chromo", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "sessions" in data
    assert "total" in data


def test_create_chromo_invalid_action(client):
    """Action must be tonify/sedate/neutral/custom."""
    body = {
        "therapy_session_id": "00000000-0000-0000-0000-000000000010",
        "patient_id": "00000000-0000-0000-0000-000000000020",
        "prescriptions": [
            {
                "meridien": "poumon",
                "color_gel": "indigo",
                "action": "INVALID",
                "duration_seconds": 180,
            }
        ],
    }
    r = client.post("/chromo", json=body, headers=HEADERS)
    assert r.status_code == 422


def test_create_chromo_empty_prescriptions(client):
    """prescriptions must have at least 1 item."""
    body = {
        "therapy_session_id": "00000000-0000-0000-0000-000000000010",
        "patient_id": "00000000-0000-0000-0000-000000000020",
        "prescriptions": [],
    }
    r = client.post("/chromo", json=body, headers=HEADERS)
    assert r.status_code == 422