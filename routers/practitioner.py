"""Practitioner CRUD router — iTherapeut 6.0.

Endpoints:
  POST   /practitioners          → create
  GET    /practitioners          → list (with pagination + filters)
  GET    /practitioners/{id}     → get one
  PUT    /practitioners/{id}     → update

Each practitioner has their own billing profile (IBAN, RCC, address).
Cabinet Pro (Plan 179) supports multiple practitioners via cabinet_id.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies import verify_token
from models.practitioner import (
    Practitioner,
    PractitionerCreate,
    PractitionerList,
    PractitionerUpdate,
    PractitionerStatus,
)
from services.supabase_client import get_supabase

router = APIRouter(
    prefix="/practitioners",
    tags=["Practitioners"],
    dependencies=[Depends(verify_token)],
)

TABLE = "practitioners"


@router.post("", response_model=Practitioner, status_code=status.HTTP_201_CREATED)
async def create_practitioner(body: PractitionerCreate):
    """Create a new practitioner profile."""
    sb = get_supabase()
    data = body.model_dump(mode="json", exclude_none=True)
    result = sb.table(TABLE).insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create practitioner")
    return result.data[0]


@router.get("", response_model=PractitionerList)
async def list_practitioners(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = Query(None, description="Search by name"),
    practitioner_status: PractitionerStatus | None = Query(None, alias="status"),
    cabinet_id: UUID | None = Query(None, description="Filter by cabinet"),
):
    """List practitioners with optional search and filters."""
    sb = get_supabase()
    query = sb.table(TABLE).select("*", count="exact")
    if search:
        query = query.or_(
            f"first_name.ilike.%{search}%,last_name.ilike.%{search}%"
        )
    if practitioner_status:
        query = query.eq("status", practitioner_status.value)
    if cabinet_id:
        query = query.eq("cabinet_id", str(cabinet_id))
    query = query.order("last_name").range(offset, offset + limit - 1)
    result = query.execute()
    return PractitionerList(practitioners=result.data, total=result.count or 0)


@router.get("/{practitioner_id}", response_model=Practitioner)
async def get_practitioner(practitioner_id: UUID):
    """Get a single practitioner by ID."""
    sb = get_supabase()
    result = sb.table(TABLE).select("*").eq("id", str(practitioner_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    return result.data[0]


@router.put("/{practitioner_id}", response_model=Practitioner)
async def update_practitioner(practitioner_id: UUID, body: PractitionerUpdate):
    """Update an existing practitioner profile."""
    sb = get_supabase()
    data = body.model_dump(mode="json", exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = (
        sb.table(TABLE)
        .update(data)
        .eq("id", str(practitioner_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    return result.data[0]
