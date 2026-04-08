"""Pydantic models for Invoices — iTherapeut 6.0 (Plan 59).

Table: invoices (Supabase PostgreSQL)
Supports QR-facture generation (SIX v2.4).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class InvoiceLineItem(BaseModel):
    """Single line item on an invoice."""
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., ge=0)
    unit_price: Decimal = Field(..., ge=0)
    tarif_code: Optional[str] = Field(None, max_length=10)  # Tarif 590


class InvoiceBase(BaseModel):
    patient_id: UUID
    therapy_session_ids: list[UUID] = Field(default_factory=list)
    invoice_date: date = Field(default_factory=date.today)
    due_date: Optional[date] = None
    line_items: list[InvoiceLineItem] = Field(..., min_length=1)
    notes: Optional[str] = None
    # Creditor info (therapist) — stored per invoice for immutability
    creditor_name: str = Field(..., max_length=200)
    creditor_street: str = Field(..., max_length=150)
    creditor_house_number: Optional[str] = Field(None, max_length=20)
    creditor_postal_code: str = Field(..., max_length=10)
    creditor_city: str = Field(..., max_length=100)
    creditor_country: str = Field(default="CH", max_length=2)
    creditor_iban: str = Field(..., max_length=34)


class InvoiceCreate(InvoiceBase):
    """Body for POST /invoices."""
    pass


class Invoice(InvoiceBase):
    """Full invoice record returned by the API."""
    id: UUID
    invoice_number: str  # Auto-generated: ITH-2026-0001
    status: InvoiceStatus = InvoiceStatus.DRAFT
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceList(BaseModel):
    """Response for GET /invoices."""
    invoices: list[Invoice]
    total: int
