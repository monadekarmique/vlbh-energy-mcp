"""Pydantic models for Authentication — iTherapeut 6.0.

Supabase Auth integration: email/password + magic link.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Body for POST /auth/register."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=200)
    role: str = Field(default="patient", pattern=r"^(patient|therapist)$")


class RegisterResponse(BaseModel):
    """Response for POST /auth/register."""
    user_id: str
    email: str
    role: str
    message: str = "Account created. Please check your email to verify."


class MagicLinkRequest(BaseModel):
    """Body for POST /auth/magic-link."""
    email: EmailStr


class MagicLinkResponse(BaseModel):
    """Response for POST /auth/magic-link."""
    email: str
    message: str = "Magic link sent. Check your email."


class LoginRequest(BaseModel):
    """Body for POST /auth/login."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Response for POST /auth/login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    email: str
    role: Optional[str] = None


class RefreshRequest(BaseModel):
    """Body for POST /auth/refresh."""
    refresh_token: str


class TokenVerifyResponse(BaseModel):
    """Response for GET /auth/me."""
    user_id: str
    email: str
    role: Optional[str] = None
    email_confirmed: bool = False
