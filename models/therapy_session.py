"""Pydantic models for Therapy Sessions — iTherapeut 6.0 (Plan 59).

Table: therapy_sessions (Supabase PostgreSQL)
NB: Named 'therapy_session' to avoid collision with existing routers/session.py
which handles SLM session sync via Make.com.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TherapySessionBase(BaseModel):
    patient_id: UUID
    date: datetime
    duration_minutes: int = Field(..., ge=15, le=480)
    session_type: str = Field(..., max_length=100)
    tarif_code: Optional[str] = Field(None, max_length=10)
    tarif_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    sla_score: Optional[Decimal] = Field(None, ge=0, le=100)
    slsa_score: Optional[Decimal] = Field(None, ge=0, le=100)
    slm_score: Optional[Decimal] = Field(None, ge=0, le=100)



class TherapySessionCreate(TherapySessionBase):
    """Body for POST /therapy-sessions."""
    pass


class TherapySessionUpdate(BaseModel):
    """Body for PUT /therapy-sessions/{id} — all fields optional."""
    patient_id: Optional[UUID] = None
    date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    session_type: Optional[str] = Field(None, max_length=100)
    tarif_code: Optional[str] = Field(None, max_length=10)
    tarif_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    sla_score: Optional[Decimal] = Field(None, ge=0, le=100)
    slsa_score: Optional[Decimal] = Field(None, ge=0, le=100)
    slm_score: Optional[Decimal] = Field(None, ge=0, le=100)


class TherapySession(TherapySessionBase):
    """Full therapy session record returned by the API."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TherapySessionList(BaseModel):
    """Response for GET /therapy-sessions."""
    sessions: list[TherapySession]
    total: int
