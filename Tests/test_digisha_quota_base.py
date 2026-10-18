"""Quota DiGiSha tenu en base (migration 2026-10-18m, fiche 9714894f) : la base décide quand elle répond ; sinon la fenêtre en
mémoire d'avant prend le relais (jamais ouvert sans compte)."""
import asyncio
import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routers import digisha as d  # noqa: E402


def _rpc(reponse, appels):
    async def f(nom, corps, timeout=10):
        appels.append((nom, corps))
        return reponse
    return f


def test_la_base_laisse_passer(monkeypatch):
    appels = []
    monkeypatch.setattr(d, "_rpc_service", _rpc({"n": 3, "ok": True}, appels))
    monkeypatch.setattr(d, "_rate_hits", {})
    asyncio.run(d._quota("uid-1", 120))
    assert appels == [("digisha_appel_heure_incr", {"p_cle": "uid-1", "p_limite": 120})]
    assert d._rate_hits == {}                       # la mémoire n'est pas touchée quand la base répond


def test_la_base_refuse_au_dela_du_plafond(monkeypatch):
    monkeypatch.setattr(d, "_rpc_service", _rpc({"n": 121, "ok": False}, []))
    with pytest.raises(HTTPException) as e:
        asyncio.run(d._quota("uid-1", 120))
    assert e.value.status_code == 429


def test_base_injoignable_la_memoire_prend_le_relais(monkeypatch):
    monkeypatch.setattr(d, "_rpc_service", _rpc(None, []))
    monkeypatch.setattr(d, "_rate_hits", {})
    asyncio.run(d._quota("ip:1.2.3.4", 2))
    asyncio.run(d._quota("ip:1.2.3.4", 2))
    with pytest.raises(HTTPException) as e:
        asyncio.run(d._quota("ip:1.2.3.4", 2))
    assert e.value.status_code == 429


def test_reponse_illisible_la_memoire_prend_le_relais(monkeypatch):
    monkeypatch.setattr(d, "_rpc_service", _rpc([1, 2], []))
    monkeypatch.setattr(d, "_rate_hits", {})
    asyncio.run(d._quota("uid-2", 1))
    with pytest.raises(HTTPException):
        asyncio.run(d._quota("uid-2", 1))
