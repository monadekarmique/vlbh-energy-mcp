"""Mode accélération (Patrick, 05.11.2026) : un DÉCODAGE au lieu du Module 1 — relier, proposer, demander ; jamais fermer
une dimension à sa place ; toutes les dimensions ouvertes."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from routers.digisha_formation_m1 import (decodage_system_block, m1_system_block, DECODAGE_WINDOWS, _M1_WINDOWS,
                                          _DECODAGE_SUR_SOI)


def test_le_decodage_n_est_pas_le_module_1():
    b = decodage_system_block()
    assert "sans analyse" not in b
    assert "NE PAS conclure" not in b
    for geste in ("1. POSER", "2. RELIER", "3. LIRE", "4. DEMANDER"):
        assert geste in b


def test_c_est_elle_qui_ferme_une_dimension():
    assert "c'est ELLE SEULE qui dit\nquand une dimension est déposée" in decodage_system_block()


def test_toutes_les_dimensions_sont_ouvertes():
    b = decodage_system_block()
    for w in DECODAGE_WINDOWS:
        assert _M1_WINDOWS[w] in b
    assert "FERMÉE" not in b


def test_le_mot_est_decodage():
    assert "jamais « mesure de lecture »" in decodage_system_block()


def test_sur_soi_dit_toi():
    assert _DECODAGE_SUR_SOI in decodage_system_block(sur_soi=True)
    assert _DECODAGE_SUR_SOI not in decodage_system_block()


def test_le_module_1_ne_change_pas():
    b = m1_system_block("ST2")
    assert b is not None and "sans analyse" in b and "4. DEMANDER" not in b
