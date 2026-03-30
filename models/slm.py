from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class ScoresLumiere(BaseModel):
    """
    Mirrors iOS ScoresLumiere struct.
    Ranges: SLA 0–350%, SLSA 0–50 000%, SLM 0–100 000%, Tot SLM 0–1 000%
    SLSA auto-calc = SA1+SA2+SA3+SA4+SA5 when any SA component is set.
    """
    sla: Optional[int] = Field(None, ge=0, le=350)
    slsa: Optional[int] = Field(None, ge=0, le=50_000)
    slsa_s1: Optional[int] = Field(None, ge=0, le=50_000, alias="slsaS1")
    slsa_s2: Optional[int] = Field(None, ge=0, le=50_000, alias="slsaS2")
    slsa_s3: Optional[int] = Field(None, ge=0, le=50_000, alias="slsaS3")
    slsa_s4: Optional[int] = Field(None, ge=0, le=50_000, alias="slsaS4")
    slsa_s5: Optional[int] = Field(None, ge=0, le=50_000, alias="slsaS5")
    slm: Optional[int] = Field(None, ge=0, le=100_000)
    tot_slm: Optional[int] = Field(None, ge=0, le=1_000, alias="totSlm")

    model_config = {"populate_by_name": True}

    @property
    def has_detailed_slsa(self) -> bool:
        return any(v is not None for v in [
            self.slsa_s1, self.slsa_s2, self.slsa_s3, self.slsa_s4, self.slsa_s5
        ])

    @property
    def slsa_auto_calc(self) -> int:
        return sum(v or 0 for v in [
            self.slsa_s1, self.slsa_s2, self.slsa_s3, self.slsa_s4, self.slsa_s5
        ])

    @property
    def slsa_effective(self) -> Optional[int]:
        return self.slsa_auto_calc if self.has_detailed_slsa else self.slsa

    @model_validator(mode="after")
    def recalc_slsa(self) -> "ScoresLumiere":
        if self.has_detailed_slsa:
            self.slsa = self.slsa_auto_calc
        return self


class SLMPushRequest(BaseModel):
    """Payload for POST /slm/push"""
    session_key: str = Field(..., alias="sessionKey", pattern=r"^PP-.+-.+-.+$")
    therapist: ScoresLumiere = Field(..., alias="scoresTherapist")
    patrick: ScoresLumiere = Field(..., alias="scoresPatrick")
    therapist_name: Optional[str] = Field(None, alias="therapistName")
    platform: str = Field("android", pattern=r"^(ios|android|web)$")

    model_config = {"populate_by_name": True}


class SLMPullRequest(BaseModel):
    """Payload for POST /slm/pull"""
    session_key: str = Field(..., alias="sessionKey", pattern=r"^PP-.+-.+-.+$")

    model_config = {"populate_by_name": True}


class SLMPullResponse(BaseModel):
    """Response from POST /slm/pull"""
    session_key: str
    therapist: Optional[ScoresLumiere] = None
    patrick: Optional[ScoresLumiere] = None
    found: bool = False
    timestamp: Optional[int] = None
