"""Test health endpoint."""
HEADERS = {"X-VLBH-Token": "test-token-12345"}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "vlbh-energy-mcp"
    assert "ts" in data