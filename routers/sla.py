from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from models.sla import SLAPushRequest, SLAPullRequest, SLAPullResponse
from services.make_service import MakeService, MakeServiceError
from dependencies import get_make_service, verify_token

router = APIRouter(prefix="/sla", tags=["SLA"])


@router.post("/push", summary="Push SLA score to Make.com → svlbh-v2", status_code=200)
async def push_sla(
    payload: SLAPushRequest,
    _: None = Depends(verify_token),
    make: MakeService = Depends(get_make_service),
) -> dict:
    try:
        result = await make.push_sla(payload)
        return {"success": True, "sessionKey": payload.session_key, **result}
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{type(e).__name__}: {e}")


@router.post("/pull", summary="Fetch SLA score from Make.com by sessionKey", response_model=SLAPullResponse)
async def pull_sla(
    payload: SLAPullRequest,
    _: None = Depends(verify_token),
    make: MakeService = Depends(get_make_service),
) -> SLAPullResponse:
    try:
        return await make.pull_sla(payload.session_key)
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{type(e).__name__}: {e}")
