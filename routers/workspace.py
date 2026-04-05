from __future__ import annotations
import os
import re
import time
from fastapi import APIRouter, Depends, status
from dependencies import verify_token, get_make_service
from models.workspace import WebhookCheck, WorkspaceSafetyReport
from services.make_service import MakeService

router = APIRouter(prefix="/workspace", tags=["Workspace"])

MAKE_WEBHOOK_PATTERN = re.compile(r"^https://hook\.[a-z0-9]+\.make\.com/[A-Za-z0-9]+$")


async def _check_webhook(client, url: str, name: str) -> WebhookCheck:
    configured = bool(url)
    valid_format = bool(MAKE_WEBHOOK_PATTERN.match(url)) if configured else False

    if not configured:
        return WebhookCheck(name=name, configured=False, valid_format=False, error="URL not set")

    if not valid_format:
        return WebhookCheck(
            name=name, configured=True, valid_format=False,
            error=f"URL does not match expected Make.com webhook pattern",
        )

    # Connectivity check: send a minimal POST and accept any 2xx/4xx as "reachable"
    # (4xx means the webhook exists but rejects the empty payload, which is fine)
    try:
        start = time.monotonic()
        resp = await client.post(url, json={"ping": True}, timeout=10.0)
        latency = int((time.monotonic() - start) * 1000)
        reachable = resp.status_code < 500
        error = None if reachable else f"HTTP {resp.status_code}"
    except Exception as exc:
        latency = None
        reachable = False
        error = f"{type(exc).__name__}: {exc}"

    return WebhookCheck(
        name=name, configured=True, valid_format=True,
        reachable=reachable, latency_ms=latency, error=error,
    )


@router.post(
    "/safety",
    summary="Check workspace configuration safety",
    response_model=WorkspaceSafetyReport,
    status_code=status.HTTP_200_OK,
)
async def check_workspace_safety(
    _: None = Depends(verify_token),
    make: MakeService = Depends(get_make_service),
) -> WorkspaceSafetyReport:
    """
    Validate that the workspace environment is correctly configured:
    - VLBH_TOKEN is set
    - MAKE_WEBHOOK_PUSH_URL / PULL_URL are valid Make.com webhook URLs
    - Webhooks are reachable (connectivity probe)
    """
    token_configured = bool(os.environ.get("VLBH_TOKEN", ""))

    push_check = await _check_webhook(make._client, make._push_url, "MAKE_WEBHOOK_PUSH_URL")
    pull_check = await _check_webhook(make._client, make._pull_url, "MAKE_WEBHOOK_PULL_URL")

    warnings: list[str] = []
    if not token_configured:
        warnings.append("VLBH_TOKEN is not configured — all authenticated endpoints will fail")
    if not push_check.configured:
        warnings.append("Push webhook URL is not configured")
    elif not push_check.valid_format:
        warnings.append("Push webhook URL does not match Make.com pattern")
    elif not push_check.reachable:
        warnings.append(f"Push webhook is unreachable: {push_check.error}")
    if not pull_check.configured:
        warnings.append("Pull webhook URL is not configured")
    elif not pull_check.valid_format:
        warnings.append("Pull webhook URL does not match Make.com pattern")
    elif not pull_check.reachable:
        warnings.append(f"Pull webhook is unreachable: {pull_check.error}")

    safe = token_configured and push_check.reachable is True and pull_check.reachable is True

    return WorkspaceSafetyReport(
        safe=safe,
        token_configured=token_configured,
        push_webhook=push_check,
        pull_webhook=pull_check,
        warnings=warnings,
    )
