"""Test pipeline CRM endpoints."""
HEADERS = {"X-VLBH-Token": "test-token-12345"}


def test_create_pipeline_lead(client):
    body = {
        "first_name": "Jean",
        "last_name": "Martin",
        "email": "jean@example.com",
        "stage": "new",
        "source": "website",
        "priority": 1,
    }
    r = client.post("/pipeline/leads", json=body, headers=HEADERS)
    assert r.status_code == 201


def test_list_pipeline_leads(client):
    r = client.get("/pipeline/leads", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "leads" in data
    assert "stage_counts" in data


def test_create_lead_invalid_stage(client):
    body = {
        "first_name": "Bad",
        "last_name": "Stage",
        "stage": "INVALID_STAGE",
    }
    r = client.post("/pipeline/leads", json=body, headers=HEADERS)
    assert r.status_code == 422


def test_create_lead_invalid_priority(client):
    body = {
        "first_name": "Bad",
        "last_name": "Priority",
        "priority": 5,
    }
    r = client.post("/pipeline/leads", json=body, headers=HEADERS)
    assert r.status_code == 422