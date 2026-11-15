"""Un dépôt qui ne se fait pas se VOIT dans la réponse (carte ac79ce6b, 15.11.2026).

Le 09.11.2026, 14 tours « À propos de » une fiche neuve ont été refusés par la base sans que rien ne le dise à l'écran :
la réponse s'affichait, le serveur n'écrivait qu'un WARNING. La réponse de /digisha/chat et de /digisha/accompagnement
porte désormais `non_garde` (booléen) et `non_garde_motif` (la phrase à afficher).

Le banc joue les deux routes avec le VRAI dépôt — fil_digisha_deposer, _rpc_personne, _rpc_service — devant une base de
théâtre qui répond par URL : c'est le code HTTP, le corps PostgREST et l'erreur réseau qui sont lus, pas un bouchon."""
import asyncio
import base64
import json as json_
import uuid

import httpx
import pytest

from routers import digisha as d
from routers import digisha_non_garde as ng

MOI = "11111111-1111-4111-8111-111111111111"
FICHE = "22222222-2222-4222-8222-222222222222"
SEANCE = "33333333-3333-4333-8333-333333333333"
VUE = "44444444-4444-4444-8444-444444444444"
PNG = base64.b64encode(b"\x89PNG petit").decode()

DEPOTS = ("digisha_fil_deposer", "digisha_relecture_deposer")
# Ce que PostgREST rend quand la fonction lève : HTTP 400, le message de RAISE EXCEPTION dans « message ».
REFUS_RELECTURE = (400, {"code": "P0001", "details": None, "hint": None, "message": "cette fiche n'est pas la tienne à relire"})
REFUS_FICHE_SOI = (400, {"code": "P0001", "details": None, "hint": None, "message": f"aucune fiche « soi » pour {MOI}"})


class _Base:
    """La base et le modèle vus du serveur. `rpc[nom]` : un (code, corps), une exception à lever, ou absent = 200 null."""

    def __init__(self):
        self.rpc = {nom: (200, SEANCE) for nom in DEPOTS}
        self.seau = (200, {"Key": "ok"})
        self.texte, self.arret = "R", "end_turn"
        self.appels = []            # les fonctions de la base appelées, dans l'ordre

    def _rend(self, quoi):
        if isinstance(quoi, Exception):
            raise quoi
        code, corps = quoi
        # Le corps écrit à la main : httpx.Response(json=None) rend un corps VIDE, pas le « null » de PostgREST.
        return httpx.Response(code, content=json_.dumps(corps, ensure_ascii=False).encode(),
                              headers={"content-type": "application/json"})

    async def post(self, url, json=None, headers=None, timeout=None, content=None, **kw):
        if url == d.ANTHROPIC_URL:
            return httpx.Response(200, json={"content": [{"type": "text", "text": self.texte}], "stop_reason": self.arret,
                                             "usage": {"input_tokens": 1, "output_tokens": 1}})
        if "/storage/v1/object/" in url:
            return self._rend(self.seau)
        assert "/rest/v1/rpc/" in url, url
        nom = url.rsplit("/", 1)[1]
        self.appels.append(nom)
        return self._rend(self.rpc.get(nom, (200, None)))

    def depots(self):
        return [n for n in self.appels if n in DEPOTS]


@pytest.fixture
def base(monkeypatch):
    b = _Base()

    async def rien(*a, **k):
        return None

    async def ident(*a, **k):
        return {"svlbh_id": MOI, "uid": "u", "stx": "ST6"}

    async def prompt():
        return {"core": "C", "tuteur_frame": "T", "accompagnement_frame": "A", "st3": "S", "version": "t"}

    async def historique(client, key, msgs):
        return None, msgs, 0

    async def canal(*a, **k):
        return "z2"

    async def vide(*a, **k):
        return ""

    async def zero(*a, **k):
        return 0

    async def liste(*a, **k):
        return []

    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("DIGISHA_SUPABASE_URL", "https://base.test")
    monkeypatch.setenv("DIGISHA_SUPABASE_SERVICE_KEY", "cle-serveur")
    for nom, f in {"authorize_caller": rien, "gate_subscription": ident, "fetch_prompt": prompt,
                   "_compter_accompagnement": zero, "preparer_historique": historique, "canal_digisha": canal,
                   "contexte_personne": vide, "relecture_pour": vide, "peut_relire": rien, "savoir_pour": vide,
                   "fetch_banque_qr": liste, "lexique_patrick": vide, "journaliser_cout": rien, "log_exchange": rien}.items():
        monkeypatch.setattr(d, nom, f)
    monkeypatch.setattr(d, "journaliser_usage", lambda *a, **k: None)
    monkeypatch.setattr(d, "passer_en_5_5", lambda payload, svlbh: payload["model"])
    monkeypatch.setattr(d, "_http", lambda: b)
    return b


def _tour(contenu="Q"):
    return [d.ChatTurn(role="user", content=contenu)]


def _accompagnement(contenu="Q", **k):
    return asyncio.run(d.digisha_accompagnement(request=None, body=d.AccompagnementRequest(messages=_tour(contenu), **k),
                                                x_digisha_token=None, authorization="Bearer t"))


def _chat(**k):
    return asyncio.run(d.digisha_chat(request=None, body=d.ChatRequest(messages=_tour(), **k), x_digisha_token=None,
                                      authorization="Bearer t"))


# ── Le tour ──────────────────────────────────────────────────────────────────────────────────────────────────────

def test_depot_reussi_rien_a_dire(base):
    for r in (_accompagnement(), _accompagnement(fil_consultante_id=FICHE), _chat()):
        assert r.reply == "R" and r.non_garde is False and r.non_garde_motif is None
    assert base.depots() == ["digisha_fil_deposer", "digisha_relecture_deposer", "digisha_fil_deposer"]
    assert "coach_view_target" not in base.appels          # un dépôt réussi ne demande rien de plus à la base


def test_depot_refuse_a_propos_d_une_fiche_se_voit(base, journal_digisha):
    """Le cas du 09.11 rejoué : la relecture est refusée, la réponse arrive ET dit qu'elle n'est pas gardée."""
    base.rpc["digisha_relecture_deposer"] = REFUS_RELECTURE
    r = _accompagnement(fil_consultante_id=FICHE)
    assert r.reply == "R"
    assert r.non_garde is True
    assert r.non_garde_motif == "Ce tour n'a pas été gardé\N{NO-BREAK SPACE}: l'enregistrement sur cette fiche a été refusé."
    assert base.depots() == ["digisha_relecture_deposer"]                  # un seul essai, pas de second dépôt
    ecrit = "\n".join(journal_digisha)
    assert "WARNING: digisha — rpc digisha_relecture_deposer HTTP 400" in ecrit      # le journal garde le détail
    assert "WARNING: digisha — non_garde=tour genre=droit" in ecrit                  # et une ligne qui se cherche


def test_depot_refuse_sur_soi_se_voit_sans_identifiant(base):
    base.rpc["digisha_fil_deposer"] = REFUS_FICHE_SOI
    for r in (_accompagnement(), _chat()):
        assert r.reply == "R" and r.non_garde is True
        assert r.non_garde_motif == ng.MOTIFS_TOUR["fiche_soi"]
        assert MOI not in r.non_garde_motif and MOI[:8] not in r.non_garde_motif


@pytest.mark.parametrize("panne", [httpx.ConnectError("réseau"), httpx.ReadTimeout("délai"), (503, {"message": "x"}),
                                   (500, {"code": "57014", "message": "canceling statement due to statement timeout"})])
def test_depot_en_erreur_reseau_se_voit(base, journal_digisha, panne):
    base.rpc["digisha_fil_deposer"] = panne
    for r in (_accompagnement(), _chat()):
        assert r.reply == "R" and r.non_garde is True
        assert r.non_garde_motif == "Ce tour n'a probablement pas été gardé\N{NO-BREAK SPACE}: la base de données n'a pas répondu."
    assert "WARNING: digisha — non_garde=tour genre=panne" in journal_digisha


def test_session_refusee_par_la_base(base):
    base.rpc["digisha_fil_deposer"] = (401, {"code": "PGRST301", "message": "JWT expired"})
    assert _accompagnement().non_garde_motif == ng.MOTIFS_TOUR["session"]


def test_voir_comme_se_dit_l_artefact_d_app_non(base, journal_digisha):
    """La base répond 200 « null » sans rien écrire dans deux cas : en « voir comme » (ça se dit), et pour le message
    d'ouverture écrit par l'app (« 🎓 … », jamais gardé : rien à dire, personne n'a rien écrit)."""
    base.rpc["digisha_fil_deposer"] = (200, None)
    base.rpc["coach_view_target"] = (200, VUE)
    r = _accompagnement()
    assert r.non_garde is True and r.non_garde_motif == ng.MOTIFS_TOUR["voir_comme"]
    assert "«\N{NO-BREAK SPACE}voir comme\N{NO-BREAK SPACE}»" in r.non_garde_motif and VUE not in r.non_garde_motif
    base.rpc["coach_view_target"] = (200, None)
    r = _accompagnement("🎓 Module 1 ouvert pour Maya")
    assert r.non_garde is False and r.non_garde_motif is None
    assert any(l.startswith("INFO: digisha — depot_sans_seance=digisha_fil_deposer") for l in journal_digisha)   # une trace, pas un écran


def test_le_sondage_parti_sur_son_mot_dit_aussi_son_depot(base, monkeypatch):
    async def parti(*a, **k):
        return "Le sondage est remis au pont."
    monkeypatch.setattr(d, "envoyer_sur_son_mot", parti)
    base.rpc["digisha_fil_deposer"] = httpx.ConnectError("réseau")
    r = _accompagnement("envoie")
    assert r.model == "sondage-sans-modele" and r.reply == "Le sondage est remis au pont."
    assert r.non_garde is True and r.non_garde_motif == ng.MOTIFS_TOUR["panne"]


def test_hors_d_une_route_le_depot_ne_demande_rien_de_plus(base):
    """fil_digisha_deposer appelé seul (bancs existants) : même retour qu'avant, aucun appel ajouté."""
    base.rpc["digisha_fil_deposer"] = (200, None)
    assert asyncio.run(d.fil_digisha_deposer("Bearer t", None, "z2", "Q", "R", "accompagnement")) is None
    assert base.appels == ["digisha_fil_deposer"]


# ── Le motif : une phrase fixe, jamais le message de la base ─────────────────────────────────────────────────────

@pytest.mark.parametrize("code, corps, genre", [
    (400, {"code": "P0001", "message": "cette fiche n'est pas la tienne à relire"}, "droit"),
    (400, {"code": "P0001", "message": "cette fiche n'est pas la tienne à accompagner"}, "droit"),
    (400, {"code": "P0001", "message": f"aucune fiche « soi » pour {MOI}"}, "fiche_soi"),
    (400, {"code": "P0001", "message": f"aucune fiche «\N{NO-BREAK SPACE}soi\N{NO-BREAK SPACE}» pour {MOI}"}, "fiche_soi"),
    (400, {"code": "P0001", "message": "fiche introuvable"}, "fiche_introuvable"),
    (400, {"code": "P0001", "message": "canal inconnu : z99"}, "canal"),
    (400, {"code": "P0001", "message": "non authentifié"}, "session"),
    (401, {"code": "PGRST301", "message": "JWT expired"}, "session"),
    (401, None, "session"),
    (403, {"code": "42501", "message": "permission denied for function digisha_fil_deposer"}, "refus"),
    (404, {"code": "PGRST202", "message": "Could not find the function public.digisha_fil_deposer"}, "refus"),
    (409, {"code": "23505", "message": "duplicate key value", "details": "Key (first_name)=(Maya) already exists."}, "refus"),
    (400, "pas du JSON", "refus"),
    (500, {"message": "cette fiche n'est pas la tienne à relire"}, "panne"),      # 5xx : la base flanche, quoi qu'elle dise
    (502, None, "panne"), (503, None, "panne"), (504, None, "panne"), (429, None, "panne"), (408, None, "panne"),
    (None, None, "panne"),
])
def test_genre_du_refus(code, corps, genre):
    texte = corps if isinstance(corps, str) or corps is None else json_.dumps(corps, ensure_ascii=False)
    assert ng.genre_du_refus(code, texte) == genre


def test_aucun_motif_ne_porte_une_donnee():
    """Les phrases sont fixes : ni chiffre (identifiant, code), ni mot venu de la base."""
    phrases = list(ng.MOTIFS_TOUR.values()) + [ng.MOTIF_CONSIGNES, ng.MOTIF_ILLUSTRATIONS, ng.motif_pieces(1, 1)]
    assert set(ng.MOTIFS_TOUR) == {"droit", "fiche_soi", "fiche_introuvable", "canal", "session", "refus", "panne", "voir_comme"}
    for p in phrases:
        assert p.endswith(".") and len(p) < 140 and not any(c.isdigit() for c in p), p
    assert ng.Suivi().champs() == {}                                     # rien à dire : la réponse garde non_garde faux


def test_motif_pieces_accorde():
    assert ng.motif_pieces(1, 1) == "La pièce jointe de ce tour n'a pas été gardée."
    assert ng.motif_pieces(2, 2) == "Les 2 pièces jointes de ce tour n'ont pas été gardées."
    assert ng.motif_pieces(1, 3) == "1 des 3 pièces jointes de ce tour n'a pas été gardée."
    assert ng.motif_pieces(2, 3) == "2 des 3 pièces jointes de ce tour n'ont pas été gardées."


# ── Ce qui s'attache à la page : pièces jointes, consignes, images du lexique ────────────────────────────────────

def _avec_photo():
    return [{"type": "text", "text": "regarde"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": PNG}}]


def test_piece_jointe_gardee_rien_a_dire(base):
    base.rpc["digisha_page_pieces_ajouter"] = (200, 1)
    r = _accompagnement(_avec_photo())
    assert r.non_garde is False and r.non_garde_motif is None
    assert "digisha_page_pieces_ajouter" in base.appels


@pytest.mark.parametrize("seau, rattachement", [((400, {"error": "Payload too large"}), (200, 1)),     # refusée par le seau
                                                ((200, {"Key": "ok"}), (200, 0)),                      # aucune page à compléter
                                                ((200, {"Key": "ok"}), (500, {"message": "x"}))])      # la base ne répond pas
def test_piece_jointe_non_gardee_se_voit_le_tour_reste(base, seau, rattachement):
    base.seau, base.rpc["digisha_page_pieces_ajouter"] = seau, rattachement
    r = _accompagnement(_avec_photo())
    assert r.reply == "R" and r.non_garde is True
    assert r.non_garde_motif == "La pièce jointe de ce tour n'a pas été gardée."


def test_tour_non_garde_ne_redit_pas_ses_pieces(base):
    base.rpc["digisha_fil_deposer"] = REFUS_FICHE_SOI
    r = _accompagnement(_avec_photo())
    assert r.non_garde_motif == ng.MOTIFS_TOUR["fiche_soi"]              # une seule phrase : le tour, pièces comprises


def test_consignes_refusees_se_voient_le_tour_reste(base, journal_digisha):
    base.texte = "Entendu.\n\nConsignes pour Maya :\n- Laisser venir la colère avant de mesurer."
    base.rpc["digisha_consignes_contexte"] = (200, {"prenom": "Maya", "consignes": []})
    base.rpc["digisha_consignes_poser"] = REFUS_RELECTURE
    r = _accompagnement(fil_consultante_id=FICHE)
    assert base.depots() == ["digisha_relecture_deposer"] and "digisha_consignes_poser" in base.appels
    assert r.non_garde is True and r.non_garde_motif == "Les consignes de ce tour n'ont pas été enregistrées."
    assert "WARNING: digisha — non_garde=consignes genre=echec" in journal_digisha
    base.rpc["digisha_consignes_poser"] = (200, {"posees": 1, "retirees": 0})
    assert _accompagnement(fil_consultante_id=FICHE).non_garde is False


def test_consignes_d_une_reponse_coupee_se_voient(base, journal_digisha):
    """Une réponse coupée ne pose rien (2026-10-18f) : la personne voit le bloc à l'écran, elle doit savoir qu'il n'est pas posé."""
    base.texte, base.arret = "Entendu.\n\nConsignes pour Maya :\n- Laisser venir la colère avant", "max_tokens"
    base.rpc["digisha_consignes_contexte"] = (200, {"prenom": "Maya", "consignes": []})
    r = _accompagnement(fil_consultante_id=FICHE)
    assert "digisha_consignes_poser" not in base.appels
    assert r.non_garde is True and r.non_garde_motif == ng.MOTIF_CONSIGNES
    assert "WARNING: digisha — non_garde=consignes genre=coupee" in journal_digisha


def test_consignes_d_une_fiche_dont_le_prenom_ne_se_lit_pas(base, journal_digisha):
    """Fiche neuve, avant sa première séance : digisha_consignes_contexte rend null (elle n'est pas encore dans
    fils_lisibles()), le serveur ne connaît pas le prénom et ne peut pas poser le bloc que la réponse affiche."""
    base.texte = "Entendu.\n\nConsignes pour Maya :\n- Laisser venir la colère avant de mesurer."
    r = _accompagnement(fil_consultante_id=FICHE)                        # contexte : 200 null
    assert base.depots() == ["digisha_relecture_deposer"] and "digisha_consignes_poser" not in base.appels
    assert r.non_garde is True and r.non_garde_motif == ng.MOTIF_CONSIGNES
    assert "WARNING: digisha — non_garde=consignes genre=prenom" in journal_digisha
    base.texte = "Entendu, je l'appliquerai à sa prochaine séance."      # aucun bloc : rien à poser, rien à dire
    assert _accompagnement(fil_consultante_id=FICHE).non_garde is False


def test_consignes_annoncees():
    assert d.consignes_annoncees("Entendu.\n\nConsignes pour Maya :\n- Laisser venir la colère.")
    assert d.consignes_annoncees("**Consignes retirées pour Maya :**\n\n1. Proposer le pont Hellinger.")
    assert not d.consignes_annoncees("Je garde tes consignes pour Maya en tête.")           # une phrase, pas un bloc
    assert not d.consignes_annoncees("Consignes pour Maya :\nRien de nouveau.")              # un titre sans ligne à puce
    assert not d.consignes_annoncees("") and not d.consignes_annoncees(None)


ILLUS = [{"heure": "09h00", "genre": "photo", "chemin": "lexique/x.png", "media_type": "image/png", "titre": "x"}]


@pytest.mark.parametrize("rendu, dit", [(1, False),          # rattachées à la page
                                        (0, True),           # aucune page à compléter
                                        (None, True)])       # la base n'a pas répondu
def test_images_du_lexique_non_rattachees_se_voient(monkeypatch, rendu, dit):
    async def service(nom, corps, timeout=10):
        assert nom == "digisha_page_pieces_ajouter" and corps["p_session"] == SEANCE
        return rendu
    monkeypatch.setattr(d, "_rpc_service", service)
    suivi = ng.Suivi()
    asyncio.run(d.garder_pieces_et_illustrations(SEANCE, d.AccompagnementRequest(messages=_tour()), ILLUS, suivi))
    assert suivi.champs() == ({"non_garde": True, "non_garde_motif": ng.MOTIF_ILLUSTRATIONS} if dit else {})


def test_images_du_lexique_sans_seance_c_est_le_tour_qui_le_dit():
    suivi = ng.Suivi()
    asyncio.run(d.garder_pieces_et_illustrations(None, d.AccompagnementRequest(messages=_tour()), ILLUS, suivi))
    assert suivi.champs() == {}


# ── Ce que l'app reçoit : le JSON de la route ───────────────────────────────────────────────────────────────────

CHAMPS_D_AVANT = {"reply", "model", "release", "illustrations", "heure"}


def _poster(client, cle=None, **corps):
    entetes = {"Authorization": "Bearer t", **({"X-DiGiSha-Envoi": cle} if cle else {})}
    r = client.post("/digisha/accompagnement", json={"messages": [{"role": "user", "content": "Q"}], **corps}, headers=entetes)
    assert r.status_code == 200, r.text
    return r.json()


def test_le_json_garde_ses_champs_et_en_gagne_deux(client, base):
    """Une app qui ne lit pas `non_garde` ne voit rien changer : les cinq champs d'avant sont là, inchangés."""
    garde = _poster(client)
    assert set(garde) == CHAMPS_D_AVANT | {"non_garde", "non_garde_motif"}
    assert garde["reply"] == "R" and garde["non_garde"] is False and garde["non_garde_motif"] is None
    base.rpc["digisha_relecture_deposer"] = REFUS_RELECTURE
    refuse = _poster(client, fil_consultante_id=FICHE)
    assert set(refuse) == set(garde) and refuse["reply"] == "R"
    assert refuse["non_garde"] is True and refuse["non_garde_motif"] == ng.MOTIFS_TOUR["droit"]


def test_une_reponse_redemandee_revient_avec_son_non_garde(client, base):
    """La même clé d'envoi rend la même réponse (digisha_envoi) : `non_garde` compris, sans second dépôt."""
    cle = str(uuid.uuid4())                                               # une clé neuve : la mémoire des envois vit 10 minutes
    base.rpc["digisha_fil_deposer"] = httpx.ConnectError("réseau")
    premiere = _poster(client, cle=cle)
    base.rpc["digisha_fil_deposer"] = (200, SEANCE)
    seconde = _poster(client, cle=cle)
    assert premiere == seconde and seconde["non_garde"] is True
    assert base.depots() == ["digisha_fil_deposer"]
