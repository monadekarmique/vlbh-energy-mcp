"""Un terme du lexique peut porter une illustration ; DiGiSha la désigne, la réponse la rend (carte 0eceae35, 04.11.2026).

Patrick, 04.11.2026 : « y-a-t-il possibilité d'ajouter des images ou des stickers à cette explication ? » (Gui et Gu)."""
import asyncio

from routers import digisha as d
from routers import digisha_apprendre as a

LEXIQUE = [{"terme": "Gui", "explication": "« Gui : ancêtre non honoré bloque les descendants »"},
           {"terme": "Gu", "explication": "« Gu : un noeud de toxines énergétiques parasites d'autres monades »"},
           {"terme": "COEX", "explication": "système d'expériences condensées"}]
ILLUS = [{"terme": "Gui", "rang": 1, "genre": "photo", "chemin": "lexique/gui/453a5a81-bba8-42d8-b5a8-f95bda657c10.png",
          "media_type": "image/png", "titre": "Gui", "legende": "ce sont les V qui bloquent"},
         {"terme": "Gu", "rang": 1, "genre": "photo", "chemin": "lexique/gu/9e53e123-516b-4c8d-a41c-e1a077909395.png",
          "media_type": "image/png", "titre": "Gu", "legende": None}]
REPONSE = "Ce sont les V qui bloquent : c'est un Gui.\n⟦Montrer : Gui⟧\n⟦À apprendre : COEX — x⟧"


def _charger():
    a._cache.update(t=0.0, bloc="", illus={})

    async def rpc(nom, corps):
        return {"digisha_lexique": LEXIQUE, "digisha_lexique_illustrations": ILLUS}.get(nom)
    return asyncio.run(a.lexique(rpc, ttl=0))


def test_cle_comme_la_base():
    assert a.cle("4 Gui") == "4gui" and a.cle("Gu toxique") == "gutoxique" and a.cle("Égo errant") == "egoerrant"


def test_le_lexique_marque_les_termes_illustres_et_annonce_la_ligne():
    bloc = _charger()
    assert "## Montrer une illustration" in bloc
    assert "**Gui** : « Gui : ancêtre non honoré bloque les descendants » (illustration : ⟦Montrer : Gui⟧)" in bloc
    assert "**COEX** : système d'expériences condensées" in bloc and "⟦Montrer : COEX⟧" not in bloc


def test_sans_illustration_pas_de_cadre():
    a._cache.update(t=0.0, bloc="", illus={})

    async def rpc(nom, corps):
        return LEXIQUE if nom == "digisha_lexique" else []
    assert "Montrer" not in asyncio.run(a.lexique(rpc, ttl=0))


def test_panne_des_illustrations_garde_les_dernieres():
    _charger()

    async def rpc(nom, corps):
        return LEXIQUE if nom == "digisha_lexique" else None
    assert "⟦Montrer : Gui⟧" in asyncio.run(a.lexique(rpc, ttl=0))


def test_extraire_montrer_deux_au_plus_sans_doublon():
    propre, termes = a.extraire_montrer("Texte.\n⟦Montrer : Gui⟧\n⟦Montrer : « gui »⟧\n⟦Montrer : Gu⟧\n⟦Montrer : COEX⟧")
    assert propre == "Texte." and termes == ["Gui", "Gu"]


def test_illustrations_forme_d_une_piece_gardee_et_terme_inconnu_ignore():
    _charger()
    pieces = a.illustrations(["gui", "Inconnu"], "16h20")
    assert pieces == [{"heure": "16h20", "genre": "photo", "chemin": ILLUS[0]["chemin"], "media_type": "image/png", "titre": "Gui"}]
    assert a.marques(pieces) == "[illustration : Gui]"


def test_accompagnement_rend_l_image_et_la_depose_dans_le_fil(monkeypatch):
    depots, pieces, systemes = [], [], []

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
        if nom == "digisha_lexique":
            return LEXIQUE
        if nom == "digisha_lexique_illustrations":
            return ILLUS
        if nom == "digisha_page_pieces_ajouter":
            pieces.append(corps)
            return 1
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

    a._cache.update(t=0.0, bloc="", illus={})
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    for nom, f in {"authorize_caller": rien, "gate_subscription": ident, "fetch_prompt": prompt, "_compter_accompagnement": zero,
                   "preparer_historique": historique, "canal_digisha": canal, "contexte_personne": vide, "relecture_pour": vide,
                   "savoir_pour": vide, "fetch_banque_qr": liste, "journaliser_cout": rien, "log_exchange": rien,
                   "fil_digisha_deposer": deposer, "_rpc_service": service, "_rpc_personne": rien}.items():
        monkeypatch.setattr(d, nom, f)
    monkeypatch.setattr(d, "refuser_st1", lambda ident: None)
    monkeypatch.setattr(d, "journaliser_usage", lambda *x, **k: None)
    monkeypatch.setattr(d, "passer_en_5_5", lambda payload, svlbh: payload["model"])
    monkeypatch.setattr(d, "heure_zurich", lambda: "16h20")
    monkeypatch.setattr(d, "_http", lambda: Client())
    corps = d.AccompagnementRequest(messages=[d.ChatTurn(role="user", content="Comment je sais que c'est un gui / gu ?")])
    rep = asyncio.run(d.digisha_accompagnement(request=None, body=corps, x_digisha_token=None, authorization="Bearer t"))
    assert rep.reply == "Ce sont les V qui bloquent : c'est un Gui."
    assert rep.illustrations == [{"heure": "16h20", "genre": "photo", "chemin": ILLUS[0]["chemin"], "media_type": "image/png",
                                  "titre": "Gui"}]
    assert depots == ["Ce sont les V qui bloquent : c'est un Gui.\n[illustration : Gui]"]
    assert pieces == [{"p_session": "seance", "p_pieces": [dict(rep.illustrations[0], role="digisha")]}]
    dernier = systemes[0]["messages"][-1]["content"][0]["text"]
    assert "(illustration : ⟦Montrer : Gui⟧)" in dernier


def test_sans_ligne_montrer_rien_ne_change():
    _charger()
    propre, termes = a.extraire_montrer("Bonjour.")
    assert (propre, termes, a.illustrations(termes, "16h20")) == ("Bonjour.", [], [])
