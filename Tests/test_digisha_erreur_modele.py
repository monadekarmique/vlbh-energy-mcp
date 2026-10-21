"""Une erreur du fournisseur de modèle : message générique en français vers le client, même code (502) ; le détail reste au
journal serveur, sans la conversation."""
import asyncio
import logging

import httpx
import pytest
from fastapi import HTTPException

from routers import digisha as d

QUESTION = "QUESTION-PRIVEE-DE-LA-PERSONNE"


class _Journal(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lignes = []

    def emit(self, record):
        self.lignes.append(record.getMessage())


@pytest.fixture()
def journal():
    h = _Journal()
    d.log.addHandler(h)
    yield h
    d.log.removeHandler(h)


def _reponse(code, corps=None, texte=None):
    req = httpx.Request("POST", d.ANTHROPIC_URL)
    if corps is not None:
        return httpx.Response(code, json=corps, request=req, headers={"request-id": "req_123"})
    return httpx.Response(code, text=texte or "", request=req)


def test_erreur_generique_sans_le_corps(journal):
    r = _reponse(400, {"type": "error", "error": {"type": "invalid_request_error", "message": "prompt is too long"}})
    e = d.erreur_du_modele(r, "chat")
    assert e.status_code == 502
    assert e.detail == d.MODELE_INDISPONIBLE
    assert "prompt" not in e.detail and "invalid_request_error" not in e.detail and "400" not in e.detail
    assert any("invalid_request_error" in l and "req_123" in l for l in journal.lignes)


@pytest.mark.parametrize("message", ["Your credit balance is too low", "You have reached your specified API usage limits"])
def test_credit_et_plafond_gardent_le_message_doux(message):
    e = d.erreur_du_modele(_reponse(400, {"type": "error", "error": {"type": "invalid_request_error", "message": message}}), "x")
    assert e.status_code == 502 and e.detail == d.MODELE_EN_PAUSE


def test_corps_non_json_ne_part_pas(journal):
    e = d.erreur_du_modele(_reponse(500, texte="Traceback (most recent call last): interne"), "accompagnement")
    assert e.status_code == 502 and e.detail == d.MODELE_INDISPONIBLE
    assert not any("Traceback" in l for l in journal.lignes)


class _ClientEnErreur:
    async def post(self, url, json=None, headers=None, timeout=None):
        return _reponse(500, {"type": "error", "error": {"type": "api_error", "message": "Internal server error"}})


def _simulacres(monkeypatch):
    async def rien(*a, **k):
        return None

    async def ident(*a, **k):
        return {"svlbh_id": "52adbc98-d2b0-4444-b89c-b1311a02a983", "uid": "u", "stx": "ST3"}

    async def prompt():
        return {"core": "CŒUR", "tuteur_frame": "T", "accompagnement_frame": "A", "st3": "S", "version": "t"}

    async def historique(client, key, msgs):
        return None, msgs, 0

    async def vide(*a, **k):
        return ""

    async def zero(*a, **k):
        return 0

    async def liste(*a, **k):
        return []

    async def canal(*a, **k):
        return "z2"

    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    for nom, f in {"authorize_caller": rien, "gate_subscription": ident, "fetch_prompt": prompt,
                   "_compter_accompagnement": zero, "preparer_historique": historique, "canal_digisha": canal,
                   "contexte_personne": vide, "relecture_pour": vide, "savoir_pour": vide, "fetch_banque_qr": liste,
                   "lexique_patrick": vide, "_rpc_service": rien, "_rpc_personne": rien}.items():
        monkeypatch.setattr(d, nom, f)
    monkeypatch.setattr(d, "refuser_st1", lambda ident: None)
    monkeypatch.setattr(d, "passer_en_5_5", lambda payload, svlbh: payload["model"])
    monkeypatch.setattr(d, "_http", lambda: _ClientEnErreur())


def test_les_deux_routes_renvoient_le_message_generique(monkeypatch, journal):
    _simulacres(monkeypatch)
    tour = [d.ChatTurn(role="user", content=QUESTION)]
    with pytest.raises(HTTPException) as e1:
        asyncio.run(d.digisha_chat(request=None, body=d.ChatRequest(messages=tour), x_digisha_token=None,
                                   authorization="Bearer t"))
    with pytest.raises(HTTPException) as e2:
        asyncio.run(d.digisha_accompagnement(request=None, body=d.AccompagnementRequest(messages=tour),
                                             x_digisha_token=None, authorization="Bearer t"))
    for e in (e1, e2):
        assert e.value.status_code == 502 and e.value.detail == d.MODELE_INDISPONIBLE
    assert journal.lignes and not any(QUESTION in l for l in journal.lignes)
