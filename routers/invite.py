"""Praticienne invite-token first-link (C4, Option B — ADR identité 24.07).

Le premier-lien Apple/Google d'une praticienne passe par un lien d'invitation
personnel, pré-lié à son svlbh_id, consommé à la 1re connexion → lie le `sub`
(via admin_link_praticienne_alias, déjà en prod). Pas de champ WhatsApp : une
praticienne bascule entre les 4 bridges (z1-z4) selon sa vibration — le lien part
par le canal qu'elle utilise, peu importe lequel. Supersede la partie WhatsApp du
prototype claim (PR #10) pour le premier-lien.

  POST /invite/mint   (admin, X-VLBH-Token)      -> crée un token pré-lié, renvoie le lien
  POST /invite/claim  (session Apple/Google)     -> valide + lie le sub -> consomme

⚠️ PROTOTYPE — non déployé ; la table (sql/2026-07-24-praticienne-invite.sql) n'est
   PAS appliquée en prod (Level C, auth). NEW file — l'existant est intouché.
"""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException

from dependencies import verify_token
from models.invite import (
    ClaimInviteRequest,
    ClaimInviteResponse,
    MintInviteRequest,
    MintInviteResponse,
)
from services.supabase_client import get_supabase

router = APIRouter(prefix="/invite", tags=["Praticienne invite"])

INVITE_BASE = "https://priv.svlbh.com/invite"


def _get_anon_client():
    from supabase import create_client
    url = os.environ["SUPABASE_URL"]
    anon = os.environ.get("SUPABASE_ANON_KEY", os.environ["SUPABASE_SERVICE_KEY"])
    return create_client(url, anon)


def _verify_session(authorization: str) -> dict:
    """Valide le Bearer access token (session Apple/Google) → {user_id, email, provider}."""
    token = (authorization or "").replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Session manquante")
    try:
        res = _get_anon_client().auth.get_user(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Session invalide: {e}")
    if res is None or res.user is None:
        raise HTTPException(status_code=401, detail="Session invalide")
    u = res.user
    return {"user_id": str(u.id), "email": u.email or "",
            "provider": (u.app_metadata or {}).get("provider", "unknown")}


def _hash(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


@router.post("/mint", response_model=MintInviteResponse, dependencies=[Depends(verify_token)])
async def mint_invite(body: MintInviteRequest):
    """Admin : crée un lien d'invitation pré-lié à une praticienne."""
    sb = get_supabase()
    p = sb.table("praticienne_profile").select("svlbh_id").eq("svlbh_id", body.svlbh_id).limit(1).execute()
    if not p.data:
        raise HTTPException(status_code=404, detail="svlbh_id praticienne inconnu")
    token = secrets.token_urlsafe(24)
    ttl = max(1, min(body.ttl_hours, 720))  # 1h..30j
    expires = datetime.now(timezone.utc) + timedelta(hours=ttl)
    sb.table("praticienne_invite").insert({
        "token_hash": _hash(token),
        "svlbh_id": body.svlbh_id,
        "expires_at": expires.isoformat(),
    }).execute()
    return MintInviteResponse(token=token, url=f"{INVITE_BASE}/{token}", expires_in=ttl * 3600)


@router.post("/claim", response_model=ClaimInviteResponse, dependencies=[Depends(verify_token)])
async def claim_invite(
    body: ClaimInviteRequest,
    authorization: str = Header(..., alias="Authorization"),
):
    """Session Apple/Google courante + token d'invitation → lie le sub à la praticienne."""
    session = _verify_session(authorization)
    sb = get_supabase()
    row = sb.table("praticienne_invite").select("*").eq("token_hash", _hash(body.token)).limit(1).execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Invitation introuvable")
    inv = row.data[0]
    if inv.get("consumed_at"):
        raise HTTPException(status_code=409, detail="Invitation déjà utilisée")
    if datetime.fromisoformat(inv["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Invitation expirée")

    # Lier l'identité courante (le sub) à la praticienne pré-liée. RPC déjà en prod,
    # idempotent (NOT EXISTS sur supabase_user_id).
    sb.rpc("admin_link_praticienne_alias", {
        "p_svlbh_id": inv["svlbh_id"],
        "p_user_id": session["user_id"],
        "p_email": session["email"],
        "p_provider": session["provider"],
        "p_note": "invite token (C4/Option B) — premier-lien Apple/Google",
    }).execute()

    sb.table("praticienne_invite").update({
        "consumed_at": datetime.now(timezone.utc).isoformat(),
        "consumed_by_user_id": session["user_id"],
    }).eq("id", inv["id"]).execute()

    return ClaimInviteResponse(linked=True, svlbh_id=inv["svlbh_id"])
