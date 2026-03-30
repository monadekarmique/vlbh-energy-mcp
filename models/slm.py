from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, validator


class ScoresLumiere(BaseModel):
    """
    Mirrors iOS ScoresLumiere struct.
    Ranges: SLA 0–350%, SLSA 0–50 000%, SLM 0–100 000%, Tot SLM 0–1 000%
    SLSA auto-calc = SA1+SA2+SA3+SA4+SA5 when any SA component is set.
    """
    sla: Optional[int] = Field(None, ge=0, le=350)
    slsa: Optional[int] = Field(None, ge=0, le=50_000)
    slsaS1: Optional[int] = Field(None, ge=0, le=50_000)
    slsaS2: Optional[int] = Field(None, ge=0, le=50_000)
    slsaS3: Optional[int] = Field(None, ge=0, le=50_000)
    slsaS4: Optional[int] = Field(None, ge=0, le=50_000)
    slsaS5: Optional[int] = Field(None, ge=0, le=50_000)
    slm: Optional[int] = Field(None, ge=0, le=100_000)
    totSlm: Optional[int] = Field(None, ge=0, le=1_000)

    class Config:
        populate_by_name = True

    @property
    def has_detailed_slsa(self) -> bool:
        return any(v is not None for v in [
            self.slsaS1, self.slsaS2, self.slsaS3, self.slsaS4, self.slsaS5
        ])

    @property
    def slsa_auto_calc(self) -> int:
        return sum(v or 0 for v in [
            self.slsaS1, self.slsaS2, self.slsaS3, self.slsaS4, self.slsaS5
        ])

    @property
    def slsa_effective(self) -> Optional[int]:
        return self.slsa_auto_calc if self.has_detailed_slsa else self.slsa

    @validator("slsa", always=True, pre=False)
    @classmethod
    def recalc_slsa(cls, v, values):
        s1 = values.get("slsaS1")
        s2 = values.get("slsaS2")
        s3 = values.get("slsaS3")
        s4 = values.get("slsaS4")
        s5 = values.get("slsaS5")
        if any(x is not None for x in [s1, s2, s3, s4, s5]):
            return sum(x or 0 for x in [s1, s2, s3, s4, s5])
        return v


class SLMPushRequest(BaseModel):
    session_key: str = Field(..., alias="sessionKey")
    therapist: ScoresLumiere = Field(..., alias="scoresTherapist")
    patrick: ScoresLumiere = Field(..., alias="scoresPatrick")
    therapist_name: Optional[str] = Field(None, alias="therapistName")
    platform: str = Field("android")

    class Config:
        populate_by_name = True


class SLMPullRequest(BaseModel):
    session_key: str = Field(..., alias="sessionKey")

    class Config:
        populate_by_name = True


class SLMPullResponse(BaseModel):
    session_key: str
    therapist: Optional[ScoresLumiere] = None
    patrick: Optional[ScoresLumiere] = None
    found: bool = False
    timestamp: Optional[int] = None
