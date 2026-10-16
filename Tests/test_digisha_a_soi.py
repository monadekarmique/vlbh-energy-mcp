"""Voie « DiGiSha à soi » (16.10.2026, fiche db642696) : le Module 1 sur sa propre fiche dit « toi »."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from routers.digisha_formation_m1 import m1_system_block, _M1_SUR_SOI


def test_ferme_reste_ferme_meme_sur_soi():
    assert m1_system_block("ST1", sur_soi=True) is None


def test_ouvert_par_fenetre_a_soi_dit_toi():
    b = m1_system_block("ST1", ouvert_par_abonnement=True, sur_soi=True)
    assert b is not None
    assert _M1_SUR_SOI in b
    assert "jamais « ton proche »" in b


def test_sur_un_proche_le_cadre_ne_change_pas():
    b = m1_system_block("ST2")
    assert b is not None and _M1_SUR_SOI not in b
