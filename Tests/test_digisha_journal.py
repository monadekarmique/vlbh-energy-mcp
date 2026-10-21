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


# ── Journal Render : identifiants masqués, ni IP ni user-agent ──────────────────────────────────────────────────

def test_extrait_journal_masque_les_uuid_avant_de_couper():
    from routers.digisha_memoire import extrait_journal
    corps = '{"message":"aucune fiche « soi » pour 52adbc98-d2b0-4444-b89c-b1311a02a983","code":"P0001"}'
    assert extrait_journal(corps) == '{"message":"aucune fiche « soi » pour 52adbc98…","code":"P0001"}'
    assert extrait_journal("A 688A23C1-F09E-48D7-BE5B-DD24C101C1C1 B") == "A 688A23C1… B"
    # Un UUID à cheval sur la limite : masqué d'abord, coupé ensuite — rien au-delà des 8 premiers caractères.
    tranche = extrait_journal("x" * 190 + " " + X, 200)
    assert len(tranche) <= 200 and "f09e" not in tranche and "688a23c1" in tranche
    assert extrait_journal(None) == "" and extrait_journal("court") == "court"
    assert len(extrait_journal("y" * 5000)) == 200


def _requete():
    from starlette.requests import Request
    return Request({"type": "http", "method": "POST", "path": "/digisha/chat", "query_string": b"",
                    "headers": [(b"user-agent", b"SondeUA/9.9"), (b"x-forwarded-for", b"203.0.113.77")],
                    "client": ("203.0.113.77", 4242)})


def test_appel_sans_session_refuse_sans_ip_ni_ua(monkeypatch, caplog):
    monkeypatch.delenv("DIGISHA_JETON_SEUL", raising=False)
    with caplog.at_level("WARNING", logger="digisha"):
        with pytest.raises(d.HTTPException):
            asyncio.run(d.authorize_caller(_requete(), None, None))
    assert "/digisha/chat" in caplog.text
    assert "SondeUA" not in caplog.text and "203.0.113.77" not in caplog.text


def test_jeton_statique_sans_ip_ni_ua(monkeypatch, caplog):
    cles = []

    async def quota(cle, limite):
        cles.append(cle)

    monkeypatch.setenv("DIGISHA_JETON_SEUL", "oui")
    monkeypatch.setattr(d, "verify_digisha_token", lambda t: None)
    monkeypatch.setattr(d, "_quota", quota)
    with caplog.at_level("WARNING", logger="digisha"):
        assert asyncio.run(d.authorize_caller(_requete(), "jeton", None)) is None
    assert "jeton statique SANS session" in caplog.text
    assert "SondeUA" not in caplog.text and "203.0.113.77" not in caplog.text
    assert cles == ["ip:203.0.113.77"]          # le quota par IP reste, hors journal
