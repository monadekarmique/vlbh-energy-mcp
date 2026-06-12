"""digiSha tutor router — Formation « Les 21 ponts » (spec v0.4.1, 12 juin 2026).

POST /digisha/chat → proxy vers l'API Claude. L'app Cercle-Lumière n'embarque
AUCUNE clé Anthropic (TestFlight → exposable) ; elle s'authentifie avec le
header X-DigiSha-Token (env DIGISHA_TOKEN).

Routage modèle (DEC Patrick 2026-06-12, échelle des parcours v0.3.0) :
  ST2 (membres, alias legacy "membre")        → claude-sonnet-4-6
  ST3-ST4 et au-delà (alias legacy "praticien") → claude-fable-5
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

import httpx
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONTENT = json.loads((DATA_DIR / "formation_21_ponts.json").read_text())
FCB_CH11 = json.loads((DATA_DIR / "fcb_chapitre11.json").read_text())

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
# ST2 → sonnet ; ST3-ST4/ST5/ST6-ST7 → fable. Legacy "membre"/"praticien" acceptés.
ST2_PARCOURS = {"membre", "st2"}

def model_for(parcours: str) -> str:
    return "claude-sonnet-4-6" if parcours in ST2_PARCOURS else "claude-fable-5"

# System prompt du tuteur digiSha — spec v0.4.1, verbatim.
SYSTEM_PROMPT = """Tu es digiSha, le tuteur de formation du Digital Shaman Lab (vlbh.energy),
au service des membres du Cercle de Lumière et des praticiens VLBH.

Ta méthode est maïeutique : tu enseignes PAR LES QUESTIONS, dans la lignée
des Questions digiSha de Libération (4 phases : distinguer le Soi du
Non-Soi, explorer les racines ancestrales, reprendre le pouvoir, compléter
le dégagement). Tu poses une question avant de donner une réponse.

Ton corpus : « Les 21 ponts » — socle Grof, tronc commun M1-M4 et 16
ponts de méthode (fourni en JSON), plus les capsules ST5 et ST6-ST7.
Ta thèse centrale : traiter le noyau traite les couches.

Règles :
1. Tu adaptes chaque explication à l'orientation d'entrée du membre :
   tu pars TOUJOURS de la méthode qu'il connaît pour amener le concept VLBH.
2. Tu respectes le cadre « Seul ce qui est vérifiable est vrai » :
   le pont épigénétique est une ANALOGIE STRUCTURELLE, jamais une preuve.
   Tu ne promets aucune guérison.
3. Parcours ST2 (membres) : langage simple, capsules courtes, pas de
   jargon sans le définir. Parcours ST3-ST4 (praticien) : tables
   complètes, instruments de mesure (SLA/SLPMO, Linggui Bafa,
   Anatomy 12D), protocole S7 — tronc commun M1-M4 validé d'abord.
4. Tu proposes à chaque fin d'échange 2-3 capsules suivantes parmi les
   voisins du graphe — jamais une liste imposée, jamais de pression.
5. Le SLSA peut dépasser 100 % (jusqu'à 50 000 %) — jamais une erreur.
6. Ton ton : chaleureux, précis, voix Digital Shaman Lab. Français.
7. Chaque capsule se termine par le temps Terre : tu donnes la
   micro-pratique d'ancrage (champ "terre" du JSON) et tu invites le
   membre à la faire réellement, maintenant, dans son corps."""


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
    parcours: Literal["membre", "praticien", "st2", "st3-st4", "st5", "st6-st7"] = "st2"
    etat: MemberState = Field(default_factory=MemberState)
    messages: list[ChatTurn] = Field(min_length=1, max_length=40)


class ChatResponse(BaseModel):
    reply: str
    model: str


def build_system(parcours: str, etat: MemberState) -> str:
    blocks = [
        SYSTEM_PROMPT,
        "## Corpus — Formation « Les 21 ponts » (JSON)\n" + json.dumps(CONTENT, ensure_ascii=False),
        "## Répertoire maïeutique — Questions digiSha de Libération (FCB Chapitre 11)\n"
        + json.dumps(FCB_CH11, ensure_ascii=False),
        "## État du membre\n"
        + json.dumps(
            {
                "parcours": parcours,
                "orientation": etat.orientation,
                "capsules_vues": etat.capsules_vues,
                "quiz_reussis": etat.quiz_reussis,
                "capsule_courante": etat.capsule_courante,
            },
            ensure_ascii=False,
        ),
    ]
    return "\n\n".join(blocks)


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
    payload = {
        "model": model,
        "max_tokens": 1024 if body.parcours in ST2_PARCOURS else 2048,
        "system": build_system(body.parcours, body.etat),
        "messages": [t.model_dump() for t in body.messages],
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            ANTHROPIC_URL,
            json=payload,
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Anthropic API error {resp.status_code}: {resp.text[:300]}",
        )
    data = resp.json()
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    return ChatResponse(reply=text, model=model)
