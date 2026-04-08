"""Rose des Vents diagnostic router — iTherapeut 6.0 (Plan 59).

Endpoints:
  POST   /rose-des-vents              → create diagnostic
  GET    /rose-des-vents              → list (filter by patient/session)
  GET    /rose-des-vents/{id}         → get one
  PUT    /rose-des-vents/{id}         → update
  GET    /rose-des-vents/reference    → static reference table (12 directions)
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies import verify_token
from models.rose_des_vents import (
    RoseDesVents,
    RoseDesVentsCreate,
    RoseDesVentsList,
    RoseDesVentsUpdate,
    DirectionInfo,
    DirectionReference,
    DIRECTION_MAP,
    RdvDirection,
)
from services.supabase_client import get_supabase

router = APIRouter(
    prefix="/rose-des-vents",
    tags=["Rose des Vents"],
    dependencies=[Depends(verify_token)],
)

TABLE = "rose_des_vents"


@router.get("/reference", response_model=DirectionReference,
            summary="Table de référence des 12+1 directions")
async def get_reference():
    """Return the static reference table for all 13 compass directions."""
    directions = []
    for direction, info in DIRECTION_MAP.items():
        directions.append(DirectionInfo(
            direction=direction,
            angle=info["angle"],
            quadrant=info.get("quadrant"),
            plan=info.get("plan"),
            domaine=info["domaine"],
            transgression=info["transgression"],
            association=info["association"],
        ))
    return DirectionReference(directions=directions)


@router.post("", response_model=RoseDesVents, status_code=status.HTTP_201_CREATED)
async def create_diagnostic(body: RoseDesVentsCreate):
    """Record a Rose des Vents diagnostic for a therapy session."""
    sb = get_supabase()
    data = body.model_dump(mode="json", exclude_none=True)
    result = sb.table(TABLE).insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create diagnostic")
    return result.data[0]


@router.get("", response_model=RoseDesVentsList)
async def list_diagnostics(
    patient_id: UUID | None = Query(None),
    therapy_session_id: UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List Rose des Vents diagnostics with optional filters."""
    sb = get_supabase()
    query = sb.table(TABLE).select("*", count="exact")
    if patient_id:
        query = query.eq("patient_id", str(patient_id))
    if therapy_session_id:
        query = query.eq("therapy_session_id", str(therapy_session_id))
    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
    result = query.execute()
    return RoseDesVentsList(diagnostics=result.data, total=result.count or 0)


@router.get("/{diagnostic_id}", response_model=RoseDesVents)
async def get_diagnostic(diagnostic_id: UUID):
    """Get a single Rose des Vents diagnostic by ID."""
    sb = get_supabase()
    result = sb.table(TABLE).select("*").eq("id", str(diagnostic_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    return result.data[0]


@router.put("/{diagnostic_id}", response_model=RoseDesVents)
async def update_diagnostic(diagnostic_id: UUID, body: RoseDesVentsUpdate):
    """Update a Rose des Vents diagnostic (partial update)."""
    sb = get_supabase()
    data = body.model_dump(mode="json", exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = (
        sb.table(TABLE)
        .update(data)
        .eq("id", str(diagnostic_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    return result.data[0]
