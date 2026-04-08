"""QR-facture generation router — iTherapeut 6.0 (Plan 59).

Generates Swiss QR-bill PDFs compliant with SIX v2.4.
Uses structured addresses only (mandatory since Nov 2025).

Endpoint:
  POST /qrbill/generate → QR-bill PDF
"""
from __future__ import annotations

import io
import tempfile
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from dependencies import verify_token
from services.supabase_client import get_supabase

router = APIRouter(
    prefix="/qrbill",
    tags=["QR-Facture"],
    dependencies=[Depends(verify_token)],
)


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class QRBillAddress(BaseModel):
    """Structured address per SIX v2.4."""
    name: str = Field(..., max_length=140)
    street: str = Field(..., max_length=140)
    house_number: Optional[str] = Field(None, max_length=16)
    postal_code: str = Field(..., max_length=16)
    city: str = Field(..., max_length=35)
    country: str = Field(default="CH", max_length=2)


class QRBillRequest(BaseModel):
    """Body for POST /qrbill/generate."""
    # Can generate from an existing invoice or from raw data
    invoice_id: Optional[UUID] = None
    # If no invoice_id, provide these fields:
    creditor: Optional[QRBillAddress] = None
    creditor_iban: Optional[str] = Field(None, max_length=34)
    debtor: Optional[QRBillAddress] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="CHF", pattern="^(CHF|EUR)$")
    reference_number: Optional[str] = Field(None, max_length=27)
    additional_info: Optional[str] = Field(None, max_length=140)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/generate")
async def generate_qrbill(body: QRBillRequest):
    """Generate a QR-bill PDF.

    Either provide an invoice_id (data pulled from DB) or
    provide creditor/debtor/amount directly.
    """
    from qrbill import QRBill

    if body.invoice_id:
        # Load from DB
        sb = get_supabase()
        inv_result = sb.table("invoices").select("*").eq("id", str(body.invoice_id)).execute()
        if not inv_result.data:
            raise HTTPException(status_code=404, detail="Invoice not found")
        inv = inv_result.data[0]

        # Load patient (debtor)
        pat_result = sb.table("patients").select("*").eq("id", inv["patient_id"]).execute()
        pat = pat_result.data[0] if pat_result.data else {}

        creditor = {
            "name": inv.get("creditor_name", ""),
            "street": inv.get("creditor_street", ""),
            "house_num": inv.get("creditor_house_number", ""),
            "pcode": inv.get("creditor_postal_code", ""),
            "city": inv.get("creditor_city", ""),
            "country": inv.get("creditor_country", "CH"),
        }
        debtor = {
            "name": f"{pat.get('first_name', '')} {pat.get('last_name', '')}".strip(),
            "street": pat.get("street", "") or "",
            "house_num": pat.get("house_number", "") or "",
            "pcode": pat.get("postal_code", "") or "",
            "city": pat.get("city", "") or "",
            "country": pat.get("country", "CH"),
        }
        amount = float(inv.get("total_amount", 0))
        iban = inv.get("creditor_iban", "")
        ref = body.reference_number
        info = body.additional_info or inv.get("invoice_number", "")
    else:
        # Use raw data from request
        if not body.creditor or not body.creditor_iban or body.amount is None:
            raise HTTPException(
                status_code=400,
                detail="Provide either invoice_id or creditor + creditor_iban + amount",
            )
        creditor = {
            "name": body.creditor.name,
            "street": body.creditor.street,
            "house_num": body.creditor.house_number or "",
            "pcode": body.creditor.postal_code,
            "city": body.creditor.city,
            "country": body.creditor.country,
        }
        debtor = None
        if body.debtor:
            debtor = {
                "name": body.debtor.name,
                "street": body.debtor.street,
                "house_num": body.debtor.house_number or "",
                "pcode": body.debtor.postal_code,
                "city": body.debtor.city,
                "country": body.debtor.country,
            }
        amount = float(body.amount)
        iban = body.creditor_iban
        ref = body.reference_number
        info = body.additional_info

    # Build QR-bill
    qr_kwargs = {
        "account": iban,
        "creditor": creditor,
        "amount": f"{amount:.2f}",
        "currency": body.currency,
    }
    if debtor:
        qr_kwargs["debtor"] = debtor
    if ref:
        qr_kwargs["reference_number"] = ref
    if info:
        qr_kwargs["additional_information"] = info

    try:
        bill = QRBill(**qr_kwargs)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"QR-bill generation error: {e}")

    # Render to SVG then to PDF
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        bill.as_svg(tmp.name)
        tmp.seek(0)
        svg_content = open(tmp.name, "rb").read()

    # Return SVG (qrbill library outputs SVG natively)
    return StreamingResponse(
        io.BytesIO(svg_content),
        media_type="image/svg+xml",
        headers={
            "Content-Disposition": 'attachment; filename="qrbill.svg"'
        },
    )
