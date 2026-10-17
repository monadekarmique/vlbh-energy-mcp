"""Passage aux modèles 5.5 (Patrick, 17.10.2026, « ok ») : l'essai sur son compte d'abord, l'effort et le plafond réglés,
rien ne change pour les autres tant que DIGISHA_MODELES_5_5 ne dit pas « tous »."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import routers.digisha as d  # noqa: E402

PATRICK, FABIENNE = "52adbc98-d2b0-4444-b89c-b1311a02a983", "64810cf3-5f13-41c5-9a1f-8402e4b3a4da"


def test_patrick_passe_en_5_5_avec_effort_et_plafond(monkeypatch):
    monkeypatch.delenv("DIGISHA_MODELES_5_5", raising=False)
    p = {"model": "claude-opus-4-8", "max_tokens": 2048}
    assert d.passer_en_5_5(p, PATRICK) == "claude-opus-5-5"
    assert p["max_tokens"] == 8192 and p["output_config"] == {"effort": "medium"}
    q = {"model": "claude-sonnet-4-6", "max_tokens": 1024}
    assert d.passer_en_5_5(q, PATRICK.upper()) == "claude-sonnet-5-5" and q["output_config"] == {"effort": "low"}


def test_les_autres_restent_tant_que_l_essai_dure(monkeypatch):
    monkeypatch.delenv("DIGISHA_MODELES_5_5", raising=False)
    p = {"model": "claude-opus-4-8", "max_tokens": 2048}
    assert d.passer_en_5_5(p, FABIENNE) == "claude-opus-4-8" and "output_config" not in p
    assert d.passer_en_5_5({"model": "claude-sonnet-4-6"}, None) == "claude-sonnet-4-6"


def test_tous(monkeypatch):
    monkeypatch.setenv("DIGISHA_MODELES_5_5", "tous")
    assert d.passer_en_5_5({"model": "claude-sonnet-4-6", "max_tokens": 2048}, FABIENNE) == "claude-sonnet-5-5"
    assert d.passer_en_5_5({"model": "claude-haiku-4-5", "max_tokens": 2048}, FABIENNE) == "claude-haiku-4-5"
