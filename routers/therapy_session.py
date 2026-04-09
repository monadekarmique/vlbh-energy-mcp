"""Therapy Session CRUD router — iTherapeut 6.0 (Plan 59).

Endpoints:
  POST   /therapy-sessions          → create
  GET    /therapy-sessions          → list (with filters)
  GET    /therapy-sessions/{id}     → get one
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies import verify_token
from models.therapy_session import (
    TherapySession,
    TherapySessionCreate,
    TherapySessionList,
)
from services.supabase_client import get_supabase

router = APIRouter(
    prefix="/therapy-sessions",
    tags=["Therapy Sessions"],
    dependencies=[Depends(verify_token)],
)

TABLE = "therapy_sessions"


@router.post("", response_model=TherapySession, status_code=status.HTTP_201_CREATED)
async def create_therapy_session(body: TherapySessionCreate):
    """Create a new therapy session."""
    sb = get_supabase()
    data = body.model_dump(mode="json", exclude_none=True)
    # Convert Decimal to float for JSON serialization
    for key in ("tarif_amount", "sla_score", "slsa_score", "slm_score"):
        if key in data and data[key] is not None:
            data[key] = float(data[key])
    result = sb.table(TABLE).insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create therapy session")
    return result.data[0]


@router.get("", response_model=TherapySessionList)
async def list_therapy_sessions(
    patient_id: UUID | None = Query(None, description="Filter by patient"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List therapy sessions with optional patient filter and pagination."""
    sb = get_supabase()
    query = sb.table(TABLE).select("*", count="exact")
    if patient_id:
        query = query.eq("patient_id", str(patient_id))
    query = query.order("date", desc=True).range(offset, offset + limit - 1)
    result = query.execute()
    return TherapySessionList(sessions=result.data, total=result.count or 0)


@router.get("/{session_id}", response_model=TherapySession)
async def get_therapy_session(session_id: UUID):
    """Get a single therapy session by ID."""
    sb = get_supabase()
    result = sb.table(TABLE).select("*").eq("id", str(session_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Therapy session not found")
    return result.data[0]
