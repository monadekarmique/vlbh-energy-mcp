"""« Poursuivre avec DiGiSha » par QR (Patrick, 17.10.2026) : le décodage scanné entre en tête de l'échange, borné ; un
identifiant mal formé n'appelle rien ; le bloc s'ajoute au système qu'il soit texte ou liste."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routers.digisha import AccompagnementRequest, ChatRequest, DECODAGE_MAX_CAR, ajouter_au_systeme, bloc_decodage, fetch_decodage  # noqa: E402


def test_le_champ_existe_sur_les_deux_chemins():
    assert ChatRequest(messages=[{"role": "user", "content": "x"}], decodage_id="abc").decodage_id == "abc"
    assert AccompagnementRequest(messages=[{"role": "user", "content": "x"}]).decodage_id is None


def test_identifiant_mal_forme_n_appelle_rien():
    assert asyncio.run(fetch_decodage("Bearer x", "pas-un-uuid")) is None
    assert asyncio.run(fetch_decodage(None, "6f1c2b3a-1111-2222-3333-444455556666")) is None


def test_le_bloc_nomme_le_soin_et_borne_le_contenu():
    d = {"menu": "Décodage composé", "provenance": "vifa_essentielles", "is_self_care": True,
         "created_at": "2026-10-15T08:00:00+00:00", "payload": {"wu_shen_stones": ["x" * 20000]}}
    b = bloc_decodage(d)
    assert b.startswith("## Le soin décodé que la personne poursuit")
    assert "« Décodage composé » du 15.10.2026 — auto-soin (outil : vifa_essentielles)" in b
    assert b.endswith("…(tronqué)") and len(b) < DECODAGE_MAX_CAR + 800
    assert bloc_decodage(None) == ""


def test_ajout_au_systeme_texte_ou_liste():
    p = {"system": "base"}
    ajouter_au_systeme(p, "dec")
    assert p["system"] == [{"type": "text", "text": "base"}, {"type": "text", "text": "dec"}]
    q = {"system": [{"type": "text", "text": "a"}]}
    ajouter_au_systeme(q, "")
    assert q["system"] == [{"type": "text", "text": "a"}]
