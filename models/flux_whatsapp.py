from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class FluxWhatsAppPushRequest(BaseModel):
    """
    Push WhatsApp flux state to Make.com → svlbh-v2.
    direction: OUTBOUND | INBOUND
    status: PENDING | SENT | DELIVERED | READ | FAILED
    """
    model_config = ConfigDict(populate_by_name=True)

    session_key: str = Field(..., alias="sessionKey")
    shamane_code: str = Field(..., alias="shamaneCode")
    phone: str = Field(..., description="E.164 phone number, e.g. +41791234567")
    template: Optional[str] = Field(None, description="WhatsApp template name")
    message: Optional[str] = Field(None, description="Free-text message body")
    direction: str = Field("OUTBOUND")
    status: str = Field("PENDING")
    error_code: Optional[str] = Field(None, alias="errorCode")
    error_detail: Optional[str] = Field(None, alias="errorDetail")
    platform: str = Field("android")


class FluxWhatsAppPullRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_key: str = Field(..., alias="sessionKey")
    shamane_code: str = Field(..., alias="shamaneCode")


class FluxWhatsAppPullResponse(BaseModel):
    session_key: str
    shamane_code: str
    phone: Optional[str] = None
    template: Optional[str] = None
    message: Optional[str] = None
    direction: Optional[str] = None
    status: Optional[str] = None
    error_code: Optional[str] = None
    error_detail: Optional[str] = None
    found: bool = False
    timestamp: Optional[int] = None
