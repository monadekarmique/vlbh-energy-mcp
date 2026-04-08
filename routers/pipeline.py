"""Lead Pipeline router — iTherapeut 6.0 (Plan 179).

Endpoints:
  POST   /pipeline/leads          → create lead
  GET    /pipeline/leads          → list/filter (kanban view)
  GET    /pipeline/leads/{id}     → get one
  PUT    /pipeline/leads/{id}     → update (move stage, edit)
  DELETE /pipeline/leads/{id}     → soft-delete
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies import verify_token
from models.pipeline import (
    PipelineLead,
    PipelineLeadCreate,
    PipelineLeadUpdate,
    PipelineStage,
    PipelineView,
)
from services.supabase_client import get_supabase

router = APIRouter(
    prefix="/pipeline",
    tags=["Pipeline CRM"],
    dependencies=[Depends(verify_token)],
)

TABLE = "pipeline_leads"


@router.post("/leads", response_model=PipelineLead, status_code=status.HTTP_201_CREATED)
async def create_pipeline_lead(body: PipelineLeadCreate):
    """Create a new lead in the pipeline."""
    sb = get_supabase()
    data = body.model_dump(mode="json", exclude_none=True)
    result = sb.table(TABLE).insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create pipeline lead")
    return result.data[0]


@router.get("/leads", response_model=PipelineView)
async def list_pipeline_leads(
    stage: PipelineStage | None = Query(None, description="Filter by stage"),
    priority: int | None = Query(None, ge=1, le=3, description="Filter by priority"),
    search: str | None = Query(None, max_length=100, description="Search name/email"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List pipeline leads with optional filters. Returns stage counts for kanban."""
    sb = get_supabase()

    # Main query
    query = sb.table(TABLE).select("*", count="exact")
    if stage:
        query = query.eq("stage", stage.value)
    if priority:
        query = query.eq("priority", priority)
    if search:
        # Search on first_name, last_name, or email
        query = query.or_(
            f"first_name.ilike.%{search}%,"
            f"last_name.ilike.%{search}%,"
            f"email.ilike.%{search}%"
        )
    query = query.order("priority", desc=False).order("updated_at", desc=True)
    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    # Stage counts (always unfiltered for kanban board)
    stage_counts = {}
    for s in PipelineStage:
        count_result = (
            sb.table(TABLE)
            .select("id", count="exact")
            .eq("stage", s.value)
            .execute()
        )
        stage_counts[s.value] = count_result.count or 0

    return PipelineView(
        leads=result.data or [],
        total=result.count or 0,
        stage_counts=stage_counts,
    )


@router.get("/leads/{lead_id}", response_model=PipelineLead)
async def get_pipeline_lead(lead_id: UUID):
    """Get a single pipeline lead by ID."""
    sb = get_supabase()
    result = sb.table(TABLE).select("*").eq("id", str(lead_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline lead not found")
    return result.data[0]


@router.put("/leads/{lead_id}", response_model=PipelineLead)
async def update_pipeline_lead(lead_id: UUID, body: PipelineLeadUpdate):
    """Update a pipeline lead (move stage, edit details)."""
    sb = get_supabase()

    # Verify exists
    existing = sb.table(TABLE).select("id").eq("id", str(lead_id)).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Pipeline lead not found")

    data = body.model_dump(mode="json", exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = sb.table(TABLE).update(data).eq("id", str(lead_id)).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update pipeline lead")
    return result.data[0]


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline_lead(lead_id: UUID):
    """Delete a pipeline lead."""
    sb = get_supabase()
    existing = sb.table(TABLE).select("id").eq("id", str(lead_id)).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Pipeline lead not found")
    sb.table(TABLE).delete().eq("id", str(lead_id)).execute()
