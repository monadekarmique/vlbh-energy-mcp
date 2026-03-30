from __future__ import annotations
import time
from fastapi import APIRouter, Depends, HTTPException, status
from models.sla import SLAPushRequest, SLAPullRequest, SLAPullResponse
from services.make_service import MakeServiceError
from dependencies import get_make_service, verify_token

router = APIRouter(prefix="/sla", tags=["SLA"])

DATASTORE_ID = 155674


@router.post("/push", summary="Push SLA score to Make.com → svlbh-v2", status_code=200)
async def push_sla(
    payload: SLAPushRequest,
    _: None = Depends(verify_token),
    make=Depends(get_make_service),
) -> dict:
    body = {
        "sessionKey": payload.session_key,
        "datastoreId": DATASTORE_ID,
        "module": "SLA",
        "therapistName": payload.therapist_name,
        "platform": payload.platform,
        "timestamp": int(time.time() * 1000),
        "SLA_T": payload.sla_therapist,
        "SLA_P": payload.sla_patrick,
    }
    try:
        resp = await make._client.post(make._push_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make push SLA failed: {resp.text}")
        return {"success": True, "sessionKey": payload.session_key, "make_status": resp.status_code}
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{type(e).__name__}: {e}")


@router.post("/pull", summary="Fetch SLA score from Make.com by sessionKey", response_model=SLAPullResponse)
async def pull_sla(
    payload: SLAPullRequest,
    _: None = Depends(verify_token),
    make=Depends(get_make_service),
) -> SLAPullResponse:
    body = {
        "sessionKey": payload.session_key,
        "datastoreId": DATASTORE_ID,
        "module": "SLA",
    }
    try:
        resp = await make._client.post(make._pull_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make pull SLA failed: {resp.text}")
        raw = resp.text.strip()
        if not raw:
            return SLAPullResponse(session_key=payload.session_key, found=False)
        try:
            data = resp.json()
        except Exception:
            return SLAPullResponse(session_key=payload.session_key, found=False)
        if not data:
            return SLAPullResponse(session_key=payload.session_key, found=False)
        return SLAPullResponse(
            session_key=payload.session_key,
            sla_therapist=data.get("SLA_T"),
            sla_patrick=data.get("SLA_P"),
            found=True,
            timestamp=data.get("timestamp"),
        )
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{type(e).__name__}: {e}")
