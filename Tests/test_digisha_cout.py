"""Coût réel par appel — ce que le serveur envoie à la RPC, et ce qu'il n'invente pas."""
from __future__ import annotations

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from routers import digisha  # noqa: E402


class _Resp:
    status_code = 204
    text = ""


class _Http:
    def __init__(self):
        self.appels: list[dict] = []

    async def post(self, url, json=None, headers=None, timeout=None):
        self.appels.append({"url": url, "json": json, "headers": headers})
        return _Resp()


@pytest.fixture
def http(monkeypatch):
    fake = _Http()
    monkeypatch.setattr(digisha, "_http", lambda: fake)
    monkeypatch.setenv("DIGISHA_SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("DIGISHA_SUPABASE_SERVICE_KEY", "sk-test")
    return fake


USAGE = {"usage": {"input_tokens": 1200, "cache_creation_input_tokens": 3000,
                   "cache_read_input_tokens": 20000, "output_tokens": 800,
                   "cache_creation": {"ephemeral_5m_input_tokens": 2500, "ephemeral_1h_input_tokens": 500}}}


def test_envoie_les_quatre_compteurs_et_la_part_1h(http):
    asyncio.run(digisha.journaliser_cout("render-tuteur", "fil", "claude-sonnet-4-6", USAGE,
                                         supabase_user_id="11111111-1111-1111-1111-111111111111"))
    assert len(http.appels) == 1
    a = http.appels[0]
    assert a["url"].endswith("/rest/v1/rpc/digisha_journaliser_cout")
    j = a["json"]
    assert (j["p_input"], j["p_cache_w"], j["p_cache_r"], j["p_output"]) == (1200, 3000, 20000, 800)
    assert j["p_cache_w_1h"] == 500
    assert (j["p_source"], j["p_mode"], j["p_model"]) == ("render-tuteur", "fil", "claude-sonnet-4-6")
    assert j["p_svlbh_id"] is None and j["p_supabase_user_id"] == "11111111-1111-1111-1111-111111111111"
    # aucun prix ne part du serveur : le tarif vit en base
    assert not any("usd" in k or "cout" in k or "prix" in k for k in j)


def test_usage_absent_donne_des_zeros_pas_une_exception(http):
    asyncio.run(digisha.journaliser_cout("render-accompagnement", "accompagnement", "claude-opus-4-8", {}))
    j = http.appels[0]["json"]
    assert (j["p_input"], j["p_cache_w"], j["p_cache_w_1h"], j["p_cache_r"], j["p_output"]) == (0, 0, 0, 0, 0)


def test_sans_cles_supabase_ne_poste_rien(http, monkeypatch):
    monkeypatch.delenv("DIGISHA_SUPABASE_SERVICE_KEY")
    asyncio.run(digisha.journaliser_cout("pwa-api", "digisha", "claude-opus-4-8", USAGE))
    assert http.appels == []
