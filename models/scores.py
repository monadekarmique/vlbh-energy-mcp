"""Pydantic models for Scores de Lumière — iTherapeut 6.0 (Plan 59).

Table: session_scores (Supabase PostgreSQL)

This model stores per-session Score de Lumière measurements for
iTherapeut cabinet management. It extends the existing ScoresLumiere
model (models/slm.py) used by the Make.com sync endpoints, adding:
  - SLPMO (Score de Lumière du Projet Monadique Originel)
  - Per-session storage with patient/session FK
  - Therapist self-scores (miroir protocol)
  - Historical tracking for trend analysis

NB: The existing /slm/push and /sla/push endpoints are NOT modified.
    This is a NEW table for the iTherapeut cabinet context.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Score de Lumière — per-session snapshot
# ---------------------------------------------------------------------------

class ScoreSnapshot(BaseModel):
    """A single Score de Lumière measurement at a point in time.

    Ranges (percentages unless noted):
      SLA:   0–350%   Score de Lumière de l'Âme
      SLSA:  0–50000% Score de Lumière de la Sur-Âme (S1–S5)
      SLPMO: 0–100%   Score de Lumière du Projet Monadique Originel
      SLM:   0–100000 Score de Lumière de la Monade
    """
    sla: Optional[Decimal] = Field(None, ge=0, le=350,
                                    description="Score de Lumière de l'Âme (%)")
    slsa: Optional[Decimal] = Field(None, ge=0, le=50000,
                                     description="Score de Lumière de la Sur-Âme (%)")
    slsa_s1: Optional[Decimal] = Field(None, ge=0, le=50000,
                                        description="SLSA Corps Atmique (S1)")
    slsa_s2: Optional[Decimal] = Field(None, ge=0, le=50000,
                                        description="SLSA Corps Monadique (S2)")
    slsa_s3: Optional[Decimal] = Field(None, ge=0, le=50000,
                                        description="SLSA Corps Logoïque (S3)")
    slsa_s4: Optional[Decimal] = Field(None, ge=0, le=50000,
                                        description="SLSA S4")
    slsa_s5: Optional[Decimal] = Field(None, ge=0, le=50000,
                                        description="SLSA S5")
    slpmo: Optional[Decimal] = Field(None, ge=0, le=100,
                                      description="Score de Lumière du Projet Monadique Originel (%)")
    slm: Optional[Decimal] = Field(None, ge=0, le=100000,
                                    description="Score de Lumière de la Monade")
    tot_slm: Optional[Decimal] = Field(None, ge=0, le=1000,
                                        description="Total SLM (%)")

    @model_validator(mode="after")
    def recalc_slsa(self) -> "ScoreSnapshot":
        """Auto-calculate SLSA from S1–S5 if components are provided."""
        components = [self.slsa_s1, self.slsa_s2, self.slsa_s3,
                      self.slsa_s4, self.slsa_s5]
        if any(c is not None for c in components):
            self.slsa = sum(c or Decimal("0") for c in components)
        return self


# ---------------------------------------------------------------------------
# Session Scores — links scores to a therapy session
# ---------------------------------------------------------------------------

class SessionScoresBase(BaseModel):
    """Scores recorded during a therapy session."""
    therapy_session_id: UUID
    patient_id: UUID
    # Patient scores (measured by therapist)
    patient_scores: ScoreSnapshot
    # Therapist self-scores (miroir protocol — Stern-Tetraeder)
    therapist_scores: Optional[ScoreSnapshot] = None
    # Notes on the measurement
    measurement_notes: Optional[str] = None
    # Was the monade appeased before measurement? (hDOM protocol)
    monade_apaisee: bool = Field(default=False,
                                  description="Monade apaisée avant mesure (protocole hDOM)")


class SessionScoresCreate(SessionScoresBase):
    """Body for POST /scores."""
    pass


class SessionScoresUpdate(BaseModel):
    """Body for PUT /scores/{id} — partial update."""
    patient_scores: Optional[ScoreSnapshot] = None
    therapist_scores: Optional[ScoreSnapshot] = None
    measurement_notes: Optional[str] = None
    monade_apaisee: Optional[bool] = None


class SessionScores(SessionScoresBase):
    """Full session scores record returned by the API."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionScoresList(BaseModel):
    """Response for GET /scores."""
    scores: list[SessionScores]
    total: int


# ---------------------------------------------------------------------------
# Score Trend — aggregated view for patient evolution
# ---------------------------------------------------------------------------

class ScoreTrend(BaseModel):
    """Trend data point for score evolution charts."""
    date: datetime
    sla: Optional[Decimal] = None
    slsa: Optional[Decimal] = None
    slpmo: Optional[Decimal] = None
    slm: Optional[Decimal] = None


class ScoreTrendResponse(BaseModel):
    """Response for GET /scores/trend/{patient_id}."""
    patient_id: UUID
    data_points: list[ScoreTrend]
    total_sessions: int
    # Summary stats
    sla_first: Optional[Decimal] = None
    sla_last: Optional[Decimal] = None
    sla_delta: Optional[Decimal] = None
