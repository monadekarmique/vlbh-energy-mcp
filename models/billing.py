from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class BillingPraticien(BaseModel):
    code: Optional[str] = None
    mobile_hash: Optional[str] = None
    nom_praticien: Optional[str] = None
    role: Optional[str] = None
    statut: Optional[str] = None
    formation_max: Optional[str] = None
    compteur_max_patient: int = 0
    compteur: int = 0
    quota_libre: int = 0
    quota_libre_pct: int = 0


class BillingListResponse(BaseModel):
    praticiens: list[BillingPraticien]
    count: int
    groupe: str = "Énergie Féminine Praticiennes Certifiées"
