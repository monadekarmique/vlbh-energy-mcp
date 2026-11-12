"""Le sondage WhatsApp que DiGiSha prépare (carte 280b0b5a, 13.11.2026). Patrick : « Valider la clé chromatique du jour » ;
« C'est moi ou une ST5 - actuellement Anne qui la valide » ; « je peux dans DiGiSha ajouter une de mes clés décodées ».
Rien ne part sans son « envoie »."""
import asyncio

import routers.digisha as d
import routers.digisha_apprendre as a
import routers.digisha_sondage as s

MOI = "306c2408-0000-0000-0000-000000000000"
CLE = "⟦Clé chromatique : Clé du matin — niveau 1 : #B26FB1 #44969E · niveau 2 : #FFFFFF⟧"
REPONSE = ("Je prépare le sondage pour Anne.\n"
           "⟦Sondage pour Anne : Valider la clé chromatique du jour | Validée | À reprendre⟧")


# ── La ligne ⟦Sondage …⟧ ────────────────────────────────────────────────────────────────────────────────────────────────

def test_la_ligne_est_retiree_et_lue():
    texte, p = s.extraire_sondage(REPONSE)
    assert texte == "Je prépare le sondage pour Anne."
    assert p == {"pour": "Anne", "question": "Valider la clé chromatique du jour", "options": ["Validée", "À reprendre"]}


def test_sans_prenom_c_est_la_validatrice_du_jour():
    _, p = s.extraire_sondage("ok\n⟦Sondage : La clé est-elle juste ? | « Oui » | Non |  ⟧")
    assert p == {"pour": s.VALIDATRICE_DU_JOUR, "question": "La clé est-elle juste ?", "options": ["Oui", "Non"]}


def test_une_seule_proposition_et_toutes_les_lignes_retirees():
    texte, p = s.extraire_sondage("a\n⟦Sondage pour moi : Q1 | x | y⟧\nb\n⟦Sondage pour Chloé : Q2 | x | y⟧")
    assert "⟦" not in texte and p["pour"] == "moi" and p["question"] == "Q1"


def test_sans_ligne_rien_ne_change():
    assert s.extraire_sondage("Bonjour.") == ("Bonjour.", None)


# ── La clé jointe par la personne ───────────────────────────────────────────────────────────────────────────────────────

def test_la_derniere_cle_jointe_par_la_personne():
    tours = [("user", "⟦Clé chromatique : Ancienne — #000000⟧"), ("assistant", "⟦Clé chromatique : de DiGiSha — #111111⟧"),
             ("user", f"Fais valider celle-ci\n{CLE}"), ("user", "à Anne")]
    assert s.cle_jointe(tours) == "Clé du matin — niveau 1 : #B26FB1 #44969E · niveau 2 : #FFFFFF"
    assert s.cle_jointe([("assistant", CLE)]) is None and s.cle_jointe([]) is None
    assert s.message_avant("Clé — #B26FB1") == "Clé chromatique : Clé — #B26FB1" and s.message_avant(None) is None


# ── « envoie » ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_envoie_et_rien_d_autre():
    for oui in ("envoie", "Envoie.", "envoie-le", " Oui, envoie ! ", "envoie le sondage", "ENVOIE LE"):
        assert s.est_envoie(oui), oui
    for non in ("", "envoie à Chloé plutôt", "n'envoie pas", "envoie demain", "j'envoie", "envoi", "oui"):
        assert not s.est_envoie(non), non


# ── La proposition : rangée, jamais envoyée ─────────────────────────────────────────────────────────────────────────────

def test_la_proposition_part_en_base_avec_la_cle_et_s_affiche():
    vus = []

    async def rpc(nom, corps):
        vus.append((nom, corps))
        return {"ok": True, "pour": "Anne", "pont": "z3", "question": corps["p_question"], "options": corps["p_options"],
                "avant": True}

    _, p = s.extraire_sondage(REPONSE)
    bloc = asyncio.run(s.proposer_sondage(rpc, MOI, p, "Clé du matin — #B26FB1"))
    assert vus == [("pont_sondage_proposer", {
        "p_auteur": MOI, "p_pour": "Anne", "p_question": "Valider la clé chromatique du jour",
        "p_options": ["Validée", "À reprendre"], "p_avant": "Clé chromatique : Clé du matin — #B26FB1"})]
    assert "rien n'est parti" in bloc and "Pour : Anne (pont z3)" in bloc
    assert "Juste avant, ce message : Clé chromatique : Clé du matin — #B26FB1" in bloc
    assert "Options : Validée · À reprendre" in bloc and "« envoie »" in bloc


def test_sans_cle_pas_de_message_avant():
    async def rpc(nom, corps):
        assert corps["p_avant"] is None
        return {"ok": True, "pour": "Patrick", "pont": "z3", "question": "Q", "options": ["a", "b"], "avant": False}

    bloc = asyncio.run(s.proposer_sondage(rpc, MOI, {"pour": "moi", "question": "Q", "options": ["a", "b"]}, None))
    assert "Juste avant" not in bloc and "Pour : Patrick" in bloc


def test_un_refus_dit_sa_raison_et_une_panne_aussi():
    def jouer(reponse):
        async def rpc(nom, corps):
            return reponse
        return asyncio.run(s.proposer_sondage(rpc, MOI, {"pour": "Zoé", "question": "Q", "options": ["a", "b"]}, None))

    inconnue = jouer({"ok": False, "raison": "inconnue", "pour": "Zoé", "validatrices": ["Anne", "Chloé", "Cornelia", "Patrick"]})
    assert "« Zoé » n'est pas parmi" in inconnue and "Anne, Chloé, Cornelia, Patrick" in inconnue
    assert "numéro WhatsApp" in jouer({"ok": False, "raison": "sans_numero", "pour": "Chloé"})
    assert "2 à 12 options" in jouer({"ok": False, "raison": "options"})
    assert "255 caractères" in jouer({"ok": False, "raison": "longueur"})
    assert "seul Patrick" in jouer({"ok": False, "raison": "auteur"})
    assert "la base n'a pas répondu" in jouer(None)
    for texte in (inconnue, jouer(None)):
        assert "rien n'est parti" not in texte and texte.startswith("Je n'ai pas préparé le sondage")


# ── L'envoi : son mot, lui seul, une proposition en suspens ─────────────────────────────────────────────────────────────

def _portes(proprio, reponse):
    appels = []

    async def personne(authorization, nom, corps):
        appels.append(nom)
        return proprio

    async def service(nom, corps):
        appels.append(nom)
        return reponse
    return appels, personne, service


def test_envoie_fait_partir_la_proposition_du_proprietaire():
    appels, personne, service = _portes(True, {"n": 1, "pour": "Anne", "pont": "z3", "question": "Valider la clé chromatique du jour"})
    r = asyncio.run(s.envoyer_sur_son_mot(personne, service, "Bearer t", MOI, "Envoie."))
    assert appels == ["is_owner_st6", "pont_sondage_envoyer"]
    assert "« Valider la clé chromatique du jour »" in r and "pont z3 pour Anne" in r


def test_rien_en_suspens_le_tour_suit_son_cours():
    appels, personne, service = _portes(True, {"n": 0, "pour": None, "pont": None, "question": None})
    assert asyncio.run(s.envoyer_sur_son_mot(personne, service, "Bearer t", MOI, "envoie")) is None
    appels, personne, service = _portes(True, None)
    assert asyncio.run(s.envoyer_sur_son_mot(personne, service, "Bearer t", MOI, "envoie")) is None


def test_une_autre_que_le_proprietaire_n_envoie_rien():
    appels, personne, service = _portes(False, {"n": 1, "pour": "Anne", "pont": "z3", "question": "Q"})
    assert asyncio.run(s.envoyer_sur_son_mot(personne, service, "Bearer t", MOI, "envoie")) is None
    assert appels == ["is_owner_st6"]


def test_un_autre_message_n_appelle_pas_la_base():
    appels, personne, service = _portes(True, {"n": 1})
    assert asyncio.run(s.envoyer_sur_son_mot(personne, service, "Bearer t", MOI, "envoie à Chloé plutôt")) is None
    assert asyncio.run(s.envoyer_sur_son_mot(personne, service, "Bearer t", None, "envoie")) is None
    assert appels == []


# ── De bout en bout, dans le tour d'accompagnement ──────────────────────────────────────────────────────────────────────

def _monter(monkeypatch, proprio, reponse_modele, messages):
    depots, services, systemes = [], [], []

    async def rien(*x, **k):
        return None

    async def ident(*x, **k):
        return {"uid": "u", "svlbh_id": MOI, "profondeur": False, "stx": "ST6" if proprio else "ST5"}

    async def prompt():
        return {"core": "CŒUR", "accompagnement_frame": "CADRE", "st3": "ST3", "version": "t"}

    async def historique(client, key, msgs):
        return None, msgs, 0

    async def canal(*x, **k):
        return "z3"

    async def vide(*x, **k):
        return ""

    async def zero(*x, **k):
        return 0

    async def liste(*x, **k):
        return []

    async def deposer(auth, cible, canal, q, r, mode, pour_elle=False):
        depots.append((q, r))
        return "seance"

    async def personne(authorization, nom, corps, timeout=10):
        return proprio if nom == "is_owner_st6" else None

    async def service(nom, corps, timeout=10):
        services.append((nom, corps))
        if nom == "pont_sondage_proposer":
            return {"ok": True, "pour": "Anne", "pont": "z3", "question": corps["p_question"],
                    "options": corps["p_options"], "avant": corps["p_avant"] is not None}
        if nom == "pont_sondage_envoyer":
            return {"n": 1, "pour": "Anne", "pont": "z3", "question": "Valider la clé chromatique du jour"}
        return None

    class Client:
        async def post(self, url, json=None, headers=None, timeout=None):
            systemes.append(json)

            class R:
                status_code = 200
                text = ""

                def json(self_inner):
                    return {"content": [{"type": "text", "text": reponse_modele}], "stop_reason": "end_turn",
                            "usage": {"input_tokens": 1, "output_tokens": 1}}
            return R()

    a._cache.update(t=0.0, bloc="")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    for nom, f in {"authorize_caller": rien, "gate_subscription": ident, "fetch_prompt": prompt, "_compter_accompagnement": zero,
                   "preparer_historique": historique, "canal_digisha": canal, "contexte_personne": vide, "relecture_pour": vide,
                   "savoir_pour": vide, "fetch_banque_qr": liste, "journaliser_cout": rien, "log_exchange": rien,
                   "fil_digisha_deposer": deposer, "_rpc_service": service, "_rpc_personne": personne,
                   "impasses_de": vide, "release_courante": rien}.items():
        monkeypatch.setattr(d, nom, f)
    monkeypatch.setattr(d, "refuser_st1", lambda ident: None)
    monkeypatch.setattr(d, "journaliser_usage", lambda *x, **k: None)
    monkeypatch.setattr(d, "passer_en_5_5", lambda payload, svlbh: payload["model"])
    monkeypatch.setattr(d, "heure_zurich", lambda: "00h40")
    monkeypatch.setattr(d, "_http", lambda: Client())
    corps = d.AccompagnementRequest(messages=[d.ChatTurn(role=r, content=c) for r, c in messages])
    rep = asyncio.run(d.digisha_accompagnement(request=None, body=corps, x_digisha_token=None, authorization="Bearer t"))
    return rep, depots, services, systemes


def test_le_proprietaire_joint_une_cle_le_sondage_est_propose_pas_envoye(monkeypatch):
    rep, depots, services, systemes = _monter(monkeypatch, True, REPONSE,
                                              [("user", f"Fais valider la clé du jour par Anne\n{CLE}")])
    assert "⟦Sondage" not in rep.reply and "rien n'est parti" in rep.reply and "Pour : Anne (pont z3)" in rep.reply
    proposes = [c for n, c in services if n == "pont_sondage_proposer"]
    assert len(proposes) == 1 and proposes[0]["p_auteur"] == MOI and proposes[0]["p_pour"] == "Anne"
    assert proposes[0]["p_avant"] == "Clé chromatique : Clé du matin — niveau 1 : #B26FB1 #44969E · niveau 2 : #FFFFFF"
    assert not [n for n, _ in services if n == "pont_sondage_envoyer"]
    assert "rien n'est parti" in depots[0][1] and "⟦Sondage" not in depots[0][1]
    assert any("Un sondage WhatsApp, à faire valider" in str(b) for b in systemes[0]["messages"][-1]["content"])


def test_une_st5_ne_recoit_pas_le_cadre_et_sa_ligne_ne_range_rien(monkeypatch):
    rep, depots, services, systemes = _monter(monkeypatch, False, REPONSE, [("user", "prépare un sondage")])
    assert "⟦Sondage" not in rep.reply and "rien n'est parti" not in rep.reply
    assert not [n for n, _ in services if n.startswith("pont_sondage")]
    assert "Un sondage WhatsApp" not in str(systemes[0])


def test_envoie_part_sans_modele_et_se_depose_dans_le_fil(monkeypatch):
    rep, depots, services, systemes = _monter(monkeypatch, True, "NE DOIT PAS ÊTRE APPELÉ",
                                              [("user", "Fais valider"), ("assistant", "Sondage prêt"), ("user", "envoie")])
    assert rep.model == "sondage-sans-modele" and rep.heure == "00h40" and "pont z3 pour Anne" in rep.reply
    assert systemes == [] and [n for n, _ in services] == ["pont_sondage_envoyer"]
    assert depots == [("envoie", rep.reply)]


def test_envoie_d_une_st5_passe_par_le_modele(monkeypatch):
    rep, depots, services, systemes = _monter(monkeypatch, False, "Envoyer quoi ?", [("user", "envoie")])
    assert rep.reply == "Envoyer quoi ?" and len(systemes) == 1
    assert not [n for n, _ in services if n.startswith("pont_sondage")]
