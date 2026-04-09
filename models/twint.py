"""Pydantic models for Twint Payment Links — iTherapeut 6.0 (Plan 179).

Table: twint_payments (Supabase PostgreSQL)
Generates and tracks Twint payment links attached to invoices.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TwintPaymentStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    PAID = "paid"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class TwintLinkCreate(BaseModel):
    """Body for POST /invoices/{id}/twint."""
    # Optional override — defaults to invoice total
    amount: Optional[Decimal] = Field(None, ge=0, description="Override amount (CHF)")
    message: Optional[str] = Field(None, max_length=200, description="Message for the Twint payment")
    # WhatsApp delivery
    send_whatsapp: bool = Field(default=False, description="Send link via WhatsApp to patient")


class TwintLink(BaseModel):
    """Response — the generated Twint payment link."""
    id: UUID
    invoice_id: UUID
    patient_id: UUID
    amount: Decimal
    currency: str = "CHF"
    status: TwintPaymentStatus = TwintPaymentStatus.PENDING
    twint_url: Optional[str] = None
    message: Optional[str] = None
    whatsapp_sent: bool = False
    created_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TwintPaymentList(BaseModel):
    """Response for listing Twint payments on an invoice."""
    payments: list[TwintLink]
    total: int
