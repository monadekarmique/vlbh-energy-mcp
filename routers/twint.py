"""Twint Payment Link router — iTherapeut 6.0 (Plan 179).

Endpoint:
  POST /invoices/{id}/twint → generate Twint payment link
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import verify_token
from models.twint import TwintLink, TwintLinkCreate, TwintPaymentStatus
from services.supabase_client import get_supabase

router = APIRouter(
    prefix="/invoices",
    tags=["Twint Payments"],
    dependencies=[Depends(verify_token)],
)

TABLE = "twint_payments"


def _build_twint_url(amount: Decimal, message: str | None = None) -> str:
    """Build a Twint deep-link URL.

    Format: twint://payment?amount=<CHF>&message=<msg>
    In production, this would integrate with the TWINT Merchant API
    or PostFinance e-Commerce gateway. For now, we generate the
    app deep-link which works for peer-to-peer requests.
    """
    base = f"twint://payment?amount={float(amount):.2f}&currency=CHF"
    if message:
        # URL-encode the message for the deep link
        import urllib.parse
        base += f"&message={urllib.parse.quote(message)}"
    return base


@router.post(
    "/{invoice_id}/twint",
    response_model=TwintLink,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Twint payment link for an invoice",
)
async def create_twint_link(invoice_id: UUID, body: TwintLinkCreate):
    """Generate a Twint payment link attached to an invoice.

    - If amount is not specified, uses the invoice total.
    - Optionally sends the link via WhatsApp to the patient.
    - Link expires in 48 hours.
    """
    sb = get_supabase()

    # Fetch invoice
    inv_result = sb.table("invoices").select("*").eq("id", str(invoice_id)).execute()
    if not inv_result.data:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice = inv_result.data[0]

    # Determine amount
    amount = body.amount if body.amount is not None else Decimal(str(invoice["total_amount"]))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    # Build message
    invoice_number = invoice.get("invoice_number", "")
    message = body.message or f"Paiement facture {invoice_number}"

    # Generate Twint URL
    twint_url = _build_twint_url(amount, message)

    # Expiration: 48h
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=48)

    # Store in DB
    data = {
        "invoice_id": str(invoice_id),
        "patient_id": invoice["patient_id"],
        "amount": float(amount),
        "currency": "CHF",
        "status": TwintPaymentStatus.PENDING.value,
        "twint_url": twint_url,
        "message": message,
        "whatsapp_sent": False,
        "expires_at": expires_at.isoformat(),
    }

    result = sb.table(TABLE).insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create Twint payment link")

    twint_record = result.data[0]

    # Optionally send via WhatsApp (via Make.com webhook)
    if body.send_whatsapp:
        whatsapp_sent = await _send_whatsapp_twint(sb, invoice, twint_url, amount)
        if whatsapp_sent:
            sb.table(TABLE).update({
                "whatsapp_sent": True,
                "status": TwintPaymentStatus.SENT.value,
            }).eq("id", twint_record["id"]).execute()
            twint_record["whatsapp_sent"] = True
            twint_record["status"] = TwintPaymentStatus.SENT.value

    return twint_record


async def _send_whatsapp_twint(sb, invoice: dict, twint_url: str, amount: Decimal) -> bool:
    """Send Twint link to patient via WhatsApp (Make.com scenario).

    Returns True if the message was queued successfully.
    This integrates with the existing Make.com webhook infrastructure.
    """
    import os
    import httpx

    webhook_url = os.environ.get("MAKE_WEBHOOK_TWINT_URL")
    if not webhook_url:
        return False

    # Get patient info
    patient_result = (
        sb.table("patients")
        .select("first_name", "last_name", "phone")
        .eq("id", invoice["patient_id"])
        .execute()
    )
    if not patient_result.data or not patient_result.data[0].get("phone"):
        return False

    patient = patient_result.data[0]

    payload = {
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "patient_phone": patient["phone"],
        "amount": float(amount),
        "currency": "CHF",
        "invoice_number": invoice.get("invoice_number", ""),
        "twint_url": twint_url,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=payload)
            return resp.status_code in range(200, 300)
    except Exception:
        return False
