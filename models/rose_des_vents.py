"""Pydantic models for Rose des Vents diagnostic — iTherapeut 6.0 (Plan 59).

Table: rose_des_vents (Supabase PostgreSQL)

The Rose des Vents maps the deviation angle of the light ray from the 9th
dimension to the Soul. A 0° angle = perfect alignment (North). Any deviation
indicates perturbation by a dominant aeon system.

Structure:
  - 12 directions (22.5° increments)
  - 4 quadrants + centre (Q V)
  - 3 anatomical planes (sagittal/coronal/transverse)
  - Each direction has specific pathological associations

Ref: VLBH skill rose-des-vents-hara
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RdvDirection(str, Enum):
    """The 12 compass directions + North (aligned)."""
    N = "N"        # 0° — Aligned / Optimal
    NNE = "NNE"    # 22.5°
    NE = "NE"      # 45°
    ENE = "ENE"    # 67.5°
    ESE = "ESE"    # 112.5°
    SE = "SE"      # 135°
    SSE = "SSE"    # 157.5°
    SSO = "SSO"    # 202.5°
    SO = "SO"      # 225°
    OSO = "OSO"    # 247.5°
    ONO = "ONO"    # 292.5°
    NO = "NO"      # 315°
    NNO = "NNO"    # 337.5°


class RdvQuadrant(str, Enum):
    """The 4 quadrants + centre."""
    Q1 = "Q1"  # Nord→Est — Monde extérieur — Abus/Viol
    Q2 = "Q2"  # Est→Sud — Famille — Abus/Viol
    Q3 = "Q3"  # Sud→Ouest — Famille — Meurtre/Vol
    Q4 = "Q4"  # Ouest→Nord — Monde extérieur — Meurtre/Vol
    Q5 = "Q5"  # Centre — Union des 4 — Intégration


class RdvPlan(str, Enum):
    """The 3 anatomical planes."""
    SAGITTAL = "sagittal"        # Karmique — cette vie
    CORONAL = "coronal"          # Transgénérationnel — lignées
    TRANSVERSE = "transverse"    # Multiverses — incarnations parallèles


class RdvTransgression(str, Enum):
    """Type of transgression associated with the quadrant."""
    AUCUNE = "aucune"
    ABUS_VIOL = "abus_viol"
    MEURTRE_VOL = "meurtre_vol"


class RdvDomaine(str, Enum):
    """Domain: external world or family."""
    ALIGNE = "aligne"
    MONDE_EXTERIEUR = "monde_exterieur"
    FAMILLE = "famille"


# ---------------------------------------------------------------------------
# Direction lookup table (static reference)
# ---------------------------------------------------------------------------

DIRECTION_MAP: dict[RdvDirection, dict] = {
    RdvDirection.N: {
        "angle": 0.0, "quadrant": None, "plan": None,
        "domaine": RdvDomaine.ALIGNE, "transgression": RdvTransgression.AUCUNE,
        "association": "Optimal — aligné",
    },
    RdvDirection.NNE: {
        "angle": 22.5, "quadrant": RdvQuadrant.Q1, "plan": RdvPlan.SAGITTAL,
        "domaine": RdvDomaine.MONDE_EXTERIEUR, "transgression": RdvTransgression.ABUS_VIOL,
        "association": "Karmique",
    },
    RdvDirection.NE: {
        "angle": 45.0, "quadrant": RdvQuadrant.Q1, "plan": RdvPlan.CORONAL,
        "domaine": RdvDomaine.MONDE_EXTERIEUR, "transgression": RdvTransgression.ABUS_VIOL,
        "association": "Transgénérationnel",
    },
    RdvDirection.ENE: {
        "angle": 67.5, "quadrant": RdvQuadrant.Q1, "plan": RdvPlan.TRANSVERSE,
        "domaine": RdvDomaine.MONDE_EXTERIEUR, "transgression": RdvTransgression.ABUS_VIOL,
        "association": "Multiverses",
    },
    RdvDirection.ESE: {
        "angle": 112.5, "quadrant": RdvQuadrant.Q2, "plan": RdvPlan.SAGITTAL,
        "domaine": RdvDomaine.FAMILLE, "transgression": RdvTransgression.ABUS_VIOL,
        "association": "Karmique",
    },
    RdvDirection.SE: {
        "angle": 135.0, "quadrant": RdvQuadrant.Q2, "plan": RdvPlan.CORONAL,
        "domaine": RdvDomaine.FAMILLE, "transgression": RdvTransgression.ABUS_VIOL,
        "association": "Transgénérationnel",
    },
    RdvDirection.SSE: {
        "angle": 157.5, "quadrant": RdvQuadrant.Q2, "plan": RdvPlan.TRANSVERSE,
        "domaine": RdvDomaine.FAMILLE, "transgression": RdvTransgression.ABUS_VIOL,
        "association": "Multiverses",
    },
    RdvDirection.SSO: {
        "angle": 202.5, "quadrant": RdvQuadrant.Q3, "plan": RdvPlan.SAGITTAL,
        "domaine": RdvDomaine.FAMILLE, "transgression": RdvTransgression.MEURTRE_VOL,
        "association": "Qliphoth",
    },
    RdvDirection.SO: {
        "angle": 225.0, "quadrant": RdvQuadrant.Q3, "plan": RdvPlan.CORONAL,
        "domaine": RdvDomaine.FAMILLE, "transgression": RdvTransgression.MEURTRE_VOL,
        "association": "Entités négatives diverses",
    },
    RdvDirection.OSO: {
        "angle": 247.5, "quadrant": RdvQuadrant.Q3, "plan": RdvPlan.TRANSVERSE,
        "domaine": RdvDomaine.FAMILLE, "transgression": RdvTransgression.MEURTRE_VOL,
        "association": "Égrégores antipsychotiques masculins",
    },
    RdvDirection.ONO: {
        "angle": 292.5, "quadrant": RdvQuadrant.Q4, "plan": RdvPlan.SAGITTAL,
        "domaine": RdvDomaine.MONDE_EXTERIEUR, "transgression": RdvTransgression.MEURTRE_VOL,
        "association": "Qliphoth + entités négatives de personnes",
    },
    RdvDirection.NO: {
        "angle": 315.0, "quadrant": RdvQuadrant.Q4, "plan": RdvPlan.CORONAL,
        "domaine": RdvDomaine.MONDE_EXTERIEUR, "transgression": RdvTransgression.MEURTRE_VOL,
        "association": "Qliphoth + douleurs persistant après règles",
    },
    RdvDirection.NNO: {
        "angle": 337.5, "quadrant": RdvQuadrant.Q4, "plan": RdvPlan.TRANSVERSE,
        "domaine": RdvDomaine.MONDE_EXTERIEUR, "transgression": RdvTransgression.MEURTRE_VOL,
        "association": "Endométriose — douleurs permanentes liées aux égrégores",
    },
}


# ---------------------------------------------------------------------------
# Measurement model
# ---------------------------------------------------------------------------

class RdvMeasurement(BaseModel):
    """A single Rose des Vents measurement point."""
    direction: RdvDirection = Field(..., description="Direction de déviation identifiée")
    angle: Optional[float] = Field(None, ge=0, lt=360,
                                    description="Angle précis (auto-rempli depuis direction si absent)")
    intensity: Optional[int] = Field(None, ge=0, le=100,
                                      description="Intensité de la perturbation (0–100%)")
    # Auto-derived fields
    quadrant: Optional[RdvQuadrant] = None
    plan: Optional[RdvPlan] = None
    domaine: Optional[RdvDomaine] = None
    transgression: Optional[RdvTransgression] = None
    association: Optional[str] = None

    @model_validator(mode="after")
    def enrich_from_direction(self) -> "RdvMeasurement":
        """Auto-fill quadrant, plan, domaine, transgression from direction lookup."""
        info = DIRECTION_MAP.get(self.direction, {})
        if self.angle is None:
            self.angle = info.get("angle")
        if self.quadrant is None:
            self.quadrant = info.get("quadrant")
        if self.plan is None:
            self.plan = info.get("plan")
        if self.domaine is None:
            self.domaine = info.get("domaine")
        if self.transgression is None:
            self.transgression = info.get("transgression")
        if self.association is None:
            self.association = info.get("association")
        return self


# ---------------------------------------------------------------------------
# Session Rose des Vents — per-session diagnostic
# ---------------------------------------------------------------------------

class RoseDesVentsBase(BaseModel):
    """Rose des Vents diagnostic for a therapy session."""
    therapy_session_id: UUID
    patient_id: UUID
    # Primary measurement (the dominant deviation)
    primary: RdvMeasurement
    # Secondary measurements (can be multiple patterns)
    secondary: list[RdvMeasurement] = Field(default_factory=list, max_length=11)
    # Overall alignment score (0 = fully deviated, 100 = aligned at 0°)
    alignment_score: Optional[int] = Field(None, ge=0, le=100,
                                            description="Score d'alignement global (0–100)")
    # Therapeutic notes
    notes: Optional[str] = None
    # Was this measured before or after treatment?
    timing: str = Field(default="before",
                         pattern=r"^(before|after|during)$",
                         description="Moment de la mesure: before/after/during")


class RoseDesVentsCreate(RoseDesVentsBase):
    """Body for POST /rose-des-vents."""
    pass


class RoseDesVentsUpdate(BaseModel):
    """Body for PUT /rose-des-vents/{id} — partial update."""
    primary: Optional[RdvMeasurement] = None
    secondary: Optional[list[RdvMeasurement]] = None
    alignment_score: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = None
    timing: Optional[str] = Field(None, pattern=r"^(before|after|during)$")


class RoseDesVents(RoseDesVentsBase):
    """Full Rose des Vents record returned by the API."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoseDesVentsList(BaseModel):
    """Response for GET /rose-des-vents."""
    diagnostics: list[RoseDesVents]
    total: int


# ---------------------------------------------------------------------------
# Reference endpoint model
# ---------------------------------------------------------------------------

class DirectionInfo(BaseModel):
    """Reference info for a single direction."""
    direction: RdvDirection
    angle: float
    quadrant: Optional[RdvQuadrant]
    plan: Optional[RdvPlan]
    domaine: RdvDomaine
    transgression: RdvTransgression
    association: str


class DirectionReference(BaseModel):
    """Full reference table for all 13 directions."""
    directions: list[DirectionInfo]
