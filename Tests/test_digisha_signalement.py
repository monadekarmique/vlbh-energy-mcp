"""Le signalement silencieux de DiGiSha, porté de Pro web au serveur (carte 38e837cf, 15.11.2026).

Patrick, 15.11.2026 à 12h19 : « Porte-le sur le serveur ». Mêmes bornes que svlbh-pro-web/src/lib/ai/signalement.ts (et ses
tests) : 3 par heure, 10 sur 24 heures, motif sur une ligne de 500 caractères au plus, 2 000 avec l'extrait."""
import asyncio
import json

from routers import digisha as d
from routers import digisha_apprendre as a
from routers import digisha_savoirs as sv
from routers import digisha_signalement as sg

IDENT = {"svlbh_id": "8f494efd-df0c-4f07-bbb1-8ff7a2a44892", "uid": "b4c8f74b-822a-40db-b9a3-ac73f8c4ccf7", "stx": "ST4"}


# ── Les fonctions pures, comme sur Pro web ─────────────────────────────────────────────────────────────────────────

def test_le_motif_tient_sur_une_ligne_et_l_extrait_garde_ses_lignes():
    ok, v = sg.valider({"motif": "  une personne\nvivante\x07  en danger  ", "extrait": "ligne 1\r\nligne 2\x00"})
    assert ok and v == {"motif": "une personne vivante en danger", "extrait": "ligne 1\nligne 2"}


def test_une_entree_sans_motif_lisible_est_refusee():
    for entree in (None, [], "texte", {}, {"motif": 3}, {"motif": "   "}, {"motif": "m", "extrait": 4}):
        ok, erreur = sg.valider(entree)
        assert not ok and isinstance(erreur, str)


def test_le_texte_est_coupe_jamais_refuse():
    ok, v = sg.valider({"motif": "m" * 900, "extrait": "e" * 3000})
    assert ok
    assert len(v["motif"]) == sg.MOTIF_MAX and v["motif"].endswith(" […]")
    assert len(v["motif"]) + len(v["extrait"]) == sg.TEXTE_MAX and v["extrait"].endswith(" […]")
    assert sg.borner("abc", 2) == "ab" and sg.borner("abc", 3) == "abc"


def test_le_commentaire_a_la_forme_de_pro_web():
    assert sg.composer_commentaire({"motif": "M", "extrait": None}) == "[DiGiSha · signalement auto] M"
    assert sg.composer_commentaire({"motif": "M", "extrait": "E"}, "uid-1") == "[DiGiSha · signalement auto · compte uid-1] M\n— E"


def test_les_plafonds_et_la_journee():
    assert sg.plafond(3, 10) is None and sg.plafond(4, 1) == "heure" and sg.plafond(1, 11) == "jour"
    # une heure pleine ne laisse pas passer plus de 3 : les tentatives refusées ne comptent pas pour la journée
    assert sg.signalements_sur_le_jour([{"n": 7}, {"n": 2}, {"n": "x"}, {"n": True}, {}, None]) == 5
    gardes, heure, jour = sg.compter_en_memoire([0.0, 50_000.0, 99_000.0], 100_000.0)
    assert gardes == [50_000.0, 99_000.0] and heure == 2 and jour == 3


# ── Le dépôt, avec une fausse base ─────────────────────────────────────────────────────────────────────────────────

def _base(compteur=None, lignes=None, refus=None):
    appels = {"rpc": [], "lire": [], "inserer": []}

    async def rpc(nom, corps, timeout=10):
        appels["rpc"].append((nom, corps))
        return compteur

    async def lire(chemin):
        appels["lire"].append(chemin)
        return lignes

    async def inserer(table, ligne):
        appels["inserer"].append((table, ligne))
        return refus
    return appels, dict(rpc_service=rpc, lire_service=lire, inserer_service=inserer)


def _deposer(entree, ident=IDENT, **base):
    return json.loads(asyncio.run(sg.deposer(entree, ident, maintenant=1_000_000.0, **base)))


def test_un_signalement_part_dans_la_file_avec_l_auteur_de_la_session():
    sg._acceptes.clear()
    appels, base = _base(compteur={"n": 1, "ok": True}, lignes=[{"n": 1}, {"n": 2}])
    r = _deposer({"motif": "Une personne vivante possiblement en danger", "extrait": "« il me menace »",
                  "author_svlbh_id": "ignoré : jamais lu"}, **base)
    assert r == {"ok": True}
    assert appels["rpc"] == [("digisha_appel_heure_incr", {"p_cle": f"signaler:{IDENT['uid']}", "p_limite": 3})]
    assert "cle=eq.signaler%3A" in appels["lire"][0] and "heure=gt." in appels["lire"][0]
    assert appels["inserer"] == [("feedback_queue", {
        "author_svlbh_id": IDENT["svlbh_id"], "author_stx": "ST4",
        "comment": "[DiGiSha · signalement auto] Une personne vivante possiblement en danger\n— « il me menace »",
        "status": "pending", "source": "digisha-auto"})]


def test_au_dela_de_trois_par_heure_rien_n_est_depose():
    sg._acceptes.clear()
    appels, base = _base(compteur={"n": 4, "ok": False})
    r = _deposer({"motif": "m"}, **base)
    assert "plafond" in r["erreur"] and "3 par heure" in r["erreur"] and "n'en parle pas" in r["erreur"]
    assert appels["inserer"] == [] and appels["lire"] == []


def test_au_dela_de_dix_sur_24_heures_rien_n_est_depose():
    sg._acceptes.clear()
    appels, base = _base(compteur={"n": 2, "ok": True}, lignes=[{"n": 3}] * 3 + [{"n": 2}])
    r = _deposer({"motif": "m"}, **base)
    assert "10 sur 24 heures" in r["erreur"] and appels["inserer"] == []


def test_base_muette_le_compte_se_fait_en_memoire():
    sg._acceptes.clear()
    appels, base = _base(compteur=None)
    resultats = [_deposer({"motif": f"m{i}"}, **base) for i in range(4)]
    assert [x.get("ok") for x in resultats[:3]] == [True, True, True]
    assert "3 par heure" in resultats[3]["erreur"] and len(appels["inserer"]) == 3


def test_un_refus_d_ecriture_se_dit_au_modele_sans_lever():
    sg._acceptes.clear()
    appels, base = _base(compteur={"n": 1, "ok": True}, lignes=[{"n": 1}], refus="HTTP 401 permission denied")
    r = _deposer({"motif": "m"}, **base)
    assert r == {"erreur": "le signalement n'a pas pu être déposé ; n'en parle pas et continue normalement"}


def test_sans_fiche_l_uid_entre_dans_l_en_tete_et_sans_compte_rien_ne_part():
    sg._acceptes.clear()
    appels, base = _base(compteur={"n": 1, "ok": True}, lignes=[{"n": 1}])
    assert _deposer({"motif": "m"}, ident={"uid": "u-9", "svlbh_id": None}, **base) == {"ok": True}
    ligne = appels["inserer"][0][1]
    assert ligne["author_svlbh_id"] is None and ligne["comment"].startswith("[DiGiSha · signalement auto · compte u-9] ")
    appels2, base2 = _base(compteur={"n": 1, "ok": True})
    assert "sans compte" in _deposer({"motif": "m"}, ident={"uid": None}, **base2)["erreur"]
    assert appels2["rpc"] == [] and appels2["inserer"] == []
    appels3, base3 = _base(compteur={"n": 1, "ok": True})
    assert "motif requis" in _deposer({"extrait": "e"}, **base3)["erreur"] and appels3["rpc"] == []


# ── La boucle d'outils ─────────────────────────────────────────────────────────────────────────────────────────────

def test_la_boucle_offre_les_deux_outils_et_n_ecrit_pas_le_signalement_dans_les_recherches():
    appels, recus = [], []

    async def poster(p):
        appels.append(json.loads(json.dumps(p)))
        if len(appels) == 1:
            return {"stop_reason": "tool_use", "usage": {"input_tokens": 10, "output_tokens": 5},
                    "content": [{"type": "tool_use", "id": "t1", "name": "signaler_difficulte", "input": {"motif": "M"}},
                                {"type": "tool_use", "id": "t2", "name": "chercher_savoir",
                                 "input": {"savoir": "rose_des_vents", "requete": "NNO"}}]}
        return {"stop_reason": "end_turn", "usage": {"input_tokens": 20, "output_tokens": 7},
                "content": [{"type": "text", "text": "Réponse."}]}

    async def executeur(entree):
        recus.append(entree)
        return '{"ok": true}'

    data, faites = asyncio.run(sv.appeler_avec_savoirs(
        poster, {"messages": [{"role": "user", "content": "?"}]}, 2, autres={sg.OUTIL_NOM: (sg.OUTIL, executeur)}))
    assert [t["name"] for t in appels[0]["tools"]] == ["chercher_savoir", "signaler_difficulte"]
    assert recus == [{"motif": "M"}] and faites == ["rose_des_vents:NNO"]
    resultats = appels[1]["messages"][-1]["content"]
    assert resultats[0] == {"type": "tool_result", "tool_use_id": "t1", "content": '{"ok": true}'}
    assert data["usage"] == {"input_tokens": 30, "output_tokens": 12}


def test_sans_savoir_le_signalement_reste_offert():
    vus = []

    async def poster(p):
        vus.append(p)
        return {"stop_reason": "end_turn", "usage": {}, "content": []}

    async def executeur(entree):
        return "{}"

    asyncio.run(sv.appeler_avec_savoirs(poster, {"messages": []}, 1, autres={sg.OUTIL_NOM: (sg.OUTIL, executeur)}))
    assert [t["name"] for t in vus[0]["tools"]] == ["signaler_difficulte"]


# ── L'accompagnement entier : le modèle signale, la personne ne voit rien, la file reçoit la ligne ────────────────────

def test_accompagnement_le_signalement_part_en_coulisse(monkeypatch):
    sg._acceptes.clear()
    depots, inserts, modele = [], [], []

    async def rien(*x, **k):
        return None

    async def ident(*x, **k):
        return dict(IDENT)

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
        if nom == "digisha_appel_heure_incr":
            return {"n": 1, "ok": True}
        return None

    async def lire(chemin, timeout=10):
        return [{"n": 1}]

    async def inserer(table, ligne, timeout=10):
        inserts.append((table, ligne))
        return None

    class Client:
        async def post(self, url, json=None, headers=None, timeout=None):
            modele.append(json)
            premier = len(modele) == 1

            class R:
                status_code = 200
                text = ""

                def json(self_inner):
                    if premier:
                        return {"stop_reason": "tool_use", "usage": {"input_tokens": 1, "output_tokens": 1},
                                "content": [{"type": "text", "text": "Je t'entends."},
                                            {"type": "tool_use", "id": "s1", "name": "signaler_difficulte",
                                             "input": {"motif": "Une personne vivante possiblement en danger réel"}}]}
                    return {"stop_reason": "end_turn", "usage": {"input_tokens": 1, "output_tokens": 1},
                            "content": [{"type": "text", "text": "Je t'entends. Reprenons ta mesure."}]}
            return R()

    a._cache.update(t=0.0, bloc="", illus={})
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    for nom, f in {"authorize_caller": rien, "gate_subscription": ident, "fetch_prompt": prompt, "_compter_accompagnement": zero,
                   "preparer_historique": historique, "canal_digisha": canal, "contexte_personne": vide, "relecture_pour": vide,
                   "savoir_pour": vide, "fetch_banque_qr": liste, "journaliser_cout": rien, "log_exchange": rien,
                   "fil_digisha_deposer": deposer, "_rpc_service": service, "_rpc_personne": rien,
                   "_lire_service": lire, "_inserer_service": inserer}.items():
        monkeypatch.setattr(d, nom, f)
    monkeypatch.setattr(d, "refuser_st1", lambda ident: None)
    monkeypatch.setattr(d, "journaliser_usage", lambda *x, **k: None)
    monkeypatch.setattr(d, "passer_en_5_5", lambda payload, svlbh: payload["model"])
    monkeypatch.setattr(d, "heure_zurich", lambda: "16h20")
    monkeypatch.setattr(d, "_http", lambda: Client())
    corps = d.AccompagnementRequest(messages=[d.ChatTurn(role="user", content="Il me menace quand je pars.")])
    rep = asyncio.run(d.digisha_accompagnement(request=None, body=corps, x_digisha_token=None, authorization="Bearer t"))
    assert rep.reply == "Je t'entends. Reprenons ta mesure."
    assert "signal" not in rep.reply.lower() and depots == ["Je t'entends. Reprenons ta mesure."]
    assert "signaler_difficulte" in [t["name"] for t in modele[0]["tools"]]
    assert modele[1]["messages"][-1]["content"][0] == {"type": "tool_result", "tool_use_id": "s1", "content": '{"ok": true}'}
    assert inserts == [("feedback_queue", {
        "author_svlbh_id": IDENT["svlbh_id"], "author_stx": "ST4",
        "comment": "[DiGiSha · signalement auto] Une personne vivante possiblement en danger réel",
        "status": "pending", "source": "digisha-auto"})]
