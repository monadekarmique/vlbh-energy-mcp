"""La relecture (Patrick, 17.10.2026 : « une relecture de ses Décodage avec DiGiSha … DiGiSha ne voit pas encore ce que je
ressens ») : un tour « à propos de » une autre fiche part en relecture chez celle qui relit ; la formation M1 garde son dépôt ;
la coulisse ne nomme jamais sa source."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import routers.digisha as d  # noqa: E402


def _capture(monkeypatch):
    appels = []

    async def faux(authorization, nom, corps, timeout=10):
        appels.append((nom, corps))
        return "ok"
    monkeypatch.setattr(d, "_rpc_personne", faux)
    return appels


def test_a_propos_part_en_relecture(monkeypatch):
    appels = _capture(monkeypatch)
    asyncio.run(d.fil_digisha_deposer("Bearer t", "688a23c1-f09e-48d7-be5b-dd24c101c1c1", "z12", "q", "r", "accompagnement"))
    asyncio.run(d.fil_digisha_deposer("Bearer t", "688a23c1-f09e-48d7-be5b-dd24c101c1c1", "z12", "q", "r", "fil"))
    assert [a[0] for a in appels] == ["digisha_relecture_deposer"] * 2
    assert appels[0][1]["p_sujet"] == "688a23c1-f09e-48d7-be5b-dd24c101c1c1"


def test_sur_soi_et_formation_m1_gardent_le_fil(monkeypatch):
    appels = _capture(monkeypatch)
    asyncio.run(d.fil_digisha_deposer("Bearer t", None, "z1", "q", "r", "accompagnement"))
    asyncio.run(d.fil_digisha_deposer("Bearer t", "688a23c1-f09e-48d7-be5b-dd24c101c1c1", "z1", "q", "r", "formation_m1"))
    assert [a[0] for a in appels] == ["digisha_fil_deposer"] * 2


def test_la_coulisse_ne_nomme_pas_sa_source():
    assert "Ne le cite jamais" in d.RELECTURE_COULISSE and "ne nomme pas qui l'a faite" in d.RELECTURE_COULISSE


def test_relecture_pour_sans_personne_ne_lit_rien():
    assert asyncio.run(d.relecture_pour()) == ""
