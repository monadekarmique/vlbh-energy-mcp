"""Pydantic models for Lead Pipeline — iTherapeut 6.0 (Plan 179).

Table: pipeline_leads (Supabase PostgreSQL)
CRM pipeline for tracking patient acquisition funnel.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    """Stages of the patient acquisition pipeline."""
    NEW = "new"                     # Premier contact / demande
    CONTACTED = "contacted"         # Contact établi
    SCHEDULED = "scheduled"         # RDV planifié
    IN_TREATMENT = "in_treatment"   # En traitement actif
    COMPLETED = "completed"         # Parcours terminé
    LOST = "lost"                   # Perdu / pas donné suite


class LeadSource(str, Enum):
    """How the lead found us."""
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    CLOSE_CRM = "close_crm"        # Synced from Close CRM
    PHONE = "phone"
    OTHER = "other"


class PipelineLeadBase(BaseModel):
    """Core fields for a pipeline lead."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    stage: PipelineStage = Field(default=PipelineStage.NEW)
    source: LeadSource = Field(default=LeadSource.OTHER)
    notes: Optional[str] = None
    # Link to patient once converted
    patient_id: Optional[UUID] = Field(None, description="Linked patient (once converted)")
    # Close CRM sync
    close_lead_id: Optional[str] = Field(None, max_length=50,
                                          description="Close CRM lead ID for sync")
    # Priority (1=hot, 2=warm, 3=cold)
    priority: int = Field(default=3, ge=1, le=3)
    # Next action
    next_action: Optional[str] = Field(None, max_length=300)
    next_action_date: Optional[datetime] = None


class PipelineLeadCreate(PipelineLeadBase):
    """Body for POST /pipeline/leads."""
    pass


class PipelineLeadUpdate(BaseModel):
    """Body for PUT /pipeline/leads/{id} — partial update."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    stage: Optional[PipelineStage] = None
    source: Optional[LeadSource] = None
    notes: Optional[str] = None
    patient_id: Optional[UUID] = None
    close_lead_id: Optional[str] = Field(None, max_length=50)
    priority: Optional[int] = Field(None, ge=1, le=3)
    next_action: Optional[str] = Field(None, max_length=300)
    next_action_date: Optional[datetime] = None


class PipelineLead(PipelineLeadBase):
    """Full pipeline lead record returned by the API."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PipelineView(BaseModel):
    """Response for GET /pipeline/leads — grouped by stage."""
    leads: list[PipelineLead]
    total: int
    # Counts per stage for kanban board
    stage_counts: dict[str, int] = Field(default_factory=dict)
