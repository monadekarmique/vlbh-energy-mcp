"""Pydantic models for Tore Sessions — iTherapeut 6.0 (Plan 179).

Table: tore_sessions (Supabase PostgreSQL)
Historical CRUD storage of tore measurements per therapy session.
Complements the existing /tore/push and /tore/pull Make.com sync endpoints.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ToreSnapshot(BaseModel):
    """Snapshot of tore measurements at a point in time.
    Mirrors the key fields from StockageEnergetique (models/tore.py).
    """
    # Champ toroïdal
    tore_intensite: Optional[int] = Field(None, ge=0, le=100_000)
    tore_coherence: Optional[int] = Field(None, ge=0, le=100)
    tore_frequence: Optional[float] = Field(None, ge=0.01, le=1000)
    tore_phase: Optional[str] = Field(None, pattern=r"^(REPOS|CHARGE|DECHARGE|EQUILIBRE)$")
    # Glycémie
    glyc_index: Optional[int] = Field(None, ge=0, le=500)
    glyc_balance: Optional[int] = Field(None, ge=0, le=100)
    glyc_resistance: Optional[int] = Field(None, ge=0, le=1000)
    # Sclérose
    scl_score: Optional[int] = Field(None, ge=0, le=1000)
    scl_elasticite: Optional[int] = Field(None, ge=0, le=100)
    # Couplage
    cp_correlation_tg: Optional[int] = Field(None, ge=-100, le=100)
    cp_correlation_ts: Optional[int] = Field(None, ge=-100, le=100)
    cp_score_couplage: Optional[int] = Field(None, ge=0, le=10_000)
    cp_phase_couplage: Optional[str] = Field(None,
        pattern=r"^(SYNERGIQUE|ANTAGONISTE|NEUTRE|TRANSITOIRE)$")
    # Stockage global
    stockage_niveau: Optional[int] = Field(None, ge=0, le=100_000)
    stockage_capacite: Optional[int] = Field(None, ge=0, le=100_000)
    stockage_rendement: Optional[float] = Field(None, ge=0, le=100)


class ToreSessionBase(BaseModel):
    """Tore measurement linked to a therapy session."""
    therapy_session_id: UUID
    patient_id: UUID
    before: ToreSnapshot = Field(..., description="Mesure avant traitement")
    after: Optional[ToreSnapshot] = Field(None, description="Mesure après traitement")
    measurement_notes: Optional[str] = None


class ToreSessionCreate(ToreSessionBase):
    """Body for POST /tore-sessions."""
    pass


class ToreSessionUpdate(BaseModel):
    """Body for PUT /tore-sessions/{id} — partial update."""
    before: Optional[ToreSnapshot] = None
    after: Optional[ToreSnapshot] = None
    measurement_notes: Optional[str] = None


class ToreSession(ToreSessionBase):
    """Full tore session record returned by the API."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    # Computed delta
    rendement_delta: Optional[float] = Field(None,
        description="Différence rendement after - before")

    model_config = {"from_attributes": True}


class ToreSessionList(BaseModel):
    """Response for GET /tore-sessions."""
    sessions: list[ToreSession]
    total: int
