"""Une réponse coupée en route se redemande avec la même clé et revient telle quelle (06.11.2026)."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from routers import digisha_envoi as ev


def _compteur():
    n = {"v": 0}

    async def calcul():
        n["v"] += 1
        await asyncio.sleep(0.01)
        return f"réponse {n['v']}"
    return n, calcul


def test_meme_cle_meme_appelant_une_seule_fois():
    n, calcul = _compteur()

    async def deux():
        a = await ev.une_seule_fois("Bearer A", "k-1", calcul)
        b = await ev.une_seule_fois("Bearer A", "k-1", calcul)
        return a, b
    assert asyncio.run(deux()) == ("réponse 1", "réponse 1") and n["v"] == 1


def test_redemande_pendant_le_calcul_attend_la_premiere():
    n, calcul = _compteur()

    async def ensemble():
        return await asyncio.gather(ev.une_seule_fois("Bearer B", "k-2", calcul), ev.une_seule_fois("Bearer B", "k-2", calcul))
    assert asyncio.run(ensemble()) == ["réponse 1", "réponse 1"] and n["v"] == 1


def test_autre_appelant_ou_sans_cle_calcule():
    n, calcul = _compteur()

    async def trois():
        await ev.une_seule_fois("Bearer C", "k-3", calcul)
        await ev.une_seule_fois("Bearer D", "k-3", calcul)        # même clé, autre personne : jamais partagée
        await ev.une_seule_fois("Bearer C", None, calcul)
        await ev.une_seule_fois("Bearer C", None, calcul)
    asyncio.run(trois())
    assert n["v"] == 4


def test_une_erreur_n_est_pas_gardee():
    essais = {"v": 0}

    async def calcul():
        essais["v"] += 1
        if essais["v"] == 1:
            raise RuntimeError("503")
        return "ok"

    async def deux():
        try:
            await ev.une_seule_fois("Bearer E", "k-4", calcul)
        except RuntimeError:
            pass
        return await ev.une_seule_fois("Bearer E", "k-4", calcul)
    assert asyncio.run(deux()) == "ok" and essais["v"] == 2
