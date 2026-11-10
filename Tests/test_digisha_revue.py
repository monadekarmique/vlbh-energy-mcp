"""Comptes de revue des magasins : réponse fixe, sans modèle (DEC Patrick 10.11.2026 : « oui fait répondre aux comptes de
revue sans appeler le modèle »). Mesuré le 10.11 : 71 appels en 7 jours du robot de Google Play sur le compte de démo."""
import asyncio

import routers.digisha as d

REVUE = "a4732493-9331-43dc-8590-5850bc3e00c6"


def test_les_deux_comptes_de_revue_sont_reconnus_et_pas_une_praticienne():
    assert d.compte_de_revue({"uid": REVUE, "svlbh_id": "eab72ae5-65a6-4050-90cf-5d371d527744"})
    assert d.compte_de_revue({"uid": "3B5D4229-6987-4148-8397-4986E7E810ED"})
    assert not d.compte_de_revue({"uid": "1ba5116b-b939-4389-a16b-5d27f57e6b0b"})      # Anne
    assert not d.compte_de_revue(None)


def _sans_modele(monkeypatch, uid):
    async def rien(*a, **k):
        return None

    async def ident(*a, **k):
        return {"uid": uid, "svlbh_id": "x", "profondeur": True, "stx": "ST5"}

    async def interdit(*a, **k):
        raise AssertionError("le modèle ou la base ne doivent pas être appelés pour un compte de revue")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setattr(d, "authorize_caller", rien)
    monkeypatch.setattr(d, "gate_subscription", ident)
    monkeypatch.setattr(d, "refuser_st1", lambda ident: None)
    monkeypatch.setattr(d, "heure_zurich", lambda: "11h05")
    for nom in ("fetch_prompt", "preparer_historique", "journaliser_cout", "log_exchange", "fil_digisha_deposer"):
        monkeypatch.setattr(d, nom, interdit)


def test_accompagnement_d_un_compte_de_revue_repond_sans_modele(monkeypatch):
    _sans_modele(monkeypatch, REVUE)
    corps = d.AccompagnementRequest(messages=[d.ChatTurn(role="user", content="REVIEW-AND-E1952AC2 Malachim Beth (ב)")])
    rep = asyncio.run(d.digisha_accompagnement(request=None, body=corps, x_digisha_token=None, authorization="Bearer t"))
    assert rep.reply == d.REPONSE_REVUE and rep.model == "revue-sans-modele" and rep.heure == "11h05"


def test_chat_d_un_compte_de_revue_repond_sans_modele(monkeypatch):
    _sans_modele(monkeypatch, REVUE)
    corps = d.ChatRequest(messages=[d.ChatTurn(role="user", content="Bonjour")])
    rep = asyncio.run(d.digisha_chat(request=None, body=corps, x_digisha_token=None, authorization="Bearer t"))
    assert rep.reply == d.REPONSE_REVUE and rep.model == "revue-sans-modele"
