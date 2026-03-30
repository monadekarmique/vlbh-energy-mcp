from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class SessionPushRequest(BaseModel):
    """
    Push session metadata to Make.com → svlbh-v2.
    Key format: programCode-patientId-sessionNum-practitionerCode (e.g. 00-12-002-0301)
    """
    model_config = ConfigDict(populate_by_name=True)

    session_key: str = Field(..., alias="sessionKey")
    patient_id: str = Field(..., alias="patientId")
    session_num: str = Field(..., alias="sessionNum")
    program_code: str = Field(..., alias="programCode")
    practitioner_code: str = Field(..., alias="practitionerCode")
    therapist_name: Optional[str] = Field(None, alias="therapistName")
    status: str = Field("ACTIVE")
    event_count: int = Field(0, alias="eventCount")
    liberated_count: int = Field(0, alias="liberatedCount")
    platform: str = Field("android")


class SessionPullRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_key: str = Field(..., alias="sessionKey")


class SessionPullResponse(BaseModel):
    session_key: str
    patient_id: Optional[str] = None
    session_num: Optional[str] = None
    program_code: Optional[str] = None
    practitioner_code: Optional[str] = None
    therapist_name: Optional[str] = None
    status: Optional[str] = None
    event_count: Optional[int] = None
    liberated_count: Optional[int] = None
    found: bool = False
    timestamp: Optional[int] = None
