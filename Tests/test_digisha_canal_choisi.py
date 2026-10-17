"""Le canal choisi dans l'app (sélecteur z1 → z12 de l'accueil Chroma 5 porté sur DiGiSha, DEC Patrick 17.10.2026) :
honoré dès ST3, jamais pour une ST2 (son canal est z1, elle travaille sur son Âme), jamais hors de la forme « zN »."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routers.digisha import canal_choisi  # noqa: E402


def test_st6_choisit_son_canal():
    assert canal_choisi("z8", "ST6") == "z8"
    assert canal_choisi(" Z12 ", "ST4") == "z12"
    assert canal_choisi("z3", "ST3") == "z3"


def test_st2_et_st1_gardent_la_regle_de_la_base():
    assert canal_choisi("z4", "ST2") is None
    assert canal_choisi("z1", "ST1") is None
    assert canal_choisi("z2", None) is None
    assert canal_choisi("z2", "") is None


def test_forme_invalide_ignoree():
    assert canal_choisi(None, "ST6") is None
    assert canal_choisi("", "ST6") is None
    assert canal_choisi("z0", "ST6") is None
    assert canal_choisi("z123", "ST6") is None
    assert canal_choisi("canal z3", "ST6") is None
    assert canal_choisi("z3; drop", "ST6") is None
