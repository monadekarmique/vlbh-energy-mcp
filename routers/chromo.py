"""Chromotherapy router — iTherapeut 6.0 (Plan 59/179).

Endpoints:
  POST   /chromo              → create chromo session
  GET    /chromo              → list chromo sessions
  GET    /chromo/{id}         → get one
  PUT    /chromo/{id}         → update
  GET    /chromo/reference    → full meridien/color/element mapping
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies import verify_token
from models.chromo import (
    ChromoReferenceResponse,
    ChromoSession,
    ChromoSessionCreate,
    ChromoSessionList,
    ChromoSessionUpdate,
    ColorGel,
    Element,
    Meridien,
    MeridienReference,
    MERIDIEN_ELEMENT_MAP,
)
from services.supabase_client import get_supabase

router = APIRouter(
    prefix="/chromo",
    tags=["Chromotherapy"],
    dependencies=[Depends(verify_token)],
)

TABLE = "chromo_sessions"


@router.get("/reference", response_model=ChromoReferenceResponse)
async def get_chromo_reference():
    """Return the full meridien → element → color gel reference table.

    Used by the frontend to populate chromo prescription UI.
    """
    meridiens = [
        MeridienReference(meridien=k, **v)
        for k, v in MERIDIEN_ELEMENT_MAP.items()
    ]
    return ChromoReferenceResponse(
        meridiens=meridiens,
        color_gels=[c.value for c in ColorGel],
        elements=[e.value for e in Element],
    )


@router.post("", response_model=ChromoSession, status_code=status.HTTP_201_CREATED)
async def create_chromo_session(body: ChromoSessionCreate):
    """Create a new chromotherapy session record."""
    sb = get_supabase()
    data = body.model_dump(mode="json", exclude_none=True)
    result = sb.table(TABLE).insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create chromo session")
    return result.data[0]


@router.get("", response_model=ChromoSessionList)
async def list_chromo_sessions(
    patient_id: UUID | None = Query(None),
    therapy_session_id: UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List chromotherapy sessions with optional filters."""
    sb = get_supabase()
    query = sb.table(TABLE).select("*", count="exact")
    if patient_id:
        query = query.eq("patient_id", str(patient_id))
    if therapy_session_id:
        query = query.eq("therapy_session_id", str(therapy_session_id))
    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
    result = query.execute()
    return ChromoSessionList(sessions=result.data or [], total=result.count or 0)


@router.get("/{chromo_id}", response_model=ChromoSession)
async def get_chromo_session(chromo_id: UUID):
    """Get a single chromo session by ID."""
    sb = get_supabase()
    result = sb.table(TABLE).select("*").eq("id", str(chromo_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Chromo session not found")
    return result.data[0]


@router.put("/{chromo_id}", response_model=ChromoSession)
async def update_chromo_session(chromo_id: UUID, body: ChromoSessionUpdate):
    """Update a chromo session."""
    sb = get_supabase()
    existing = sb.table(TABLE).select("id").eq("id", str(chromo_id)).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Chromo session not found")

    data = body.model_dump(mode="json", exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = sb.table(TABLE).update(data).eq("id", str(chromo_id)).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update chromo session")
    return result.data[0]
