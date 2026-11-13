"""Ce que DiGiSha sait de la personne (carte c4b0a17e, 19.10.2026) : tout ce qui a été décodé et discuté pour elle, sans les
relances de DiGiSha (banc : les relances gardées font imiter « Mesure : … ? », 3/3)."""
import asyncio
from unittest.mock import AsyncMock, patch

from routers import digisha
from routers.digisha_contexte import mettre_en_forme, sans_relances

PAGE = ("**Giulia · 03h18 :** C'est z3\n\n**DiGiSha :** Z3 — même fil que SP 19.\n\nMesure : **le SLSA de cette énergie ?**\n\n"
        "**Giulia · 03h19 :** 23% — tu crois que c'est mon père ?\n\n**DiGiSha :** Bleu foncé : la couleur de ton papa (G7).\n\nTu le sens où ?")


def test_les_relances_partent_le_decode_reste():
    t = sans_relances(PAGE)
    assert "Mesure" not in t and "Tu le sens où" not in t
    assert "Z3 — même fil que SP 19." in t and "la couleur de ton papa (G7)" in t


def test_les_paroles_des_personnes_ne_sont_pas_touchees():
    t = sans_relances(PAGE)
    assert "**Giulia · 03h19 :** 23% — tu crois que c'est mon père ?" in t
    assert "**Giulia · 03h18 :** C'est z3" in t


def test_le_fil_est_rendu_tel_quel():
    fil = "**Patrick · 10h00 :** Mesure : ton SLSA ?"
    bloc = mettre_en_forme([{"jour": "2026-10-18", "genre": "fil", "auteur": "Patrick", "titre": "F", "corps": fil}])
    assert "Mesure : ton SLSA ?" in bloc


def test_les_trois_genres_dans_l_ordre_et_le_decodage_signe():
    bloc = mettre_en_forme([
        {"jour": "2026-10-17", "genre": "decodage", "auteur": "Patrick", "titre": "D", "corps": "**Patrick · 13h35 :** égrégore coex"},
        {"jour": "2026-10-18", "genre": "fil", "auteur": "Patrick", "titre": "F", "corps": "fil"},
        {"jour": "2026-10-18", "genre": "digisha", "auteur": "Giulia", "titre": "T", "corps": PAGE},
    ])
    assert bloc.index("Décodages posés") < bloc.index("Ses dernières discussions") < bloc.index("Ses séances DiGiSha")
    assert "(2026-10-17 — Patrick)" in bloc and "égrégore coex" in bloc
    assert "Mesure" not in bloc


def test_chaque_genre_garde_son_budget_et_la_page_recente():
    vieux = {"jour": "2026-10-10", "genre": "fil", "auteur": "P", "titre": "vieux", "corps": "a" * 5000}
    recent = {"jour": "2026-10-18", "genre": "fil", "auteur": "P", "titre": "récent", "corps": "b" * 5000}
    bloc = mettre_en_forme([vieux, recent], budgets={"fil": 6000})
    assert "b" * 5000 in bloc and "a" * 1000 in bloc and "a" * 1001 not in bloc
    assert bloc.index("vieux") < bloc.index("récent")


def test_vide_ou_refuse_rend_rien():
    assert mettre_en_forme([]) == "" and mettre_en_forme(None) == ""


def test_sans_la_fonction_en_base_l_ancienne_reprise_sans_relances():
    with patch.object(digisha, "_rpc_personne", AsyncMock(return_value=None)), \
         patch.object(digisha, "fil_digisha_reprise", AsyncMock(return_value=PAGE)):
        t = asyncio.run(digisha.contexte_personne("Bearer x", None, "z3"))
    assert "Mesure" not in t and "la couleur de ton papa" in t


def test_avec_la_fonction_en_base_elle_seule_sert():
    rows = [{"jour": "2026-10-17", "genre": "decodage", "auteur": "Patrick", "titre": "D", "corps": "nœud COEX"}]
    with patch.object(digisha, "_rpc_personne", AsyncMock(return_value=rows)) as rpc, \
         patch.object(digisha, "fil_digisha_reprise", AsyncMock(return_value="ANCIEN")):
        t = asyncio.run(digisha.contexte_personne("Bearer x", "433bbdd5", "z3"))
    assert "nœud COEX" in t and "ANCIEN" not in t
    assert rpc.call_args.args[1] == "digisha_contexte"
    assert rpc.call_args.args[2] == {"p_consultante": "433bbdd5", "p_max_digisha": 120000}   # la page du jour entière


def test_le_plafond_de_depenses_donne_le_message_doux():
    # 19.10.2026 08h09 : « You have reached your specified API usage limits » — ni « credit » ni « billing » : l'erreur brute
    # partait vers les apprenantes. Le même message doux que pour le crédit épuisé.
    src = open("routers/digisha.py").read()
    assert src.count('"usage limit" in low') == src.count('"credit" in low')


def test_les_modeles_5_5_pour_toutes(monkeypatch):
    # 19.10.2026 : l'essai 5.5 était resté sur le seul compte de Patrick ; sur son « ok » du 17.10 et le banc du 19.10, toutes.
    monkeypatch.delenv("DIGISHA_MODELES_5_5", raising=False)
    p = {"model": "claude-sonnet-4-6", "max_tokens": 2048}
    assert digisha.passer_en_5_5(p, "8f494efd-df0c-4f07-bbb1-8ff7a2a44892") == "claude-sonnet-5-5"
    assert p["output_config"] == {"effort": "low"} and p["max_tokens"] == 8192
    q = {"model": "claude-opus-4-8", "max_tokens": 2048}
    assert digisha.passer_en_5_5(q, None) == "claude-opus-5-5"


# ── 13.11.2026 (fiche 3ce90fd5) : le début d'une longue page n'est plus perdu ─────────────────────────────────────────
# Anne, 10.11 16h40 : « Ton message de 10h38 n'est pas dans ce que je vois » (page de 48 136 car., reprise de sa seule fin).
from routers.digisha_contexte import ENTIER, decouper_page, resumer_debuts  # noqa: E402


def _echange(i, car=2300):
    h = f"{10 + i // 6:02d}h{(i % 6) * 10 + 8:02d}"
    return (f"**Anne · {h} :** mesure {i} : SLSA {20 + i} % " + "x" * (car // 2) + "\n\n"
            f"**DiGiSha :** lecture {i} " + "y" * (car // 2) + "\n\nMesure : **et ensuite ?**\n\n")


def _page(n):
    return "".join(_echange(i) for i in range(n))


def test_la_page_se_decoupe_sans_rien_perdre_et_par_echanges_entiers():
    page = _page(20)
    blocs, suite = decouper_page(page)
    assert "".join(blocs) + suite == page                                   # au caractère près
    assert len(blocs) >= 5 and all(b.startswith("**Anne · ") and len(b) >= 6000 for b in blocs)
    assert suite.startswith("**Anne · ") and 4000 <= len(suite) < 4000 + 6000 + 2400   # la suite, mot pour mot, bornée
    assert "**Anne · 10h08 :** mesure 0" in blocs[0]                        # le premier message est dans le premier bloc


def test_les_blocs_ne_bougent_pas_quand_la_page_grandit():
    """Sans cela chaque tour redemanderait ses résumés : le coût d'un résumé par tour au lieu d'un par bloc."""
    avant, _ = decouper_page(_page(20))
    for n in (21, 22, 25, 30):
        apres, suite = decouper_page(_page(n))
        assert apres[:len(avant)] == avant and len(suite) >= 4000


def test_une_page_courte_ou_un_seul_long_echange_ne_se_decoupe_pas():
    assert decouper_page(_page(2)) == ([], _page(2)) and decouper_page(_page(4)) == ([], _page(4))
    assert decouper_page("") == ([], "")
    un = "**Anne · 09h00 :** " + "z" * 30000
    assert decouper_page(un) == ([], un)                                    # rien après lui : il reste entier, _fin fera foi


def test_le_debut_est_resume_la_suite_mot_pour_mot_et_rien_n_est_coupe():
    appels = []

    async def resumer(texte):
        appels.append(texte)
        return f"RÉSUMÉ-{len(appels)} : " + texte[:40]

    page = _page(20)
    lignes = [{"jour": "2026-11-09", "genre": "digisha", "auteur": "Anne", "titre": "veille", "corps": "ancienne page"},
              {"jour": "2026-11-10", "genre": "fil", "auteur": "P", "titre": "fil", "corps": "fil du jour"},
              {"jour": "2026-11-10", "genre": "digisha", "auteur": "Anne", "titre": "jour", "corps": page}]
    prep = asyncio.run(resumer_debuts(lignes, resumer))
    blocs, suite = decouper_page(page)
    assert len(appels) == len(blocs) and all("Mesure :" not in a for a in appels)    # les relances ne se résument pas
    assert prep[2][ENTIER] and prep[:2] == lignes[:2] and lignes[2]["corps"] == page   # l'entrée n'est pas modifiée
    bloc = mettre_en_forme(prep)
    assert "RÉSUMÉ-1" in bloc and f"partie 1/{len(blocs)} (10h08–" in bloc            # les heures du bloc sont nommées
    assert "…" not in bloc.split("### Ses séances DiGiSha")[1]                        # aucune coupe dans la page du jour
    assert "**Anne · 13h18 :** mesure 19 : SLSA 39 %" in bloc                         # la fin, mot pour mot
    assert sans_relances(suite).strip()[:200] in bloc
    assert "fil du jour" in bloc


def test_un_resume_en_echec_ou_une_page_coupee_par_la_base_rend_la_fin_comme_avant():
    async def panne(texte):
        return None

    async def jamais(texte):
        raise AssertionError("ne doit pas être appelé")

    page = _page(20)
    lignes = [{"jour": "2026-11-10", "genre": "digisha", "auteur": "Anne", "titre": "jour", "corps": page}]
    assert asyncio.run(resumer_debuts(lignes, panne)) == lignes
    assert asyncio.run(resumer_debuts([dict(lignes[0], corps="…" + page)], jamais))[0]["corps"].startswith("…")
    assert asyncio.run(resumer_debuts([dict(lignes[0], corps=_page(2))], jamais))[0]["corps"] == _page(2)
    geant = "**Anne · 09h00 :** " + "z" * 30000                                       # un seul échange, trop long
    assert asyncio.run(resumer_debuts([dict(lignes[0], corps=geant)], jamais)) == [dict(lignes[0], corps=geant)]
    assert asyncio.run(resumer_debuts(lignes, None)) == lignes and asyncio.run(resumer_debuts(None, jamais)) is None
    bloc = mettre_en_forme(lignes)                                                    # l'ancienne coupe, inchangée
    assert bloc.count("…") >= 1 and "mesure 19" in bloc and "mesure 0 :" not in bloc


def test_le_resume_d_un_bloc_se_fait_une_fois_et_son_cout_s_inscrit(monkeypatch):
    from routers import digisha_memoire as m
    envois, couts = [], []

    class Client:
        async def post(self, url, json=None, headers=None, timeout=None):
            envois.append(json)

            class R:
                status_code = 200
                text = ""

                def json(self_inner):
                    return {"content": [{"type": "thinking", "thinking": ""}, {"type": "text", "text": "10h38 : SLSA 23 %."}],
                            "stop_reason": "end_turn", "usage": {"input_tokens": 3000, "output_tokens": 200}}
            return R()

    async def cout(data):
        couts.append(data["usage"])

    monkeypatch.setattr(m, "_resumes", type(m._resumes)())
    c = Client()
    r1 = asyncio.run(m.resumer_texte(c, "k", "bloc A", cout=cout))
    r2 = asyncio.run(m.resumer_texte(c, "k", "bloc A", cout=cout))
    asyncio.run(m.resumer_texte(c, "k", "bloc B", cout=cout))
    assert r1 == r2 == "10h38 : SLSA 23 %." and len(envois) == 2 and len(couts) == 2   # « bloc A » : un seul appel payé
    assert envois[0]["model"] == "claude-sonnet-5-5" and "bloc A" in envois[0]["messages"][0]["content"]


def test_un_resume_coupe_n_entre_pas_en_memoire(monkeypatch):
    from routers import digisha_memoire as m

    class Client:
        async def post(self, url, json=None, headers=None, timeout=None):
            class R:
                status_code = 200
                text = ""

                def json(self_inner):
                    return {"content": [{"type": "text", "text": "10h38 : SLSA"}], "stop_reason": "max_tokens", "usage": {}}
            return R()

    monkeypatch.setattr(m, "_resumes", type(m._resumes)())
    assert asyncio.run(m.resumer_texte(Client(), "k", "bloc C")) is None and not m._resumes


def test_contexte_personne_resume_le_debut_et_inscrit_le_cout_au_nom_de_la_personne(monkeypatch):
    page = _page(20)
    rows = [{"jour": "2026-11-10", "genre": "digisha", "auteur": "Anne", "titre": "jour", "corps": page}]
    vus = []

    async def resumer_texte(client, api_key, texte, cout=None):
        await cout({"usage": {"input_tokens": 1}})
        return "RÉSUMÉ " + texte[:30]

    async def journal(source, mode, model, data, svlbh_id=None, supabase_user_id=None):
        vus.append((source, mode, model, svlbh_id))

    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setattr(digisha, "resumer_texte", resumer_texte)
    monkeypatch.setattr(digisha, "journaliser_cout", journal)
    monkeypatch.setattr(digisha, "_http", lambda: None)
    with patch.object(digisha, "_rpc_personne", AsyncMock(return_value=rows)):
        t = asyncio.run(digisha.contexte_personne("Bearer x", None, "z3", qui="57bd2f8e"))
    assert "RÉSUMÉ **Anne · 10h08 :** mesure 0" in t and "mesure 19 : SLSA 39 %" in t
    assert vus and set(vus) == {("render-resume-reprise", "reprise", "claude-sonnet-5-5", "57bd2f8e")}


def test_une_page_qui_tient_en_un_bloc_et_sa_suite_passe_entiere_sans_resume():
    async def jamais(texte):
        raise AssertionError("ne doit pas être appelé")

    page = _page(4)                                                         # ≈ 9 400 car. : plus que le budget, moins que 10 000
    assert 6000 < len(sans_relances(page)) and len(page) <= 10000
    lignes = [{"jour": "2026-11-10", "genre": "digisha", "auteur": "Anne", "titre": "jour", "corps": page}]
    prep = asyncio.run(resumer_debuts(lignes, jamais))
    bloc = mettre_en_forme(prep)
    assert prep[0][ENTIER] and "…" not in bloc and "mesure 0 : SLSA 20 %" in bloc and "mesure 3 : SLSA 23 %" in bloc
    assert "mesure 0 : SLSA 20 %" not in mettre_en_forme(lignes)            # avant : son début était coupé
