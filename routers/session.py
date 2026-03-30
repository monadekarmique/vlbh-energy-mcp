from __future__ import annotations
import time
from fastapi import APIRouter, Depends, HTTPException, status
from models.session import SessionPushRequest, SessionPullRequest, SessionPullResponse
from services.make_service import MakeServiceError
from dependencies import get_make_service, verify_token

router = APIRouter(prefix="/session", tags=["Session"])

DATASTORE_ID = 155674


@router.post("/push", summary="Push session metadata to Make.com → svlbh-v2", status_code=200)
async def push_session(
    payload: SessionPushRequest,
    _: None = Depends(verify_token),
    make=Depends(get_make_service),
) -> dict:
    body = {
        "sessionKey": payload.session_key,
        "datastoreId": DATASTORE_ID,
        "module": "SESSION",
        "patientId": payload.patient_id,
        "sessionNum": payload.session_num,
        "programCode": payload.program_code,
        "practitionerCode": payload.practitioner_code,
        "therapistName": payload.therapist_name,
        "status": payload.status,
        "eventCount": payload.event_count,
        "liberatedCount": payload.liberated_count,
        "platform": payload.platform,
        "timestamp": int(time.time() * 1000),
    }
    try:
        resp = await make._client.post(make._push_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make push session failed: {resp.text}")
        return {"success": True, "sessionKey": payload.session_key, "make_status": resp.status_code}
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{type(e).__name__}: {e}")


@router.post("/pull", summary="Fetch session metadata from Make.com by sessionKey", response_model=SessionPullResponse)
async def pull_session(
    payload: SessionPullRequest,
    _: None = Depends(verify_token),
    make=Depends(get_make_service),
) -> SessionPullResponse:
    body = {
        "sessionKey": payload.session_key,
        "datastoreId": DATASTORE_ID,
        "module": "SESSION",
    }
    try:
        resp = await make._client.post(make._pull_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make pull session failed: {resp.text}")
        raw = resp.text.strip()
        if not raw:
            return SessionPullResponse(session_key=payload.session_key, found=False)
        try:
            data = resp.json()
        except Exception:
            return SessionPullResponse(session_key=payload.session_key, found=False)
        if not data:
            return SessionPullResponse(session_key=payload.session_key, found=False)
        return SessionPullResponse(
            session_key=payload.session_key,
            patient_id=data.get("patientId"),
            session_num=data.get("sessionNum"),
            program_code=data.get("programCode"),
            practitioner_code=data.get("practitionerCode"),
            therapist_name=data.get("therapistName"),
            status=data.get("status"),
            event_count=data.get("eventCount"),
            liberated_count=data.get("liberatedCount"),
            found=True,
            timestamp=data.get("timestamp"),
        )
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{type(e).__name__}: {e}")
