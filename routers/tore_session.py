"""Tore Sessions CRUD router — iTherapeut 6.0 (Plan 179).

Historical storage of tore measurements in Supabase.
Complements the existing /tore/push and /tore/pull Make.com sync.

Endpoints:
  POST   /tore-sessions          → create
  GET    /tore-sessions          → list
  GET    /tore-sessions/{id}     → get one
  PUT    /tore-sessions/{id}     → update (add 'after' measurement)
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies import verify_token
from models.tore_session import (
    ToreSession,
    ToreSessionCreate,
    ToreSessionList,
    ToreSessionUpdate,
)
from services.supabase_client import get_supabase

router = APIRouter(
    prefix="/tore-sessions",
    tags=["Tore Sessions"],
    dependencies=[Depends(verify_token)],
)

TABLE = "tore_sessions"


def _compute_delta(record: dict) -> dict:
    """Add rendement_delta to a tore session record."""
    before = record.get("before") or {}
    after = record.get("after") or {}
    b_rend = before.get("stockage_rendement")
    a_rend = after.get("stockage_rendement")
    if b_rend is not None and a_rend is not None:
        record["rendement_delta"] = round(a_rend - b_rend, 2)
    else:
        record["rendement_delta"] = None
    return record


@router.post("", response_model=ToreSession, status_code=status.HTTP_201_CREATED)
async def create_tore_session(body: ToreSessionCreate):
    """Create a new tore measurement session (before + optionally after)."""
    sb = get_supabase()
    data = body.model_dump(mode="json", exclude_none=True)
    result = sb.table(TABLE).insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create tore session")
    return _compute_delta(result.data[0])


@router.get("", response_model=ToreSessionList)
async def list_tore_sessions(
    patient_id: UUID | None = Query(None),
    therapy_session_id: UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List tore sessions with optional filters."""
    sb = get_supabase()
    query = sb.table(TABLE).select("*", count="exact")
    if patient_id:
        query = query.eq("patient_id", str(patient_id))
    if therapy_session_id:
        query = query.eq("therapy_session_id", str(therapy_session_id))
    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
    result = query.execute()
    sessions = [_compute_delta(r) for r in (result.data or [])]
    return ToreSessionList(sessions=sessions, total=result.count or 0)


@router.get("/{session_id}", response_model=ToreSession)
async def get_tore_session(session_id: UUID):
    """Get a single tore session by ID."""
    sb = get_supabase()
    result = sb.table(TABLE).select("*").eq("id", str(session_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tore session not found")
    return _compute_delta(result.data[0])


@router.put("/{session_id}", response_model=ToreSession)
async def update_tore_session(session_id: UUID, body: ToreSessionUpdate):
    """Update a tore session (typically to add 'after' measurement)."""
    sb = get_supabase()
    existing = sb.table(TABLE).select("id").eq("id", str(session_id)).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Tore session not found")

    data = body.model_dump(mode="json", exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = sb.table(TABLE).update(data).eq("id", str(session_id)).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update tore session")
    return _compute_delta(result.data[0])
