from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class LeadPushRequest(BaseModel):
    """
    Push lead slot state to Make.com → svlbh-v2.
    status: ACTIVE | WAITING | COMPLETED
    tier: LEAD | FORMATION | CERTIFIEE | SUPERVISEUR
    Known codes: Cornelia=300, Flavia=301, Anne=302, Patrick=455000
    """
    model_config = ConfigDict(populate_by_name=True)

    shamane_code: str = Field(..., alias="shamaneCode")
    prenom: str
    nom: Optional[str] = Field(None)
    tier: str = Field("CERTIFIEE")
    status: str = Field("ACTIVE")
    session_key: Optional[str] = Field(None, alias="sessionKey")
    platform: str = Field("android")


class LeadPullRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    shamane_code: str = Field(..., alias="shamaneCode")


class LeadPullResponse(BaseModel):
    shamane_code: str
    prenom: Optional[str] = None
    nom: Optional[str] = None
    tier: Optional[str] = None
    status: Optional[str] = None
    session_key: Optional[str] = None
    found: bool = False
    timestamp: Optional[int] = None
