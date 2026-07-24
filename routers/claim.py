"""Onboarding claim flow — bind an orphan Apple session to its record.

Fixes the Apple-onboarding headache: instead of depending on Apple sending a real
e-mail that matches a record (broken by Hide My Email / mixed methods), the person
proves possession of a channel ON FILE (WhatsApp z4 / e-mail) and we auto-alias the
current Apple session (by user_id) to their svlbh_id — doctrine #11.

Endpoints:
  POST /claim/request  → locate record by identifier, send a code to the on-file channel
  POST /claim/confirm  → verify the code, alias the current session → svlbh_id

⚠️ PROTOTYPE — see docs/specs/onboarding-claim-flow-spec-v0.1.md for the hardening
   list (rate-limit, anti-enumeration, tests). NOT deployed; DB objects in
   sql/2026-07-24-auth-claim-flow.sql are NOT applied to prod yet.

See CLAUDE.md rule d'or: this is a NEW file; existing routers are untouched.
"""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status

from dependencies import verify_token
from models.claim import (
    ClaimConfirm,
    ClaimConfirmResponse,
    ClaimRequest,
    ClaimRequestResponse,
)
from services.supabase_client import get_supabase

router = APIRouter(prefix="/claim", tags=["Onboarding claim"])

CODE_TTL_SECONDS = 600  # 10 min


# ── helpers ─────────────────────────────────────────────────────────

def _get_anon_client():
    """Anon-key client, used only to verify a user's access token (get_user)."""
    from supabase import create_client
    url = os.environ["SUPABASE_URL"]
    anon_key = os.environ.get("SUPABASE_ANON_KEY", os.environ["SUPABASE_SERVICE_KEY"])
    return create_client(url, anon_key)


def _verify_session(authorization: str) -> dict:
    """Verify the Bearer access token → return {user_id, email, provider}."""
    token = (authorization or "").replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Session manquante")
    try:
        res = _get_anon_client().auth.get_user(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Session invalide: {e}")
    if res is None or res.user is None:
        raise HTTPException(status_code=401, detail="Session invalide")
    user = res.user
    provider = (user.app_metadata or {}).get("provider", "unknown")
    return {"user_id": str(user.id), "email": user.email or "", "provider": provider}


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _mask_email(email: str) -> str:
    name, _, domain = email.partition("@")
    head = name[:1] if name else "•"
    return f"{head}•••@{domain}" if domain else "•••"


def _mask_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    return f"•••••{digits[-2:]}" if len(digits) >= 2 else "•••••"


def _already_linked(sb, user_id: str) -> bool:
    a = sb.table("praticienne_user_alias").select("svlbh_id").eq(
        "supabase_user_id", user_id).limit(1).execute()
    if a.data:
        return True
    p = sb.table("praticienne_profile").select("svlbh_id").eq(
        "supabase_user_id", user_id).limit(1).execute()
    return bool(p.data)


def _find_target(sb, identifier: str) -> dict | None:
    """Locate the praticienne record + a canonical ON-FILE channel from an identifier.

    Returns {svlbh_id, channel, destination, hint} or None. The destination is taken
    from the record on file — never from the user-supplied identifier verbatim.
    """
    ident = identifier.strip().lower()

    # 1. Direct praticienne match by e-mail.
    prof = sb.table("praticienne_profile").select("svlbh_id,email").ilike(
        "email", ident).limit(1).execute()
    svlbh_id = prof.data[0]["svlbh_id"] if prof.data else None
    on_file_email = prof.data[0]["email"] if prof.data else None

    # 2. Else locate via consultante_record (e-mail / mobile / whatsapp) → derive email.
    cons = None
    if not svlbh_id:
        cons = sb.table("consultante_record").select(
            "email,mobile,whatsapp_number,whatsapp_bridge").or_(
            f"email.ilike.{ident},mobile.eq.{ident},whatsapp_number.eq.{ident}"
        ).limit(1).execute()
        if cons.data:
            on_file_email = cons.data[0].get("email")
            if on_file_email:
                prof = sb.table("praticienne_profile").select("svlbh_id,email").ilike(
                    "email", on_file_email.lower()).limit(1).execute()
                svlbh_id = prof.data[0]["svlbh_id"] if prof.data else None

    if not svlbh_id:
        return None

    # Prefer WhatsApp if a number is on file for this person, else e-mail.
    wa = sb.table("consultante_record").select("whatsapp_number,mobile,whatsapp_bridge").ilike(
        "email", (on_file_email or "").lower()).limit(1).execute()
    number = None
    if wa.data:
        number = wa.data[0].get("whatsapp_number") or wa.data[0].get("mobile")
    if number:
        return {"svlbh_id": svlbh_id, "channel": "whatsapp",
                "destination": number, "hint": _mask_phone(number)}
    if on_file_email:
        return {"svlbh_id": svlbh_id, "channel": "email",
                "destination": on_file_email, "hint": _mask_email(on_file_email)}
    return None


async def _send_code(channel: str, destination: str, code: str) -> bool:
    """Send the verification code via the on-file channel. Prototype integration.

    WhatsApp → z4-bridge.svlbh.com (CF Access). E-mail → Resend. Returns False (and
    logs) if the channel's secrets aren't configured, so the flow degrades safely.
    """
    message = (
        f"SVLBH — ton code de confirmation : {code}\n"
        f"Il expire dans 10 minutes. Si tu n'as rien demandé, ignore ce message."
    )
    try:
        if channel == "whatsapp":
            cid = os.environ.get("MAKE_Z4_BRIDGE_CF_ACCESS_CLIENT_ID")
            csec = os.environ.get("MAKE_Z4_BRIDGE_CF_ACCESS_CLIENT_SECRET")
            if not (cid and csec):
                return False
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(
                    "https://z4-bridge.svlbh.com/api/send",
                    headers={"CF-Access-Client-Id": cid, "CF-Access-Client-Secret": csec},
                    json={"recipient": destination, "message": message},
                )
            return r.status_code < 300
        else:  # email via Resend
            key = os.environ.get("RESEND_API_KEY")
            if not key:
                return False
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {key}"},
                    json={
                        "from": "SVLBH <cercle@send.svlbh.com>",
                        "to": [destination],
                        "subject": "Ton code de confirmation SVLBH",
                        "text": message,
                        "reply_to": "pb@vlbh.energy",
                    },
                )
            return r.status_code < 300
    except Exception:
        return False


# ── endpoints ───────────────────────────────────────────────────────

@router.post("/request", response_model=ClaimRequestResponse, dependencies=[Depends(verify_token)])
async def claim_request(
    body: ClaimRequest,
    authorization: str = Header(..., alias="Authorization"),
):
    """Locate the record by identifier and send a code to the ON-FILE channel."""
    session = _verify_session(authorization)
    sb = get_supabase()

    if _already_linked(sb, session["user_id"]):
        raise HTTPException(status_code=409, detail="Cette session est déjà reliée à un dossier.")

    target = _find_target(sb, body.identifier)
    if not target:
        # NOTE prototype: reveals non-existence. Harden to a generic 200 like /magic-link.
        raise HTTPException(status_code=404, detail="Aucun dossier trouvé pour cet identifiant.")

    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=CODE_TTL_SECONDS)

    ins = sb.table("auth_claim_challenge").insert({
        "claimant_user_id": session["user_id"],
        "target_svlbh_id": target["svlbh_id"],
        "code_hash": _hash_code(code),
        "channel": target["channel"],
        "channel_hint": target["hint"],
        "expires_at": expires_at.isoformat(),
    }).execute()
    challenge_id = ins.data[0]["id"]

    sent = await _send_code(target["channel"], target["destination"], code)
    if not sent:
        raise HTTPException(
            status_code=503,
            detail=f"Canal {target['channel']} non configuré (prototype) — code non envoyé.",
        )

    return ClaimRequestResponse(
        challenge_id=challenge_id,
        channel=target["channel"],
        channel_hint=target["hint"],
        expires_in=CODE_TTL_SECONDS,
    )


@router.post("/confirm", response_model=ClaimConfirmResponse, dependencies=[Depends(verify_token)])
async def claim_confirm(
    body: ClaimConfirm,
    authorization: str = Header(..., alias="Authorization"),
):
    """Verify the code and alias the current session → svlbh_id (doctrine #11)."""
    session = _verify_session(authorization)
    sb = get_supabase()

    ch = sb.table("auth_claim_challenge").select("*").eq("id", body.challenge_id).limit(1).execute()
    if not ch.data:
        raise HTTPException(status_code=404, detail="Défi introuvable.")
    challenge = ch.data[0]

    if challenge["claimant_user_id"] != session["user_id"]:
        raise HTTPException(status_code=403, detail="Ce défi n'appartient pas à cette session.")
    if challenge.get("consumed_at"):
        raise HTTPException(status_code=409, detail="Défi déjà utilisé.")
    if datetime.fromisoformat(challenge["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Code expiré.")
    if challenge["attempts"] >= challenge["max_attempts"]:
        raise HTTPException(status_code=429, detail="Trop de tentatives.")

    if _hash_code(body.code) != challenge["code_hash"]:
        sb.table("auth_claim_challenge").update(
            {"attempts": challenge["attempts"] + 1}).eq("id", challenge["id"]).execute()
        raise HTTPException(status_code=401, detail="Code incorrect.")

    sb.rpc("admin_link_praticienne_alias", {
        "p_svlbh_id": challenge["target_svlbh_id"],
        "p_user_id": session["user_id"],
        "p_email": session["email"],
        "p_provider": session["provider"],
        "p_note": "claim flow (doctrine #11) — proof-of-possession canal sur fiche",
    }).execute()

    sb.table("auth_claim_challenge").update(
        {"consumed_at": datetime.now(timezone.utc).isoformat()}).eq("id", challenge["id"]).execute()

    return ClaimConfirmResponse(linked=True, svlbh_id=challenge["target_svlbh_id"])
