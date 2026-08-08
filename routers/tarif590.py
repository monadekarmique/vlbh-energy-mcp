"""POST /tarif590/generate — facture Tarif 590 officielle en PDF.

Premier chantier du standard WeasyPrint (DEC Patrick 2026-08-08 : « WeasyPrint
devient le moteur standard de tous mes PDF praticiennes », ordre « 2. tarif 590 »).
Les modèles existaient depuis iTherapeut 6.0 sans router — le SPRINT_STATE les
disait DONE, l'endpoint rendait 404 : cette page ferme cet écart.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response

from dependencies import verify_token
from models.tarif590 import Tarif590Method, Tarif590Request, Tarif590TvaCode
from pdf.engine import render_pdf

router = APIRouter(prefix="/tarif590", tags=["Tarif 590"])

_METHODE_LABELS = {
    Tarif590Method.NATUROPATHIE: "Naturopathie",
    Tarif590Method.HOMEOPATHIE: "Homéopathie",
    Tarif590Method.MTC: "Médecine Traditionnelle Chinoise",
    Tarif590Method.AYURVEDA: "Ayurvéda",
    Tarif590Method.PHYTOTHERAPIE: "Phytothérapie",
    Tarif590Method.REFLEXOLOGIE: "Réflexologie",
    Tarif590Method.SHIATSU: "Shiatsu",
    Tarif590Method.OSTEOPATHIE: "Ostéopathie",
    Tarif590Method.KINESIOLOGIE: "Kinésiologie",
    Tarif590Method.DRAINAGE_LYMPHATIQUE: "Drainage lymphatique",
    Tarif590Method.MASSAGE_THERAPEUTIQUE: "Massage thérapeutique",
    Tarif590Method.THERAPIE_CRANIOSACRALE: "Thérapie craniosacrale",
    Tarif590Method.HYPNOSE: "Hypnose",
    Tarif590Method.SOPHROLOGIE: "Sophrologie",
    Tarif590Method.ACUPUNCTURE: "Acupuncture",
    Tarif590Method.AUTRE: "Autre",
}

_TVA_LABELS = {
    Tarif590TvaCode.EXONERE: "exonéré",
    Tarif590TvaCode.NORMAL: "8.1%",
    Tarif590TvaCode.REDUIT: "2.6%",
}


@router.post("/generate")
def generate(req: Tarif590Request, _: None = Depends(verify_token)) -> Response:
    invoice_number = req.invoice_number or (
        "T590-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    )
    methode = _METHODE_LABELS.get(req.therapeute.method, "Autre")
    if req.therapeute.method == Tarif590Method.AUTRE and req.therapeute.method_text:
        methode = req.therapeute.method_text

    prestations = []
    for p in req.prestations:
        d = p.model_dump()
        d["service_date"] = p.service_date.strftime("%d.%m.%Y")
        d["tva_label"] = _TVA_LABELS.get(p.tva_code, "exonéré")
        prestations.append(d)

    pdf = render_pdf("tarif590.html", {
        "invoice_number": invoice_number,
        "invoice_date": req.invoice_date.strftime("%d.%m.%Y"),
        "reference_number": req.reference_number,
        "maladie": req.maladie,
        "accident": req.accident,
        "diagnostic": req.diagnostic,
        "therapeute": req.therapeute,
        "methode_label": methode,
        "patient": req.patient,
        "prestations": prestations,
        "total_amount": req.total_amount,
    })
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="tarif590-{invoice_number}.pdf"',
            "X-Invoice-Number": invoice_number,
        },
    )
