from __future__ import annotations
import time
from fastapi import APIRouter, Depends, HTTPException, status
from models.lead import LeadPushRequest, LeadPullRequest, LeadPullResponse
from services.make_service import MakeServiceError
from dependencies import get_make_service, verify_token

router = APIRouter(prefix="/lead", tags=["Lead"])

DATASTORE_ID = 155674


@router.post("/push", summary="Push lead slot state to Make.com → svlbh-v2", status_code=200)
async def push_lead(
    payload: LeadPushRequest,
    _: None = Depends(verify_token),
    make=Depends(get_make_service),
) -> dict:
    body = {
        "shamaneCode": payload.shamane_code,
        "datastoreId": DATASTORE_ID,
        "module": "LEAD",
        "prenom": payload.prenom,
        "nom": payload.nom,
        "tier": payload.tier,
        "status": payload.status,
        "sessionKey": payload.session_key,
        "platform": payload.platform,
        "timestamp": int(time.time() * 1000),
    }
    try:
        resp = await make._client.post(make._push_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make push lead failed: {resp.text}")
        return {"success": True, "shamaneCode": payload.shamane_code, "make_status": resp.status_code}
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{type(e).__name__}: {e}")


@router.post("/pull", summary="Fetch lead state from Make.com by shamaneCode", response_model=LeadPullResponse)
async def pull_lead(
    payload: LeadPullRequest,
    _: None = Depends(verify_token),
    make=Depends(get_make_service),
) -> LeadPullResponse:
    body = {
        "shamaneCode": payload.shamane_code,
        "datastoreId": DATASTORE_ID,
        "module": "LEAD",
    }
    try:
        resp = await make._client.post(make._pull_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make pull lead failed: {resp.text}")
        raw = resp.text.strip()
        if not raw:
            return LeadPullResponse(shamane_code=payload.shamane_code, found=False)
        try:
            data = resp.json()
        except Exception:
            return LeadPullResponse(shamane_code=payload.shamane_code, found=False)
        if not data:
            return LeadPullResponse(shamane_code=payload.shamane_code, found=False)
        return LeadPullResponse(
            shamane_code=payload.shamane_code,
            prenom=data.get("prenom"),
            nom=data.get("nom"),
            tier=data.get("tier"),
            status=data.get("status"),
            session_key=data.get("sessionKey"),
            found=True,
            timestamp=data.get("timestamp"),
        )
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{type(e).__name__}: {e}")
