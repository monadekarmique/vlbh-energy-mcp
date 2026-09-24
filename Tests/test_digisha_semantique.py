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


def test_un_passage_trouve_par_les_deux_voies_monte_et_ne_sort_qu_une_fois():
    lex = [p("s1", "2026-09-01", "A"), p("s2", "2026-09-02", "B")]
    sem = [p("s3", "2026-09-03", "C"), p("s2", "2026-09-02", "B")]
    out = digisha.fusionner_passages(lex, sem)
    corps = [x["corps"] for x in out]
    assert corps.count("B") == 1
    assert len(out) == 3


def test_tous_les_mois_passent_avant_les_suivants():
    # douze passages de septembre bien classés, un seul d'avril tout en bas : avril doit rester dans la tête
    lex = [p(f"s{i}", "2026-09-%02d" % (i + 1), f"sept{i}") for i in range(12)] + [p("sa", "2026-04-10", "avril")]
    out = digisha.fusionner_passages(lex, [])
    mois_tete = [x["jour"][:7] for x in out[:2]]
    assert "2026-04" in mois_tete


def test_sans_voie_semantique_le_lexical_reste_intact():
    lex = [p("s1", "2026-05-01", "A"), p("s2", "2026-05-02", "B")]
    assert [x["corps"] for x in digisha.fusionner_passages(lex, None)] == ["A", "B"]


def test_coupe_circuit_desactive_la_voie_semantique(monkeypatch):
    monkeypatch.setenv("DIGISHA_SEMANTIQUE", "0")
    assert asyncio.run(digisha_semantique.vecteur_question("sa mère")) is None
    assert asyncio.run(digisha.fetch_passages_semantiques("x", "sa mère", "Bearer t")) is None


def test_sans_session_pas_de_voie_semantique():
    assert asyncio.run(digisha.fetch_passages_semantiques("x", "q", None)) is None
