"""ST1 a) (DEC Patrick 21.10.2026) : quand le stade d'une session ne se lit pas (réseau, 5xx, réponse inexploitable), le
gate ne laisse plus passer — 503 « réessaie dans un instant » pour toutes. Un stade lu reste traité comme avant : ST1 → 403,
abonnée → passe, compte désactivé → 402. Une session refusée par l'auth n'est pas une panne (rien à lire, comme avant)."""
import asyncio

import httpx
import pytest
from fastapi import HTTPException

from routers import digisha as d

UID = "00000000-0000-4000-8000-000000000001"
SVLBH = "00000000-0000-4000-8000-0000000000aa"


class _R:
    def __init__(self, code, corps):
        self.status_code, self._corps = code, corps

    def json(self):
        if isinstance(self._corps, Exception):
            raise self._corps
        return self._corps


class _Client:
    """Répond par table : (dernier segment de l'URL, clé du filtre) → _R ou exception levée."""

    def __init__(self, table):
        self.table, self.vus = table, []

    async def get(self, url, params=None, headers=None, timeout=None):
        cle = url.rsplit("/", 1)[-1] + (":" + next(iter(params)) if params else "")
        self.vus.append(cle)
        r = self.table[cle]
        if isinstance(r, Exception):
            raise r
        return r


AUTH_OK = _R(200, {"id": UID})


def _gate(monkeypatch, table):
    client = _Client(table)
    monkeypatch.setenv("DIGISHA_SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("DIGISHA_SUPABASE_SERVICE_KEY", "k")
    monkeypatch.setattr(d, "_http", lambda: client)
    return client, asyncio.run(d.gate_subscription("Bearer jeton"))


@pytest.mark.parametrize("table", [
    {"user": httpx.ConnectError("injoignable")},                                           # auth : réseau
    {"user": _R(503, {})},                                                                  # auth : 5xx
    {"user": _R(429, {})},                                                                  # auth : saturée
    {"user": _R(200, ValueError("pas du JSON"))},                                           # auth : corps illisible
    {"user": _R(200, {})},                                                                  # auth : pas d'id
    {"user": AUTH_OK, "praticienne_profile:supabase_user_id": httpx.ReadTimeout("lent")},   # profil : réseau
    {"user": AUTH_OK, "praticienne_profile:supabase_user_id": _R(500, {"message": "x"})},   # profil : 5xx
    {"user": AUTH_OK, "praticienne_profile:supabase_user_id": _R(200, {"message": "x"})},   # profil : pas une liste
    {"user": AUTH_OK, "praticienne_profile:supabase_user_id": _R(200, ["texte"])},          # profil : pas des objets
    {"user": AUTH_OK, "praticienne_profile:supabase_user_id": _R(200, []),
     "praticienne_user_alias:supabase_user_id": _R(502, None)},                             # alias : 5xx
    {"user": AUTH_OK, "praticienne_profile:supabase_user_id": _R(200, []),
     "praticienne_user_alias:supabase_user_id": _R(200, [{"svlbh_id": SVLBH}]),
     "praticienne_profile:svlbh_id": httpx.ConnectError("injoignable")},                    # profil de l'alias : réseau
])
def test_stade_illisible_refuse_tout_le_monde_en_503(monkeypatch, table):
    with pytest.raises(HTTPException) as e:
        _gate(monkeypatch, table)
    assert e.value.status_code == 503
    assert e.value.detail == "DiGiSha est momentanément indisponible, réessaie dans un instant."


def test_st1_lue_reste_refusee_en_403(monkeypatch):
    _, ident = _gate(monkeypatch, {"user": AUTH_OK, "praticienne_profile:supabase_user_id":
                                   _R(200, [{"svlbh_id": SVLBH, "pro_status": "ACTIVE", "stx": "ST1"}])})
    with pytest.raises(HTTPException) as e:
        d.refuser_st1(ident)
    assert e.value.status_code == 403


def test_abonnee_lue_passe(monkeypatch):
    _, ident = _gate(monkeypatch, {"user": AUTH_OK, "praticienne_profile:supabase_user_id":
                                   _R(200, [{"svlbh_id": SVLBH, "pro_status": "ACTIVE", "stx": "ST3"}])})
    d.refuser_st1(ident)
    assert ident["svlbh_id"] == SVLBH and ident["stx"] == "ST3"


def test_abonnee_par_alias_passe(monkeypatch):
    client, ident = _gate(monkeypatch, {
        "user": AUTH_OK, "praticienne_profile:supabase_user_id": _R(200, []),
        "praticienne_user_alias:supabase_user_id": _R(200, [{"svlbh_id": SVLBH}]),
        "praticienne_profile:svlbh_id": _R(200, [{"svlbh_id": SVLBH, "pro_status": "ACTIVE", "stx": "ST6"}])})
    assert ident["svlbh_id"] == SVLBH and ident["profondeur"] is True
    assert client.vus == ["user", "praticienne_profile:supabase_user_id", "praticienne_user_alias:supabase_user_id",
                          "praticienne_profile:svlbh_id"]


def test_sans_profil_lu_passe_comme_avant(monkeypatch):
    _, ident = _gate(monkeypatch, {"user": AUTH_OK, "praticienne_profile:supabase_user_id": _R(200, []),
                                   "praticienne_user_alias:supabase_user_id": _R(200, [])})
    assert ident == {"uid": UID, "svlbh_id": None, "profondeur": False}


def test_compte_desactive_lu_reste_en_402(monkeypatch):
    with pytest.raises(HTTPException) as e:
        _gate(monkeypatch, {"user": AUTH_OK, "praticienne_profile:supabase_user_id":
                            _R(200, [{"svlbh_id": SVLBH, "pro_status": "SUSPENDED", "stx": "ST3"}])})
    assert e.value.status_code == 402


@pytest.mark.parametrize("code", [401, 403])
def test_session_refusee_par_l_auth_n_est_pas_une_panne(monkeypatch, code):
    client, ident = _gate(monkeypatch, {"user": _R(code, {"msg": "invalid JWT"})})
    assert ident is None and client.vus == ["user"]


def test_la_route_chat_rend_503_avant_tout_appel(monkeypatch):
    """Sur /chat le stade se lit juste après l'autorisation : ni prompt, ni résumé d'historique avant le 503."""
    appels = []

    async def rien(*a, **k):
        return None

    async def trace(*a, **k):
        appels.append("apres_le_gate")
        return None

    client = _Client({"user": AUTH_OK, "praticienne_profile:supabase_user_id": _R(503, None)})
    monkeypatch.setenv("DIGISHA_SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("DIGISHA_SUPABASE_SERVICE_KEY", "k")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setattr(d, "_http", lambda: client)
    monkeypatch.setattr(d, "authorize_caller", rien)
    monkeypatch.setattr(d, "fetch_prompt", trace)
    monkeypatch.setattr(d, "preparer_historique", trace)
    tour = [d.ChatTurn(role="user", content="bonjour")]
    for appel in (lambda: d.digisha_chat(request=None, body=d.ChatRequest(messages=tour), x_digisha_token=None,
                                         authorization="Bearer t"),
                  lambda: d.digisha_accompagnement(request=None, body=d.AccompagnementRequest(messages=tour),
                                                   x_digisha_token=None, authorization="Bearer t")):
        with pytest.raises(HTTPException) as e:
            asyncio.run(appel())
        assert e.value.status_code == 503
    assert appels == []
