from __future__ import annotations
import time
from fastapi import APIRouter, Depends, HTTPException, status
from models.flux_whatsapp import (
    FluxWhatsAppPushRequest,
    FluxWhatsAppPullRequest,
    FluxWhatsAppPullResponse,
)
from services.make_service import MakeServiceError
from dependencies import get_make_service, verify_token

router = APIRouter(prefix="/flux-whatsapp", tags=["Flux WhatsApp"])

DATASTORE_ID = 155674


@router.post("/push", summary="Push WhatsApp flux state to Make.com → svlbh-v2", status_code=200)
async def push_flux_whatsapp(
    payload: FluxWhatsAppPushRequest,
    _: None = Depends(verify_token),
    make=Depends(get_make_service),
) -> dict:
    body = {
        "sessionKey": payload.session_key,
        "shamaneCode": payload.shamane_code,
        "datastoreId": DATASTORE_ID,
        "module": "FLUX_WHATSAPP",
        "phone": payload.phone,
        "template": payload.template,
        "message": payload.message,
        "direction": payload.direction,
        "status": payload.status,
        "errorCode": payload.error_code,
        "errorDetail": payload.error_detail,
        "platform": payload.platform,
        "timestamp": int(time.time() * 1000),
    }
    try:
        resp = await make._client.post(make._push_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make push flux_whatsapp failed: {resp.text}")
        return {
            "success": True,
            "sessionKey": payload.session_key,
            "shamaneCode": payload.shamane_code,
            "make_status": resp.status_code,
        }
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{type(e).__name__}: {e}",
        )


@router.post(
    "/pull",
    summary="Fetch WhatsApp flux state from Make.com by sessionKey + shamaneCode",
    response_model=FluxWhatsAppPullResponse,
)
async def pull_flux_whatsapp(
    payload: FluxWhatsAppPullRequest,
    _: None = Depends(verify_token),
    make=Depends(get_make_service),
) -> FluxWhatsAppPullResponse:
    body = {
        "sessionKey": payload.session_key,
        "shamaneCode": payload.shamane_code,
        "datastoreId": DATASTORE_ID,
        "module": "FLUX_WHATSAPP",
    }
    try:
        resp = await make._client.post(make._pull_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make pull flux_whatsapp failed: {resp.text}")

        raw = resp.text.strip()
        if not raw:
            return FluxWhatsAppPullResponse(
                session_key=payload.session_key,
                shamane_code=payload.shamane_code,
                found=False,
            )

        try:
            data = resp.json()
        except Exception:
            # Make.com returns "Accepted" when the pull scenario has no Webhook Response module
            return FluxWhatsAppPullResponse(
                session_key=payload.session_key,
                shamane_code=payload.shamane_code,
                found=False,
            )

        if not data:
            return FluxWhatsAppPullResponse(
                session_key=payload.session_key,
                shamane_code=payload.shamane_code,
                found=False,
            )

        return FluxWhatsAppPullResponse(
            session_key=payload.session_key,
            shamane_code=payload.shamane_code,
            phone=data.get("phone"),
            template=data.get("template"),
            message=data.get("message"),
            direction=data.get("direction"),
            status=data.get("status"),
            error_code=data.get("errorCode"),
            error_detail=data.get("errorDetail"),
            found=True,
            timestamp=data.get("timestamp"),
        )
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{type(e).__name__}: {e}",
        )
