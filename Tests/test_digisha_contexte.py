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
    assert rpc.call_args.args[1] == "digisha_contexte" and rpc.call_args.args[2] == {"p_consultante": "433bbdd5"}
