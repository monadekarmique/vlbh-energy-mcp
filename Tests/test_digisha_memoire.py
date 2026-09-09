"""Mémoire DiGiSha par blocs — découpage stable, résumé une fois, repli brut."""
from __future__ import annotations

import asyncio
import os
import sys

import httpx
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from routers import digisha_memoire as m  # noqa: E402


def conv(n: int, start: int = 0) -> list[dict]:
    """n messages alternés user/assistant, numérotés depuis `start`."""
    return [{"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(start, start + n)]


def test_court_reste_brut():
    blocs, recents = m.decouper(conv(20))
    assert blocs == [] and len(recents) == 20


def test_frontiere_par_pas_de_dix():
    for n in range(21, 30):
        blocs, recents = m.decouper(conv(n))
        assert [len(b) for b in blocs] == [10] and len(recents) == n - 10
    for n in range(30, 40):
        blocs, recents = m.decouper(conv(n))
        assert [len(b) for b in blocs] == [10, 10] and len(recents) == n - 20
    blocs, recents = m.decouper(conv(40))
    assert [len(b) for b in blocs] == [10, 10, 10] and len(recents) == 10


def test_recents_commencent_par_user():
    msgs = [{"role": "assistant", "content": "intro"}] + conv(30)
    blocs, recents = m.decouper(msgs)
    assert recents[0]["role"] == "user"
    assert sum(len(b) for b in blocs) + len(recents) == len(msgs)


def test_blocs_stables_quand_le_debut_ne_bouge_pas():
    """Fenêtre par blocs (Priv-1 09.09) : 10 tours de suite, mêmes blocs."""
    empreintes = {m.empreinte(b) for n in range(31, 40) for b in m.decouper(conv(n))[0]}
    assert len(empreintes) == 2


def test_fenetre_glissante_decale_les_blocs():
    """Ancien client (suffix 30) : chaque tour produit d'autres blocs — documenté."""
    a = {m.empreinte(b) for b in m.decouper(conv(30, start=0))[0]}
    b = {m.empreinte(b) for b in m.decouper(conv(30, start=1))[0]}
    assert a.isdisjoint(b)


def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_resume_une_fois_puis_cache():
    m._resumes.clear()
    appels = []

    async def ok(req):
        appels.append(req.url.path)
        return httpx.Response(200, json={"content": [{"type": "text", "text": "résumé"}],
                                         "usage": {"input_tokens": 10, "output_tokens": 3}})

    async def run():
        c = _client(ok)
        bloc1, rec1, n1 = await m.preparer_historique(c, "k", conv(31))
        bloc2, rec2, n2 = await m.preparer_historique(c, "k", conv(32))
        return bloc1, rec1, n1, bloc2, rec2, n2

    bloc1, rec1, n1, bloc2, rec2, n2 = asyncio.run(run())
    assert n1 == 2 and n2 == 2
    assert len(appels) == 2, "deux blocs → deux résumés, puis plus aucun appel"
    assert bloc1["cache_control"] == {"type": "ephemeral"} and "Bloc 2" in bloc1["text"]
    assert bloc1["text"] == bloc2["text"]
    assert len(rec1) == 11 and len(rec2) == 12 and rec1[0]["role"] == "user"


def test_refus_du_resume_renvoie_tout_brut():
    m._resumes.clear()

    async def refuse(req):
        return httpx.Response(429, text="rate")

    bloc, recents, n = asyncio.run(m.preparer_historique(_client(refuse), "k", conv(35)))
    assert bloc is None and n == 0 and len(recents) == 35


def test_cache_borne():
    m._resumes.clear()
    for i in range(m.CACHE_MAX + 20):
        m._resumes[f"k{i}"] = "x"
        while len(m._resumes) > m.CACHE_MAX:
            m._resumes.popitem(last=False)
    assert len(m._resumes) == m.CACHE_MAX and "k0" not in m._resumes
