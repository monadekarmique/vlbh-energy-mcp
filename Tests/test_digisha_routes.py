"""Les routes DiGiSha exposées : /chat et /accompagnement, rien d'autre."""
from fastapi.openapi.utils import get_openapi

import main


def test_les_routes_digisha(client):
    schema = get_openapi(title="t", version="0", routes=main.app.routes)
    chemins = {p for p in schema["paths"] if p.startswith("/digisha")}
    assert chemins == {"/digisha/chat", "/digisha/accompagnement"}


def test_compare_n_existe_plus(client):
    assert client.post("/digisha/chat", json={}).status_code == 422          # la route vivante répond
    assert client.post("/digisha/compare", json={"message": "x"}).status_code == 404
