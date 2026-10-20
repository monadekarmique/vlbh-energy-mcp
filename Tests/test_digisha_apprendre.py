"""Ce que DiGiSha ne sait pas expliquer part à Patrick ; ce qu'il lui apprend revient en lexique (carte 6f1ef080, 19.10.2026)."""
import asyncio

from routers import digisha as d
from routers import digisha_apprendre as a

REPONSE = ("Je ne sais pas encore l'expliquer ; je le demande à Patrick.\n\nMesure ton Z3.\n"
           "⟦À apprendre : COEX — ce que Patrick appelle un nœud COEX⟧")


def test_la_ligne_part_et_le_terme_reste():
    propre, termes = a.extraire(REPONSE)
    assert "⟦" not in propre and propre.endswith("Mesure ton Z3.")
    assert termes == [("COEX", "ce que Patrick appelle un nœud COEX")]


def test_trait_d_union_deux_au_plus_sans_doublon():
    t = "x\n⟦À apprendre : Sthāna-saṃśraya — le temps 4⟧\n⟦À apprendre : coex : a⟧\n⟦À apprendre : COEX — b⟧\n⟦À apprendre : trois — c⟧"
    propre, termes = a.extraire(t)
    assert propre == "x" and [x for x, _ in termes] == ["Sthāna-saṃśraya", "coex"]


def test_sans_ligne_rien_ne_change():
    assert a.extraire("Bonjour.") == ("Bonjour.", [])


def test_lexique_mis_en_forme_et_panne_garde_le_dernier():
    a._cache.update(t=0.0, bloc="")

    async def rpc(nom, corps):
        return [{"terme": "COEX", "explication": "système d'expériences condensées (Grof)"}]
    bloc = asyncio.run(a.lexique(rpc, ttl=0))
    assert "**COEX** : système d'expériences condensées (Grof)" in bloc

    async def panne(nom, corps):
        return None
    assert asyncio.run(a.lexique(panne, ttl=0)) == bloc


def test_noter_passe_le_terme_et_l_extrait():
    appels = []

    async def rpc(nom, corps):
        appels.append((nom, corps))
        return "note"
    asyncio.run(a.noter(rpc, [("COEX", "x")], "s", "c", "mon z3 et ce noed coex", "réponse"))
    nom, corps = appels[0]
    assert nom == "digisha_a_apprendre_noter" and corps["p_terme"] == "COEX" and corps["p_svlbh"] == "s"
    assert "noed coex" in corps["p_extrait"] and "— DiGiSha : réponse" in corps["p_extrait"]


def test_accompagnement_retire_la_ligne_avant_affichage_et_depot(monkeypatch):
    depots, notes, systemes = [], [], []

    async def rien(*x, **k):
        return None

    async def ident(*x, **k):
        return {"svlbh_id": "8f494efd-df0c-4f07-bbb1-8ff7a2a44892", "uid": "b4c8f74b-822a-40db-b9a3-ac73f8c4ccf7", "stx": "ST4"}

    async def prompt():
        return {"core": "CŒUR", "accompagnement_frame": "CADRE", "st3": "ST3", "version": "t"}

    async def historique(client, key, msgs):
        return None, msgs, 0

    async def canal(*x, **k):
        return "z3"

    async def vide(*x, **k):
        return ""

    async def zero(*x, **k):
        return 0

    async def liste(*x, **k):
        return []

    async def deposer(auth, cible, canal, q, r, mode, pour_elle=False):
        depots.append(r)
        return "seance"

    async def service(nom, corps, timeout=10):
        if nom == "digisha_a_apprendre_noter":
            notes.append(corps["p_terme"])
            return "note"
        if nom == "digisha_lexique":
            return [{"terme": "logoïque", "explication": "projection mentale d'un système masculin ego sur une Âme"}]
        return None

    class Client:
        async def post(self, url, json=None, headers=None, timeout=None):
            systemes.append(json)

            class R:
                status_code = 200
                text = ""

                def json(self_inner):
                    return {"content": [{"type": "text", "text": REPONSE}], "stop_reason": "end_turn",
                            "usage": {"input_tokens": 1, "output_tokens": 1}}
            return R()

    a._cache.update(t=0.0, bloc="")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    for nom, f in {"authorize_caller": rien, "gate_subscription": ident, "fetch_prompt": prompt, "_compter_accompagnement": zero,
                   "preparer_historique": historique, "canal_digisha": canal, "contexte_personne": vide, "relecture_pour": vide,
                   "savoir_pour": vide, "fetch_banque_qr": liste, "journaliser_cout": rien, "log_exchange": rien,
                   "fil_digisha_deposer": deposer, "_rpc_service": service, "_rpc_personne": rien}.items():
        monkeypatch.setattr(d, nom, f)
    monkeypatch.setattr(d, "refuser_st1", lambda ident: None)
    monkeypatch.setattr(d, "journaliser_usage", lambda *x, **k: None)
    monkeypatch.setattr(d, "passer_en_5_5", lambda payload, svlbh: payload["model"])
    monkeypatch.setattr(d, "_http", lambda: Client())
    corps = d.AccompagnementRequest(messages=[d.ChatTurn(role="user", content="mon z3 a à faire avec ce noed coex")])
    rep = asyncio.run(d.digisha_accompagnement(request=None, body=corps, x_digisha_token=None, authorization="Bearer t"))
    assert "⟦" not in rep.reply and "⟦" not in depots[0]
    assert notes == ["COEX"]
    dernier = systemes[0]["messages"][-1]["content"][0]["text"]
    assert "Ce que tu ne sais pas expliquer" in dernier and "**logoïque** : projection mentale" in dernier


def test_appris_retire_la_ligne_et_rend_le_terme():
    propre, termes = a.extraire_appris("Rangé, Patrick.\n⟦Appris : égo errant⟧\n⟦Appris : Égo errant⟧\n⟦Appris : b⟧\n⟦Appris : c⟧")
    assert propre == "Rangé, Patrick." and termes == ["égo errant", "b"]
    assert a.extraire_appris("Bonjour.") == ("Bonjour.", [])


def test_apprendre_en_seance_passe_son_message_tel_quel():
    appels = []

    async def rpc(nom, corps):
        appels.append((nom, corps))
        return "appris"
    msg = "Un Egor en errance qui ne provient pas d’une lignée  et une projection logoïque"
    assert asyncio.run(a.apprendre_en_seance(rpc, ["égo errant"], "52adbc98", msg)) == ["appris"]
    assert appels == [("digisha_a_apprendre_appris_en_seance", {"p_terme": "égo errant", "p_texte": msg, "p_svlbh": "52adbc98"})]
    assert asyncio.run(a.apprendre_en_seance(rpc, ["x"], None, msg)) == [] and len(appels) == 1


def test_le_cadre_annonce_la_ligne_appris():
    assert "⟦Appris : <le terme>⟧" in a.APPRENDRE_CADRE
