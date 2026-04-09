"""Pydantic models for Patient CRUD — iTherapeut 6.0 (Plan 59).

Table: patients (Supabase PostgreSQL)
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Shared fields
# ---------------------------------------------------------------------------

class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    # Structured address (SIX v2.4 QR-facture requirement)
    street: Optional[str] = Field(None, max_length=150)
    house_number: Optional[str] = Field(None, max_length=20)
    postal_code: Optional[str] = Field(None, max_length=10)
    city: Optional[str] = Field(None, max_length=100)
    country: str = Field(default="CH", max_length=2)
    # Therapist-specific
    notes: Optional[str] = None
    insurance_name: Optional[str] = Field(None, max_length=150)
    insurance_number: Optional[str] = Field(None, max_length=50)


# ---------------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------------

class PatientCreate(PatientBase):
    """Body for POST /patients."""
    pass


class PatientUpdate(BaseModel):
    """Body for PUT /patients/{id} — all fields optional."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    street: Optional[str] = Field(None, max_length=150)
    house_number: Optional[str] = Field(None, max_length=20)
    postal_code: Optional[str] = Field(None, max_length=10)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=2)
    notes: Optional[str] = None
    insurance_name: Optional[str] = Field(None, max_length=150)
    insurance_number: Optional[str] = Field(None, max_length=50)



# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class Patient(PatientBase):
    """Full patient record returned by the API."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PatientList(BaseModel):
    """Response for GET /patients."""
    patients: list[Patient]
    total: int
