"""Dashboard Statistics router — iTherapeut 6.0 (Plan 59 finition).

Endpoint:
  GET /stats/dashboard → aggregated KPIs
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends

from dependencies import verify_token
from models.stats import DashboardStats, PeriodStats
from services.supabase_client import get_supabase

router = APIRouter(
    prefix="/stats",
    tags=["Statistics"],
    dependencies=[Depends(verify_token)],
)


def _first_of_month(d: date) -> str:
    return d.replace(day=1).isoformat()


def _last_of_month(d: date) -> str:
    if d.month == 12:
        return date(d.year + 1, 1, 1).isoformat()
    return date(d.year, d.month + 1, 1).isoformat()


def _period_stats(sb, month_start: str, month_end: str) -> PeriodStats:
    """Compute stats for a given month range [month_start, month_end)."""
    # Sessions in period
    sessions = (
        sb.table("therapy_sessions")
        .select("id", count="exact")
        .gte("date", month_start)
        .lt("date", month_end)
        .execute()
    )
    sessions_count = sessions.count or 0

    # Distinct active patients in period
    active_patients = (
        sb.table("therapy_sessions")
        .select("patient_id")
        .gte("date", month_start)
        .lt("date", month_end)
        .execute()
    )
    unique_patients = set()
    for row in (active_patients.data or []):
        unique_patients.add(row["patient_id"])

    # Invoices in period
    inv_sent = (
        sb.table("invoices")
        .select("id", count="exact")
        .gte("invoice_date", month_start)
        .lt("invoice_date", month_end)
        .eq("status", "sent")
        .execute()
    )
    inv_paid = (
        sb.table("invoices")
        .select("total_amount", count="exact")
        .gte("invoice_date", month_start)
        .lt("invoice_date", month_end)
        .eq("status", "paid")
        .execute()
    )
    inv_overdue = (
        sb.table("invoices")
        .select("id", count="exact")
        .gte("invoice_date", month_start)
        .lt("invoice_date", month_end)
        .eq("status", "overdue")
        .execute()
    )

    # Revenue from paid invoices in period
    revenue = Decimal("0")
    for row in (inv_paid.data or []):
        revenue += Decimal(str(row.get("total_amount", 0)))

    # Average scores in period
    scores_data = (
        sb.table("session_scores")
        .select("patient_scores")
        .gte("created_at", month_start)
        .lt("created_at", month_end)
        .execute()
    )
    sla_vals, slsa_vals, slpmo_vals = [], [], []
    for row in (scores_data.data or []):
        ps = row.get("patient_scores") or {}
        if ps.get("sla") is not None:
            sla_vals.append(Decimal(str(ps["sla"])))
        if ps.get("slsa") is not None:
            slsa_vals.append(Decimal(str(ps["slsa"])))
        if ps.get("slpmo") is not None:
            slpmo_vals.append(Decimal(str(ps["slpmo"])))

    return PeriodStats(
        sessions_count=sessions_count,
        patients_active=len(unique_patients),
        revenue_total=revenue,
        invoices_sent=inv_sent.count or 0,
        invoices_paid=inv_paid.count or 0,
        invoices_overdue=inv_overdue.count or 0,
        avg_sla=sum(sla_vals) / len(sla_vals) if sla_vals else None,
        avg_slsa=sum(slsa_vals) / len(slsa_vals) if slsa_vals else None,
        avg_slpmo=sum(slpmo_vals) / len(slpmo_vals) if slpmo_vals else None,
    )


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard():
    """Aggregated KPI dashboard for the therapist."""
    sb = get_supabase()
    today = date.today()

    # --- Overall totals ---
    total_patients = sb.table("patients").select("id", count="exact").execute()
    total_sessions = sb.table("therapy_sessions").select("id", count="exact").execute()

    # Total revenue (all paid invoices ever)
    all_paid = sb.table("invoices").select("total_amount").eq("status", "paid").execute()
    total_revenue = sum(Decimal(str(r.get("total_amount", 0))) for r in (all_paid.data or []))

    # --- Current month ---
    cm_start = _first_of_month(today)
    cm_end = _last_of_month(today)
    cm_label = today.strftime("%B %Y")
    current = _period_stats(sb, cm_start, cm_end)

    # --- Previous month ---
    prev_date = (today.replace(day=1) - timedelta(days=1))
    pm_start = _first_of_month(prev_date)
    pm_end = _first_of_month(today)
    pm_label = prev_date.strftime("%B %Y")
    previous = _period_stats(sb, pm_start, pm_end)

    # --- Pending invoices amount ---
    pending = sb.table("invoices").select("total_amount").in_("status", ["sent", "overdue"]).execute()
    pending_amount = sum(Decimal(str(r.get("total_amount", 0))) for r in (pending.data or []))

    # --- Patients last 30 days ---
    thirty_days_ago = (today - timedelta(days=30)).isoformat()
    recent_patients = (
        sb.table("therapy_sessions")
        .select("patient_id")
        .gte("date", thirty_days_ago)
        .execute()
    )
    unique_recent = set(r["patient_id"] for r in (recent_patients.data or []))

    return DashboardStats(
        total_patients=total_patients.count or 0,
        total_sessions=total_sessions.count or 0,
        total_revenue=total_revenue,
        current_month=current,
        current_month_label=cm_label,
        previous_month=previous,
        previous_month_label=pm_label,
        pending_invoices_amount=pending_amount,
        patients_last_30_days=len(unique_recent),
    )
