from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from models.lead import LeadPushRequest, LeadPullRequest, LeadPullResponse
from services.make_service import MakeService, MakeServiceError
from dependencies import get_make_service, verify_token

router = APIRouter(prefix="/lead", tags=["Lead"])


@router.post("/push", summary="Push lead slot state to Make.com → svlbh-v2", status_code=200)
async def push_lead(
    payload: LeadPushRequest,
    _: None = Depends(verify_token),
    make: MakeService = Depends(get_make_service),
) -> dict:
    try:
        result = await make.push_lead(payload)
        return {"success": True, "shamaneCode": payload.shamane_code, **result}
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{type(e).__name__}: {e}")


@router.post("/pull", summary="Fetch lead state from Make.com by shamaneCode", response_model=LeadPullResponse)
async def pull_lead(
    payload: LeadPullRequest,
    _: None = Depends(verify_token),
    make: MakeService = Depends(get_make_service),
) -> LeadPullResponse:
    try:
        return await make.pull_lead(payload.shamane_code)
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{type(e).__name__}: {e}")
