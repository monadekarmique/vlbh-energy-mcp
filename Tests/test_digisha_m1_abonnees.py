"""Module 1 « Accompagner un proche » : une accompagnante abonnée MyShamanFamily PRO n'est plus arrêtée par le
parcours ST0/ST1 du proche (Patrick, 15.10.2026 : « Fabienne est Abonnée MyShamanFamily je comprends pas pourquoi
STx nous bloque encore »). Sans abonnement, la règle du 07.07 reste entière ; une panne ne rouvre rien."""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from routers import digisha  # noqa: E402
from routers.digisha_formation_m1 import (  # noqa: E402
    M1_ST2_WINDOWS, M1_ST3_WINDOWS, m1_open_windows, m1_system_block)


def test_sans_abonnement_st0_st1_et_vide_restent_fermes():
    for p in ("st0", "ST1", "", None):
        assert m1_open_windows(p) is None
        assert m1_system_block(p or "") is None


def test_abonnee_ouvre_st1_sur_les_fenetres_de_depart_et_le_dit_au_modele():
    assert m1_open_windows("ST1", ouvert_par_abonnement=True) == M1_ST2_WINDOWS
    bloc = m1_system_block("ST1", ouvert_par_abonnement=True)
    assert bloc is not None
    assert "parcours ST1, ouvert par l'abonnement MyShamanFamily PRO" in bloc
    assert "D1 · D5 · D7 · D8 · D9" in bloc


def test_abonnement_ne_change_rien_en_st2_ni_en_st3():
    assert m1_open_windows("st2", ouvert_par_abonnement=True) == M1_ST2_WINDOWS
    assert m1_open_windows("st4", ouvert_par_abonnement=True) == M1_ST3_WINDOWS
    assert m1_system_block("st2", True) == m1_system_block("st2")
    assert m1_system_block("st4", True) == m1_system_block("st4")


class _Rep:
    def __init__(self, code, corps):
        self.status_code, self._corps = code, corps

    def json(self):
        return self._corps


class _Client:
    def __init__(self, rep=None, panne=False):
        self.rep, self.panne, self.appels = rep, panne, []

    async def post(self, url, json=None, headers=None, timeout=None):
        self.appels.append((url, headers))
        if self.panne:
            raise RuntimeError("réseau")
        return self.rep


def _env(monkeypatch, client):
    monkeypatch.setenv("DIGISHA_SUPABASE_URL", "https://exemple.supabase.co")
    monkeypatch.setenv("DIGISHA_SUPABASE_SERVICE_KEY", "cle-serveur")
    monkeypatch.setattr(digisha, "_http", lambda: client)


def test_abonnee_lue_en_base_avec_son_jeton(monkeypatch):
    c = _Client(_Rep(200, ["audit-entites-familiales", "vifa-entites-familiales"]))
    _env(monkeypatch, c)
    assert asyncio.run(digisha.est_abonnee_myshamanfamily("Bearer jeton-de-fabienne")) is True
    url, entetes = c.appels[0]
    assert url.endswith("/rest/v1/rpc/programmes_myshaman_accessibles")
    assert entetes["Authorization"] == "Bearer jeton-de-fabienne"


def test_non_abonnee_sans_session_ou_panne_ne_rouvre_rien(monkeypatch):
    _env(monkeypatch, _Client(_Rep(200, [])))
    assert asyncio.run(digisha.est_abonnee_myshamanfamily("Bearer x")) is False
    _env(monkeypatch, _Client(_Rep(401, {"message": "JWT expired"})))
    assert asyncio.run(digisha.est_abonnee_myshamanfamily("Bearer x")) is False
    _env(monkeypatch, _Client(panne=True))
    assert asyncio.run(digisha.est_abonnee_myshamanfamily("Bearer x")) is False
    c = _Client(_Rep(200, ["x"]))
    _env(monkeypatch, c)
    assert asyncio.run(digisha.est_abonnee_myshamanfamily(None)) is False
    assert c.appels == []
