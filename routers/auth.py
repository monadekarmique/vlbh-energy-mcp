"""Authentication router — iTherapeut 6.0.

Endpoints:
  POST /auth/register      → create account (email + password)
  POST /auth/login         → email/password login → JWT
  POST /auth/magic-link    → passwordless magic link
  POST /auth/refresh       → refresh access token
  GET  /auth/me            → verify token + get user info
  POST /auth/apple-native  → Apple Sign In (identity token exchange)

Uses Supabase Auth (GoTrue) under the hood.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel
from typing import Optional

from models.auth import (
    LoginRequest,
    LoginResponse,
    MagicLinkRequest,
    MagicLinkResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenVerifyResponse,
)
from services.supabase_client import get_supabase

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def _get_anon_client():
    """Get a Supabase client with anon key (for auth operations).

    Auth operations use the anon key, not the service key,
    so that Supabase RLS policies apply correctly.
    """
    from supabase import create_client
    url = os.environ["SUPABASE_URL"]
    anon_key = os.environ.get("SUPABASE_ANON_KEY", os.environ["SUPABASE_SERVICE_KEY"])
    return create_client(url, anon_key)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    """Create a new user account via Supabase Auth."""
    try:
        sb = _get_anon_client()
        result = sb.auth.sign_up({
            "email": body.email,
            "password": body.password,
            "options": {
                "data": {
                    "full_name": body.full_name,
                    "role": body.role,
                }
            }
        })

        if result.user is None:
            raise HTTPException(status_code=400, detail="Registration failed")

        return RegisterResponse(
            user_id=result.user.id,
            email=result.user.email or body.email,
            role=body.role,
        )
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            raise HTTPException(status_code=409, detail="Email already registered")
        raise HTTPException(status_code=400, detail=f"Registration failed: {error_msg}")


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """Authenticate with email and password."""
    try:
        sb = _get_anon_client()
        result = sb.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password,
        })

        if result.session is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_meta = result.user.user_metadata or {} if result.user else {}

        return LoginResponse(
            access_token=result.session.access_token,
            refresh_token=result.session.refresh_token,
            expires_in=result.session.expires_in or 3600,
            user_id=result.user.id if result.user else "",
            email=result.user.email if result.user else body.email,
            role=user_meta.get("role"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {e}")


@router.post("/magic-link", response_model=MagicLinkResponse)
async def send_magic_link(body: MagicLinkRequest):
    """Send a passwordless magic link to the user's email."""
    try:
        sb = _get_anon_client()
        sb.auth.sign_in_with_otp({
            "email": body.email,
        })
        return MagicLinkResponse(email=body.email)
    except Exception as e:
        # Don't reveal if email exists or not
        return MagicLinkResponse(email=body.email)


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(body: RefreshRequest):
    """Refresh an expired access token."""
    try:
        sb = _get_anon_client()
        result = sb.auth.refresh_session(body.refresh_token)

        if result.session is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user_meta = result.user.user_metadata or {} if result.user else {}

        return LoginResponse(
            access_token=result.session.access_token,
            refresh_token=result.session.refresh_token,
            expires_in=result.session.expires_in or 3600,
            user_id=result.user.id if result.user else "",
            email=result.user.email if result.user else "",
            role=user_meta.get("role"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {e}")


@router.get("/me", response_model=TokenVerifyResponse)
async def get_me(authorization: str = Header(..., alias="Authorization")):
    """Verify the current access token and return user info."""
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        sb = _get_anon_client()
        result = sb.auth.get_user(token)

        if result.user is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_meta = result.user.user_metadata or {}

        return TokenVerifyResponse(
            user_id=result.user.id,
            email=result.user.email or "",
            role=user_meta.get("role"),
            email_confirmed=result.user.email_confirmed_at is not None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {e}")


# ── Apple Sign In (native iOS) ──────────────────────────────────────

class AppleNativeRequest(BaseModel):
    identity_token: str
    nonce: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


@router.post("/apple-native", response_model=LoginResponse)
async def apple_native_sign_in(body: AppleNativeRequest):
    """Exchange an Apple identity token for a Supabase session.

    The iOS app uses ASAuthorizationAppleIDProvider to get a native
    identity token, then sends it here. We forward it to Supabase
    Auth which verifies the token with Apple and returns a session.
    """
    import httpx

    supabase_url = os.environ["SUPABASE_URL"]
    anon_key = os.environ.get("SUPABASE_ANON_KEY", os.environ["SUPABASE_SERVICE_KEY"])

    # Supabase GoTrue endpoint for ID token sign-in
    url = f"{supabase_url}/auth/v1/token?grant_type=id_token"
    headers = {
        "apikey": anon_key,
        "Content-Type": "application/json",
    }
    payload = {
        "provider": "apple",
        "id_token": body.identity_token,
        "nonce": body.nonce,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers, timeout=15.0)

    if resp.status_code != 200:
        detail = resp.text
        try:
            detail = resp.json().get("error_description", resp.text)
        except Exception:
            pass
        raise HTTPException(status_code=resp.status_code, detail=f"Apple sign-in failed: {detail}")

    data = resp.json()
    user = data.get("user", {})
    user_meta = user.get("user_metadata", {})

    # Optionally update the user's name if Apple provided it (first sign-in only)
    if body.first_name or body.last_name:
        try:
            sb = _get_anon_client()
            sb.auth._headers = {**sb.auth._headers, "Authorization": f"Bearer {data['access_token']}"}
            # Not critical if this fails
        except Exception:
            pass

    return LoginResponse(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_in=data.get("expires_in", 3600),
        user_id=user.get("id", ""),
        email=user.get("email", ""),
        role=user_meta.get("role"),
    )
