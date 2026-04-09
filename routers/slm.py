from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from models.slm import SLMPushRequest, SLMPullRequest, SLMPullResponse
from services.make_service import MakeService, MakeServiceError
from dependencies import get_make_service, verify_token

router = APIRouter(prefix="/slm", tags=["SLM"])


@router.post(
    "/push",
    summary="Push SLM scores to Make.com → svlbh-v2",
    status_code=status.HTTP_200_OK,
)
async def push_slm(
    payload: SLMPushRequest,
    _: None = Depends(verify_token),
    make: MakeService = Depends(get_make_service),
) -> dict:
    """
    Forward SLM scores (Thérapeute + Patrick) to Make.com datastore svlbh-v2.
    SLSA is auto-calculated server-side if SA1–SA5 components are provided.
    """
    try:
        result = await make.push_slm(payload)
        return {"success": True, "sessionKey": payload.session_key, **result}
    except MakeServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{type(e).__name__}: {e}"
        )


@router.post(
    "/pull",
    summary="Fetch SLM scores from Make.com → svlbh-v2 by sessionKey",
    response_model=SLMPullResponse,
)
async def pull_slm(
    payload: SLMPullRequest,
    _: None = Depends(verify_token),
    make: MakeService = Depends(get_make_service),
) -> SLMPullResponse:
    """
    Retrieve previously stored SLM scores by session key.
    Session key format: PP-patientId-sessionNum-praticienCode
    """
    try:
        return await make.pull_slm(payload.session_key)
    except MakeServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{type(e).__name__}: {e}"
        )
