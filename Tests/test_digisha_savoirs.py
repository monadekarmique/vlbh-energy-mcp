"""Les savoirs des apps (06.11.2026) : DiGiSha les cherche par l'outil chercher_savoir, à son stade ; et la marque
⟦Corrigé : …⟧ range une correction de Patrick dans le lexique."""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from routers import digisha_savoirs as sv
from routers.digisha_apprendre import corriger_en_seance, extraire_corrige, texte_de_correction


def _premier(savoir, requete, stade):
    r = json.loads(sv.chercher(savoir, requete, stade))
    return r, (r["resultats"][0]["entree"] if r.get("resultats") else None)


def test_les_sept_savoirs_sont_charges():
    assert set(sv.SAVOIRS) == {"rose_des_vents", "types_de_lmasc", "sephiroth_chromatique", "wu_shen_dynapathomu",
                               "hdom_phantom", "dodecaedre_branches", "meridiens_vifa"}
    for s in sv.SAVOIRS.values():
        assert s["versions"] and all(v["entrees"] and v["source"] and v["stade"] in (2, 3, 4, 5) for v in s["versions"])


def test_la_table_des_meridiens_porte_chong_mai():
    """07.11.2026 — Patrick : « ouvrir la table des méridiens dans svlbh-priv-4 pour extraire les informations Chong Mai »."""
    chong = _premier("meridiens_vifa", "Chong Mai", 2)[1]
    assert chong["abbr"] == "Chg" and chong["genre"] == "vaisseau extraordinaire" and chong["yuanPoint"] == "SP4 Gongsun"
    assert "Mer du Sang" in chong["protectionNote"] and "color" not in chong
    # lue au cœur (svlbh-core SVLBHMeridiens20, v0.198.0) : le Triple Réchauffeur est TE, jamais TH (DEC Patrick 04.08)
    abbrs = {e["abbr"] for e in sv.SAVOIRS["meridiens_vifa"]["versions"][0]["entrees"]}
    assert "TE" in abbrs and "TH" not in abbrs and len(abbrs) == 20
    assert sv.SAVOIRS["meridiens_vifa"]["versions"][0]["source"].startswith("svlbh-core/")


def test_le_dodecaedre_par_niveau():
    """07.11.2026 — Patrick : « la face 5 fenêtre 7h-9h Na Zi Fa Chén 5ème des 12 branches terrestres ». Niveau 1 = ST2,
    Niveau 2 = ST3, Niveau 3 = ST5 (DEC Patrick 04.08.2026)."""
    face5 = lambda st: _premier("dodecaedre_branches", "face 5 Chén", st)[1]
    assert face5(2)["fenetre"] == "7 h – 9 h (Na Zi Fa)" and face5(2)["meridien"] == "ST — Estomac" and "harmonie_六合" not in face5(2)
    assert face5(3)["harmonie_六合"] == "酉 Yǒu" and "linggui_bafa" not in face5(3)
    assert face5(5)["linggui_bafa"]["valeur_de_la_branche"] == 10 and face5(6)["opposition_六沖"] == "戌 Xū"
    assert [v["stade"] for v in sv.SAVOIRS["dodecaedre_branches"]["versions"]] == [2, 3, 5]


def test_une_cle_se_trouve_en_premier():
    assert _premier("rose_des_vents", "NNO", 2)[1]["cle"] == "NNO"
    assert _premier("types_de_lmasc", "KI-DE-03", 2)[1]["cle"] == "KI-DE-03"
    assert _premier("hdom_phantom", "GV4", 2)[1]["nom"] == "Porte du Sacrum"
    assert _premier("wu_shen_dynapathomu", "hun→shen", 2)[1]["cle"] == "hun→shen"


def test_le_stade_ferme_ce_qui_est_au_dessus():
    # D22 vit dans Ancrage (z3) : une ST2 ne la lit pas, une ST3 oui.
    assert json.loads(sv.chercher("hdom_phantom", "D22", 2))["trouves"] == 0
    assert json.loads(sv.chercher("hdom_phantom", "D22", 3))["trouves"] > 0
    # La DynaPathoMu de Pro Core (z4) n'apparaît qu'en ST4.
    sources = lambda st: {r["source"] for r in json.loads(sv.chercher("wu_shen_dynapathomu", "cascade", st))["resultats"]}
    assert not any("Pro Core" in s for s in sources(3))
    assert sv.versions_lisibles(sv.SAVOIRS["wu_shen_dynapathomu"], 4)[-1]["app"] == "SVLBH Pro Core"


def test_pas_d_outil_en_st1_ni_sans_stade():
    assert sv.outil(1) is None and sv.outil(0) is None
    assert sv.stade_de("ST4") == 4 and sv.stade_de(None) == 0 and sv.stade_de("ST6") == 6


def test_lmasc_une_seule_entree_par_type():
    cles = [e["cle"] for _, e in sv._entrees(sv.SAVOIRS["types_de_lmasc"], 9)]
    assert len(cles) == len(set(cles))


def test_requete_vide_rend_la_liste_des_cles():
    r = json.loads(sv.chercher("rose_des_vents", "", 3))
    assert [v["stade"] for v in r["versions"]] == ["ST2", "ST3"] and "NNE" in r["versions"][0]["cles"]


def test_le_resultat_est_borne_et_nomme_ce_qu_il_coupe():
    assert len(sv.chercher("hdom_phantom", "chakra symptomes signes", 9)) <= sv.MAX_CAR_RESULTAT
    r = json.loads(sv.chercher("types_de_lmasc", "LR foie", 4))
    assert r["trouves"] > len(r["resultats"])
    assert any(x.startswith("LR-DE-") for x in r["autres_a_redemander_par_cle"])


def test_la_boucle_execute_l_outil_puis_rend_la_reponse():
    appels = []

    async def poster(p):
        appels.append(json.loads(json.dumps(p)))
        if len(appels) == 1:
            return {"stop_reason": "tool_use", "usage": {"input_tokens": 10, "output_tokens": 5},
                    "content": [{"type": "tool_use", "id": "t1", "name": "chercher_savoir",
                                 "input": {"savoir": "rose_des_vents", "requete": "NNO"}}]}
        return {"stop_reason": "end_turn", "usage": {"input_tokens": 20, "output_tokens": 7},
                "content": [{"type": "text", "text": "NNO : Endométriose…"}]}

    data, faites = asyncio.run(sv.appeler_avec_savoirs(poster, {"messages": [{"role": "user", "content": "NNO ?"}]}, 2))
    assert faites == ["rose_des_vents:NNO"]
    assert data["usage"] == {"input_tokens": 30, "output_tokens": 12}
    assert appels[0]["tools"][0]["name"] == "chercher_savoir"
    resultat = appels[1]["messages"][-1]["content"][0]
    assert resultat["type"] == "tool_result" and "NNO" in resultat["content"]


def test_la_boucle_s_arrete_apres_deux_recherches():
    appels = []

    async def poster(p):
        appels.append(p.get("tool_choice"))
        if p.get("tool_choice") == {"type": "none"}:
            return {"stop_reason": "end_turn", "usage": {}, "content": [{"type": "text", "text": "ok"}]}
        return {"stop_reason": "tool_use", "usage": {},
                "content": [{"type": "tool_use", "id": f"t{len(appels)}", "name": "chercher_savoir",
                             "input": {"savoir": "hdom_phantom", "requete": "GV4"}}]}

    payload = {"messages": []}
    data, faites = asyncio.run(sv.appeler_avec_savoirs(poster, payload, 3))
    assert len(faites) == sv.MAX_TOURS_OUTIL and appels[-1] == {"type": "none"} and data["stop_reason"] == "end_turn"
    assert payload["messages"][-1]["content"][-1] == {"type": "text", "text": sv.DERNIERE_PASSE}


def test_sans_stade_aucun_outil_n_est_envoye():
    vus = []

    async def poster(p):
        vus.append(p)
        return {"stop_reason": "end_turn", "usage": {}, "content": []}

    asyncio.run(sv.appeler_avec_savoirs(poster, {"messages": []}, 1))
    assert "tools" not in vus[0]


# ── La marque ⟦Corrigé : …⟧ ──────────────────────────────────────────────────────────────────────────────────────

def test_la_marque_corrige_est_retiree_et_lue():
    t, c = extraire_corrige("Tu as raison.\n⟦Corrigé : absinthe — la table des Dark entities de HVLBH Priv-6 la libère⟧")
    assert t == "Tu as raison."
    assert c == [("absinthe", "la table des Dark entities de HVLBH Priv-6 la libère")]


def test_deux_corrections_au_plus_sans_doublon():
    _, c = extraire_corrige("x\n⟦Corrigé : A — 1⟧\n⟦Corrigé : a — 2⟧\n⟦Corrigé : B⟧\n⟦Corrigé : C — 3⟧")
    assert c == [("A", "1"), ("B", "")]


def test_ses_mots_d_abord():
    assert texte_de_correction("Correction : c'est GV20", "porte du Sommet", "06.11.2026") == \
        "Correction de Patrick du 06.11.2026 : « Correction : c'est GV20 » — retenu : porte du Sommet"


def test_la_correction_part_en_base_par_la_porte_de_patrick():
    vus = []

    async def rpc(nom, args):
        vus.append((nom, args))
        return "nouveau"

    r = asyncio.run(corriger_en_seance(rpc, [("absinthe", "Dark entities")], "306c2408", "Correction : …", "06.11.2026"))
    assert r == ["nouveau"]
    assert vus == [("digisha_a_apprendre_appris_en_seance",
                    {"p_terme": "absinthe", "p_svlbh": "306c2408",
                     "p_texte": "Correction de Patrick du 06.11.2026 : « Correction : … » — retenu : Dark entities"})]
    assert asyncio.run(corriger_en_seance(rpc, [("x", "")], None, "m", "j")) == []


def test_un_chiffre_seul_departage_les_faces():
    """14.11.2026 — servi le 13.11 : « face 8 » rendait les faces 1 et 2 (le chiffre était jeté, « face » est dans toutes
    les clés), et DiGiSha cherchait une seconde fois par le nom entier."""
    for n, nom in ((8, "Face 8"), (5, "Face 5"), (7, "Face 7"), (10, "Face 10")):
        d = json.loads(sv.chercher("dodecaedre_branches", f"face {n}", 9))
        assert str(d["resultats"][0]["entree"]["cle"]).startswith(nom + " "), (n, d["resultats"][0]["entree"]["cle"])


def test_une_entree_deja_rendue_dans_la_reponse_est_nommee_pas_renvoyee():
    deja: set = set()
    un = json.loads(sv.chercher("dodecaedre_branches", "face 8", 9, deja))
    cles = [str(r["entree"]["cle"]) for r in un["resultats"]]
    assert cles and deja
    deux_texte = sv.chercher("dodecaedre_branches", "Face 8 — 未 Wèi", 9, deja)
    deux = json.loads(deux_texte)
    assert cles[0] in deux["deja_rendues_plus_haut_dans_cette_reponse"]
    assert cles[0] not in [str(r["entree"]["cle"]) for r in deux["resultats"]]
    # Sans mémoire (un autre message), la même recherche rend l'entrée entière.
    assert cles[0] in [str(r["entree"]["cle"]) for r in json.loads(sv.chercher("dodecaedre_branches", "Face 8 — 未 Wèi", 9))["resultats"]]
