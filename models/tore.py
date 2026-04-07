from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


class ChampToroidal(BaseModel):
    """
    Champ toroïdal hDOM — paramètres du tore énergétique.
    intensite: puissance du champ (0–100 000)
    coherence: cohérence de phase du tore (0–100%)
    frequence: fréquence dominante en Hz (0.01–1000)
    phase: phase de restauration (REPOS | CHARGE | DECHARGE | EQUILIBRE)
    """
    model_config = ConfigDict(populate_by_name=True)

    intensite: Optional[int] = Field(None, ge=0, le=100_000)
    coherence: Optional[int] = Field(None, ge=0, le=100)
    frequence: Optional[float] = Field(None, ge=0.01, le=1000)
    phase: Optional[str] = Field(None, pattern=r"^(REPOS|CHARGE|DECHARGE|EQUILIBRE)$")


class Glycemie(BaseModel):
    """
    Marqueurs glycémiques liés au stockage énergétique.
    index: indice glycémique énergétique (0–500)
    balance: équilibre glycémique (0–100%)
    absorption: taux d'absorption (0–100%)
    resistanceScore: score de résistance insulinique (0–1000)
    """
    model_config = ConfigDict(populate_by_name=True)

    index: Optional[int] = Field(None, ge=0, le=500)
    balance: Optional[int] = Field(None, ge=0, le=100)
    absorption: Optional[int] = Field(None, ge=0, le=100)
    resistanceScore: Optional[int] = Field(None, ge=0, le=1000, alias="resistanceScore")


class Sclerose(BaseModel):
    """
    Marqueurs de sclérose liés au stockage énergétique.
    score: score de sclérose global (0–1000)
    densite: densité tissulaire (0–100%)
    elasticite: élasticité résiduelle (0–100%)
    permeabilite: perméabilité membranaire (0–100%)
    """
    model_config = ConfigDict(populate_by_name=True)

    score: Optional[int] = Field(None, ge=0, le=1000)
    densite: Optional[int] = Field(None, ge=0, le=100)
    elasticite: Optional[int] = Field(None, ge=0, le=100)
    permeabilite: Optional[int] = Field(None, ge=0, le=100)


class StockageEnergetique(BaseModel):
    """
    Restauration du stockage énergétique — intègre le champ toroïdal
    dans le contexte glycémie/sclérose.
    niveau: niveau de stockage global (0–100 000)
    capacite: capacité maximale de stockage (0–100 000)
    tauxRestauration: taux de restauration (0–100%)
    Auto-calcul: rendement = (niveau / capacite) * 100 quand les deux sont définis.
    """
    model_config = ConfigDict(populate_by_name=True)

    tore: Optional[ChampToroidal] = None
    glycemie: Optional[Glycemie] = None
    sclerose: Optional[Sclerose] = None
    niveau: Optional[int] = Field(None, ge=0, le=100_000)
    capacite: Optional[int] = Field(None, ge=0, le=100_000)
    tauxRestauration: Optional[int] = Field(None, ge=0, le=100, alias="tauxRestauration")
    rendement: Optional[float] = Field(None, ge=0, le=100)

    @model_validator(mode="after")
    def calc_rendement(self) -> "StockageEnergetique":
        if self.niveau is not None and self.capacite is not None and self.capacite > 0:
            self.rendement = round((self.niveau / self.capacite) * 100, 2)
        return self


class TorePushRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_key: str = Field(..., alias="sessionKey")
    stockage: StockageEnergetique
    therapist_name: Optional[str] = Field(None, alias="therapistName")
    platform: str = Field("android")


class TorePullRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_key: str = Field(..., alias="sessionKey")


class TorePullResponse(BaseModel):
    session_key: str
    stockage: Optional[StockageEnergetique] = None
    found: bool = False
    timestamp: Optional[int] = None
