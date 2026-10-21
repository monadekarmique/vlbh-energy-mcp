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


# ── Le serveur ferme ce que le menu cache : une porte de list_portes(), B2C seul pour une proxy ───────────────────
import asyncio  # noqa: E402

from routers import digisha as d  # noqa: E402

PORTES = [{"id": "z1", "libelle": "L'Âme", "segment": "B2C", "zone": None},
          {"id": "z2", "libelle": "Ma famille d'Âmes", "segment": "B2C", "zone": None},
          {"id": "z3", "libelle": "Ma Monade", "segment": "B2B", "zone": None},
          {"id": "z12", "libelle": "z12", "segment": None, "zone": "z12"}]


def test_porte_permise_regle_du_selecteur():
    assert d.porte_permise(PORTES, "z2", proxy=True)                  # B2C : ouverte à la proxy
    assert not d.porte_permise(PORTES, "z3", proxy=True)              # « Anne ne devrait voir ni z3, ni z4, ni z5 »
    assert not d.porte_permise(PORTES, "z12", proxy=True)
    assert d.porte_permise(PORTES, "z3", proxy=False) and d.porte_permise(PORTES, "z12", proxy=False)
    assert not d.porte_permise(PORTES, "z3", proxy=None)              # rôle illisible : seul le B2C passe
    assert not d.porte_permise(PORTES, "z13", proxy=False)            # hors du sélecteur
    assert not d.porte_permise(PORTES, "z99", proxy=False)
    assert not d.porte_permise(None, "z1", proxy=False)               # catalogue illisible : rien


def _base(monkeypatch, portes, role, appels):
    async def rpc(auth, nom, corps, timeout=10):
        appels.append(nom)
        return {"list_portes": portes, "effective_svlbh_id": "e4f77c12-aeda-4dac-b653-3d6514a6e0c0",
                "digisha_canal": "z4"}.get(nom)

    async def proxy(auth):
        appels.append("fiche_role")
        return role

    monkeypatch.setattr(d, "_rpc_personne", rpc)
    monkeypatch.setattr(d, "est_proxy", proxy)


def _canal(choisi, stx="ST4"):
    return asyncio.run(d.canal_digisha("Bearer t", "e4f77c12-aeda-4dac-b653-3d6514a6e0c0", False, choisi=choisi, stx=stx))


def test_canal_digisha_honore_une_porte_permise(monkeypatch):
    appels = []
    _base(monkeypatch, PORTES, False, appels)
    assert _canal("z3") == "z3" and appels == ["list_portes", "fiche_role"]
    appels.clear()
    assert _canal("z1") == "z1" and appels == ["list_portes"]          # B2C : le rôle n'est pas lu


def test_canal_digisha_refuse_retombe_sur_la_base(monkeypatch):
    appels = []
    _base(monkeypatch, PORTES, True, appels)
    assert _canal("z12") == "z4"                                       # proxy : z12 refusé, digisha_canal décide
    _base(monkeypatch, PORTES, False, appels)
    assert _canal("z42") == "z4"                                       # pas une porte du sélecteur
    _base(monkeypatch, None, False, appels)
    assert _canal("z3") == "z4"                                        # list_portes en panne : la base décide
    _base(monkeypatch, PORTES, None, appels)
    assert _canal("z3") == "z4"                                        # rôle illisible : hors B2C refusé
    assert _canal("z2") == "z2"                                        # … le B2C reste permis


def test_est_proxy_lit_le_role_de_l_identite_effective(monkeypatch):
    vus = []

    class _Client:
        def __init__(self, code, lignes):
            self.code, self.lignes = code, lignes

        async def get(self, url, params=None, headers=None, timeout=None):
            vus.append((url.rsplit("/", 1)[-1], params["svlbh_id"], headers["Authorization"]))
            code, lignes = self.code, self.lignes

            class R:
                status_code = code

                def json(self_inner):
                    return lignes
            return R()

    async def rpc(auth, nom, corps, timeout=10):
        return "57BD2F8E-53C5-49F8-A778-ED8C2CD75BCC" if nom == "effective_svlbh_id" else None

    monkeypatch.setenv("DIGISHA_SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("DIGISHA_SUPABASE_SERVICE_KEY", "k")
    monkeypatch.setattr(d, "_rpc_personne", rpc)
    for code, lignes, attendu in ((200, [{"role": "proxy"}], True), (200, [{"role": "praticienne"}], False),
                                  (200, [], False), (500, None, None)):
        monkeypatch.setattr(d, "_http", lambda c=code, l=lignes: _Client(c, l))
        assert asyncio.run(d.est_proxy("Bearer jeton-perso")) is attendu
    assert vus[0] == ("fiche_role", "eq.57bd2f8e-53c5-49f8-a778-ed8c2cd75bcc", "Bearer jeton-perso")

    async def sans_identite(auth, nom, corps, timeout=10):
        return None
    monkeypatch.setattr(d, "_rpc_personne", sans_identite)
    assert asyncio.run(d.est_proxy("Bearer jeton-perso")) is None
