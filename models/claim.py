"""Models for the onboarding claim flow.

See docs/specs/onboarding-claim-flow-spec-v0.1.md
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ClaimRequest(BaseModel):
    """Start a claim: the orphan session asserts who they are (to locate the record).

    `identifier` is the e-mail or mobile the person registered with — used ONLY to
    find their record. The verification code is sent to the channel ON FILE, never
    to a user-supplied destination.
    """
    identifier: str = Field(..., description="e-mail ou mobile enregistré sur la fiche")


class ClaimRequestResponse(BaseModel):
    challenge_id: str
    channel: str            # 'whatsapp' | 'email'
    channel_hint: str       # masked destination, e.g. "•••@bluewin.ch" / "+41•• •• •• 00"
    expires_in: int         # seconds


class ClaimConfirm(BaseModel):
    challenge_id: str
    code: str = Field(..., min_length=4, max_length=8)


class ClaimConfirmResponse(BaseModel):
    linked: bool
    svlbh_id: Optional[str] = None
