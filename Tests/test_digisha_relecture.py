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
    assert "Ne les cite jamais" in d.RELECTURE_COULISSE and "ne nomme pas qui les a donnés" in d.RELECTURE_COULISSE
    assert "Tu ne cherches pas dans son fil de quoi lui répondre" in d.RELECTURE_CADRE


def test_relecture_pour_sans_personne_ne_lit_rien():
    assert asyncio.run(d.relecture_pour()) == ""


def test_savoir_exclut_la_personne_et_ne_cherche_pas_a_vide(monkeypatch):
    appels = []

    async def faux(nom, corps, timeout=10):
        appels.append((nom, corps))
        return "— une fiche"
    monkeypatch.setattr(d, "_rpc_service", faux)
    assert asyncio.run(d.savoir_pour("   ")) == ""
    assert asyncio.run(d.savoir_pour("estomac et honte", exclure_svlbh="64810cf3")) == "— une fiche"
    assert appels == [("digisha_savoir_chercher", {"p_question": "estomac et honte", "p_exclure": None,
                                                   "p_exclure_svlbh": "64810cf3", "p_limite": 6, "p_max_car": 6000})]
    assert "ne le lui attribue jamais" in d.SAVOIR_CADRE


def _droits(monkeypatch, proprietaire, lisibles):
    async def faux(authorization, nom, corps, timeout=10):
        return {"is_owner_st6": proprietaire, "fils_lisibles": lisibles}.get(nom)
    monkeypatch.setattr(d, "_rpc_personne", faux)


def test_peut_relire_suit_la_porte_du_depot(monkeypatch):
    x = "688a23c1-0000-4000-8000-000000000001"
    _droits(monkeypatch, True, [])
    assert asyncio.run(d.peut_relire("Bearer t", x)) is True
    _droits(monkeypatch, False, [x.upper()])
    assert asyncio.run(d.peut_relire("Bearer t", x)) is True
    _droits(monkeypatch, False, [{"fils_lisibles": x}])
    assert asyncio.run(d.peut_relire("Bearer t", x)) is True


def test_peut_relire_refuse_sans_droit_et_sur_panne(monkeypatch):
    x = "688a23c1-0000-4000-8000-000000000001"
    _droits(monkeypatch, False, ["14bd87df-0000-4000-8000-000000000002"])
    assert asyncio.run(d.peut_relire("Bearer t", x)) is False
    _droits(monkeypatch, None, None)                       # panne : _rpc_personne rend None
    assert asyncio.run(d.peut_relire("Bearer t", x)) is False
    assert asyncio.run(d.peut_relire("Bearer t", None)) is False
