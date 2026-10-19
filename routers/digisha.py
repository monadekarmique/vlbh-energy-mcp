"""digiSha router — tuteur « Les 26 ponts » + accompagnement DiGiSha.

POST /digisha/chat          → tuteur de formation (proxy Claude).
POST /digisha/accompagnement → présence d'accompagnement.

Le prompt est CENTRALISÉ dans Supabase (table digisha_prompt, ligne active) et
fetché au runtime (cache ~60 s) avec fallback en dur. L'app n'embarque AUCUNE
clé Anthropic ; elle s'authentifie avec X-DigiSha-Token (env DIGISHA_TOKEN).

Routage modèle (DEC Patrick 2026-06-12) :
  ST2 (alias legacy "membre")        → claude-sonnet-4-6
  ST3-ST4 et au-delà ("praticien")   → claude-fable-5
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import re
import time
import uuid
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import httpx
from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from routers import digisha_semantique
from routers.digisha_formation_m1 import m1_system_block
from routers.digisha_memoire import journaliser_usage, preparer_historique
from routers.digisha_contexte import mettre_en_forme, sans_relances
from routers.digisha_pieces import Contenu, compter_pieces, marquer_cache, texte_de, valider_contenu
from routers.digisha_cache import du_tour, partage, ranger_pour_cache

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONTENT = json.loads((DATA_DIR / "formation_26_ponts.json").read_text())
FCB_CH11 = json.loads((DATA_DIR / "fcb_chapitre11.json").read_text())

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# ── Client HTTP partagé ──────────────────────────────────────────────────────
# Mesuré sur Render le 09.09.2026 : un `httpx.AsyncClient()` par appel sortant
# reconstruit à chaque fois son contexte SSL (trousseau de certificats compris),
# et ces allocations OpenSSL ne sont jamais rendues au système — +4 MB de RSS
# par requête DiGiSha, escalier qui ne redescend pas, OOM du starter 512 MB
# après ~100 requêtes. Un seul client par process = un seul contexte SSL.
# Les délais restent ceux de chaque appel (`timeout=…` sur la requête).
_http_client: httpx.AsyncClient | None = None


def _http() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=10)  # défaut = l'ancien délai Supabase
    return _http_client


async def close_http() -> None:
    """Ferme le client partagé (arrêt propre du process — lifespan)."""
    global _http_client
    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()
    _http_client = None
# Version servie si la table digisha_prompt est injoignable (le fetch renvoie la vraie).
FALLBACK_VERSION = "digisha-v2.1-radiesthesie-defunts (router fallback)"
# ST2 → sonnet ; ST3-ST4/ST5/ST6-ST7 → fable. Legacy "membre"/"praticien" acceptés.
ST2_PARCOURS = {"membre", "st1", "st2"}   # membres → sonnet ; st3+ → fable

def model_for(parcours: str) -> str:
    # DEC Patrick 2026-07-06 (économie post-incident crédit) : le TUTEUR tourne
    # sur sonnet pour TOUS les parcours (~5x moins cher que fable, largement au
    # niveau pour la maïeutique). L'accompagnement reste sur ACCOMPAGNEMENT_MODEL.
    # (Remplace la DEC 2026-06-12 : ST3+ → fable-5.)
    return "claude-sonnet-4-6"


# ── Économie de tokens (DEC Patrick 2026-07-06, incident crédit API) ──────────
# Avant : le corpus COMPLET (~187K tokens) partait dans CHAQUE message, sans
# cache → ~2,5-3,5 $ le message sur fable-5 (les ~50 $/mois d'Anne à elle seule).
# Après : (a) system en BLOCS avec prompt caching (préfixe statique partagé,
# TTL 5 min, lecture -90 %) ; (b) corpus SLIM (résumés, ~32K tokens) dans le
# bloc caché, la capsule COURANTE complète voyage dans le bloc dynamique.
# Revert corpus complet : env DIGISHA_FULL_CORPUS=1 (reste caché).
_SLIM_KEYS = ("id", "code", "famille", "famille_secondaire", "titre", "title",
              "auteurs", "orientations", "resume_membre", "resume")


def _slim_list(items):
    if not isinstance(items, list):
        return items
    return [{k: it[k] for k in _SLIM_KEYS if k in it} if isinstance(it, dict) else it
            for it in items]


def _build_static_corpus() -> str:
    if os.environ.get("DIGISHA_FULL_CORPUS") == "1":
        return json.dumps(CONTENT, ensure_ascii=False)
    slim = {
        "meta": CONTENT.get("meta"),
        "socle": CONTENT.get("socle"),
        "tronc_commun": _slim_list(CONTENT.get("tronc_commun")),
        "st1": CONTENT.get("st1"),
        "st2_modules": _slim_list(CONTENT.get("st2_modules")),
        "st5": CONTENT.get("st5"),
        "st6_st7": CONTENT.get("st6_st7"),
        "ponts": _slim_list(CONTENT.get("ponts")),
        "protocole_s7": CONTENT.get("protocole_s7"),
        "transverses": CONTENT.get("transverses"),
        "bibliotheque_ecoute": CONTENT.get("bibliotheque_ecoute"),
        "note": "Corpus en RÉSUMÉS (id/titre/résumé). Le contenu COMPLET de la "
                "capsule courante est fourni dans « État du membre ». Pour "
                "enseigner une autre capsule, demande au membre de l'ouvrir.",
    }
    return json.dumps(slim, ensure_ascii=False)


STATIC_CORPUS_JSON = _build_static_corpus()


def _full_item(capsule_id):
    if not capsule_id:
        return None
    for coll in ("ponts", "tronc_commun", "st2_modules"):
        for it in CONTENT.get(coll) or []:
            if isinstance(it, dict) and it.get("id") == capsule_id:
                return it
    return None

# Tuteur — FALLBACK en dur si la table digisha_prompt est injoignable.
TUTEUR_FALLBACK = """Tu es digiSha, le tuteur de formation du Digital Shaman Lab (vlbh.energy),
au service des membres du Cercle de Lumière et des praticiens VLBH.

Ta méthode est maïeutique : tu enseignes PAR LES QUESTIONS, dans la lignée
des Questions digiSha de Libération (4 phases : distinguer le Soi du
Non-Soi, explorer les racines ancestrales, reprendre le pouvoir, compléter
le dégagement). Tu poses une question avant de donner une réponse.

Ton corpus : « Les 26 ponts » — socle Grof, tronc commun M1-M4 et 16
ponts de méthode (fourni en JSON), plus les capsules ST5 et ST6-ST7.
Ta thèse centrale : traiter le noyau traite les couches.

Règles :
1. Tu adaptes chaque explication à l'orientation d'entrée du membre :
   tu pars TOUJOURS de la méthode qu'il connaît pour amener le concept VLBH.
2. Tu respectes le cadre « Seul ce qui est vérifiable est vrai » :
   le pont épigénétique est une ANALOGIE STRUCTURELLE, jamais une preuve.
   Tu ne promets aucune guérison.
3. Parcours ST2 (membres) : langage simple, capsules courtes, pas de
   jargon sans le définir — M1 (métrologie) avant les ponts. Parcours
   ST3-ST4 (praticien) : tables complètes, instruments de mesure
   (SLA/SLPMO, Linggui Bafa, Anatomy 12D), protocole S7 — gating
   progressif : M1-M2 pour ST3, M1-M4 pour la certification ST4.
4. Tu proposes à chaque fin d'échange 2-3 capsules suivantes parmi les
   voisins du graphe — jamais une liste imposée, jamais de pression.
5. Le SLSA peut dépasser 100 % (jusqu'à 50 000 %) — jamais une erreur.
6. Ton ton : chaleureux, précis, voix Digital Shaman Lab. Français.
7. Chaque capsule se termine par le temps Terre : tu donnes la
   micro-pratique d'ancrage (champ "terre" du JSON) et tu invites le
   membre à la faire réellement, maintenant, dans son corps.
8. TU ENSEIGNES, tu ne récites pas : suis le "plan_tuteur" de la
   capsule (séquence question → insight cible → fausse piste à
   détecter), puise dans "lecon" pour nourrir tes relances, applique
   l'adaptation correspondant à l'orientation du membre, et termine
   par la vérification du plan. La leçon est ta réserve, jamais un
   bloc à coller.
8b. En parcours ST2, si l'accompagnante mentionne que son proche
   pratique une méthode précise (EMDR, ostéopathie, IFS...), propose-lui
   la grille d'écoute correspondante (section "bibliotheque_ecoute") —
   uniquement à la demande, jamais comme étape du programme."""


# Accompagnement — FALLBACK en dur.
ACCOMPAGNEMENT_FALLBACK = """Tu es « DiGiSha », l'IA Digital Shaman de SVLBH — la présence d'accompagnement personnelle de la praticienne du Cercle de Lumière (Digital Shaman Lab). Tu n'es pas un chatbot générique : tu es une accompagnatrice énergétique et pédagogique, dans la posture et le vocabulaire SVLBH.

Posture :
- Tu t'adresses à une femme certifiée (ST3+) qui a déjà traversé ses propres démons dans sa chair. Tu ne l'infantilises pas, tu ne la censures pas, tu ne moralises pas, tu n'ajoutes pas de disclaimer médical ni de « registre de prudence » générique. Le gating SVLBH EST la garantie de privacy.
- Vous explorez radiesthésiquement une situation pour découvrir à quel niveau des lignées de défunts (Lfem / Lmasc) les énergies vibratoires se sont accumulées. Des mots médicaux (cancer, tumeur, pathologie, stade) désignent le plus souvent les maux des défunts d'une lignée — pas un vivant en danger : AUCUN rabattage « médecin / 144 / psy ». Pour une praticienne, le sujet est ce qu'elle décode, souvent pour autrui ; elle n'est pas la souffrante.
- Tu restes dans le cadre vibratoire / transgénérationnel SVLBH.
- Français, chaleureux, incarné, précis et concis. Jamais bavard. Tu n'exposes pas ton raisonnement interne."""

ACCOMPAGNEMENT_MODEL = "claude-opus-4-8"   # même modèle que Pilote/DiGiSha pro-web


# Prompt DiGiSha CENTRALISÉ : table Supabase digisha_prompt (ligne active),
# fetchée au runtime avec cache ~60 s + fallback en dur ci-dessus.
_prompt_cache: dict | None = None
_prompt_cache_at: float = 0.0


async def fetch_prompt() -> dict | None:
    """Lit la ligne active de digisha_prompt (best effort). None → fallback."""
    global _prompt_cache, _prompt_cache_at
    now = time.monotonic()
    if _prompt_cache is not None and now - _prompt_cache_at < 60:
        return _prompt_cache
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        return None
    try:
        client = _http()
        resp = await client.get(
            f"{supa_url}/rest/v1/digisha_prompt",
            params={
                "active": "eq.true",
                "select": "version,core,accompagnement_frame,st3,tuteur_frame",
                "limit": "1",
            },
            headers={"apikey": supa_key, "Authorization": f"Bearer {supa_key}"},
            timeout=10,
        )
        if resp.status_code == 200:
            rows = resp.json()
            if rows and rows[0].get("core"):
                _prompt_cache = rows[0]
                _prompt_cache_at = now
                return _prompt_cache
    except Exception:
        pass
    return None


def verify_digisha_token(x_digisha_token: str) -> None:
    expected = os.environ.get("DIGISHA_TOKEN", "")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DIGISHA_TOKEN not configured",
        )
    if x_digisha_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-DigiSha-Token",
        )


log = logging.getLogger("digisha")
if not log.handlers:  # uvicorn ne touche pas au root logger : sans ceci, rien sous WARNING ne sort
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(levelname)s: digisha — %(message)s"))
    log.addHandler(_h)
    log.setLevel(logging.INFO)
    log.propagate = False


def _role_de_cle(cle: str) -> str:
    """Rôle porté par une clé Supabase, sans jamais l'afficher : JWT hérité
    (claim `role`) ou nouvelle clé `sb_secret_…` / `sb_publishable_…`."""
    if not cle:
        return "ABSENTE"
    if cle.startswith("sb_secret_"):
        return "sb_secret (serveur)"
    if cle.startswith("sb_publishable_"):
        return "sb_publishable (PAS une clé serveur)"
    try:
        payload = cle.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return str(json.loads(base64.urlsafe_b64decode(payload)).get("role", "?"))
    except Exception:
        return "illisible"


def journaliser_env() -> None:
    """Une ligne au démarrage : les variables DiGiSha sont-elles là, et la clé
    est-elle bien une clé serveur ? (Réponse au journal muet du 30.08 — sans
    accès aux valeurs, qui ne sortent jamais.)"""
    url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    projet = re.sub(r"^https?://([a-z0-9]+)\..*$", r"\1", url) if url else "ABSENTE"
    role = _role_de_cle(os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", ""))
    ok = bool(url) and role in ("service_role", "sb_secret (serveur)")
    (log.info if ok else log.warning)(
        "env DiGiSha : DIGISHA_SUPABASE_URL=%s · DIGISHA_SUPABASE_SERVICE_KEY rôle=%s · ANTHROPIC_API_KEY=%s%s",
        projet, role, "présente" if os.environ.get("ANTHROPIC_API_KEY") else "ABSENTE",
        "" if ok else " — le journal digisha_chat_log et le compteur Profondeur ne peuvent pas écrire",
    )


journaliser_env()

# ── Garde d'appel — durcissement 2026-08-21 (audit sécurité 5 apps Priv) ─────
# `X-DigiSha-Token` est un secret PARTAGÉ, embarqué en clair dans six binaires
# publiés : `strings` sur une IPA suffit à le lire. Il n'établit donc RIEN sur
# l'appelant, alors qu'il ouvre un proxy LLM facturé. Tant que des builds
# installés ne savent faire que ça, on le garde comme laissez-passer de repli —
# mais il ne vaut plus autant qu'une session :
#   • une session Supabase valide (Bearer) suffit désormais à elle seule ;
#   • le repli « jeton seul » est plafonné par IP, et bien plus bas ;
#   • chaque appel sans session est journalisé, pour mesurer l'adoption et l'abus.
# Le jeton sera retiré quand les six apps enverront leur JWT (étape 3 du plan).
RATE_ANON_PER_HOUR = int(os.environ.get("DIGISHA_RATE_ANON_HOUR", "12"))
RATE_USER_PER_HOUR = int(os.environ.get("DIGISHA_RATE_USER_HOUR", "120"))

# Fenêtre glissante en mémoire. Le service tourne en instance unique (Render
# starter, numInstances=1) : pas de store partagé nécessaire aujourd'hui. Si on
# passe à plusieurs instances, ce compteur devient par-instance — le noter alors.
_rate_hits: dict[str, list[float]] = {}


def _rate_check(key: str, limit: int) -> None:
    now = time.time()
    hits = [t for t in _rate_hits.get(key, []) if now - t < 3600]
    if len(hits) >= limit:
        _rate_hits[key] = hits
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop d'appels sur cette heure — réessaie plus tard.",
        )
    hits.append(now)
    _rate_hits[key] = hits


async def resolve_uid(authorization: str | None) -> str | None:
    """UID Supabase du porteur du Bearer, ou None. Un seul appel /auth/v1/user,
    sans lecture de profil : sert à décider du titre d'accès et à clé le quota."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        return None
    try:
        client = _http()
        r = await client.get(
            f"{supa_url}/auth/v1/user",
            headers={"apikey": supa_key, "Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        return r.json().get("id")
    except Exception:
        return None


async def _quota(key: str, limit: int) -> None:
    """Le quota par heure, tenu EN BASE (migration 2026-10-18m, digisha_appel_heure_incr) : il survit à un redéploiement et le
    web pro lit le même compteur (clé = uid, ou « ip:… »). Base injoignable → la fenêtre en mémoire, comme avant (jamais ouvert
    sans compte). fable, 18.10.2026, fiche 9714894f."""
    r = await _rpc_service("digisha_appel_heure_incr", {"p_cle": key, "p_limite": limit}, timeout=5)
    if isinstance(r, dict) and "ok" in r:
        if not r.get("ok"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Trop d'appels sur cette heure — réessaie plus tard.",
            )
        return
    _rate_check(key, limit)


async def authorize_caller(
    request: Request,
    x_digisha_token: str | None,
    authorization: str | None,
) -> str | None:
    """Autorise l'appel et applique le quota. Renvoie l'uid s'il y en a un.

    Session valide → on passe, quota généreux, le jeton n'est même pas regardé.
    Pas de session → refusé (401) depuis le 19.10 ; DIGISHA_JETON_SEUL=oui rouvre le jeton statique, quota bas par IP + trace.
    """
    uid = await resolve_uid(authorization)
    if uid:
        await _quota(uid, RATE_USER_PER_HOUR)          # même clé que le web pro : l'uid seul
        return uid
    # 19.10.2026 (fiche 271f6a10) : le jeton statique SEUL ne suffit plus. Il était dans l'APK Priv-1 téléchargeable sans
    # connexion (v2.5.1, remplacée le 18.10) ; mesuré au journal Render du 14.10 au 19.10 : AUCUN appel « jeton sans session ».
    # Filet : DIGISHA_JETON_SEUL=oui (variable Render) rouvre l'ancien passage sans toucher au code.
    if os.environ.get("DIGISHA_JETON_SEUL", "").lower() not in ("oui", "1", "true"):
        log.warning("digisha: appel SANS session refusé (path=%s ua=%s)", request.url.path, request.headers.get("user-agent", "?"))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Connexion requise pour DiGiSha — reconnecte-toi dans l'app.")
    verify_digisha_token(x_digisha_token or "")
    ip = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip() \
        or (request.client.host if request.client else "unknown")
    log.warning(
        "digisha: appel au jeton statique SANS session (ip=%s path=%s ua=%s)",
        ip, request.url.path, request.headers.get("user-agent", "?"),
    )
    await _quota(f"ip:{ip}", RATE_ANON_PER_HOUR)
    return None


async def gate_subscription(authorization: str | None) -> dict | None:
    """Gate abonnement Phase 1 (DEC Patrick 2026-06-16).

    Si un Bearer JWT Supabase est fourni (app Priv-1, désormais sur le projet
    canonique), on vérifie pro_status : un compte praticienne explicitement
    désactivé (SUSPENDED/REVOKED) reçoit 402. Sans Bearer (Cercle Lumière, pas
    de session utilisateur) ou sans praticienne_profile (patiente / membre ST2),
    on laisse passer. Fail-open : toute erreur de validation/réseau ne bloque
    PAS DiGiSha — le gate ne retire l'accès qu'aux comptes désactivés.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        return
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        return
    try:
        client = _http()
        ur = await client.get(
            f"{supa_url}/auth/v1/user",
            headers={"apikey": supa_key, "Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if ur.status_code != 200:
            return
        uid = ur.json().get("id")
        if not uid:
            return
        profile_select = "svlbh_id,pro_status,stx,digisha_profondeur,digisha_profondeur_trial_until"
        pr = await client.get(
            f"{supa_url}/rest/v1/praticienne_profile",
            params={"supabase_user_id": f"eq.{uid}",
                    "select": profile_select,
                    "limit": 1},
            headers={"apikey": supa_key, "Authorization": f"Bearer {supa_key}"},
        )
        rows = pr.json() if pr.status_code == 200 else []
        if not rows:
            # Doctrine #11 : multi-comptes → 1 svlbh_id canonique. Si le slot
            # direct ne matche pas, résoudre via praticienne_user_alias pour
            # ne pas perdre l'exemption ST5+/profondeur des comptes secondaires.
            al = await client.get(
                f"{supa_url}/rest/v1/praticienne_user_alias",
                params={"supabase_user_id": f"eq.{uid}", "select": "svlbh_id", "limit": 1},
                headers={"apikey": supa_key, "Authorization": f"Bearer {supa_key}"},
            )
            alias_rows = al.json() if al.status_code == 200 else []
            alias_svlbh = alias_rows[0].get("svlbh_id") if alias_rows else None
            if alias_svlbh:
                pr2 = await client.get(
                    f"{supa_url}/rest/v1/praticienne_profile",
                    params={"svlbh_id": f"eq.{alias_svlbh}",
                            "select": profile_select,
                            "limit": 1},
                    headers={"apikey": supa_key, "Authorization": f"Bearer {supa_key}"},
                )
                rows = pr2.json() if pr2.status_code == 200 else []
    except Exception:
        return None
    status_val = rows[0].get("pro_status") if rows else None
    if status_val in ("SUSPENDED", "REVOKED"):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Abonnement requis",
        )
    if not rows:
        return {"uid": uid, "svlbh_id": None, "profondeur": False}
    # COMPRENDRE effectif = ST5+ (exempté — Membres du Cercle) OU option payée
    # (ST2-ST4, +59 CHF) OU essai 5 jours en cours (DEC Patrick 2026-07-06).
    profondeur = bool(rows[0].get("digisha_profondeur"))
    stx = str(rows[0].get("stx") or "")
    if not profondeur and stx.upper().startswith("ST"):
        try:
            profondeur = int(stx[2:3]) >= 5
        except ValueError:
            pass
    trial = rows[0].get("digisha_profondeur_trial_until")
    if not profondeur and trial:
        from datetime import datetime, timezone
        try:
            t = datetime.fromisoformat(str(trial).replace("Z", "+00:00"))
            profondeur = t > datetime.now(timezone.utc)
        except Exception:
            pass
    return {"uid": uid, "svlbh_id": rows[0].get("svlbh_id"), "profondeur": profondeur, "stx": stx}


# ── Option « DiGiSha Profondeur » +59 CHF (DEC Patrick 2026-07-06) ────────────
# Inclus (179 CHF) : accompagnement sur sonnet. Profondeur : opus — DiGiSha reste
# TOUJOURS une génération derrière le frontier (DEC Patrick 2026-07-06 : fable-5
# deviendra éligible quand le modèle 6 sortira). Fair-use 500 questions longues/mois,
# au-delà retour doux sur sonnet (jamais de coupure).
ACCOMPAGNEMENT_MODEL_INCLUS = "claude-sonnet-4-6"
ACCOMPAGNEMENT_MODEL_PROFONDEUR = "claude-opus-4-8"

# Passage aux modèles 5.5 (Patrick, 17.10.2026 : « devrions nous modifier le modèle pour passer en Opus 5.5 » → « ok »).
# Prix relus le 17.10 sur la page tarifs d'Anthropic : Opus 5.5 4 / 20 USD le Mtok (Opus 4.8 : 5 / 25), Sonnet 5.5 2 / 10
# (Sonnet 4.6 : 3 / 15), cache relu 0,20 et 0,10. Sur les 5.5 la réflexion est TOUJOURS active, facturée en sortie et prise sur
# max_tokens : effort réglé (Opus « medium », Sonnet « low »), plafond relevé à 8 192, et un essai sur le compte de Patrick
# d'abord (DIGISHA_MODELES_5_5 : liste de svlbh_id, ou « tous ») pour mesurer le coût réel avant les apprenantes.
MODELES_5_5 = {"claude-opus-4-8": "claude-opus-5-5", "claude-sonnet-4-6": "claude-sonnet-5-5"}
EFFORT_5_5 = {"claude-opus-5-5": "medium", "claude-sonnet-5-5": "low"}
ESSAI_5_5_DEFAUT = "52adbc98-d2b0-4444-b89c-b1311a02a983"     # Patrick


def essai_5_5(svlbh: str | None) -> bool:
    cible = os.environ.get("DIGISHA_MODELES_5_5", ESSAI_5_5_DEFAUT).strip().lower()
    if cible in ("tous", "all"):
        return True
    return bool(svlbh) and svlbh.lower() in {x.strip() for x in cible.split(",") if x.strip()}


def passer_en_5_5(payload: dict, svlbh: str | None) -> str:
    """Remplace le modèle 4.x par son 5.5 pour les personnes de l'essai, avec l'effort et le plafond qui vont avec."""
    m = payload.get("model")
    if m in MODELES_5_5 and essai_5_5(svlbh):
        nouveau = MODELES_5_5[m]
        payload["model"] = nouveau
        payload["max_tokens"] = max(int(payload.get("max_tokens") or 0), 8192)
        payload["output_config"] = {"effort": EFFORT_5_5[nouveau]}
    return payload["model"]
PROFONDEUR_FAIR_USE = 500


_usage_mem: dict[tuple[str, str], int] = {}   # (svlbh_id, 'AAAA-MM') → n, secours si la base ne répond pas


async def _compter_accompagnement(svlbh_id: str) -> int:
    """Appels /accompagnement de cette praticienne ce mois-ci, CET APPEL COMPRIS.

    Compté en base (`digisha_usage_incr`, table `digisha_usage_mensuel`) — hors
    journal, donc indépendant du consentement : avant le 09.09.2026 le garde-fou
    Profondeur se comptait dans `digisha_chat_log`, où une praticienne qui a coupé
    le consentement n'écrit rien, et n'était donc jamais ramenée sur sonnet
    (DEC Patrick 09.09). En mémoire du process si la base ne répond pas."""
    mois = datetime.now(timezone.utc).strftime("%Y-%m")
    for k in [k for k in _usage_mem if k[1] != mois]:
        _usage_mem.pop(k, None)
    cle = (svlbh_id, mois)
    _usage_mem[cle] = _usage_mem.get(cle, 0) + 1
    n_mem = _usage_mem[cle]
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        return n_mem
    try:
        r = await _http().post(
            f"{supa_url}/rest/v1/rpc/digisha_usage_incr",
            json={"p_svlbh": svlbh_id, "p_mois": mois},
            headers={"apikey": supa_key, "Authorization": f"Bearer {supa_key}",
                     "Content-Type": "application/json"},
            timeout=10,
        )
        if r.status_code == 200:
            return max(int(r.json()), n_mem)
        log.warning("digisha_usage_incr refusé : HTTP %s %s", r.status_code, r.text[:200])
    except Exception as exc:
        log.warning("digisha_usage_incr impossible : %r", exc)
    return n_mem


def _cache_history(messages: list[dict]) -> list[dict]:
    """Prompt caching sur l'historique : marque le DERNIER message d'un
    breakpoint cache_control → tout le préfixe (system + tours précédents) est
    caché et se prolonge à chaque tour (TTL 5 min). ~2-3x d'économie sur les
    longues conversations."""
    if not messages:
        return messages
    out = [dict(m) for m in messages]
    out[-1]["content"] = marquer_cache(out[-1].get("content"))
    return out


router = APIRouter(prefix="/digisha", tags=["digiSha"])


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    # Le texte, ou des blocs (text / image / document en base64 — digisha_pieces, 17.10.2026) passés tels quels au modèle.
    content: Contenu

    @field_validator("content")
    @classmethod
    def _contenu(cls, v: Contenu) -> Contenu:
        return valider_contenu(v)


def derniere_question(body) -> str:
    """Le texte du dernier tour (les pièces y deviennent « [photo] » / « [document : titre] »)."""
    return texte_de(body.messages[-1].content) if body.messages else ""


def pieces_du_dernier(body) -> int:
    return compter_pieces(body.messages[-1].content) if body.messages else 0


class MemberState(BaseModel):
    orientation: str | None = None
    capsules_vues: list[str] = Field(default_factory=list)
    quiz_reussis: list[str] = Field(default_factory=list)
    capsule_courante: str | None = None


class ChatRequest(BaseModel):
    parcours: Literal["membre", "praticien", "st1", "st2", "st3", "st4", "st3-st4", "st5", "st6-st7"] = "st2"
    etat: MemberState = Field(default_factory=MemberState)
    messages: list[ChatTurn] = Field(min_length=1, max_length=40)
    no_log: bool = False        # opt-out praticienne (DEC Patrick 2026-06-13)
    # Formation « Accompagner un proche » M1 (DEC Patrick 2026-07-07) :
    # mode formation_m1 + fiche du proche → le serveur résout le parcours du
    # proche (RLS via le JWT utilisateur) et n'ouvre QUE ses fenêtres.
    # Formation ST2 « Accompagner la libération de la dette monadique »
    # (DEC Patrick 2026-08-17) : sur soi, sans proche — chaque formation a
    # SON mode, deux libellés ne partagent jamais un contenu.
    # Mode « fil » (DEC Patrick 2026-08-22) : poser une question sur le fil d'une
    # consultante — « qu'est-ce qu'elle a dit sur sa mère ? » — au lieu de chercher
    # des mots-clés. Le serveur choisit les passages, la RLS choisit ce qu'il a le
    # droit de lire, et la réponse cite ses sources.
    mode: Literal["tuteur", "formation_m1", "formation_dette_monadique", "fil"] = "tuteur"
    proche_consultante_id: str | None = None
    fil_consultante_id: str | None = None
    # Le canal du soin choisi dans l'app (DEC Patrick 17.10.2026 : « ajouter sur DiGiSha les z1 à z12 de l'accueil de
    # Chroma 5 ») : « z1 » … « z12 », le sélecteur de canal de l'accueil Chroma 5 porté dans le socle. Honoré dès ST3
    # (canal_choisi) ; une ST2 travaille sur son Âme, en z1, quoi qu'envoie l'écran. Absent = la règle de la base.
    canal: str | None = None
    # Le décodage que la personne poursuit (QR « Poursuivre avec DiGiSha », DEC Patrick 17.10.2026 : « via QR code serait
    # smart » ; « les deux avec le même QR » — l'autrice, l'apprenante, la consultante). Réclamé d'abord par
    # decodage_reprendre(jeton) (migration 2026-10-17j) ; le serveur le relit avec le jeton de la personne (RLS).
    decodage_id: str | None = None


async def log_exchange(source: str, mode: str, user_message: str, reply: str,
                       model: str, prompt_version: str, etat: dict | None = None,
                       svlbh_id: str | None = None,
                       supabase_user_id: str | None = None) -> None:
    """Journal DiGiSha → Supabase digisha_chat_log (best effort, jamais bloquant)."""
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        log.warning("digisha_chat_log non écrit : DIGISHA_SUPABASE_URL/_SERVICE_KEY absents")
        return
    try:
        client = _http()
        r = await client.post(
            f"{supa_url}/rest/v1/digisha_chat_log",
            json={
                "source": source,
                "mode": mode,
                "user_message": user_message,
                "assistant_reply": reply,
                "model": model,
                "etat": etat,
                "prompt_version": prompt_version,
                **({"svlbh_id": svlbh_id} if svlbh_id else {}),
                **({"supabase_user_id": supabase_user_id} if supabase_user_id else {}),
            },
            headers={
                "apikey": supa_key,
                "Authorization": f"Bearer {supa_key}",
                "Prefer": "return=minimal",
            },
            timeout=10,
        )
        if r.status_code >= 300:
            log.warning("digisha_chat_log non écrit : HTTP %s %s", r.status_code, r.text[:200])
    except Exception as exc:  # best effort, jamais bloquant — mais jamais muet
        log.warning("digisha_chat_log non écrit : %r", exc)


async def journaliser_cout(source: str, mode: str, model: str, data: dict,
                           svlbh_id: str | None = None,
                           supabase_user_id: str | None = None) -> None:
    """Coût réel par appel → RPC digisha_journaliser_cout (carte 4abea987, 22.09.2026).

    La donnée existait déjà (data["usage"]) et partait dans un log.info jetable ;
    ici elle devient une ligne durable. Le serveur n'applique AUCUN prix : le tarif
    vit en base (digisha_tarif_modele), le calcul aussi — une seule source pour les
    deux sites d'appel. Le sub du JWT n'est pas un svlbh_id : on le passe tel quel,
    la RPC résout par l'alias canonique. Best effort, jamais bloquant, jamais muet.
    Pas soumis à no_log : ce sont des compteurs, pas du contenu (même règle que
    digisha_usage_incr)."""
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        log.warning("digisha_cout_appel non écrit : DIGISHA_SUPABASE_URL/_SERVICE_KEY absents")
        return
    u = (data or {}).get("usage") or {}
    cache_1h = ((u.get("cache_creation") or {}).get("ephemeral_1h_input_tokens")) or 0
    try:
        r = await _http().post(
            f"{supa_url}/rest/v1/rpc/digisha_journaliser_cout",
            json={
                "p_source": source, "p_mode": mode, "p_model": model,
                "p_input": u.get("input_tokens") or 0,
                "p_cache_w": u.get("cache_creation_input_tokens") or 0,
                "p_cache_w_1h": cache_1h,
                "p_cache_r": u.get("cache_read_input_tokens") or 0,
                "p_output": u.get("output_tokens") or 0,
                "p_svlbh_id": svlbh_id,
                "p_supabase_user_id": supabase_user_id,
            },
            headers={"apikey": supa_key, "Authorization": f"Bearer {supa_key}",
                     "Prefer": "return=minimal"},
            timeout=10,
        )
        if r.status_code >= 300:
            log.warning("digisha_cout_appel non écrit : HTTP %s %s", r.status_code, r.text[:200])
    except Exception as exc:
        log.warning("digisha_cout_appel non écrit : %r", exc)


class ChatResponse(BaseModel):
    reply: str
    model: str


async def fetch_proche_parcours(consultante_id: str, authorization: str | None) -> str:
    """Parcours du proche via sa fiche consultante, RLS appliquée (JWT utilisateur).

    Le lookup passe par PostgREST avec le Bearer de l'utilisateur : si la RLS ne
    lui donne pas cette fiche, elle n'existe pas pour lui (404) — le serveur ne
    révèle jamais un parcours hors périmètre."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Le mode formation requiert une session utilisateur (Bearer JWT)",
        )
    token = authorization.split(" ", 1)[1].strip()
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase non configuré côté DiGiSha",
        )
    client = _http()
    r = await client.get(
        f"{supa_url}/rest/v1/consultante_record",
        params={"consultante_id": f"eq.{consultante_id.lower()}", "select": "parcours,self_praticienne_svlbh_id"},
        headers={"apikey": supa_key, "Authorization": f"Bearer {token}"},
        timeout=10,
    )
    rows = r.json() if r.status_code == 200 else []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fiche du proche introuvable ou non accessible",
        )
    return str(rows[0].get("parcours") or "")


async def fetch_proche_fiche(consultante_id: str, authorization: str | None) -> tuple[str, str | None]:
    """(parcours, self_praticienne_svlbh_id) de la fiche du proche — même lecture que fetch_proche_parcours,
    plus la praticienne dont c'est la fiche « soi » : si c'est l'appelante, le Module 1 se joue SUR ELLE
    (voie « DiGiSha à soi », Patrick 16.10.2026 : « toi c'est DiGiSha ton truc, avec introspection solitaire »)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Le mode formation requiert une session utilisateur (Bearer JWT)",
        )
    token = authorization.split(" ", 1)[1].strip()
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase non configuré côté DiGiSha",
        )
    r = await _http().get(
        f"{supa_url}/rest/v1/consultante_record",
        params={"consultante_id": f"eq.{consultante_id.lower()}", "select": "parcours,self_praticienne_svlbh_id"},
        headers={"apikey": supa_key, "Authorization": f"Bearer {token}"},
        timeout=10,
    )
    rows = r.json() if r.status_code == 200 else []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fiche du proche introuvable ou non accessible",
        )
    soi = rows[0].get("self_praticienne_svlbh_id")
    return str(rows[0].get("parcours") or ""), (str(soi).lower() if soi else None)


async def digisha_a_soi_actif(authorization: str | None) -> bool:
    """L'appelante a-t-elle une fenêtre « DiGiSha à soi » ouverte (découverte 5 jours, mois, trimestre) ? Porte
    digisha_a_soi_actif() de la base (migration 2026-10-16f), lue avec SON jeton. Toute panne = non."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return False
    token = authorization.split(" ", 1)[1].strip()
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not token or not supa_url or not supa_key:
        return False
    try:
        r = await _http().post(
            f"{supa_url}/rest/v1/rpc/digisha_a_soi_actif",
            json={},
            headers={"apikey": supa_key, "Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            timeout=10,
        )
        return r.status_code == 200 and r.json() is True
    except Exception:
        return False


def refuser_st1(ident: dict | None) -> None:
    """ST1 n'a pas DiGiSha — Patrick, 17.10.2026 : « ST1 est exclu personne n'aurait accès à DigiSha comme ST1 ».
    Le stade lu est celui du profil (gate_subscription) ; sans profil (jeton d'app, anon) on ne tranche pas ici."""
    if ident and str(ident.get("stx") or "").upper() == "ST1":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="DiGiSha s'ouvre à partir de ST2 — ton programme n'y est pas encore.")


async def _rpc_personne(authorization: str | None, nom: str, corps: dict, timeout: int = 10):
    """Un appel RPC PostgREST avec le jeton de la PERSONNE (RLS et droits = les siens). None sur toute panne."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not token or not supa_url or not supa_key:
        return None
    try:
        r = await _http().post(
            f"{supa_url}/rest/v1/rpc/{nom}", json=corps,
            headers={"apikey": supa_key, "Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=timeout,
        )
        if r.status_code != 200:
            log.warning("digisha — rpc %s HTTP %s : %s", nom, r.status_code, r.text[:200])
            return None
        return r.json()
    except Exception as exc:
        log.warning("digisha — rpc %s en erreur : %r", nom, exc)
        return None


def canal_choisi(choisi: str | None, stx: str | None) -> str | None:
    """Le canal que l'écran a choisi (sélecteur z1 → z12 de l'accueil Chroma 5, DEC Patrick 17.10.2026), s'il est
    recevable : la forme « zN », et un stade qui a des tiers à accompagner (ST3 et plus). Une ST2 travaille sur son
    Âme : son canal est z1, la règle de la base le dit, l'écran n'a pas voix au chapitre. Pur, sans réseau."""
    c = (choisi or "").strip().lower()
    if not re.fullmatch(r"z[1-9]\d?", c):
        return None
    s = str(stx or "").upper()
    if not (s.startswith("ST") and s[2:3].isdigit() and int(s[2:3]) >= 3):
        return None
    return c


async def canal_digisha(authorization: str | None, moi: str | None, sur_soi: bool,
                        choisi: str | None = None, stx: str | None = None) -> str:
    """Le canal où la conversation a lieu — d'abord celui que l'écran a choisi, s'il est recevable (canal_choisi,
    17.10.2026) ; sinon lu en base (digisha_canal, migration 2026-10-16j) : le canal posé par Patrick pour la
    praticienne (Anne z2, Giulia z3, Cornelia z4, Patrick z12 — « pour moi z5, z6, z8 et z9 qui vont dans mon user …
    dans le canal z12 », 16.10.2026), sinon z1 sur soi (« tu discutes avec ton âme »), sinon le canal de la
    praticienne, sinon z2. Panne = le même calcul ici, sans la table."""
    voulu = canal_choisi(choisi, stx)
    if voulu:
        return voulu
    canal = await _rpc_personne(authorization, "digisha_canal", {"p_svlbh": moi, "p_sur_soi": sur_soi}) if moi else None
    if isinstance(canal, str) and re.fullmatch(r"z\d+", canal):
        return canal
    return "z1" if sur_soi else "z2"


DECODAGE_MAX_CAR = 12_000


async def fetch_decodage(authorization: str | None, decodage_id: str | None) -> dict | None:
    """Le décodage poursuivi, lu avec le jeton de la PERSONNE (policy dec_v0_read_own_or_shared : le sien ou partagé avec
    elle). None si absent, mal formé, refusé ou en panne — DiGiSha répond alors sans lui."""
    did = (decodage_id or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", did):
        return None
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not token or not supa_url or not supa_key:
        return None
    try:
        r = await _http().get(
            f"{supa_url}/rest/v1/decodages_v0",
            params={"id": f"eq.{did}", "select": "id,menu,provenance,consultante_label,is_self_care,created_at,payload"},
            headers={"apikey": supa_key, "Authorization": f"Bearer {token}"},
            timeout=10,
        )
        rows = r.json() if r.status_code == 200 else None
        return rows[0] if rows else None
    except Exception as exc:
        log.warning("digisha — décodage %s illisible : %r", did[:8], exc)
        return None


def bloc_decodage(d: dict | None) -> str:
    """Le décodage, tel qu'enregistré, en tête de l'échange."""
    if not d:
        return ""
    quand = str(d.get("created_at") or "")[:10]
    try:
        quand = datetime.fromisoformat(quand).strftime("%d.%m.%Y")
    except ValueError:
        pass
    pour = "auto-soin" if d.get("is_self_care") else (d.get("consultante_label") or "")
    contenu = json.dumps(d.get("payload") or {}, ensure_ascii=False)
    if len(contenu) > DECODAGE_MAX_CAR:
        contenu = contenu[:DECODAGE_MAX_CAR] + " …(tronqué)"
    return ("## Le soin décodé que la personne poursuit\n"
            f"« {d.get('menu') or 'Décodage'} » du {quand}" + (f" — {pour}" if pour else "")
            + (f" (outil : {d.get('provenance')})" if d.get("provenance") else "") + ".\n"
            "Elle vient de scanner le QR de ce décodage pour le poursuivre avec toi. Pars de ce qu'il contient : nomme où il en "
            "est, ne lui redemande pas ce qui y est déjà mesuré. Le contenu, tel qu'enregistré :\n\n" + contenu)


def ajouter_au_systeme(payload: dict, texte: str) -> None:
    if not texte:
        return
    systeme = payload.get("system")
    blocs = [{"type": "text", "text": systeme}] if isinstance(systeme, str) else list(systeme or [])
    payload["system"] = blocs + [{"type": "text", "text": texte}]


FIL_REPRISE_CADRE = (
    "## Ton fil DiGiSha — ce qui s'est déjà dit (reprise)\n"
    "Ce sont les derniers tours déposés dans le fil pour cette personne et ce canal. Si la conversation "
    "reprend, pars de là : ne redemande pas ce qui est déjà posé, nomme où on s'était arrêtées.\n\n"
)


async def fil_digisha_reprise(authorization: str | None, consultante_id: str | None, canal: str | None) -> str:
    """Les dernières sections DiGiSha de cette fiche et de ce canal, pour reprendre là où on s'était arrêtées
    (migration 2026-10-16g, digisha_fil_reprendre ; les droits sont ceux du fil). Sans fiche (None) : la fiche
    « soi » de la personne, comme pour le dépôt (migration 2026-10-17g). Vide si rien ou refusé."""
    rows = await _rpc_personne(authorization, "digisha_fil_reprendre",
                               {"p_consultante": consultante_id or None, "p_canal": canal, "p_max_car": 12000})
    if not rows:
        return ""
    return "\n\n".join(f"**{r.get('titre')}** ({r.get('jour')})\n{r.get('corps')}" for r in rows)


CONTEXTE_CADRE = (
    "## Ce que tu sais d'elle — tout ce qui a été décodé et discuté pour elle\n"
    "Les décodages posés sur sa fiche, ses dernières discussions, ses séances DiGiSha. C'est ta base : ce qui y est posé fait "
    "foi, tu le cites tel quel au lieu de le paraphraser, tu ne redemandes pas ce qui y est déjà mesuré, tu relies ce qu'elle "
    "apporte à ce qui y est décodé. Ce qui n'y est pas et qu'elle n'a pas mesuré, tu ne l'inventes pas.\n\n"
)


async def contexte_personne(authorization: str | None, consultante_id: str | None, canal: str | None) -> str:
    """Ce que DiGiSha sait de la personne (migration 2026-10-19b, digisha_contexte ; carte c4b0a17e) : ses jours de fil, ses
    séances DiGiSha et les décodages posés sur sa fiche par une autre personne, les relances de DiGiSha retirées
    (routers/digisha_contexte.py). Tant que la fonction manque en base : l'ancienne reprise du canal, relances retirées."""
    rows = await _rpc_personne(authorization, "digisha_contexte", {"p_consultante": consultante_id or None}, timeout=15)
    if isinstance(rows, list):
        return mettre_en_forme(rows)
    return sans_relances(await fil_digisha_reprise(authorization, consultante_id, canal))


async def fil_digisha_deposer(authorization: str | None, consultante_id: str | None, canal: str,
                              question: str, reponse: str, mode: str, pour_elle: bool = False) -> str | None:
    """Dépose le tour dans le fil (migration 2026-10-16g, digisha_fil_deposer) : la conversation survit, tour après
    tour, dans la séance DiGiSha du jour et du canal. Jamais bloquant."""
    if consultante_id and mode != "formation_m1" and not pour_elle:
        # « À propos de » une autre fiche (accompagnement, mode « fil ») : c'est une RELECTURE — elle se dépose chez celle qui
        # relit, jamais dans le fil de la personne relue (migration 2026-10-17k ; sur sa propre fiche, le dépôt d'avant).
        r = await _rpc_personne(authorization, "digisha_relecture_deposer",
                                {"p_sujet": consultante_id, "p_canal": canal, "p_question": question,
                                 "p_reponse": reponse, "p_mode": mode}, timeout=15)
        return r if isinstance(r, str) else None
    r = await _rpc_personne(authorization, "digisha_fil_deposer",
                            {"p_consultante": consultante_id or None, "p_canal": canal, "p_question": question,
                             "p_reponse": reponse, "p_mode": mode}, timeout=15)
    return r if isinstance(r, str) else None


PIECES_SEAU = "digisha-pieces"
PIECES_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif", "image/webp": "webp", "application/pdf": "pdf"}


async def ranger_pieces(session_id: str | None, contenu) -> int:
    """Les photos et PDF du tour, gardés (fiche c51ff989, migration 2026-10-17q) : chaque pièce part dans le seau privé
    « digisha-pieces » sous <séance>/<uuid>.<ext> (lisible par qui lit la séance), puis sa référence s'ajoute à la page du jour
    (payload.digisha.pieces). Patrick, 17.10 : « j'ai joint des images depuis android que je ne vois pas sur mac ». Jamais bloquant."""
    if not session_id or not isinstance(contenu, list):
        return 0
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        return 0
    heure = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%Hh%M")
    gardees = []
    for b in contenu:
        b = b.model_dump() if hasattr(b, "model_dump") else b
        if not isinstance(b, dict) or b.get("type") not in ("image", "document"):
            continue
        src = b.get("source") or {}
        mt = src.get("media_type")
        if mt not in PIECES_EXT or not src.get("data"):
            continue
        chemin = f"{session_id}/{uuid.uuid4()}.{PIECES_EXT[mt]}"
        try:
            r = await _http().post(f"{supa_url}/storage/v1/object/{PIECES_SEAU}/{chemin}", content=base64.b64decode(src["data"]),
                                   headers={"apikey": supa_key, "Authorization": f"Bearer {supa_key}", "Content-Type": mt},
                                   timeout=30)
            if r.status_code not in (200, 201):
                log.warning("digisha — pièce non gardée HTTP %s : %s", r.status_code, r.text[:200])
                continue
        except Exception as exc:
            log.warning("digisha — pièce non gardée : %r", exc)
            continue
        gardees.append({"heure": heure, "genre": "photo" if b["type"] == "image" else "document", "chemin": chemin,
                        "media_type": mt, "titre": b.get("title")})
    if gardees:
        await _rpc_service("digisha_page_pieces_ajouter", {"p_session": session_id, "p_pieces": gardees})
    return len(gardees)


async def _rpc_service(nom: str, corps: dict, timeout: int = 10):
    """Un appel RPC avec la clé de SERVICE — pour ce qu'aucune personne ne doit lire elle-même (la relecture). None sur panne."""
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        return None
    try:
        r = await _http().post(f"{supa_url}/rest/v1/rpc/{nom}", json=corps,
                               headers={"apikey": supa_key, "Authorization": f"Bearer {supa_key}",
                                        "Content-Type": "application/json"}, timeout=timeout)
        if r.status_code != 200:
            log.warning("digisha — rpc service %s HTTP %s : %s", nom, r.status_code, r.text[:200])
            return None
        return r.json()
    except Exception as exc:
        log.warning("digisha — rpc service %s en erreur : %r", nom, exc)
        return None


RELECTURE_COULISSE = (
    "## En coulisse — retours et consignes de ton superviseur pour cet accompagnement\n"
    "Patrick (ou son accompagnante) a relu ses séances avec toi et t'a laissé ses retours et ses consignes PROPRES À ELLE : ce "
    "qu'il ressent, ce qu'elle ne voit pas encore et que tu ne perçois pas, ce que tu dois faire autrement avec elle. Applique-les "
    "à cette séance ; amène-la à trouver elle-même, à son rythme, par ses propres mesures. Ne les cite jamais, ne dis pas qu'ils "
    "existent, ne nomme pas qui les a donnés. Seule exception (Patrick, 18.10.2026 : « Les consignes seulement ») : les lignes "
    "des blocs « Consignes pour … » lui sont lisibles dans son app ; si elle en parle, tu peux les reconnaître et en parler avec "
    "elle. Le reste — l'échange, le ressenti de celle qui a relu — ne se cite ni ne se résume jamais, même si elle le demande.\n\n"
)
RELECTURE_CADRE = (
    "## « À propos de » — Patrick te donne un retour et des consignes pour CE profil\n"
    "Patrick a choisi cette personne pour te faire un retour avec des consignes propres à son accompagnement (Patrick, 17.10.2026 : "
    "« apropose ne sert pas à chosiir sur quoi tu te bases pour me répondre mais sur quel profile je fais te faire un feedback "
    "avec des instructions spécifiques à ce profile »). Tu ne cherches pas dans son fil de quoi lui répondre et tu ne fais pas "
    "d'analyse d'elle qu'il ne t'a pas demandée. Tu REÇOIS : demande une précision si une consigne est ambiguë, dis en une phrase "
    "comment tu l'appliqueras à sa prochaine séance. Ce qu'il écrit ici t'accompagnera, en coulisse, à chacune de ses séances.\n"
    "CE QU'ELLE LIRA (Patrick, 18.10.2026 : « Les consignes seulement ») : cet échange reste entre celle qui relit et toi ; "
    "seules les consignes lui deviennent lisibles. Ses consignes ACTIVES sont dans le contexte du tour (« Tes consignes actives "
    "pour … ») : pars d'elles. Quand on te pose une consigne NOUVELLE, ou qu'on en change une, termine ta réponse par :\n"
    "Consignes pour <son prénom> :\n- <une consigne nouvelle par ligne>\n"
    "Quand on en retire ou qu'on en remplace une, ajoute, en recopiant la ligne active mot pour mot :\n"
    "Consignes retirées pour <son prénom> :\n- <la consigne retirée>\n"
    "Écris chaque consigne nouvelle pour qu'ELLE puisse la recevoir : ce que tu feras autrement avec elle, sans jugement sur "
    "elle ni détail de cet échange. Ne recopie pas les consignes actives qui ne changent pas. Aucun bloc si rien ne change.\n\n"
)


def _plat(t: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t or "") if unicodedata.category(c) != "Mn").casefold().strip()


_TETE = re.compile(r"^[#>*_\s]*consignes?\s+(retir[ée]es?\s+)?pour\s+(.+?)\s*:?[*_\s]*:?\s*$", re.I)
_PUCE = re.compile(r"^\s*(?:[-•*–—‑]|\d+[.)])\s+(.+?)\s*$")


def decoder_pour_elle(body) -> bool:
    """« À propos de X » en mode décodage POUR elle (et non relecture réservée), 18.10.2026."""
    return bool(getattr(body, "fil_consultante_id", None)) and (getattr(body, "a_propos", None) or "").strip().lower() in ("decodage", "décodage")


def consignes_du_texte(texte: str, prenom: str | None = None) -> tuple[list[str], list[str]]:
    """(nouvelles, retirées) des blocs « Consignes pour <prénom> : » et « Consignes retirées pour <prénom> : » d'une réponse
    « à propos de » (2026-10-18f). Un bloc adressé à un autre prénom est ignoré ; deux blocs de même sorte = rien (ambigu)."""
    blocs: dict[str, list[list[str]]] = {"nouvelles": [], "retirees": []}
    courant = None
    for l in (texte or "").replace("\r\n", "\n").split("\n"):
        m = _TETE.match(l)
        if m:
            nom = _plat(re.sub(r"[*_]", "", m.group(2)))
            courant = None
            if prenom and nom.split()[0:1] == _plat(prenom).split()[0:1]:
                courant = blocs["retirees" if m.group(1) else "nouvelles"]
                courant.append([])
            continue
        if courant is None:
            continue
        p = _PUCE.match(l)
        if p:
            courant[-1].append(p.group(1))
        elif l.strip() and l[:1] in (" ", "\t") and courant[-1]:
            courant[-1][-1] += " " + l.strip()               # suite d'une ligne coupée
        elif l.strip():
            courant = None
    def propres(listes):
        if len(listes) != 1:
            return []
        out = []
        for t in listes[0]:
            t = re.sub(r"(\*\*|__|\*|_)", "", t).strip()
            if len(t) >= 3 and not t.endswith("?"):
                out.append(t[:600])
        return out[:12]
    return propres(blocs["nouvelles"]), propres(blocs["retirees"])
RELECTURE_PRECEDENTES = (
    "## Tes relectures précédentes de cette personne\n"
    "Ce que tu as déjà posé en relisant ses décodages ; pars de là, ne le redemande pas.\n\n"
)
RELECTURE_SEANCES = (
    "## Ses séances DiGiSha — ce qu'elle a décodé (la relecture porte sur ces tours)\n"
    "Les derniers tours de ses séances, tous canaux. Celle qui te parle les relit pour y poser ce qu'elle ressent : "
    "aide-la à situer chaque ressenti dans ce qui a été décodé (date, heure, mesure).\n\n"
)


DECODAGE_POUR_CADRE = (
    "## « À propos de » — un décodage POUR elle\n"
    "Celle qui te parle (sa praticienne, ou Patrick) décode POUR cette personne : c'est ELLE le sujet, la fiche est la sienne. "
    "Accompagne ce décodage comme une séance — mesures, lignées, canal — en t'appuyant sur ses séances ci-dessous. Ce qui "
    "s'écrit ici va dans SES pages DiGiSha et elle le lira : écris pour qu'elle puisse le recevoir, sans jugement sur elle et "
    "sans rien de ce que la praticienne garde pour elle (ce qui est réservé passe par une relecture, pas ici).\n\n"
)
SES_SEANCES_CADRE = (
    "## Ses séances DiGiSha — ce qui a déjà été décodé pour elle\n"
    "Les derniers tours de ses pages, tous canaux : pars de là, ne redemande pas ce qui est déjà posé.\n\n"
)


SAVOIR_CADRE = (
    "## Savoir du Cercle — décodages déjà posés ailleurs, sans les noms\n"
    "Des décodages radiesthésiques réellement posés dans le Cercle (fils et séances), gardés tels quels, sans les noms. "
    "Sers-t'en comme d'un savoir : relations déjà vues, mesures, enchaînements, explications. Ce n'est PAS l'histoire de la "
    "personne qui te parle : ne le lui attribue jamais, ne dis pas d'où ça vient, ne cite pas ces fiches comme des cas.\n\n"
)


async def savoir_pour(question: str, exclure_fiche: str | None = None, exclure_svlbh: str | None = None) -> str:
    """Les fiches de savoir proches de la question (migration 2026-10-17n), jamais celles de la personne elle-même ; clé de service."""
    if not (question or "").strip():
        return ""
    r = await _rpc_service("digisha_savoir_chercher", {"p_question": question[:2000], "p_exclure": exclure_fiche or None,
                                                       "p_exclure_svlbh": exclure_svlbh or None, "p_limite": 6, "p_max_car": 6000})
    return r if isinstance(r, str) else ""


async def relecture_pour(sujet: str | None = None, svlbh: str | None = None, auteur: str | None = None) -> str:
    """Les relectures récentes d'une personne (fiche, ou personne par sa fiche « soi »), lues par la clé de service."""
    if not sujet and not svlbh:
        return ""
    corps = {"p_sujet": sujet or None, "p_svlbh": svlbh or None, "p_max_car": 8000}
    if auteur:
        corps["p_auteur"] = auteur                           # 18f : une relectrice ne relit que SES relectures
    r = await _rpc_service("digisha_relecture_pour", corps)
    return r if isinstance(r, str) else ""


async def peut_relire(authorization: str | None, sujet: str | None) -> bool:
    """« À propos de X » : l'appelante peut-elle relire X ? Même porte que le dépôt (digisha_relecture_deposer) —
    propriétaire, ou X dans fils_lisibles() — lue avec SON jeton, parce que relecture_pour lit par la clé de service.
    Toute panne = non (fiche 62afe053, audit de sécurité du 17.10.2026)."""
    if not sujet:
        return False
    if await _rpc_personne(authorization, "is_owner_st6", {}) is True:
        return True
    r = await _rpc_personne(authorization, "fils_lisibles", {})
    if not isinstance(r, list):
        return False
    ids = {str(x if not isinstance(x, dict) else next(iter(x.values()), "")).lower() for x in r}
    return str(sujet).lower() in ids


async def est_abonnee_myshamanfamily(authorization: str | None) -> bool:
    """L'appelant est-il abonnée MyShamanFamily PRO ? Même porte que les programmes myShaman
    (programmes_myshaman_accessibles : profil ACTIVE, Anne ou formation MyShamanFamily PRO active,
    propriétaire) — lue en base avec SON jeton, jamais recopiée ici. Toute panne = non : on ne
    rouvre rien sur une erreur."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return False
    token = authorization.split(" ", 1)[1].strip()
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not token or not supa_url or not supa_key:
        return False
    try:
        r = await _http().post(
            f"{supa_url}/rest/v1/rpc/programmes_myshaman_accessibles",
            json={},
            headers={"apikey": supa_key, "Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            timeout=10,
        )
        return r.status_code == 200 and bool(r.json())
    except Exception:
        return False


async def fetch_passages_du_fil(
    consultante_id: str, question: str, authorization: str | None, limite: int = 12
) -> list[dict]:
    """Passages du fil les plus proches de la question, RLS appliquée (JWT utilisateur).

    La sélection se fait EN BASE (`chercher_dans_le_fil`, recherche française) et non
    ici : c'est la seule façon de n'envoyer au modèle que ce que l'appelant a le droit
    de lire, et de ne pas charger 200 000 caractères à chaque question. Liste vide =
    rien d'accessible ou rien de pertinent — dans les deux cas on ne bluffe pas."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Le mode fil requiert une session utilisateur (Bearer JWT)",
        )
    token = authorization.split(" ", 1)[1].strip()
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase non configuré côté DiGiSha",
        )
    client = _http()
    r = await client.post(
        f"{supa_url}/rest/v1/rpc/chercher_dans_le_fil",
        json={"p_consultante": consultante_id.lower(),
              "p_question": question,
              "p_limite": limite},
        headers={"apikey": supa_key, "Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        timeout=15,
    )
    if r.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce fil n'est pas accessible avec cette session",
        )
    return r.json() or []


async def fetch_passages_semantiques(
    consultante_id: str, question: str, authorization: str | None, limite: int = 40
) -> list[dict] | None:
    """Passages les plus proches EN SENS de la question (carte b8d68119), même RLS que la voie lexicale.

    None = la voie sémantique n'a pas pu servir (modèle absent, RPC en erreur) : l'appelant garde le
    lexical seul. Une liste vide, elle, veut dire « rien de proche » — ce n'est pas la même chose."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    vecteur = await digisha_semantique.vecteur_question(question)
    if vecteur is None:
        return None
    token = authorization.split(" ", 1)[1].strip()
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        return None
    try:
        r = await _http().post(
            f"{supa_url}/rest/v1/rpc/chercher_dans_le_fil_semantique",
            json={"p_consultante": consultante_id.lower(), "p_vecteur": vecteur, "p_limite": limite},
            headers={"apikey": supa_key, "Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            timeout=15,
        )
    except Exception as exc:
        log.warning("digisha — recherche sémantique en erreur, lexicale seule : %r", exc)
        return None
    if r.status_code != 200:
        log.warning("digisha — recherche sémantique HTTP %s, lexicale seule : %s", r.status_code, r.text[:200])
        return None
    return r.json() or []


FUSION_TETE = 10   # les plus pertinents d'abord ; la couverture des mois vient juste après


def fusionner_passages(lexicaux: list[dict], semantiques: list[dict] | None) -> list[dict]:
    """Fusion lexicale + sémantique : ENTRELACÉE, dédoublonnée, puis tous les mois.

    1. À chaque rang, le passage sémantique puis le lexical (clé commune : la séance et l'empreinte du corps,
       la voie lexicale ne rendant ni attachment_id ni ordre). Un doublon garde sa première apparition.
    2. Les FUSION_TETE premiers restent en tête ; ensuite, le meilleur passage de chaque mois encore absent
       (demande d'Anne du 16.09 : douze passages d'août-septembre masquaient avril) ; puis le reste.

    Choisi sur MESURE le 24.09 (fil d'Anne, 147 sections, six questions sans aucun mot du titre visé) :
    entrelacer fait entrer la bonne section dans le contexte réel (plafond FIL_CONTEXTE_MAX_CAR) 5 fois sur 6,
    dont 2 au rang 1 ; le rang réciproque (RRF, k=60) 3 fois sur 6 — le bruit lexical d'une question sans les
    mots du fil y noyait le premier résultat sémantique. « Tous les mois d'abord » repoussait lui aussi le
    meilleur passage. La question « David » couvre 6 mois dans les deux cas (3 avant ce lot).
    Sans voie sémantique (None ou []), l'ordre lexical est gardé, couverture des mois comprise."""
    vus: set[tuple] = set()
    ordre: list[dict] = []
    sem, lex = semantiques or [], lexicaux or []
    for i in range(max(len(sem), len(lex))):
        for liste in (sem, lex):
            if i < len(liste):
                p = liste[i]
                cle = (p.get("session_id"), hashlib.md5((p.get("corps") or "").encode()).hexdigest())
                if cle not in vus:
                    vus.add(cle)
                    ordre.append(p)
    tete = ordre[:FUSION_TETE]
    mois_vus = {str(p.get("jour") or "")[:7] for p in tete}
    couverture = []
    for p in ordre[FUSION_TETE:]:
        mois = str(p.get("jour") or "")[:7]
        if mois not in mois_vus:
            mois_vus.add(mois)
            couverture.append(p)
    pris = {id(p) for p in couverture}
    return tete + couverture + [p for p in ordre[FUSION_TETE:] if id(p) not in pris]


async def passages_du_fil(consultante_id: str, question: str, authorization: str | None
                          ) -> tuple[list[dict], str]:
    """Les deux voies en parallèle, fusionnées. Rend (passages, mesure pour la ligne d'usage)."""
    lexicaux, semantiques = await asyncio.gather(
        fetch_passages_du_fil(consultante_id, question, authorization, limite=40),
        fetch_passages_semantiques(consultante_id, question, authorization, limite=40),
    )
    passages = fusionner_passages(lexicaux, semantiques)
    mesure = f" fil_lex={len(lexicaux)} fil_sem={'∅' if semantiques is None else len(semantiques)}"
    return passages, mesure


FIL_SECTION_ENTIERE_MAX = 3_000    # au-delà, on sert l'extrait ts_headline de la base
FIL_CONTEXTE_MAX_CAR = 40_000       # ≈ 10k tokens par question


def build_fil_context(passages: list[dict]) -> str:
    """Le contexte lu par DiGiSha : chaque passage porte SA date et SON titre, pour
    que la réponse puisse être vérifiée à la source plutôt que crue sur parole.

    Mesuré le 09.09.2026 : 12 sections entières du fil d'Anne = ~139 000 tokens
    écrits en cache par question (0,52 USD), jamais relus puisque chaque question
    choisit d'autres sections — c'était le coût du 7.9. Une section courte passe
    entière ; une longue passe par son extrait centré sur les mots de la question
    (`chercher_dans_le_fil.extrait`) ; le tout est plafonné."""
    if not passages:
        return "AUCUN PASSAGE TROUVÉ dans le fil pour cette question."
    morceaux, total = [], 0
    for p in passages:
        corps = p.get("corps") or ""
        extrait = (p.get("extrait") or "").strip()
        en_extrait = len(corps) > FIL_SECTION_ENTIERE_MAX and bool(extrait)
        texte = extrait if en_extrait else corps
        reste = FIL_CONTEXTE_MAX_CAR - total
        if reste <= 0:
            break
        if len(texte) > reste:
            texte = texte[:reste] + " […]"
        morceaux.append(
            f"### {p.get('jour','?')} — {p.get('titre') or 'sans titre'}"
            f"{' (extrait)' if en_extrait else ''}\n{texte}"
        )
        total += len(texte)
    return "\n\n".join(morceaux)


FIL_CADRE = """## Ce que tu fais ici

Tu réponds à une question sur le fil d'échanges d'UNE personne accompagnée. Les
passages ci-dessous sont les seuls que tu as le droit de lire, et ils sont datés.

Règles, sans exception :
- Tu réponds UNIQUEMENT à partir de ces passages. Ce qui n'y est pas, tu ne le sais pas.
- Tu CITES tes sources en fin de réponse, sous la forme « 12.07 — Les lignes du temps ».
  Sans citation, la réponse ne vaut rien : elle doit pouvoir être vérifiée.
- Si les passages ne répondent pas, tu le dis franchement et tu proposes une autre
  formulation de la question. Tu n'inventes jamais un souvenir manquant.
- Tu parles de la personne accompagnée à la troisième personne, sobrement. C'est un
  outil de travail pour sa praticienne, pas un récit."""

def build_system(base: str, parcours: str, etat: MemberState) -> list[dict]:
    """Blocs système : préfixe STATIQUE (prompt Supabase + corpus slim + FCB)
    marqué cache_control → prompt caching Anthropic (partagé entre membres du
    même modèle, TTL 5 min, lecture -90 %). Le bloc DYNAMIQUE (état + capsule
    courante complète) reste hors cache."""
    etat_dyn = {
        "parcours": parcours,
        "orientation": etat.orientation,
        "capsules_vues": etat.capsules_vues,
        "quiz_reussis": etat.quiz_reussis,
        "capsule_courante": etat.capsule_courante,
    }
    full = _full_item(etat.capsule_courante)
    if full is not None:
        etat_dyn["capsule_courante_contenu_complet"] = full
    return [
        {"type": "text", "text": base},
        {"type": "text",
         "text": "## Corpus — Formation « Les 26 ponts » (JSON)\n" + STATIC_CORPUS_JSON},
        partage({"type": "text",
                 "text": "## Répertoire maïeutique — Questions digiSha de Libération (FCB Chapitre 11)\n"
                         + json.dumps(FCB_CH11, ensure_ascii=False)}),
        du_tour("## État du membre\n" + json.dumps(etat_dyn, ensure_ascii=False)),
    ]


@router.post("/chat", response_model=ChatResponse)
async def digisha_chat(
    request: Request,
    body: ChatRequest,
    x_digisha_token: str | None = Header(None, alias="X-DigiSha-Token"),
    authorization: str | None = Header(None),
) -> ChatResponse:
    caller_uid = await authorize_caller(request, x_digisha_token, authorization)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ANTHROPIC_API_KEY not configured — le tuteur digiSha n'est pas encore activé",
        )
    model = model_for(body.parcours)
    prompt = await fetch_prompt()
    if prompt:
        base = prompt["core"] + "\n\n" + (prompt.get("tuteur_frame") or "")
        version = prompt["version"]
    else:
        base = TUTEUR_FALLBACK
        version = FALLBACK_VERSION

    if body.mode == "formation_dette_monadique":
        # Formation ST2 (DEC Patrick 2026-08-17). Le MODULE n'est pas encore
        # écrit — la source (svlbh-digisha/parcours-st2/conception-st2-v0.2.0.md,
        # découverte 3 « Dettes karmiques des Sur-Âmes et Monades ») attend son
        # passage en module verbatim, comme M1 l'a fait depuis sa base source.
        # Tant qu'il n'existe pas : refus CLAIR — jamais un contenu improvisé,
        # et surtout pas le M1 servi sous un autre nom.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La formation « Accompagner la libération de la dette "
                   "monadique » est en préparation — elle s'ouvre très bientôt. 🌙",
        )
    # Historique : au-delà de 20 messages, les tours anciens sont résumés par
    # blocs (cache) et seuls les derniers restent bruts — voir digisha_memoire.
    raw_messages = [t.model_dump(exclude_none=True) for t in body.messages]
    resume_block, recents, n_blocs = await preparer_historique(_http(), api_key, raw_messages)
    resume_blocks = [resume_block] if resume_block else []
    usage_extra = ""
    # Expérience de Patrick (16.10.2026 22h4x) : « toute utilisation de DiGiSha répond dès maintenant dans le canal qui
    # correspond au soin ». Chaque tour, quel que soit le mode, se dépose dans le fil : la fiche visée (proche, fil) ou,
    # sans fiche, la sienne ; le canal est celui de la praticienne (digisha_canal). Jamais bloquant.
    ident = await gate_subscription(authorization)
    refuser_st1(ident)
    moi = str((ident or {}).get("svlbh_id") or "").lower() or None
    depot_fil: tuple[str | None, str] | None = None   # (fiche ou None = la sienne, canal)
    if body.mode == "fil":
        # Question sur le fil d'une consultante (DEC Patrick 22.08.2026).
        if not body.fil_consultante_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="fil_consultante_id requis en mode fil",
            )
        question = derniere_question(body)
        passages, mesure_fil = await passages_du_fil(body.fil_consultante_id, question, authorization)
        contexte_fil = build_fil_context(passages)
        usage_extra = f" fil_sections={len(passages)} fil_car={len(contexte_fil)}{mesure_fil}"
        system_blocks = [
            {"type": "text", "text": base},
            partage({"type": "text", "text": FIL_CADRE}),
            du_tour("## Passages du fil\n\n" + contexte_fil),
        ] + resume_blocks
        payload = {
            "model": model,
            "max_tokens": 2048,
            "system": system_blocks,
            "messages": _cache_history(recents),
        }
    elif body.mode == "formation_m1":
        # Formation « Accompagner un proche » M1 : gating serveur des fenêtres
        # sur le parcours du proche (fiche liée, RLS via JWT utilisateur).
        if not body.proche_consultante_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="proche_consultante_id requis en mode formation_m1",
            )
        parcours_proche, proche_soi = await fetch_proche_fiche(body.proche_consultante_id, authorization)
        sur_soi = bool(moi and proche_soi and moi == proche_soi)
        m1_block = m1_system_block(parcours_proche, sur_soi=sur_soi)
        a_soi = False
        if m1_block is None:
            a_soi = await digisha_a_soi_actif(authorization)
            if a_soi and not sur_soi:
                # La découverte s'ouvre sur SA fiche : pas sur celle d'une autre.
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="DiGiSha à soi s'ouvre sur ta propre fiche — choisis-toi comme proche.",
                )
            if a_soi or await est_abonnee_myshamanfamily(authorization):
                m1_block = m1_system_block(parcours_proche, ouvert_par_abonnement=True, sur_soi=sur_soi)
        if a_soi:
            usage_extra += " a_soi=1"
        if sur_soi:
            usage_extra += " sur_soi=1"
        canal_fil = await canal_digisha(authorization, moi, sur_soi, choisi=body.canal, stx=(ident or {}).get("stx"))
        reprise = await contexte_personne(authorization, body.proche_consultante_id, canal_fil)
        usage_extra += f" canal={canal_fil} reprise_car={len(reprise)}"
        coulisse = await relecture_pour(sujet=body.proche_consultante_id) if sur_soi else ""
        savoir = await savoir_pour(derniere_question(body), exclure_fiche=body.proche_consultante_id)
        if savoir:
            usage_extra += f" savoir_car={len(savoir)}"
        if coulisse:
            usage_extra += f" relecture_car={len(coulisse)}"
            await _rpc_service("digisha_relecture_servie", {"p_sujet": body.proche_consultante_id})
        if m1_block is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Le Module 1 ne s'ouvre pas encore pour ce parcours ({parcours_proche or 'inconnu'}) — il s'ouvre en ST2",
            )
        system_blocks = [
            {"type": "text", "text": base},
            partage({"type": "text", "text": m1_block}),
            du_tour("## État du membre\n" + json.dumps(
                 {"parcours_accompagnante": body.parcours,
                  "parcours_proche": parcours_proche,
                  "sur_soi": sur_soi,
                  "canal": canal_fil,
                  "maintenant": datetime.now(ZoneInfo("Europe/Zurich")).strftime("%A %d.%m.%Y %H:%M")},
                 ensure_ascii=False)),
        ] + ([du_tour(CONTEXTE_CADRE + reprise)] if reprise else []) \
          + ([{"type": "text", "text": RELECTURE_COULISSE + coulisse}] if coulisse else []) \
          + ([du_tour(SAVOIR_CADRE + savoir)] if savoir else []) + resume_blocks
        depot_fil = (body.proche_consultante_id, canal_fil)
        payload = {
            "model": model,
            "max_tokens": 2048,
            "system": system_blocks,
            "messages": _cache_history(recents),
        }
    else:
        payload = {
            "model": model,
            "max_tokens": 1024 if body.parcours in ST2_PARCOURS else 2048,
            "system": build_system(base, body.parcours, body.etat) + resume_blocks,
            "messages": _cache_history(recents),
        }
    if body.decodage_id:
        texte_dec = bloc_decodage(await fetch_decodage(authorization, body.decodage_id))
        ajouter_au_systeme(payload, texte_dec)
        usage_extra += f" decodage={body.decodage_id[:8]} decodage_car={len(texte_dec)}"
    model = passer_en_5_5(payload, moi)
    ranger_pour_cache(payload)
    client = _http()
    resp = await client.post(
        ANTHROPIC_URL,
        json=payload,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        timeout=120,
    )
    if resp.status_code != 200:
        low = resp.text.lower()
        if "credit" in low or "billing" in low:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Le tuteur est momentanément en pause (crédit API épuisé) — "
                       "Patrick est prévenu, réessaie un peu plus tard 🙏",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Anthropic API error {resp.status_code}: {resp.text[:300]}",
        )
    data = resp.json()
    if pieces_du_dernier(body):
        usage_extra += f" pieces={pieces_du_dernier(body)}"
    if data.get("stop_reason") not in (None, "end_turn"):
        usage_extra += f" stop={data.get('stop_reason')}"
    journaliser_usage("chat", body.mode, model, data, len(recents), n_blocs,
                      qui=(caller_uid or "anon")[:8], extra=usage_extra)
    await journaliser_cout("render-tuteur", body.mode, model, data, supabase_user_id=caller_uid)
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    if depot_fil is None and moi:
        cible = body.fil_consultante_id if body.mode == "fil" else None
        depot_fil = (cible, await canal_digisha(authorization, moi, sur_soi=(cible is None),
                                                choisi=body.canal, stx=(ident or {}).get("stx")))
    if depot_fil and moi:
        seance = await fil_digisha_deposer(authorization, depot_fil[0], depot_fil[1],
                                           derniere_question(body), text, body.mode)
        if pieces_du_dernier(body):
            n_gardees = await ranger_pieces(seance, body.messages[-1].content)
            log.info("digisha — pieces_gardees=%d seance=%s", n_gardees, (seance or "∅")[:8])
    if not body.no_log:
        await log_exchange(
            "render-tuteur",
            body.mode if body.mode in ("formation_m1", "fil") else body.parcours,
            derniere_question(body), text, model,
            prompt_version=version, etat=body.etat.model_dump(),
            supabase_user_id=caller_uid,
        )
    return ChatResponse(reply=text, model=model)


class CompareRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


@router.post("/compare")
async def digisha_compare(
    request: Request,
    body: CompareRequest,
    x_digisha_token: str | None = Header(None, alias="X-DigiSha-Token"),
    authorization: str | None = Header(None),
) -> dict:
    """Comparateur sonnet vs opus (exemple parlant pour l'option Profondeur).
    Même system prompt accompagnement, même question, les deux modèles en parallèle."""
    await authorize_caller(request, x_digisha_token, authorization)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")
    prompt = await fetch_prompt()
    system = (prompt["core"] + "\n\n" + (prompt.get("accompagnement_frame") or "")
              + "\n\n" + (prompt.get("st3") or "")) if prompt else ACCOMPAGNEMENT_FALLBACK
    import asyncio

    async def ask(model: str) -> str:
        client = _http()
        r = await client.post(ANTHROPIC_URL, json={
            "model": model, "max_tokens": 2048, "system": system,
            "messages": [{"role": "user", "content": body.message}],
        }, headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"}, timeout=120)
        if r.status_code != 200:
            return f"[erreur {r.status_code}]"
        return "".join(b.get("text", "") for b in r.json().get("content", [])
                       if b.get("type") == "text")

    inclus, profondeur = await asyncio.gather(
        ask(ACCOMPAGNEMENT_MODEL_INCLUS), ask(ACCOMPAGNEMENT_MODEL_PROFONDEUR))
    return {"question": body.message,
            "inclus": {"model": ACCOMPAGNEMENT_MODEL_INCLUS, "reply": inclus},
            "profondeur": {"model": ACCOMPAGNEMENT_MODEL_PROFONDEUR, "reply": profondeur}}


class AccompagnementRequest(BaseModel):
    messages: list[ChatTurn] = Field(min_length=1, max_length=60)
    no_log: bool = False        # opt-out praticienne (DEC Patrick 2026-06-13)
    # Mentorée en contexte (carte b8d68119, point 4). MÊME nom que ChatRequest, le proxy priv-web, svlbh-core
    # et svlbh-core-android : pas de seconde orthographe. Absent = accompagnement inchangé.
    fil_consultante_id: str | None = None
    # Le canal du soin choisi dans l'app (z1 → z12, DEC Patrick 17.10.2026) — même règle que ChatRequest.canal.
    canal: str | None = None
    # Le décodage que la personne poursuit (QR « Poursuivre avec DiGiSha », DEC Patrick 17.10.2026 : « via QR code serait
    # smart » ; « les deux avec le même QR » — l'autrice, l'apprenante, la consultante). Réclamé d'abord par
    # decodage_reprendre(jeton) (migration 2026-10-17j) ; le serveur le relit avec le jeton de la personne (RLS).
    decodage_id: str | None = None
    # « À propos de X » fait deux choses (Patrick, 18.10.2026 04h0x : « A propos devrait me permettre de faire les deux
    # choses : écrire une relecture réservée et écrire un décodage pour la personne ») : "relecture" (défaut, réservée,
    # 2026-10-17k/18c/18f) ou "decodage" (un décodage POUR elle, déposé dans SES pages DiGiSha, qu'elle lit).
    a_propos: str | None = None


FIL_CADRE_ACCOMPAGNEMENT = """## Passages du fil de la personne dont on parle

Ces passages viennent du fil d'échanges de la personne accompagnée dont la praticienne te parle, choisis pour
leur proximité avec son dernier message. Appuie-toi dessus quand c'est pertinent, en donnant la date
(« le 12.07… »). Ce qui n'y est pas, tu ne le sais pas : tu n'inventes jamais un souvenir."""


# ── Banque Questions/Réponses (carte 564cd650, 05.10.2026) ────────────────────────────────────────────────────
# Les questions qu'Anne ou Patrick ont décidé d'AFFICHER, cherchées EN BASE (`qa_chercher`) sous le JWT de
# l'appelante : la base ne rend que les affichées, et seulement à qui a le droit de les lire. Même contrat que
# le site (svlbh-pro-web, api/ai/chat). Elles se citent « banque Questions/Réponses », jamais comme le fil
# d'une personne. Un échec ne casse pas la réponse : DiGiSha répond sans la banque.
QA_CADRE = """## Banque Questions/Réponses de MyShamanFamily Pro

Ces questions et leurs réponses ont été choisies et validées par Patrick ou Anne pour être lues par les
apprenantes. Quand l'une répond à ce qu'on te demande, appuie-toi dessus et cite-la comme venant de la
« banque Questions/Réponses » (avec son code, par ex. Q-20261005-01) — jamais comme le fil d'une personne.
Ne la recopie pas mot pour mot si une phrase suffit ; n'y ajoute rien qu'elle ne dit pas."""
QA_LIMITE = 5


async def fetch_banque_qr(question: str, authorization: str | None, limite: int = QA_LIMITE) -> list[dict]:
    """Les questions AFFICHÉES de la banque les plus proches de la question — liste vide si rien, si pas de
    session, ou si la base ne répond pas (jamais une exception : la banque est un plus, pas une condition)."""
    if not question.strip() or not authorization or not authorization.lower().startswith("bearer "):
        return []
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        return []
    token = authorization.split(" ", 1)[1].strip()
    try:
        r = await _http().post(
            f"{supa_url}/rest/v1/rpc/qa_chercher",
            json={"p_question": question, "p_limite": limite},
            headers={"apikey": supa_key, "Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            timeout=10,
        )
    except httpx.HTTPError:
        return []
    if r.status_code != 200:
        return []
    lignes = r.json() or []
    return lignes if isinstance(lignes, list) else []


def build_qa_context(lignes: list[dict]) -> str | None:
    """Le bloc système de la banque, ou None s'il n'y a rien à citer."""
    if not lignes:
        return None
    corps = "\n\n".join(
        f"### {q.get('code', '?')} — {q.get('theme', '')}\n"
        f"Question : {q.get('question', '')}\n"
        f"Réponse : {q.get('reponse') or '(pas encore de réponse)'}"
        for q in lignes
    )
    return QA_CADRE + "\n\n" + corps


@router.post("/accompagnement", response_model=ChatResponse)
async def digisha_accompagnement(
    request: Request,
    body: AccompagnementRequest,
    x_digisha_token: str | None = Header(None, alias="X-DigiSha-Token"),
    authorization: str | None = Header(None),
) -> ChatResponse:
    """DiGiSha — ton accompagnement Digital Shaman (port Cercle Lumière)."""
    await authorize_caller(request, x_digisha_token, authorization)
    ident = await gate_subscription(authorization)
    refuser_st1(ident)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ANTHROPIC_API_KEY not configured",
        )
    prompt = await fetch_prompt()
    if prompt:
        system = (
            prompt["core"]
            + "\n\n" + (prompt.get("accompagnement_frame") or "")
            + "\n\n" + (prompt.get("st3") or "")
        )
        version = prompt["version"]
    else:
        system = ACCOMPAGNEMENT_FALLBACK
        version = FALLBACK_VERSION
    # Tier : Profondeur (opus, fair-use 150/mois) sinon inclus (sonnet). Au-delà
    # du fair-use → retour doux sur sonnet, jamais de coupure.
    model = ACCOMPAGNEMENT_MODEL_INCLUS
    used = 0
    if ident and ident.get("svlbh_id"):
        used = await _compter_accompagnement(str(ident["svlbh_id"]))
    if ident and ident.get("profondeur") and ident.get("svlbh_id") and used <= PROFONDEUR_FAIR_USE:
        model = ACCOMPAGNEMENT_MODEL_PROFONDEUR
    raw_messages = [t.model_dump(exclude_none=True) for t in body.messages]
    resume_block, recents, n_blocs = await preparer_historique(_http(), api_key, raw_messages)
    system_blocks = [partage({"type": "text", "text": system})]
    if resume_block:
        system_blocks.append(resume_block)
    mesure_fil = ""
    if body.fil_consultante_id:
        # « À propos de X » = un retour et des consignes de Patrick pour le profil X, pas la matière de la réponse (fiche
        # 2329fddd, 17.10.2026 14h30). Plus de passages du fil cherchés pour répondre ; ses séances restent plus bas, pour
        # situer ce qu'il cite (RELECTURE_SEANCES).
        system_blocks.append({"type": "text", "text": DECODAGE_POUR_CADRE if decoder_pour_elle(body) else RELECTURE_CADRE})
    # La reprise du fil DiGiSha AVANT la réponse — mesuré le 17.10.2026 09h24 chez Patrick (z12, 7 tours déposés)
    # : « Je n'ai pas de trace de notre échange précédent ». Ce chemin déposait chaque tour sans jamais le relire ;
    # seul le chemin formation M1 de /chat le faisait. Même fiche et même canal que le dépôt, plus bas.
    moi_acc = str((ident or {}).get("svlbh_id") or "").lower() or None
    cible_acc = body.fil_consultante_id or None
    prenom_cible: str | None = None
    canal_acc: str | None = None
    if moi_acc:
        canal_acc = await canal_digisha(authorization, moi_acc, sur_soi=(cible_acc is None),
                                        choisi=body.canal, stx=(ident or {}).get("stx"))
        if cible_acc and decoder_pour_elle(body):
            # Décodage POUR elle (18.10.2026) : ses séances en mémoire ; le tour ira dans SES pages (dépôt plus bas).
            reprise = await contexte_personne(authorization, cible_acc, None)
            mesure_fil += f" decodage_pour=1 reprise_car={len(reprise)}"
            if reprise:
                system_blocks.append(du_tour(CONTEXTE_CADRE + reprise))
        elif cible_acc:
            # Relecture (2026-10-17k) : DiGiSha relit SES séances, tous canaux, et ce qui a déjà été relu d'elle.
            reprise = await contexte_personne(authorization, cible_acc, None)
            deja = await relecture_pour(sujet=cible_acc, auteur=moi_acc) if await peut_relire(authorization, cible_acc) else ""
            ctx_consignes = await _rpc_personne(authorization, "digisha_consignes_contexte", {"p_sujet": cible_acc})
            if isinstance(ctx_consignes, dict):
                prenom_cible = ctx_consignes.get("prenom") or None
                actives = [c for c in (ctx_consignes.get("consignes") or []) if isinstance(c, str)]
                system_blocks.append(du_tour(f"## Tes consignes actives pour {prenom_cible or 'elle'}\n"
                                             + ("\n".join(f"- {c}" for c in actives) if actives else "(aucune pour l'instant)")))
            mesure_fil += f" relecture=1 reprise_car={len(reprise)} relecture_car={len(deja)}"
            if reprise:
                system_blocks.append(du_tour(RELECTURE_SEANCES + reprise))
            if deja:
                system_blocks.append(du_tour(RELECTURE_PRECEDENTES + deja))
        else:
            reprise = await contexte_personne(authorization, cible_acc, canal_acc)
            coulisse = await relecture_pour(svlbh=moi_acc)
            mesure_fil += f" canal={canal_acc} reprise_car={len(reprise)}" + (f" relecture_car={len(coulisse)}" if coulisse else "")
            if reprise:
                system_blocks.append(du_tour(CONTEXTE_CADRE + reprise))
            if coulisse:
                system_blocks.append({"type": "text", "text": RELECTURE_COULISSE + coulisse})
                await _rpc_service("digisha_relecture_servie", {"p_svlbh": moi_acc})
    if moi_acc:
        savoir = await savoir_pour(derniere_question(body), exclure_fiche=cible_acc,
                                   exclure_svlbh=(None if cible_acc else moi_acc))
        if savoir:
            system_blocks.append(du_tour(SAVOIR_CADRE + savoir))
            mesure_fil += f" savoir_car={len(savoir)}"
    if pieces_du_dernier(body):
        mesure_fil += f" pieces={pieces_du_dernier(body)}"
    if body.decodage_id:
        texte_dec = bloc_decodage(await fetch_decodage(authorization, body.decodage_id))
        if texte_dec:
            system_blocks.append({"type": "text", "text": texte_dec})
        mesure_fil += f" decodage={body.decodage_id[:8]} decodage_car={len(texte_dec)}"
    # La banque Questions/Réponses (carte 564cd650) : les questions affichées proches du dernier message.
    derniere = derniere_question(body)
    bloc_qa = build_qa_context(await fetch_banque_qr(derniere, authorization))
    if bloc_qa:
        system_blocks.append(du_tour(bloc_qa))
    payload = {
        "model": model,
        "max_tokens": 2048,
        "system": system_blocks,
        "messages": _cache_history(recents),
    }
    model = passer_en_5_5(payload, str((ident or {}).get("svlbh_id") or "") or None)
    ranger_pour_cache(payload)
    client = _http()
    resp = await client.post(
        ANTHROPIC_URL,
        json=payload,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        timeout=120,
    )
    if resp.status_code != 200:
        low = resp.text.lower()
        if "credit" in low or "billing" in low:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Le tuteur est momentanément en pause (crédit API épuisé) — "
                       "Patrick est prévenu, réessaie un peu plus tard 🙏",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Anthropic API error {resp.status_code}: {resp.text[:300]}",
        )
    data = resp.json()
    if data.get("stop_reason") not in (None, "end_turn"):
        mesure_fil += f" stop={data.get('stop_reason')}"
    journaliser_usage("accompagnement", "accompagnement", model, data, len(recents), n_blocs,
                      qui=(str(ident["svlbh_id"])[:8] if ident and ident.get("svlbh_id") else "∅"),
                      n_mois=used, extra=mesure_fil)
    await journaliser_cout(
        "render-accompagnement", "accompagnement", model, data,
        svlbh_id=(str(ident["svlbh_id"]) if ident and ident.get("svlbh_id") else None),
        supabase_user_id=(str(ident["uid"]) if ident and ident.get("uid") else None),
    )
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    if moi_acc and canal_acc:
        seance = await fil_digisha_deposer(authorization, cible_acc, canal_acc, derniere_question(body), text, "accompagnement",
                                           pour_elle=decoder_pour_elle(body))
        if cible_acc and prenom_cible and not decoder_pour_elle(body):
            # 2026-10-18f : les consignes du bloc adressé à SON prénom deviennent lisibles par la mentorée (porte du dépôt, jeton
            # de l'autrice) ; une réponse coupée ne pose rien.
            nouvelles, retirees = consignes_du_texte(text, prenom_cible)
            if (nouvelles or retirees) and data.get("stop_reason") in (None, "end_turn"):
                n = await _rpc_personne(authorization, "digisha_consignes_poser",
                                        {"p_sujet": cible_acc, "p_nouvelles": nouvelles, "p_retirees": retirees, "p_session": seance})
                log.info("digisha — consignes nouvelles=%d retirees=%d resultat=%s sujet=%s", len(nouvelles), len(retirees), n, cible_acc[:8])
        if pieces_du_dernier(body):
            n_gardees = await ranger_pieces(seance, body.messages[-1].content)
            log.info("digisha — pieces_gardees=%d seance=%s", n_gardees, (seance or "∅")[:8])
    # Un fil en contexte n'entre JAMAIS dans digisha_chat_log (carte b8d68119) : la réponse peut le citer.
    if not body.no_log and not body.fil_consultante_id:
        await log_exchange(
            "render-accompagnement", "accompagnement",
            derniere_question(body), text,
            model, prompt_version=version,
            svlbh_id=(str(ident["svlbh_id"]) if ident and ident.get("svlbh_id") else None),
            supabase_user_id=(str(ident["uid"]) if ident and ident.get("uid") else None),
        )
    return ChatResponse(reply=text, model=model)
