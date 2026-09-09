"""Variables au démarrage (rôle de clé, jamais la valeur) et compteur Profondeur hors journal."""
from __future__ import annotations

import asyncio
import base64
import json
import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("MAKE_WEBHOOK_PUSH_URL", "https://hook.test/push")
os.environ.setdefault("MAKE_WEBHOOK_PULL_URL", "https://hook.test/pull")
from routers import digisha as d  # noqa: E402


def _jwt(role: str) -> str:
    body = base64.urlsafe_b64encode(json.dumps({"role": role}).encode()).decode().rstrip("=")
    return f"eyJhbGciOiJIUzI1NiJ9.{body}.sig"


def test_role_de_cle():
    assert d._role_de_cle("") == "ABSENTE"
    assert d._role_de_cle(_jwt("service_role")) == "service_role"
    assert d._role_de_cle(_jwt("anon")) == "anon"
    assert d._role_de_cle("sb_secret_abc") == "sb_secret (serveur)"
    assert d._role_de_cle("sb_publishable_abc").startswith("sb_publishable")
    assert d._role_de_cle("pas.un.jwt") == "illisible"


def test_compteur_prend_le_max_base_memoire(monkeypatch):
    monkeypatch.setenv("DIGISHA_SUPABASE_URL", "https://supa.test")
    monkeypatch.setenv("DIGISHA_SUPABASE_SERVICE_KEY", _jwt("service_role"))
    d._usage_mem.clear()
    vus = []

    async def rpc(req):
        vus.append(json.loads(req.content))
        return httpx.Response(200, json=41)

    d._http_client = httpx.AsyncClient(transport=httpx.MockTransport(rpc))
    n = asyncio.run(d._compter_accompagnement("57bd2f8e-0000-0000-0000-000000000000"))
    assert n == 41 and vus[0]["p_svlbh"].startswith("57bd2f8e") and len(vus[0]["p_mois"]) == 7


def test_compteur_sans_base_compte_en_memoire(monkeypatch):
    monkeypatch.delenv("DIGISHA_SUPABASE_URL", raising=False)
    monkeypatch.delenv("DIGISHA_SUPABASE_SERVICE_KEY", raising=False)
    d._usage_mem.clear()
    a = asyncio.run(d._compter_accompagnement("x"))
    b = asyncio.run(d._compter_accompagnement("x"))
    assert (a, b) == (1, 2)


def test_compteur_base_refusee_retombe_en_memoire(monkeypatch):
    monkeypatch.setenv("DIGISHA_SUPABASE_URL", "https://supa.test")
    monkeypatch.setenv("DIGISHA_SUPABASE_SERVICE_KEY", _jwt("anon"))
    d._usage_mem.clear()

    async def refus(req):
        return httpx.Response(401, text="Invalid API key")

    d._http_client = httpx.AsyncClient(transport=httpx.MockTransport(refus))
    assert asyncio.run(d._compter_accompagnement("y")) == 1
