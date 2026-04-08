from __future__ import annotations
import os
from fastapi import APIRouter, Depends, HTTPException, status
from models.billing import BillingPraticien, BillingListResponse
from services.make_service import MakeServiceError
from dependencies import get_make_service, verify_token

router = APIRouter(prefix="/billing", tags=["Billing Praticiens"])

BILLING_LIST_WEBHOOK = os.environ.get("MAKE_WEBHOOK_BILLING_LIST_URL", "")


@router.get(
    "/list",
    summary="List active practitioners from billing_praticien",
    response_model=BillingListResponse,
)
async def list_active_praticiens(
    _: None = Depends(verify_token),
    make=Depends(get_make_service),
) -> BillingListResponse:
    """
    Calls the SVLBH Billing List webhook on Make.com which returns
    all active practitioners from billing_praticien #156396.
    """
    if not BILLING_LIST_WEBHOOK:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MAKE_WEBHOOK_BILLING_LIST_URL not configured",
        )

    try:
        resp = await make._client.post(BILLING_LIST_WEBHOOK, json={"action": "list"})
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make billing list failed: {resp.text}")

        raw = resp.text.strip()
        if not raw:
            return BillingListResponse(praticiens=[], count=0)

        try:
            data = resp.json()
        except Exception:
            return BillingListResponse(praticiens=[], count=0)

        if not isinstance(data, list):
            data = [data] if data else []

        praticiens = [
            BillingPraticien(
                code=item.get("code"),
                mobile_hash=item.get("mobile_hash"),
                nom_praticien=item.get("nom_praticien"),
                role=item.get("role"),
                statut=item.get("statut"),
                formation_max=item.get("formation_max"),
                compteur_max_patient=item.get("compteur_max_patient", 0) or 0,
                compteur=item.get("compteur", 0) or 0,
                quota_libre=item.get("quota_libre", 0) or 0,
                quota_libre_pct=item.get("quota_libre_pct", 0) or 0,
            )
            for item in data
            if item.get("statut") == "active" and item.get("role") in ("certifiee", "superviseur")
        ]

        return BillingListResponse(
            praticiens=praticiens,
            count=len(praticiens),
        )

    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{type(e).__name__}: {e}",
        )
