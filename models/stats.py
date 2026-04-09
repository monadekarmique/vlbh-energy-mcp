"""Pydantic models for Dashboard Statistics — iTherapeut 6.0 (Plan 59).

Aggregation endpoint — no dedicated table.
Queries: patients, therapy_sessions, invoices, session_scores.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class PeriodStats(BaseModel):
    """Stats for a given period (current month, previous month, etc.)."""
    sessions_count: int = 0
    patients_active: int = 0
    revenue_total: Decimal = Decimal("0")
    invoices_sent: int = 0
    invoices_paid: int = 0
    invoices_overdue: int = 0
    avg_sla: Optional[Decimal] = None
    avg_slsa: Optional[Decimal] = None
    avg_slpmo: Optional[Decimal] = None


class DashboardStats(BaseModel):
    """Response for GET /stats/dashboard."""
    # Overall totals
    total_patients: int = 0
    total_sessions: int = 0
    total_revenue: Decimal = Decimal("0")
    # Current month
    current_month: PeriodStats = Field(default_factory=PeriodStats)
    current_month_label: str = ""
    # Previous month (for comparison)
    previous_month: PeriodStats = Field(default_factory=PeriodStats)
    previous_month_label: str = ""
    # Quick indicators
    pending_invoices_amount: Decimal = Decimal("0")
    patients_last_30_days: int = 0
    # Generated at
    generated_at: date = Field(default_factory=date.today)
