"""digisha_chat_log : un tour qui porte le fil d'une personne en contexte n'y entre jamais (carte b8d68119), sur /chat
(mode « fil ») comme sur /accompagnement (fil_consultante_id), quoi qu'envoie l'écran (no_log absent ou faux)."""
import asyncio

import pytest

from routers import digisha as d

X = "688a23c1-f09e-48d7-be5b-dd24c101c1c1"


class _Client:
    async def post(self, url, json=None, headers=None, timeout=None):
        class R:
            status_code = 200
            text = ""

            def json(self_inner):
                return {"content": [{"type": "text", "text": "R"}], "stop_reason": "end_turn",
                        "usage": {"input_tokens": 1, "output_tokens": 1}}
        return R()


@pytest.fixture
def journal(monkeypatch):
    ecrits = []

    async def rien(*a, **k):
        return None

    async def log_exchange(*a, **k):
        ecrits.append(a[1] if len(a) > 1 else k.get("mode"))

    async def ident(*a, **k):
        return {"svlbh_id": "52adbc98-d2b0-4444-b89c-b1311a02a983", "uid": "u", "stx": "ST6"}

    async def prompt():
        return {"core": "C", "tuteur_frame": "T", "accompagnement_frame": "A", "st3": "S", "version": "t"}

    async def historique(client, key, msgs):
        return None, msgs, 0

    async def canal(*a, **k):
        return "z2"

    async def vide(*a, **k):
        return ""

    async def zero(*a, **k):
        return 0

    async def liste(*a, **k):
        return []

    async def passages(cid, q, auth):
        return [{"jour": "12.07", "titre": "T", "corps": "FIL"}], ""

    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    for nom, f in {"authorize_caller": rien, "gate_subscription": ident, "fetch_prompt": prompt,
                   "_compter_accompagnement": zero, "preparer_historique": historique, "canal_digisha": canal,
                   "contexte_personne": vide, "relecture_pour": vide, "peut_relire": rien, "savoir_pour": vide,
                   "passages_du_fil": passages, "fetch_banque_qr": liste, "lexique_patrick": vide,
                   "journaliser_cout": rien, "log_exchange": log_exchange, "fil_digisha_deposer": rien,
                   "_rpc_service": rien, "_rpc_personne": rien}.items():
        monkeypatch.setattr(d, nom, f)
    monkeypatch.setattr(d, "journaliser_usage", lambda *a, **k: None)
    monkeypatch.setattr(d, "passer_en_5_5", lambda payload, svlbh: payload["model"])
    monkeypatch.setattr(d, "_http", lambda: _Client())
    return ecrits


TOUR = [d.ChatTurn(role="user", content="Q")]


def _chat(**k):
    return d.digisha_chat(request=None, body=d.ChatRequest(messages=TOUR, **k), x_digisha_token=None,
                          authorization="Bearer t")


def _accompagnement(**k):
    return d.digisha_accompagnement(request=None, body=d.AccompagnementRequest(messages=TOUR, **k),
                                    x_digisha_token=None, authorization="Bearer t")


def test_chat_en_mode_fil_ne_journalise_pas(journal):
    asyncio.run(_chat(mode="fil", fil_consultante_id=X))
    assert journal == []


def test_chat_tuteur_journalise_toujours(journal):
    asyncio.run(_chat())
    assert journal == ["st2"]


def test_accompagnement_avec_fil_ne_journalise_pas(journal):
    asyncio.run(_accompagnement(fil_consultante_id=X))
    assert journal == []


def test_accompagnement_sans_fil_journalise(journal):
    asyncio.run(_accompagnement())
    assert journal == ["accompagnement"]


def test_journal_permis_une_seule_regle():
    assert d.journal_permis(d.ChatRequest(messages=TOUR))
    assert not d.journal_permis(d.ChatRequest(messages=TOUR, no_log=True))
    assert not d.journal_permis(d.ChatRequest(messages=TOUR, mode="fil", fil_consultante_id=X))
    assert d.journal_permis(d.AccompagnementRequest(messages=TOUR))
    assert not d.journal_permis(d.AccompagnementRequest(messages=TOUR, fil_consultante_id=X))
