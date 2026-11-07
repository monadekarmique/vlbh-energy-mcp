"""« Impasse » et « Compte-rendu », les mots codes de Patrick ; l'heure de chaque tour (07.11.2026)."""
import asyncio
from types import SimpleNamespace

from routers import digisha as d
from routers import digisha_heures as h
from routers import digisha_impasse as i

REPONSE = ("Je laisse la paire Po→Hun : elle ne porte pas la Vésicule biliaire.\nQu'as-tu mesuré sur GB ?\n"
           "⟦Impasse : Po→Hun pour l'axe LR-GB — les tables Wu Shen ne portent pas la Vésicule biliaire⟧")


def test_la_ligne_part_et_l_impasse_reste():
    propre, dites = i.extraire_impasse(REPONSE)
    assert "⟦" not in propre and propre.endswith("Qu'as-tu mesuré sur GB ?")
    assert dites == [("Po→Hun pour l'axe LR-GB", "les tables Wu Shen ne portent pas la Vésicule biliaire")]


def test_deux_au_plus_sans_doublon():
    t = "x\n⟦Impasse : A — 1⟧\n⟦Impasse : a — 2⟧\n⟦Impasse : B⟧\n⟦Impasse : C — 3⟧"
    propre, dites = i.extraire_impasse(t)
    assert propre == "x" and dites == [("A", "1"), ("B", "")]


def test_le_mot_code():
    assert i.dit_impasse("Impasse")
    assert i.dit_impasse("impasse : les lectures sont fausses")
    assert i.dit_impasse("C'est une IMPASSE.")
    assert not i.dit_impasse("Les impasses de la vie")            # pluriel : pas le mot code
    assert not i.dit_impasse("")


def test_secours_quand_la_ligne_manque():
    chemin, raison = i.impasse_de_secours("Impasse : les lectures à mesurer sont fausses",
                                          "**Po (N1) puis Hun (N2) : la paire po→hun**\n- Cycle : Ke")
    assert chemin == "Po (N1) puis Hun (N2) : la paire po→hun"
    assert raison == "les lectures à mesurer sont fausses"
    assert i.impasse_de_secours("Impasse", "") == ("la réponse précédente", "Patrick : « Impasse »")


def test_bloc_des_chemins_fermes():
    b = i.bloc_impasses([{"chemin": "Po→Hun pour LR-GB", "raison": "pas de GB", "le": "07.11"}, {"x": 1}])
    assert b.startswith(i.IMPASSES_CADRE) and "- Po→Hun pour LR-GB — pas de GB (07.11)" in b
    assert i.bloc_impasses(None) == "" and i.bloc_impasses([]) == ""


def test_noter_et_relire_par_rpc():
    appels = []

    async def rpc(nom, corps):
        appels.append((nom, corps))
        return [{"chemin": "A", "raison": "r"}] if nom == "digisha_impasses" else "ok"

    sorties = asyncio.run(i.noter_impasses(rpc, [("A", "r")], "patrick", "fiche", "Impasse : r"))
    assert sorties == ["ok"] and appels[0][1] == {"p_auteur": "patrick", "p_consultante": "fiche", "p_chemin": "A",
                                                  "p_raison": "r", "p_message": "Impasse : r"}
    assert "- A — r" in asyncio.run(i.impasses(rpc, "patrick", None))
    assert asyncio.run(i.impasses(rpc, None, None)) == "" and asyncio.run(i.noter_impasses(rpc, [("A", "")], None, None, "")) == []


def _corps(*tours):
    return SimpleNamespace(messages=[SimpleNamespace(role=r, content=c) for r, c in tours])


def test_garder_impasses_proprietaire_seul(monkeypatch):
    notees = []

    async def rpc(nom, corps):
        notees.append(corps)
        return "ok"

    monkeypatch.setattr(d, "_rpc_service", rpc)
    corps = _corps(("assistant", "**Po→Hun**\nCycle Ke"), ("user", "Impasse : pas de GB dans Wu Shen"))
    # le modèle a oublié la ligne : le serveur garde quand même l'impasse
    texte = asyncio.run(d.garder_impasses("[21h50] Je laisse Po→Hun.", corps, True, "patrick", "fiche"))
    assert texte == "Je laisse Po→Hun." and notees[0]["p_chemin"] == "Po→Hun" and notees[0]["p_raison"] == "pas de GB dans Wu Shen"
    # une autre personne : la ligne est retirée, rien n'est gardé
    notees.clear()
    texte = asyncio.run(d.garder_impasses("ok\n⟦Impasse : X — y⟧", corps, False, "autre", None))
    assert texte == "ok" and notees == []


def test_cadres_de_seance(monkeypatch):
    async def personne(auth, nom, corps):
        return True

    async def rpc(nom, corps):
        return [{"chemin": "A"}]

    monkeypatch.setattr(d, "_rpc_personne", personne)
    monkeypatch.setattr(d, "_rpc_service", rpc)
    payload = {"system": [{"type": "text", "text": "base"}]}
    assert asyncio.run(d.cadres_de_seance(payload, "Bearer x", "patrick", None)) is True
    textes = [b["text"] for b in payload["system"]]
    assert any(t.startswith("## L'heure") for t in textes)
    assert any("« Impasse »" in t and "« Compte-rendu »" in t and "- A" in t for t in textes)
    assert all(b.get(d.ranger_pour_cache.__globals__["MARQUE"]) for b in payload["system"][1:])   # du tour : hors cache


def test_heures():
    assert h.normaliser("21:36") == "21h36" and h.normaliser("9h05") == "09h05"
    assert h.normaliser("2026-11-07T21:36:00+01:00") == "21h36" and h.normaliser("demain") is None and h.normaliser(None) is None
    msgs = h.avec_heures([{"role": "user", "content": "Bonjour", "heure": "21:36"},
                          {"role": "assistant", "content": [{"type": "text", "text": "x"}], "heure": "21h37"},
                          {"role": "user", "content": "sans heure"}])
    assert msgs[0] == {"role": "user", "content": "[21h36] Bonjour"}
    assert msgs[1]["content"][0] == {"type": "text", "text": "[21h37]"} and "heure" not in msgs[1]
    assert msgs[2] == {"role": "user", "content": "sans heure"}
    assert h.sans_heure_en_tete("[21h38] Réponse") == "Réponse" and h.sans_heure_en_tete("Réponse [21h38]") == "Réponse [21h38]"


def test_le_tour_accepte_une_heure():
    t = d.ChatTurn(role="user", content="Bonjour", heure="21:36")
    assert t.model_dump(exclude_none=True)["heure"] == "21:36"
    assert "heure" not in d.ChatTurn(role="user", content="Bonjour").model_dump(exclude_none=True)
    assert d.ChatResponse(reply="x", model="m", heure="21h36").heure == "21h36"
