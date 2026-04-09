from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class WebhookCheck(BaseModel):
    name: str
    configured: bool
    valid_format: bool
    reachable: Optional[bool] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None


class WorkspaceSafetyReport(BaseModel):
    safe: bool
    token_configured: bool
    push_webhook: WebhookCheck
    pull_webhook: WebhookCheck
    warnings: list[str] = []
