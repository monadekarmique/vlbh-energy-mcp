"""Carte 5142f03a (15.11.2026) : le résumé de l'historique est compté au coût, et une écriture d'apprentissage qui
n'aboutit pas se dit dans la réponse (non_garde), comme la page du tour."""
import asyncio

from routers import digisha as d
from routers import digisha_apprendre as a
from routers import digisha_memoire as m
from routers import digisha_non_garde as ng

IDENT = {"svlbh_id": "52adbc98-d2b0-4444-b89c-b1311a02a983", "uid": "306c2408-0000-4000-8000-000000000001", "stx": "ST6"}


def conv(n: int) -> list[dict]:
    return [{"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(n)]


class ClientResume:
    def __init__(self):
        self.envois = []

    async def post(self, url, json=None, headers=None, timeout=None):
        self.envois.append(json)

        class R:
            status_code = 200
            text = ""

            def json(self_inner):
                return {"content": [{"type": "text", "text": "Résumé du bloc."}], "stop_reason": "end_turn",
                        "usage": {"input_tokens": 900, "output_tokens": 60}}
        return R()


# ── ① le résumé de l'historique est compté ────────────────────────────────────────────────────────────────────────

def test_un_resume_de_bloc_paye_est_compte_une_fois_et_pas_sa_relecture(monkeypatch):
    monkeypatch.setattr(m, "_resumes", type(m._resumes)())
    couts = []

    async def cout(data):
        couts.append(data["usage"])

    c = ClientResume()
    bloc = conv(10)
    assert asyncio.run(m.resumer_bloc(c, "k", bloc, cout=cout)) == "Résumé du bloc."
    assert asyncio.run(m.resumer_bloc(c, "k", bloc, cout=cout)) == "Résumé du bloc."     # relu du cache
    assert len(c.envois) == 1 and couts == [{"input_tokens": 900, "output_tokens": 60}]


def test_preparer_historique_compte_chaque_bloc_resume(monkeypatch):
    monkeypatch.setattr(m, "_resumes", type(m._resumes)())
    couts = []

    async def cout(data):
        couts.append(data)

    bloc, recents, n = asyncio.run(m.preparer_historique(ClientResume(), "k", conv(35), cout=cout))
    assert n == 2 and len(couts) == 2 and bloc is not None


def test_sans_compteur_rien_ne_change(monkeypatch):
    monkeypatch.setattr(m, "_resumes", type(m._resumes)())
    bloc, recents, n = asyncio.run(m.preparer_historique(ClientResume(), "k", conv(25)))
    assert n == 1 and bloc is not None


def test_un_compteur_en_panne_ne_bloque_pas_le_resume(monkeypatch):
    monkeypatch.setattr(m, "_resumes", type(m._resumes)())

    async def cout(data):
        raise RuntimeError("base muette")

    assert asyncio.run(m.resumer_bloc(ClientResume(), "k", conv(10), cout=cout)) == "Résumé du bloc."


# ── ② les écritures d'apprentissage qui n'aboutissent pas se disent ──────────────────────────────────────────────────

def test_seuls_refus_et_absence_de_reponse_sont_des_echecs():
    assert ng.ecritures_en_echec(["appris", "redefini", "nouveau", "note", "compte", "deja", "gardee", "vide", "exclu"]) == 0
    assert ng.ecritures_en_echec([None, "refus", "appris"]) == 2
    assert ng.ecritures_en_echec(None) == 0 and ng.ecritures_en_echec([]) == 0


def test_le_suivi_dit_une_ecriture_en_echec_une_seule_fois():
    suivi = ng.ouvrir()
    ng.noter_ecritures("appris", ng.MOTIF_APPRIS, ["appris"])
    assert suivi.champs() == {}
    ng.noter_ecritures("appris", ng.MOTIF_APPRIS, [None])
    ng.noter_ecritures("appris", ng.MOTIF_APPRIS, ["refus"])
    assert suivi.champs() == {"non_garde": True, "non_garde_motif": ng.MOTIF_APPRIS}


def _monter(monkeypatch, reponse_modele: str, rpc_service, couts: list, n_messages: int = 1):
    """L'accompagnement entier, comme dans test_digisha_illustrations, sous l'identité de la propriétaire."""
    async def rien(*x, **k):
        return None

    async def ident(*x, **k):
        return dict(IDENT)

    async def prompt():
        return {"core": "CŒUR", "accompagnement_frame": "CADRE", "st3": "ST3", "version": "t"}

    async def canal(*x, **k):
        return "z12"

    async def vide(*x, **k):
        return ""

    async def zero(*x, **k):
        return 0

    async def liste(*x, **k):
        return []

    async def deposer(*x, **k):
        return "seance"

    async def personne(auth, nom, corps, timeout=10):
        return True if nom == "is_owner_st6" else None

    async def cout(source, mode, model, data, **k):
        couts.append((source, mode, model))

    class Client:
        async def post(self, url, json=None, headers=None, timeout=None):
            resume = "Résume cet extrait" in str((json or {}).get("messages", ""))

            class R:
                status_code = 200
                text = ""

                def json(self_inner):
                    texte = "Résumé." if resume else reponse_modele
                    return {"content": [{"type": "text", "text": texte}], "stop_reason": "end_turn",
                            "usage": {"input_tokens": 1, "output_tokens": 1}}
            return R()

    a._cache.update(t=0.0, bloc="", illus={})
    monkeypatch.setattr(m, "_resumes", type(m._resumes)())
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    for nom, f in {"authorize_caller": rien, "gate_subscription": ident, "fetch_prompt": prompt, "_compter_accompagnement": zero,
                   "canal_digisha": canal, "contexte_personne": vide, "relecture_pour": vide, "savoir_pour": vide,
                   "fetch_banque_qr": liste, "journaliser_cout": cout, "log_exchange": rien, "fil_digisha_deposer": deposer,
                   "_rpc_service": rpc_service, "_rpc_personne": personne,
                   "garder_pieces_et_illustrations": rien, "release_courante": rien}.items():
        monkeypatch.setattr(d, nom, f)
    monkeypatch.setattr(d, "refuser_st1", lambda ident: None)
    monkeypatch.setattr(d, "journaliser_usage", lambda *x, **k: None)
    monkeypatch.setattr(d, "passer_en_5_5", lambda payload, svlbh: payload["model"])
    monkeypatch.setattr(d, "heure_zurich", lambda: "13h00")
    monkeypatch.setattr(d, "_http", lambda: Client())
    tours = [d.ChatTurn(role=("user" if i % 2 == 0 else "assistant"), content=f"tour {i}") for i in range(n_messages - 1)]
    corps = d.AccompagnementRequest(messages=tours + [d.ChatTurn(role="user", content="Le Gui, c'est l'ancêtre non honoré.")])
    return asyncio.run(d.digisha_accompagnement(request=None, body=corps, x_digisha_token=None, authorization="Bearer t"))


def _service(appris_rend):
    async def service(nom, corps, timeout=10):
        if nom == "digisha_a_apprendre_appris_en_seance":
            return appris_rend
        return None
    return service


def test_accompagnement_un_enseignement_refuse_se_dit_a_patrick(monkeypatch):
    rep = _monter(monkeypatch, "Rangé, Patrick.\n⟦Appris : Gui⟧", _service(None), [])
    assert rep.reply == "Rangé, Patrick." and rep.non_garde is True and rep.non_garde_motif == ng.MOTIF_APPRIS


def test_accompagnement_un_enseignement_garde_ne_dit_rien(monkeypatch):
    rep = _monter(monkeypatch, "Rangé, Patrick.\n⟦Appris : Gui⟧", _service("appris"), [])
    assert rep.reply == "Rangé, Patrick." and rep.non_garde is False and rep.non_garde_motif is None


def test_accompagnement_long_compte_les_resumes_au_nom_de_la_personne(monkeypatch):
    couts = []
    _monter(monkeypatch, "Bien.", _service("appris"), couts, n_messages=25)
    assert ("render-resume", "accompagnement", m.RESUME_MODEL) in couts
    assert ("render-accompagnement", "accompagnement", d.ACCOMPAGNEMENT_MODEL_PROFONDEUR) in couts \
        or any(s == "render-accompagnement" for s, _, _ in couts)
