"""Invoice CRUD router — iTherapeut 6.0 (Plan 59).

Endpoints:
  POST   /invoices          → create
  GET    /invoices          → list
  GET    /invoices/{id}     → get one
  GET    /invoices/{id}/pdf → download PDF
"""
from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from dependencies import verify_token
from models.invoice import Invoice, InvoiceCreate, InvoiceList, InvoiceStatus
from services.supabase_client import get_supabase

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
    dependencies=[Depends(verify_token)],
)

TABLE = "invoices"


def _generate_invoice_number(sb) -> str:
    """Generate sequential invoice number: ITH-YYYY-NNNN."""
    year = date.today().year
    result = (
        sb.table(TABLE)
        .select("invoice_number")
        .ilike("invoice_number", f"ITH-{year}-%")
        .order("invoice_number", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        last = result.data[0]["invoice_number"]
        seq = int(last.split("-")[-1]) + 1
    else:
        seq = 1
    return f"ITH-{year}-{seq:04d}"


def _compute_total(line_items: list[dict]) -> Decimal:
    """Sum quantity * unit_price for all line items."""
    total = Decimal("0")
    for item in line_items:
        total += Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"]))
    return total


@router.post("", response_model=Invoice, status_code=status.HTTP_201_CREATED)
async def create_invoice(body: InvoiceCreate):
    """Create a new invoice with auto-generated number."""
    sb = get_supabase()

    data = body.model_dump(mode="json", exclude_none=True)

    # Compute total
    total = _compute_total(data.get("line_items", []))
    data["total_amount"] = float(total)
    data["invoice_number"] = _generate_invoice_number(sb)
    data["status"] = InvoiceStatus.DRAFT.value

    # Convert Decimal fields
    for item in data.get("line_items", []):
        item["quantity"] = float(item["quantity"])
        item["unit_price"] = float(item["unit_price"])

    result = sb.table(TABLE).insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create invoice")
    return result.data[0]


@router.get("", response_model=InvoiceList)
async def list_invoices(
    patient_id: UUID | None = Query(None),
    invoice_status: InvoiceStatus | None = Query(None, alias="status"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List invoices with optional filters."""
    sb = get_supabase()
    query = sb.table(TABLE).select("*", count="exact")
    if patient_id:
        query = query.eq("patient_id", str(patient_id))
    if invoice_status:
        query = query.eq("status", invoice_status.value)
    query = query.order("invoice_date", desc=True).range(offset, offset + limit - 1)
    result = query.execute()
    return InvoiceList(invoices=result.data, total=result.count or 0)


@router.get("/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: UUID):
    """Get a single invoice by ID."""
    sb = get_supabase()
    result = sb.table(TABLE).select("*").eq("id", str(invoice_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return result.data[0]


@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(invoice_id: UUID):
    """Generate and return a PDF for the invoice."""
    sb = get_supabase()
    result = sb.table(TABLE).select("*").eq("id", str(invoice_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice_data = result.data[0]

    # Get patient info for the PDF
    patient_result = (
        sb.table("patients")
        .select("*")
        .eq("id", invoice_data["patient_id"])
        .execute()
    )
    patient = patient_result.data[0] if patient_result.data else {}

    pdf_bytes = _render_invoice_pdf(invoice_data, patient)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{invoice_data["invoice_number"]}.pdf"'
        },
    )


def _render_invoice_pdf(invoice: dict, patient: dict) -> bytes:
    """Render invoice as PDF using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, height - 25 * mm, f"Facture {invoice.get('invoice_number', '')}")

    c.setFont("Helvetica", 10)
    y = height - 40 * mm

    # Creditor info
    c.drawString(20 * mm, y, f"{invoice.get('creditor_name', '')}")
    y -= 5 * mm
    street = invoice.get("creditor_street", "")
    house = invoice.get("creditor_house_number", "") or ""
    c.drawString(20 * mm, y, f"{street} {house}".strip())
    y -= 5 * mm
    c.drawString(20 * mm, y, f"{invoice.get('creditor_postal_code', '')} {invoice.get('creditor_city', '')}")
    y -= 10 * mm

    # Patient info
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y, "Patient:")
    c.setFont("Helvetica", 10)
    y -= 5 * mm
    c.drawString(20 * mm, y, f"{patient.get('first_name', '')} {patient.get('last_name', '')}")
    y -= 5 * mm
    p_street = patient.get("street", "") or ""
    p_house = patient.get("house_number", "") or ""
    c.drawString(20 * mm, y, f"{p_street} {p_house}".strip())
    y -= 5 * mm
    c.drawString(20 * mm, y, f"{patient.get('postal_code', '')} {patient.get('city', '')}")
    y -= 10 * mm

    # Invoice details
    c.drawString(20 * mm, y, f"Date: {invoice.get('invoice_date', '')}")
    y -= 5 * mm
    if invoice.get("due_date"):
        c.drawString(20 * mm, y, f"Echéance: {invoice['due_date']}")
        y -= 5 * mm
    y -= 5 * mm

    # Line items header
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Description")
    c.drawString(120 * mm, y, "Qté")
    c.drawString(140 * mm, y, "Prix unit.")
    c.drawString(170 * mm, y, "Total")
    y -= 2 * mm
    c.line(20 * mm, y, 190 * mm, y)
    y -= 5 * mm

    # Line items
    c.setFont("Helvetica", 10)
    for item in invoice.get("line_items", []):
        desc = item.get("description", "")
        qty = item.get("quantity", 0)
        price = item.get("unit_price", 0)
        line_total = float(qty) * float(price)
        c.drawString(20 * mm, y, desc[:60])
        c.drawString(120 * mm, y, str(qty))
        c.drawString(140 * mm, y, f"{float(price):.2f}")
        c.drawString(170 * mm, y, f"{line_total:.2f}")
        y -= 5 * mm

    # Total
    y -= 3 * mm
    c.line(20 * mm, y, 190 * mm, y)
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(140 * mm, y, "Total CHF")
    c.drawString(170 * mm, y, f"{float(invoice.get('total_amount', 0)):.2f}")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
