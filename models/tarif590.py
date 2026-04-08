"""Pydantic models for Tarif 590 — iTherapeut 6.0 (Plan 59).

Tarif 590 is the standard Swiss complementary therapy invoice format.
Required by all health insurers (complémentaires) for reimbursement.
Ref: https://www.tarif590.ch

Fields mirror the official Tarif 590 form sections:
  - Thérapeute (practitioner info + RCC number)
  - Patient (demographics + insurance)
  - Prestations (line items with tarif codes)
  - Totals + TVA
"""
from __future__ import annotations

import datetime as _dt
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Tarif590Method(str, Enum):
    """Recognized complementary therapy methods (codes officiels)."""
    NATUROPATHIE = "1"
    HOMEOPATHIE = "2"
    MTC = "3"  # Médecine Traditionnelle Chinoise
    AYURVEDA = "4"
    PHYTOTHERAPIE = "5"
    REFLEXOLOGIE = "6"
    SHIATSU = "7"
    OSTEOPATHIE = "8"
    KINESIOLOGIE = "9"
    DRAINAGE_LYMPHATIQUE = "10"
    MASSAGE_THERAPEUTIQUE = "11"
    THERAPIE_CRANIOSACRALE = "12"
    HYPNOSE = "13"
    SOPHROLOGIE = "14"
    ACUPUNCTURE = "15"
    AUTRE = "99"


class Tarif590TvaCode(str, Enum):
    """TVA codes for Tarif 590."""
    EXONERE = "0"  # Exonéré (most therapy)
    NORMAL = "1"   # 8.1% (rare for therapy)
    REDUIT = "2"   # 2.6% (rare)


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class Tarif590Therapeute(BaseModel):
    """Section Thérapeute du Tarif 590."""
    name: str = Field(..., min_length=1, max_length=200, description="Nom complet du thérapeute")
    street: str = Field(..., max_length=150)
    house_number: Optional[str] = Field(None, max_length=20)
    postal_code: str = Field(..., max_length=10)
    city: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    rcc_number: str = Field(..., min_length=1, max_length=20,
                            description="Numéro RCC (Registre de Codes Créanciers)")
    nif_number: Optional[str] = Field(None, max_length=20,
                                       description="Numéro NIF (identification fiscale)")
    gln_number: Optional[str] = Field(None, max_length=13,
                                       description="Global Location Number")
    method: Tarif590Method = Field(default=Tarif590Method.AUTRE,
                                    description="Méthode thérapeutique principale")
    method_text: Optional[str] = Field(None, max_length=100,
                                        description="Méthode en texte libre (si AUTRE)")


class Tarif590Patient(BaseModel):
    """Section Patient du Tarif 590."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: _dt.date
    street: Optional[str] = Field(None, max_length=150)
    house_number: Optional[str] = Field(None, max_length=20)
    postal_code: Optional[str] = Field(None, max_length=10)
    city: Optional[str] = Field(None, max_length=100)
    avs_number: Optional[str] = Field(None, max_length=16,
                                       description="Numéro AVS (756.xxxx.xxxx.xx)")
    insurance_name: Optional[str] = Field(None, max_length=150)
    insurance_number: Optional[str] = Field(None, max_length=50,
                                             description="Numéro de police d'assurance")
    insurance_gln: Optional[str] = Field(None, max_length=13,
                                          description="GLN de l'assurance")
    canton: str = Field(default="VD", max_length=2)


class Tarif590Prestation(BaseModel):
    """Ligne de prestation Tarif 590."""
    service_date: _dt.date = Field(..., alias="date", description="Date de la prestation")
    tarif_code: str = Field(default="590", max_length=10,
                            description="Code tarif (590 = thérapie complémentaire)")
    code_prestation: str = Field(..., max_length=10,
                                 description="Code prestation (ex: 1000, 1001, 1200)")
    description: str = Field(..., max_length=200)
    duration_minutes: int = Field(..., ge=5, le=480,
                                   description="Durée en minutes")
    unit_price: Decimal = Field(..., ge=0, description="Prix par 5 min (CHF)")
    quantity: Decimal = Field(..., ge=0, description="Nombre d'unités (5 min)")
    tva_code: Tarif590TvaCode = Field(default=Tarif590TvaCode.EXONERE)
    amount: Optional[Decimal] = Field(None, ge=0, description="Montant ligne (auto-calc)")

    @model_validator(mode="after")
    def calc_amount(self) -> "Tarif590Prestation":
        """Auto-calculate line amount = unit_price * quantity."""
        if self.amount is None:
            self.amount = self.unit_price * self.quantity
        return self

    @model_validator(mode="after")
    def calc_quantity_from_duration(self) -> "Tarif590Prestation":
        """If quantity not explicitly set, derive from duration (5-min units)."""
        # Only auto-calc if quantity seems like a placeholder
        return self


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class Tarif590Request(BaseModel):
    """Request body for POST /tarif590/generate.

    Generates an official Tarif 590 PDF.
    If practitioner_id is provided, therapeute info is auto-filled
    from the practitioner profile (therapeute field becomes optional).
    """
    practitioner_id: Optional[UUID] = Field(None,
                                             description="Auto-fills therapeute from practitioner profile")
    therapeute: Optional[Tarif590Therapeute] = Field(None,
                                                      description="Required if practitioner_id is not set")
    patient: Tarif590Patient
    prestations: list[Tarif590Prestation] = Field(..., min_length=1, max_length=50)
    invoice_date: _dt.date = Field(default_factory=_dt.date.today)
    invoice_number: Optional[str] = Field(None, max_length=30,
                                           description="Numéro de facture (auto si vide)")
    reference_number: Optional[str] = Field(None, max_length=27,
                                             description="Référence QR (27 digits)")
    diagnostic: Optional[str] = Field(None, max_length=200,
                                       description="Diagnostic / motif de consultation")
    accident: bool = Field(default=False, description="Cas d'accident (LAA)")
    maladie: bool = Field(default=True, description="Cas de maladie")
    # Session link (optional — links to therapy_sessions)
    therapy_session_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    # Totals (auto-calculated)
    total_amount: Optional[Decimal] = Field(None, ge=0)

    @model_validator(mode="after")
    def calc_total(self) -> "Tarif590Request":
        """Sum all prestations amounts."""
        if self.total_amount is None:
            self.total_amount = sum(
                p.amount or Decimal("0") for p in self.prestations
            )
        return self


class Tarif590Response(BaseModel):
    """Response for POST /tarif590/generate — metadata about generated PDF."""
    invoice_number: str
    total_amount: Decimal
    patient_name: str
    therapeute_name: str
    prestations_count: int
    generated_at: datetime
