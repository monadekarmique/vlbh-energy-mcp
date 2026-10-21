"""Les routes DiGiSha exposées : /chat et /accompagnement, rien d'autre."""


def test_les_routes_digisha(client):
    chemins = {r.path for r in client.app.routes if getattr(r, "path", "").startswith("/digisha")}
    assert chemins == {"/digisha/chat", "/digisha/accompagnement"}


def test_compare_n_existe_plus(client):
    r = client.post("/digisha/compare", json={"message": "x"})
    assert r.status_code == 404
