"""Le numéro de release rendu avec chaque réponse (carte 9331e3e6) : lu en base, gardé 5 minutes, jamais bloquant."""
import asyncio

from routers import digisha_release as dr
from routers.digisha import ChatResponse


def _remise():
    dr._cache.update(t=-1e9, numero=None)


def test_lit_le_numero_puis_le_garde():
    _remise()
    appels = []

    async def rpc(nom, corps):
        appels.append(nom)
        return [{"numero": "2.6", "lignes": ["a"], "avis": False}]

    assert asyncio.run(dr.release_courante(rpc)) == "2.6"
    assert asyncio.run(dr.release_courante(rpc)) == "2.6"
    assert appels == ["digisha_release_courante"]


def test_panne_garde_le_dernier_numero():
    _remise()

    async def ok(nom, corps):
        return [{"numero": "2.6"}]

    async def panne(nom, corps):
        return None

    assert asyncio.run(dr.release_courante(ok)) == "2.6"
    assert asyncio.run(dr.release_courante(panne, ttl=0)) == "2.6"


def test_fonction_absente_ne_bloque_pas_et_ne_reessaie_pas_a_chaque_tour():
    _remise()
    appels = []

    async def absente(nom, corps):
        appels.append(nom)
        return None

    assert asyncio.run(dr.release_courante(absente)) is None
    assert asyncio.run(dr.release_courante(absente)) is None
    assert len(appels) == 1


def test_la_reponse_porte_la_release_et_reste_valide_sans():
    assert ChatResponse(reply="x", model="m").release is None
    assert ChatResponse(reply="x", model="m", release="2.6").model_dump()["release"] == "2.6"
