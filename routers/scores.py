"""Scores de Lumière CRUD router — iTherapeut 6.0 (Plan 59).

Endpoints:
  POST   /scores                     → create (record scores for a session)
  GET    /scores                     → list (filter by patient/session)
  GET    /scores/{id}                → get one
  PUT    /scores/{id}                → update
  GET    /scores/trend/{patient_id}  → score evolution over time
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies import verify_token
from models.scores import (
    SessionScores,
    SessionScoresCreate,
    SessionScoresList,
    SessionScoresUpdate,
    ScoreTrend,
    ScoreTrendResponse,
)
from services.supabase_client import get_supabase

router = APIRouter(
    prefix="/scores",
    tags=["Scores de Lumière"],
    dependencies=[Depends(verify_token)],
)

TABLE = "session_scores"


@router.post("", response_model=SessionScores, status_code=status.HTTP_201_CREATED)
async def create_scores(body: SessionScoresCreate):
    """Record Scores de Lumière for a therapy session."""
    sb = get_supabase()
    data = body.model_dump(mode="json", exclude_none=True)
    result = sb.table(TABLE).insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create scores")
    return result.data[0]


@router.get("", response_model=SessionScoresList)
async def list_scores(
    patient_id: UUID | None = Query(None),
    therapy_session_id: UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List session scores with optional filters."""
    sb = get_supabase()
    query = sb.table(TABLE).select("*", count="exact")
    if patient_id:
        query = query.eq("patient_id", str(patient_id))
    if therapy_session_id:
        query = query.eq("therapy_session_id", str(therapy_session_id))
    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
    result = query.execute()
    return SessionScoresList(scores=result.data, total=result.count or 0)


@router.get("/trend/{patient_id}", response_model=ScoreTrendResponse)
async def get_score_trend(patient_id: UUID):
    """Get score evolution over time for a patient."""
    sb = get_supabase()
    result = (
        sb.table(TABLE)
        .select("created_at, patient_scores")
        .eq("patient_id", str(patient_id))
        .order("created_at", desc=False)
        .execute()
    )

    data_points = []
    for row in result.data:
        ps = row.get("patient_scores", {}) or {}
        data_points.append(ScoreTrend(
            date=row["created_at"],
            sla=ps.get("sla"),
            slsa=ps.get("slsa"),
            slpmo=ps.get("slpmo"),
            slm=ps.get("slm"),
        ))

    # Summary stats
    sla_first = data_points[0].sla if data_points and data_points[0].sla else None
    sla_last = data_points[-1].sla if data_points and data_points[-1].sla else None
    sla_delta = None
    if sla_first is not None and sla_last is not None:
        sla_delta = sla_last - sla_first

    return ScoreTrendResponse(
        patient_id=patient_id,
        data_points=data_points,
        total_sessions=len(data_points),
        sla_first=sla_first,
        sla_last=sla_last,
        sla_delta=sla_delta,
    )


@router.get("/{score_id}", response_model=SessionScores)
async def get_scores(score_id: UUID):
    """Get a single session scores record by ID."""
    sb = get_supabase()
    result = sb.table(TABLE).select("*").eq("id", str(score_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Scores not found")
    return result.data[0]


@router.put("/{score_id}", response_model=SessionScores)
async def update_scores(score_id: UUID, body: SessionScoresUpdate):
    """Update session scores (partial update)."""
    sb = get_supabase()
    data = body.model_dump(mode="json", exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = (
        sb.table(TABLE)
        .update(data)
        .eq("id", str(score_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Scores not found")
    return result.data[0]
