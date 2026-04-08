"""Tarif 590 PDF generation router — iTherapeut 6.0 (Plan 59).

Endpoint:
  POST /tarif590/generate → generates an official Tarif 590 PDF

The Tarif 590 is the standard Swiss complementary therapy invoice format,
required by all complementary health insurers for reimbursement claims.
Layout follows the official tarif590.ch specification.
"""
from __future__ import annotations

import io
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from dependencies import verify_token
from models.tarif590 import (
    Tarif590Method,
    Tarif590Request,
    Tarif590Response,
    Tarif590Therapeute,
    Tarif590Patient,
    Tarif590Prestation,
    Tarif590TvaCode,
)
from services.supabase_client import get_supabase

router = APIRouter(
    prefix="/tarif590",
    tags=["Tarif 590"],
    dependencies=[Depends(verify_token)],
)


def _generate_tarif590_number(sb) -> str:
    """Generate sequential tarif590 number: T590-YYYY-NNNN."""
    from datetime import date as d
    year = d.today().year
    result = (
        sb.table("tarif590_invoices")
        .select("invoice_number")
        .ilike("invoice_number", f"T590-{year}-%")
        .order("invoice_number", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        last = result.data[0]["invoice_number"]
        seq = int(last.split("-")[-1]) + 1
    else:
        seq = 1
    return f"T590-{year}-{seq:04d}"


def _resolve_therapeute(sb, body: Tarif590Request) -> Tarif590Therapeute:
    """Resolve therapeute info from practitioner_id or request body."""
    if body.practitioner_id:
        result = sb.table("practitioners").select("*").eq("id", str(body.practitioner_id)).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Practitioner not found")
        prac = result.data[0]
        method = Tarif590Method(prac["therapy_method"]) if prac.get("therapy_method") else Tarif590Method.AUTRE
        return Tarif590Therapeute(
            name=f"{prac['first_name']} {prac['last_name']}",
            street=prac["street"],
            house_number=prac.get("house_number"),
            postal_code=prac["postal_code"],
            city=prac["city"],
            phone=prac.get("phone"),
            rcc_number=prac["rcc_number"],
            nif_number=prac.get("nif_number"),
            gln_number=prac.get("gln_number"),
            method=method,
            method_text=prac.get("therapy_method_text"),
        )
    if body.therapeute:
        return body.therapeute
    raise HTTPException(
        status_code=422,
        detail="Either practitioner_id or therapeute must be provided",
    )


@router.post("/generate", summary="Générer un PDF Tarif 590")
async def generate_tarif590(body: Tarif590Request):
    """Generate an official Tarif 590 PDF and return it as a download.

    If practitioner_id is provided, therapeute info is auto-filled
    from the practitioner profile.
    Optionally stores a record in the tarif590_invoices table.
    """
    sb = get_supabase()

    # Resolve therapeute (from practitioner or request body)
    therapeute = _resolve_therapeute(sb, body)

    # Auto-generate invoice number if not provided
    invoice_number = body.invoice_number or _generate_tarif590_number(sb)

    # Inject resolved therapeute into body for PDF rendering
    body.therapeute = therapeute

    # Render the PDF
    pdf_bytes = _render_tarif590_pdf(body, invoice_number)

    # Store record in DB (non-blocking — if table doesn't exist yet, skip)
    try:
        record = {
            "invoice_number": invoice_number,
            "therapeute_name": therapeute.name,
            "therapeute_rcc": therapeute.rcc_number,
            "patient_name": f"{body.patient.first_name} {body.patient.last_name}",
            "patient_dob": body.patient.date_of_birth.isoformat(),
            "invoice_date": body.invoice_date.isoformat(),
            "total_amount": float(body.total_amount or 0),
            "prestations_count": len(body.prestations),
            "diagnostic": body.diagnostic,
        }
        if body.patient_id:
            record["patient_id"] = str(body.patient_id)
        if body.therapy_session_id:
            record["therapy_session_id"] = str(body.therapy_session_id)
        if body.practitioner_id:
            record["practitioner_id"] = str(body.practitioner_id)
        sb.table("tarif590_invoices").insert(record).execute()
    except Exception:
        pass  # Table may not exist yet — PDF generation still works

    # Return PDF
    filename = f"Tarif590_{invoice_number}_{body.patient.last_name}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/generate/json", response_model=Tarif590Response,
             summary="Générer un Tarif 590 — métadonnées uniquement")
async def generate_tarif590_json(body: Tarif590Request):
    """Return Tarif 590 metadata without PDF (useful for previews)."""
    sb = get_supabase()
    therapeute = _resolve_therapeute(sb, body)
    invoice_number = body.invoice_number or _generate_tarif590_number(sb)
    return Tarif590Response(
        invoice_number=invoice_number,
        total_amount=body.total_amount or Decimal("0"),
        patient_name=f"{body.patient.first_name} {body.patient.last_name}",
        therapeute_name=therapeute.name,
        prestations_count=len(body.prestations),
        generated_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# PDF Rendering — Official Tarif 590 layout
# ---------------------------------------------------------------------------

def _render_tarif590_pdf(req: Tarif590Request, invoice_number: str) -> bytes:
    """Render an official Tarif 590 PDF using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    margin_l = 15 * mm
    margin_r = width - 15 * mm
    content_w = margin_r - margin_l

    y = height - 15 * mm

    # === HEADER ===
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_l, y, "Tarif 590 — Facture thérapie complémentaire")
    y -= 4 * mm
    c.setStrokeColor(colors.HexColor("#2563EB"))
    c.setLineWidth(1.5)
    c.line(margin_l, y, margin_r, y)
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    y -= 8 * mm

    # === THERAPEUTE / PATIENT — two columns ===
    col_mid = margin_l + content_w / 2
    yt = y

    # Left: Thérapeute
    t = req.therapeute
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin_l, yt, "Thérapeute / Fournisseur de prestations")
    yt -= 4.5 * mm
    c.setFont("Helvetica", 8)
    c.drawString(margin_l, yt, t.name)
    yt -= 3.5 * mm
    addr = f"{t.street or ''} {t.house_number or ''}".strip()
    c.drawString(margin_l, yt, addr)
    yt -= 3.5 * mm
    c.drawString(margin_l, yt, f"{t.postal_code} {t.city}")
    yt -= 3.5 * mm
    if t.phone:
        c.drawString(margin_l, yt, f"Tél: {t.phone}")
        yt -= 3.5 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin_l, yt, f"N° RCC: {t.rcc_number}")
    yt -= 3.5 * mm
    if t.gln_number:
        c.drawString(margin_l, yt, f"GLN: {t.gln_number}")
        yt -= 3.5 * mm
    if t.nif_number:
        c.drawString(margin_l, yt, f"NIF: {t.nif_number}")
        yt -= 3.5 * mm
    method_text = t.method_text or t.method.name.replace("_", " ").title()
    c.setFont("Helvetica", 8)
    c.drawString(margin_l, yt, f"Méthode: {method_text}")
    yt_left = yt

    # Right: Patient
    yp = y
    p = req.patient
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_mid + 5 * mm, yp, "Patient / Assuré")
    yp -= 4.5 * mm
    c.setFont("Helvetica", 8)
    c.drawString(col_mid + 5 * mm, yp, f"{p.last_name} {p.first_name}")
    yp -= 3.5 * mm
    c.drawString(col_mid + 5 * mm, yp, f"Né(e) le: {p.date_of_birth.strftime('%d.%m.%Y')}")
    yp -= 3.5 * mm
    if p.street:
        addr_p = f"{p.street or ''} {p.house_number or ''}".strip()
        c.drawString(col_mid + 5 * mm, yp, addr_p)
        yp -= 3.5 * mm
    if p.postal_code:
        c.drawString(col_mid + 5 * mm, yp, f"{p.postal_code} {p.city or ''}")
        yp -= 3.5 * mm
    if p.avs_number:
        c.drawString(col_mid + 5 * mm, yp, f"N° AVS: {p.avs_number}")
        yp -= 3.5 * mm
    if p.insurance_name:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(col_mid + 5 * mm, yp, f"Assurance: {p.insurance_name}")
        yp -= 3.5 * mm
        c.setFont("Helvetica", 8)
    if p.insurance_number:
        c.drawString(col_mid + 5 * mm, yp, f"N° police: {p.insurance_number}")
        yp -= 3.5 * mm
    c.drawString(col_mid + 5 * mm, yp, f"Canton: {p.canton}")
    yp_right = yp

    y = min(yt_left, yp_right) - 6 * mm
    c.line(margin_l, y, margin_r, y)
    y -= 6 * mm

    # === INVOICE META ===
    c.setFont("Helvetica", 8)
    c.drawString(margin_l, y, f"N° facture: {invoice_number}")
    c.drawString(col_mid + 5 * mm, y, f"Date: {req.invoice_date.strftime('%d.%m.%Y')}")
    y -= 4 * mm

    # Accident / Maladie
    type_txt = []
    if req.maladie:
        type_txt.append("Maladie")
    if req.accident:
        type_txt.append("Accident (LAA)")
    c.drawString(margin_l, y, f"Type: {' / '.join(type_txt)}")
    y -= 4 * mm

    # Diagnostic
    if req.diagnostic:
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(margin_l, y, f"Diagnostic: {req.diagnostic}")
        y -= 4 * mm

    y -= 2 * mm
    c.line(margin_l, y, margin_r, y)
    y -= 5 * mm

    # === PRESTATIONS TABLE ===
    # Column positions
    col_date = margin_l
    col_code = margin_l + 22 * mm
    col_desc = margin_l + 40 * mm
    col_dur = margin_l + 115 * mm
    col_prix = margin_l + 132 * mm
    col_qte = margin_l + 150 * mm
    col_montant = margin_l + 163 * mm

    # Header
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(col_date, y, "Date")
    c.drawString(col_code, y, "Code")
    c.drawString(col_desc, y, "Description")
    c.drawString(col_dur, y, "Durée")
    c.drawString(col_prix, y, "Prix/5min")
    c.drawString(col_qte, y, "Qté")
    c.drawRightString(margin_r, y, "Montant")
    y -= 2 * mm
    c.line(margin_l, y, margin_r, y)
    y -= 4 * mm

    # Rows
    c.setFont("Helvetica", 7.5)
    total = Decimal("0")
    for pr in req.prestations:
        if y < 35 * mm:
            # New page
            c.showPage()
            y = height - 20 * mm
            c.setFont("Helvetica", 7.5)

        amt = pr.amount or (pr.unit_price * pr.quantity)
        total += amt
        c.drawString(col_date, y, pr.date.strftime("%d.%m.%Y"))
        c.drawString(col_code, y, pr.code_prestation)
        # Truncate description if needed
        desc = pr.description[:45]
        c.drawString(col_desc, y, desc)
        c.drawString(col_dur, y, f"{pr.duration_minutes} min")
        c.drawString(col_prix, y, f"{float(pr.unit_price):.2f}")
        c.drawString(col_qte, y, f"{float(pr.quantity):.1f}")
        c.drawRightString(margin_r, y, f"{float(amt):.2f}")
        y -= 4 * mm

    # === TOTALS ===
    y -= 2 * mm
    c.line(margin_l, y, margin_r, y)
    y -= 6 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin_l, y, "Total CHF")
    c.drawRightString(margin_r, y, f"{float(total):.2f}")
    y -= 5 * mm

    # TVA line
    c.setFont("Helvetica", 7.5)
    c.drawString(margin_l, y, "TVA: exonéré (prestations de santé)")
    y -= 8 * mm

    # === FOOTER ===
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#6B7280"))
    c.drawString(margin_l, y,
                 "Document généré par iTherapeut 6.0 — conforme Tarif 590 (tarif590.ch)")
    y -= 3.5 * mm
    c.drawString(margin_l, y, f"RCC: {req.therapeute.rcc_number} — "
                 f"Patient: {req.patient.last_name} {req.patient.first_name}")
    c.setFillColor(colors.black)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
