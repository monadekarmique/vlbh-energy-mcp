"""Fusion lexicale + sémantique du fil (carte b8d68119) : dédoublonner, faire monter l'accord, couvrir les mois,
et ne jamais casser le mode fil quand la voie sémantique n'est pas là."""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from routers import digisha, digisha_semantique  # noqa: E402


def p(session, jour, corps, titre="t"):
    return {"session_id": session, "jour": jour, "corps": corps, "titre": titre, "extrait": ""}


def test_entrelace_semantique_puis_lexical_et_un_doublon_ne_sort_qu_une_fois():
    lex = [p("s1", "2026-09-01", "A"), p("s2", "2026-09-02", "B")]
    sem = [p("s3", "2026-09-03", "C"), p("s2", "2026-09-02", "B")]
    out = [x["corps"] for x in digisha.fusionner_passages(lex, sem)]
    assert out == ["C", "A", "B"]          # rang 1 sémantique, rang 1 lexical, puis B une seule fois


def test_le_premier_semantique_n_est_pas_noye_par_le_bruit_lexical():
    # question sans les mots du fil : 40 passages lexicaux de bruit, la bonne section en tête du sémantique
    lex = [p(f"l{i}", "2026-07-%02d" % (i % 28 + 1), f"bruit{i}") for i in range(40)]
    sem = [p("vitrail", "2026-07-29", "La lampe en vitrail")] + [p(f"x{i}", "2026-06-01", f"s{i}") for i in range(39)]
    assert digisha.fusionner_passages(lex, sem)[0]["corps"] == "La lampe en vitrail"


def test_chaque_mois_entre_juste_apres_les_dix_premiers():
    # douze passages de septembre bien classés, un seul d'avril tout en bas : avril passe 11e, pas 13e
    lex = [p(f"s{i}", "2026-09-%02d" % (i + 1), f"sept{i}") for i in range(12)] + [p("sa", "2026-04-10", "avril")]
    out = digisha.fusionner_passages(lex, [])
    assert out[0]["corps"] == "sept0"
    assert out[digisha.FUSION_TETE]["jour"].startswith("2026-04")


def test_sans_voie_semantique_le_lexical_reste_intact():
    lex = [p("s1", "2026-05-01", "A"), p("s2", "2026-05-02", "B")]
    assert [x["corps"] for x in digisha.fusionner_passages(lex, None)] == ["A", "B"]


def test_coupe_circuit_desactive_la_voie_semantique(monkeypatch):
    monkeypatch.setenv("DIGISHA_SEMANTIQUE", "0")
    assert asyncio.run(digisha_semantique.vecteur_question("sa mère")) is None
    assert asyncio.run(digisha.fetch_passages_semantiques("x", "sa mère", "Bearer t")) is None


def test_sans_session_pas_de_voie_semantique():
    assert asyncio.run(digisha.fetch_passages_semantiques("x", "q", None)) is None
