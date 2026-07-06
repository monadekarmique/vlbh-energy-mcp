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

import json
import os
import time
from pathlib import Path
from typing import Literal

import httpx
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONTENT = json.loads((DATA_DIR / "formation_26_ponts.json").read_text())
FCB_CH11 = json.loads((DATA_DIR / "fcb_chapitre11.json").read_text())

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
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
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{supa_url}/rest/v1/digisha_prompt",
                params={
                    "active": "eq.true",
                    "select": "version,core,accompagnement_frame,st3,tuteur_frame",
                    "limit": "1",
                },
                headers={"apikey": supa_key, "Authorization": f"Bearer {supa_key}"},
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


def verify_digisha_token(x_digisha_token: str = Header(..., alias="X-DigiSha-Token")) -> None:
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
        async with httpx.AsyncClient(timeout=10) as client:
            ur = await client.get(
                f"{supa_url}/auth/v1/user",
                headers={"apikey": supa_key, "Authorization": f"Bearer {token}"},
            )
            if ur.status_code != 200:
                return
            uid = ur.json().get("id")
            if not uid:
                return
            pr = await client.get(
                f"{supa_url}/rest/v1/praticienne_profile",
                params={"supabase_user_id": f"eq.{uid}",
                        "select": "svlbh_id,pro_status,digisha_profondeur,digisha_profondeur_trial_until",
                        "limit": 1},
                headers={"apikey": supa_key, "Authorization": f"Bearer {supa_key}"},
            )
            rows = pr.json() if pr.status_code == 200 else []
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
    # Profondeur effective = option payée OU essai 48 h en cours (DEC 2026-07-06).
    profondeur = bool(rows[0].get("digisha_profondeur"))
    trial = rows[0].get("digisha_profondeur_trial_until")
    if not profondeur and trial:
        from datetime import datetime, timezone
        try:
            t = datetime.fromisoformat(str(trial).replace("Z", "+00:00"))
            profondeur = t > datetime.now(timezone.utc)
        except Exception:
            pass
    return {"uid": uid, "svlbh_id": rows[0].get("svlbh_id"), "profondeur": profondeur}


# ── Option « DiGiSha Profondeur » +59 CHF (DEC Patrick 2026-07-06) ────────────
# Inclus (179 CHF) : accompagnement sur sonnet. Profondeur : opus — DiGiSha reste
# TOUJOURS une génération derrière le frontier (DEC Patrick 2026-07-06 : fable-5
# deviendra éligible quand le modèle 6 sortira). Fair-use 150 échanges opus/mois,
# au-delà retour doux sur sonnet (jamais de coupure).
ACCOMPAGNEMENT_MODEL_INCLUS = "claude-sonnet-4-6"
ACCOMPAGNEMENT_MODEL_PROFONDEUR = "claude-opus-4-8"
PROFONDEUR_FAIR_USE = 150


async def _monthly_accompagnement_count(svlbh_id: str) -> int:
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key or not svlbh_id:
        return 0
    from datetime import datetime, timezone
    month_start = datetime.now(timezone.utc).strftime("%Y-%m-01T00:00:00Z")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{supa_url}/rest/v1/digisha_chat_log",
                params={"svlbh_id": f"eq.{svlbh_id}", "mode": "eq.accompagnement",
                        "created_at": f"gte.{month_start}", "select": "id"},
                headers={"apikey": supa_key, "Authorization": f"Bearer {supa_key}",
                         "Prefer": "count=exact", "Range": "0-0"},
            )
        cr = r.headers.get("content-range", "")
        return int(cr.split("/")[-1]) if "/" in cr and cr.split("/")[-1].isdigit() else 0
    except Exception:
        return 0


def _cache_history(messages: list[dict]) -> list[dict]:
    """Prompt caching sur l'historique : marque le DERNIER message d'un
    breakpoint cache_control → tout le préfixe (system + tours précédents) est
    caché et se prolonge à chaque tour (TTL 5 min). ~2-3x d'économie sur les
    longues conversations."""
    if not messages:
        return messages
    out = [dict(m) for m in messages]
    last = out[-1]
    content = last.get("content")
    if isinstance(content, str):
        last["content"] = [{"type": "text", "text": content,
                           "cache_control": {"type": "ephemeral"}}]
    return out


router = APIRouter(prefix="/digisha", tags=["digiSha"])


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


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


async def log_exchange(source: str, mode: str, user_message: str, reply: str,
                       model: str, prompt_version: str, etat: dict | None = None,
                       svlbh_id: str | None = None,
                       supabase_user_id: str | None = None) -> None:
    """Journal DiGiSha → Supabase digisha_chat_log (best effort, jamais bloquant)."""
    supa_url = os.environ.get("DIGISHA_SUPABASE_URL", "")
    supa_key = os.environ.get("DIGISHA_SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
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
            )
    except Exception:
        pass


class ChatResponse(BaseModel):
    reply: str
    model: str


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
        {"type": "text",
         "text": "## Répertoire maïeutique — Questions digiSha de Libération (FCB Chapitre 11)\n"
                 + json.dumps(FCB_CH11, ensure_ascii=False),
         "cache_control": {"type": "ephemeral"}},
        {"type": "text",
         "text": "## État du membre\n" + json.dumps(etat_dyn, ensure_ascii=False)},
    ]


@router.post("/chat", response_model=ChatResponse)
async def digisha_chat(
    body: ChatRequest,
    x_digisha_token: str = Header(..., alias="X-DigiSha-Token"),
) -> ChatResponse:
    verify_digisha_token(x_digisha_token)
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
    payload = {
        "model": model,
        "max_tokens": 1024 if body.parcours in ST2_PARCOURS else 2048,
        "system": build_system(base, body.parcours, body.etat),
        "messages": _cache_history([t.model_dump() for t in body.messages]),
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            ANTHROPIC_URL,
            json=payload,
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
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
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    if not body.no_log:
        await log_exchange(
            "render-tuteur", body.parcours,
            body.messages[-1].content if body.messages else "", text, model,
            prompt_version=version, etat=body.etat.model_dump(),
        )
    return ChatResponse(reply=text, model=model)


class CompareRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


@router.post("/compare")
async def digisha_compare(
    body: CompareRequest,
    x_digisha_token: str = Header(..., alias="X-DigiSha-Token"),
) -> dict:
    """Comparateur sonnet vs opus (exemple parlant pour l'option Profondeur).
    Même system prompt accompagnement, même question, les deux modèles en parallèle."""
    verify_digisha_token(x_digisha_token)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")
    prompt = await fetch_prompt()
    system = (prompt["core"] + "\n\n" + (prompt.get("accompagnement_frame") or "")
              + "\n\n" + (prompt.get("st3") or "")) if prompt else ACCOMPAGNEMENT_FALLBACK
    import asyncio

    async def ask(model: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(ANTHROPIC_URL, json={
                "model": model, "max_tokens": 2048, "system": system,
                "messages": [{"role": "user", "content": body.message}],
            }, headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"})
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


@router.post("/accompagnement", response_model=ChatResponse)
async def digisha_accompagnement(
    body: AccompagnementRequest,
    x_digisha_token: str = Header(..., alias="X-DigiSha-Token"),
    authorization: str | None = Header(None),
) -> ChatResponse:
    """DiGiSha — ton accompagnement Digital Shaman (port Cercle Lumière)."""
    verify_digisha_token(x_digisha_token)
    ident = await gate_subscription(authorization)
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
    if ident and ident.get("profondeur") and ident.get("svlbh_id"):
        used = await _monthly_accompagnement_count(str(ident["svlbh_id"]))
        if used < PROFONDEUR_FAIR_USE:
            model = ACCOMPAGNEMENT_MODEL_PROFONDEUR
    payload = {
        "model": model,
        "max_tokens": 2048,
        "system": system,
        "messages": _cache_history([t.model_dump() for t in body.messages]),
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            ANTHROPIC_URL,
            json=payload,
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
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
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    if not body.no_log:
        await log_exchange(
            "render-accompagnement", "accompagnement",
            body.messages[-1].content if body.messages else "", text,
            model, prompt_version=version,
            svlbh_id=(str(ident["svlbh_id"]) if ident and ident.get("svlbh_id") else None),
            supabase_user_id=(str(ident["uid"]) if ident and ident.get("uid") else None),
        )
    return ChatResponse(reply=text, model=model)
