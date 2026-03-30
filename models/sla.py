from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class SLAPushRequest(BaseModel):
    """
    Push SLA score for both practitioners.
    Range: SLA 0–350%
    """
    model_config = ConfigDict(populate_by_name=True)

    session_key: str = Field(..., alias="sessionKey")
    sla_therapist: Optional[int] = Field(None, alias="slaTherapist", ge=0, le=350)
    sla_patrick: Optional[int] = Field(None, alias="slaPatrick", ge=0, le=350)
    therapist_name: Optional[str] = Field(None, alias="therapistName")
    platform: str = Field("android")


class SLAPullRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_key: str = Field(..., alias="sessionKey")


class SLAPullResponse(BaseModel):
    session_key: str
    sla_therapist: Optional[int] = None
    sla_patrick: Optional[int] = None
    found: bool = False
    timestamp: Optional[int] = None
