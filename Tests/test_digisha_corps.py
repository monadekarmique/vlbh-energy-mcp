"""La taille du corps des routes DiGiSha est bornée AVANT l'authentification et avant la lecture du JSON (413)."""
import pytest
from fastapi import HTTPException

from routers import digisha as d
from routers import digisha_corps as c

PETIT = b'{"messages": [{"role": "user", "content": "bonjour"}]}'


@pytest.fixture()
def appels(monkeypatch):
    vus = []

    async def authorize_caller(request, x_digisha_token, authorization):
        vus.append(request.url.path)
        raise HTTPException(status_code=401, detail="refusé (test)")

    monkeypatch.setattr(d, "authorize_caller", authorize_caller)
    monkeypatch.setenv("DIGISHA_CORPS_MAX_OCTETS", "2000")
    return vus


def _morceaux(n, taille=1000):
    for _ in range(n):
        yield b"x" * taille


def test_content_length_trop_grand_refuse_avant_l_authentification(client, appels):
    for route in ("/digisha/chat", "/digisha/accompagnement"):
        r = client.post(route, content=b"x" * 5000, headers={"content-type": "application/json"})
        assert r.status_code == 413, route
        assert r.json()["detail"] == c.MESSAGE_413
    assert appels == []


def test_corps_par_morceaux_trop_grand_refuse_sans_rien_passer(client, appels):
    r = client.post("/digisha/accompagnement", content=_morceaux(3), headers={"content-type": "application/json"})
    assert r.status_code == 413
    assert appels == []


def test_sous_la_borne_la_requete_arrive_a_la_route(client, appels):
    r = client.post("/digisha/chat", content=PETIT, headers={"content-type": "application/json"})
    assert r.status_code == 401
    r = client.post("/digisha/chat", content=iter([PETIT[:20], PETIT[20:]]), headers={"content-type": "application/json"})
    assert r.status_code == 401                         # le corps lu par morceaux est rejoué, le JSON se lit
    assert appels == ["/digisha/chat", "/digisha/chat"]


def test_les_autres_routes_ne_sont_pas_concernees(client, appels):
    r = client.post("/health", content=b"x" * 5000)
    assert r.status_code == 405


def test_borne_par_defaut(monkeypatch):
    monkeypatch.delenv("DIGISHA_CORPS_MAX_OCTETS", raising=False)
    assert c.corps_max() == 32 * 1024 * 1024
    monkeypatch.setenv("DIGISHA_CORPS_MAX_OCTETS", "pas-un-nombre")
    assert c.corps_max() == 32 * 1024 * 1024
    monkeypatch.setenv("DIGISHA_CORPS_MAX_OCTETS", "1000")
    assert c.corps_max() == 1000
