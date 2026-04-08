"""Pydantic models for Practitioner (Praticien) — iTherapeut 6.0.

Table: practitioners (Supabase PostgreSQL)

Each practitioner in a cabinet has their own profile with:
- Identity (name, address, phone, email)
- Billing info (IBAN for QR-facture creditor)
- Tarif 590 info (RCC number, NIF, GLN, therapy method)
- Subscription plan (59 CHF Therapeute / 179 CHF Cabinet Pro)

When creating invoices or Tarif 590 PDFs, passing a practitioner_id
auto-fills the creditor/therapeute info from this profile.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PractitionerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class SubscriptionPlan(str, Enum):
    THERAPEUTE = "therapeute_59"       # 59 CHF/mois
    CABINET_PRO = "cabinet_pro_179"    # 179 CHF/mois


# ---------------------------------------------------------------------------
# Shared fields
# ---------------------------------------------------------------------------

class PractitionerBase(BaseModel):
    # Identity
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)

    # Structured address (SIX v2.4 QR-facture requirement)
    street: str = Field(..., max_length=150)
    house_number: Optional[str] = Field(None, max_length=20)
    postal_code: str = Field(..., max_length=10)
    city: str = Field(..., max_length=100)
    country: str = Field(default="CH", max_length=2)

    # Billing — QR-facture creditor
    iban: str = Field(..., max_length=34, description="IBAN for QR-facture (creditor)")

    # Tarif 590
    rcc_number: str = Field(..., min_length=1, max_length=20,
                            description="Numéro RCC (Registre de Codes Créanciers)")
    nif_number: Optional[str] = Field(None, max_length=20,
                                       description="Numéro NIF (identification fiscale)")
    gln_number: Optional[str] = Field(None, max_length=13,
                                       description="Global Location Number")
    therapy_method: Optional[str] = Field(None, max_length=10,
                                           description="Code méthode Tarif 590 (1-15, 99)")
    therapy_method_text: Optional[str] = Field(None, max_length=100,
                                                description="Méthode en texte libre")

    # Plan & status
    plan: SubscriptionPlan = Field(default=SubscriptionPlan.THERAPEUTE)
    status: PractitionerStatus = Field(default=PractitionerStatus.ACTIVE)

    # Cabinet reference (for multi-practitioner cabinets — Plan 179)
    cabinet_id: Optional[UUID] = Field(None,
                                        description="Links practitioners in the same cabinet")

    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------------

class PractitionerCreate(PractitionerBase):
    """Body for POST /practitioners."""
    pass


class PractitionerUpdate(BaseModel):
    """Body for PUT /practitioners/{id} — all fields optional."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    street: Optional[str] = Field(None, max_length=150)
    house_number: Optional[str] = Field(None, max_length=20)
    postal_code: Optional[str] = Field(None, max_length=10)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=2)
    iban: Optional[str] = Field(None, max_length=34)
    rcc_number: Optional[str] = Field(None, min_length=1, max_length=20)
    nif_number: Optional[str] = Field(None, max_length=20)
    gln_number: Optional[str] = Field(None, max_length=13)
    therapy_method: Optional[str] = Field(None, max_length=10)
    therapy_method_text: Optional[str] = Field(None, max_length=100)
    plan: Optional[SubscriptionPlan] = None
    status: Optional[PractitionerStatus] = None
    cabinet_id: Optional[UUID] = None
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class Practitioner(PractitionerBase):
    """Full practitioner record returned by the API."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PractitionerList(BaseModel):
    """Response for GET /practitioners."""
    practitioners: list[Practitioner]
    total: int
