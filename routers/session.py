from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from models.session import SessionPushRequest, SessionPullRequest, SessionPullResponse
from services.make_service import MakeService, MakeServiceError
from dependencies import get_make_service, verify_token

router = APIRouter(prefix="/session", tags=["Session"])


@router.post("/push", summary="Push session metadata to Make.com → svlbh-v2", status_code=200)
async def push_session(
    payload: SessionPushRequest,
    _: None = Depends(verify_token),
    make: MakeService = Depends(get_make_service),
) -> dict:
    try:
        result = await make.push_session(payload)
        return {"success": True, "sessionKey": payload.session_key, **result}
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{type(e).__name__}: {e}")


@router.post("/pull", summary="Fetch session metadata from Make.com by sessionKey", response_model=SessionPullResponse)
async def pull_session(
    payload: SessionPullRequest,
    _: None = Depends(verify_token),
    make: MakeService = Depends(get_make_service),
) -> SessionPullResponse:
    try:
        return await make.pull_session(payload.session_key)
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{type(e).__name__}: {e}")
