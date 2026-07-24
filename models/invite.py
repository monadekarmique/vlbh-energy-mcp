"""Models for the praticienne invite-token flow (C4, Option B).

See sql/2026-07-24-praticienne-invite.sql and routers/invite.py.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class MintInviteRequest(BaseModel):
    svlbh_id: str = Field(..., description="praticienne à qui l'invitation est pré-liée")
    ttl_hours: int = Field(168, description="durée de validité en heures (défaut 7 jours)")


class MintInviteResponse(BaseModel):
    token: str
    url: str
    expires_in: int  # seconds


class ClaimInviteRequest(BaseModel):
    token: str


class ClaimInviteResponse(BaseModel):
    linked: bool
    svlbh_id: Optional[str] = None
