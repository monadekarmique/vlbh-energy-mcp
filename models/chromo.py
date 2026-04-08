"""Pydantic models for Chromotherapy — iTherapeut 6.0 (Plan 59/179).

Table: chromo_sessions (Supabase PostgreSQL)
Chromotherapy prescriptions: Color Gels per meridian, 5 Elements mapping.

References:
  - 12 principaux méridiens MTC + 2 merveilleux vaisseaux (Du Mai, Ren Mai)
  - Color Gels Dinshah (Spectro-Chrome system)
  - 5 Éléments (Bois, Feu, Terre, Métal, Eau) — correspondances couleur
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Color Gel System (Dinshah Spectro-Chrome)
# ---------------------------------------------------------------------------

class ColorGel(str, Enum):
    """12 Color Gels du système Spectro-Chrome de Dinshah."""
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    LEMON = "lemon"
    GREEN = "green"
    TURQUOISE = "turquoise"
    BLUE = "blue"
    INDIGO = "indigo"
    VIOLET = "violet"
    PURPLE = "purple"
    MAGENTA = "magenta"
    SCARLET = "scarlet"


class Element(str, Enum):
    """5 Éléments MTC."""
    BOIS = "bois"       # Vert — Foie/Vésicule Biliaire
    FEU = "feu"         # Rouge — Cœur/Intestin Grêle
    TERRE = "terre"     # Jaune — Rate/Estomac
    METAL = "metal"     # Blanc/Indigo — Poumon/Gros Intestin
    EAU = "eau"         # Bleu/Noir — Rein/Vessie


class Meridien(str, Enum):
    """14 méridiens principaux."""
    POUMON = "poumon"               # P  — Métal
    GROS_INTESTIN = "gros_intestin" # GI — Métal
    ESTOMAC = "estomac"             # E  — Terre
    RATE = "rate"                   # Rt — Terre
    COEUR = "coeur"                 # C  — Feu
    INTESTIN_GRELE = "intestin_grele"  # IG — Feu
    VESSIE = "vessie"               # V  — Eau
    REIN = "rein"                   # Rn — Eau
    MAITRE_COEUR = "maitre_coeur"   # MC — Feu ministériel
    TRIPLE_RECHAUFFEUR = "triple_rechauffeur"  # TR — Feu ministériel
    VESICULE_BILIAIRE = "vesicule_biliaire"    # VB — Bois
    FOIE = "foie"                   # F  — Bois
    DU_MAI = "du_mai"               # GV — Vaisseau Gouverneur
    REN_MAI = "ren_mai"             # CV — Vaisseau Conception


# ---------------------------------------------------------------------------
# Meridien → Element → Color mapping (référence statique)
# ---------------------------------------------------------------------------

MERIDIEN_ELEMENT_MAP: dict[str, dict] = {
    "poumon":              {"element": "metal",  "yin_yang": "yin",  "color_tonify": "indigo",    "color_sedate": "orange",   "color_neutral": "green"},
    "gros_intestin":       {"element": "metal",  "yin_yang": "yang", "color_tonify": "indigo",    "color_sedate": "orange",   "color_neutral": "green"},
    "estomac":             {"element": "terre",  "yin_yang": "yang", "color_tonify": "yellow",    "color_sedate": "violet",   "color_neutral": "green"},
    "rate":                {"element": "terre",  "yin_yang": "yin",  "color_tonify": "yellow",    "color_sedate": "violet",   "color_neutral": "green"},
    "coeur":               {"element": "feu",    "yin_yang": "yin",  "color_tonify": "red",       "color_sedate": "blue",     "color_neutral": "green"},
    "intestin_grele":      {"element": "feu",    "yin_yang": "yang", "color_tonify": "red",       "color_sedate": "blue",     "color_neutral": "green"},
    "vessie":              {"element": "eau",    "yin_yang": "yang", "color_tonify": "blue",      "color_sedate": "yellow",   "color_neutral": "green"},
    "rein":                {"element": "eau",    "yin_yang": "yin",  "color_tonify": "blue",      "color_sedate": "yellow",   "color_neutral": "green"},
    "maitre_coeur":        {"element": "feu",    "yin_yang": "yin",  "color_tonify": "scarlet",   "color_sedate": "turquoise","color_neutral": "green"},
    "triple_rechauffeur":  {"element": "feu",    "yin_yang": "yang", "color_tonify": "scarlet",   "color_sedate": "turquoise","color_neutral": "green"},
    "vesicule_biliaire":   {"element": "bois",   "yin_yang": "yang", "color_tonify": "green",     "color_sedate": "magenta",  "color_neutral": "lemon"},
    "foie":                {"element": "bois",   "yin_yang": "yin",  "color_tonify": "green",     "color_sedate": "magenta",  "color_neutral": "lemon"},
    "du_mai":              {"element": "feu",    "yin_yang": "yang", "color_tonify": "red",       "color_sedate": "blue",     "color_neutral": "purple"},
    "ren_mai":             {"element": "eau",    "yin_yang": "yin",  "color_tonify": "blue",      "color_sedate": "red",      "color_neutral": "purple"},
}


# ---------------------------------------------------------------------------
# Chromo Prescription — per meridien per session
# ---------------------------------------------------------------------------

class ChromoPrescriptionItem(BaseModel):
    """Single color gel application on a meridian."""
    meridien: Meridien
    color_gel: ColorGel
    action: str = Field(..., pattern=r"^(tonify|sedate|neutral|custom)$",
                         description="tonify/sedate/neutral based on 5 Elements, or custom")
    duration_seconds: int = Field(default=180, ge=30, le=1800,
                                   description="Durée d'exposition en secondes")
    point_acupuncture: Optional[str] = Field(None, max_length=20,
                                              description="Point spécifique (ex: P7, Rn3, GV20)")
    notes: Optional[str] = None


class ChromoSessionBase(BaseModel):
    """Chromotherapy session record."""
    therapy_session_id: UUID
    patient_id: UUID
    prescriptions: list[ChromoPrescriptionItem] = Field(..., min_length=1)
    # Rose des Vents context
    rose_des_vents_id: Optional[UUID] = Field(None,
        description="Lien vers l'analyse Rose des Vents qui a guidé la prescription")
    # Scores context
    scores_id: Optional[UUID] = Field(None,
        description="Lien vers les scores de la séance")
    # Global notes
    observation: Optional[str] = None
    # Protocol source
    protocol_source: str = Field(default="5_elements",
        pattern=r"^(5_elements|hdom|spectro_chrome|custom)$",
        description="Méthode de prescription utilisée")


class ChromoSessionCreate(ChromoSessionBase):
    """Body for POST /chromo."""
    pass


class ChromoSessionUpdate(BaseModel):
    """Body for PUT /chromo/{id} — partial update."""
    prescriptions: Optional[list[ChromoPrescriptionItem]] = None
    observation: Optional[str] = None
    protocol_source: Optional[str] = Field(None, pattern=r"^(5_elements|hdom|spectro_chrome|custom)$")


class ChromoSession(ChromoSessionBase):
    """Full chromo session record returned by the API."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChromoSessionList(BaseModel):
    """Response for GET /chromo."""
    sessions: list[ChromoSession]
    total: int


class MeridienReference(BaseModel):
    """Reference data for a single meridian — color gel mapping."""
    meridien: str
    element: str
    yin_yang: str
    color_tonify: str
    color_sedate: str
    color_neutral: str


class ChromoReferenceResponse(BaseModel):
    """Response for GET /chromo/reference — full mapping table."""
    meridiens: list[MeridienReference]
    color_gels: list[str]
    elements: list[str]
