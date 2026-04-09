"""Patient CRUD router — iTherapeut 6.0 (Plan 59).

Endpoints:
  POST   /patients          → create
  GET    /patients          → list (with pagination)
  GET    /patients/{id}     → get one
  PUT    /patients/{id}     → update
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies import verify_token
from models.patient import Patient, PatientCreate, PatientList, PatientUpdate
from services.supabase_client import get_supabase

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
    dependencies=[Depends(verify_token)],
)

TABLE = "patients"


@router.post("", response_model=Patient, status_code=status.HTTP_201_CREATED)
async def create_patient(body: PatientCreate):
    """Create a new patient record."""
    sb = get_supabase()
    data = body.model_dump(mode="json", exclude_none=True)
    result = sb.table(TABLE).insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create patient")
    return result.data[0]


@router.get("", response_model=PatientList)
async def list_patients(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = Query(None, description="Search by name"),
):
    """List patients with optional search and pagination."""
    sb = get_supabase()
    query = sb.table(TABLE).select("*", count="exact")
    if search:
        # ilike search on first_name or last_name
        query = query.or_(
            f"first_name.ilike.%{search}%,last_name.ilike.%{search}%"
        )
    query = query.order("last_name").range(offset, offset + limit - 1)
    result = query.execute()
    return PatientList(patients=result.data, total=result.count or 0)


@router.get("/{patient_id}", response_model=Patient)
async def get_patient(patient_id: UUID):
    """Get a single patient by ID."""
    sb = get_supabase()
    result = sb.table(TABLE).select("*").eq("id", str(patient_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Patient not found")
    return result.data[0]


@router.put("/{patient_id}", response_model=Patient)
async def update_patient(patient_id: UUID, body: PatientUpdate):
    """Update an existing patient."""
    sb = get_supabase()
    data = body.model_dump(mode="json", exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = (
        sb.table(TABLE)
        .update(data)
        .eq("id", str(patient_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Patient not found")
    return result.data[0]
