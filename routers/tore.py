from __future__ import annotations
import time
from fastapi import APIRouter, Depends, HTTPException, status
from models.tore import (
    TorePushRequest, TorePullRequest, TorePullResponse,
    StockageEnergetique, ChampToroidal, Glycemie, Sclerose,
    CouplageToreGlycemie, ScleroseTissulaire,
)
from services.make_service import MakeServiceError
from dependencies import get_make_service, verify_token

router = APIRouter(prefix="/tore", tags=["Tore — Stockage Énergétique"])

DATASTORE_ID = 155674


@router.post(
    "/push",
    summary="Push stockage énergétique (tore + glycémie + sclérose) → Make.com",
    status_code=200,
)
async def push_tore(
    payload: TorePushRequest,
    _: None = Depends(verify_token),
    make=Depends(get_make_service),
) -> dict:
    """
    Forward restauration du stockage énergétique to Make.com datastore svlbh-v2.
    Inclut le champ toroïdal, les marqueurs glycémiques et de sclérose.
    Le rendement est auto-calculé si niveau et capacité sont fournis.
    """
    s = payload.stockage
    t = s.tore or ChampToroidal()
    g = s.glycemie or Glycemie()
    sc = s.sclerose or Sclerose()
    cp = s.couplage or CouplageToreGlycemie()
    st = cp.scleroseTissulaire or ScleroseTissulaire()

    body = {
        "sessionKey": payload.session_key,
        "datastoreId": DATASTORE_ID,
        "module": "TORE",
        "therapistName": payload.therapist_name,
        "platform": payload.platform,
        "timestamp": int(time.time() * 1000),

        # Champ toroïdal
        "tore_intensite": t.intensite,
        "tore_coherence": t.coherence,
        "tore_frequence": t.frequence,
        "tore_phase": t.phase,

        # Glycémie
        "glyc_index": g.index,
        "glyc_balance": g.balance,
        "glyc_absorption": g.absorption,
        "glyc_resistanceScore": g.resistanceScore,

        # Sclérose
        "scl_score": sc.score,
        "scl_densite": sc.densite,
        "scl_elasticite": sc.elasticite,
        "scl_permeabilite": sc.permeabilite,

        # Couplage tore–glycémie–sclérose
        "cp_correlationTG": cp.correlationTG,
        "cp_correlationTS": cp.correlationTS,
        "cp_correlationGS": cp.correlationGS,
        "cp_scoreCouplage": cp.scoreCouplage,
        "cp_fluxNet": cp.fluxNet,
        "cp_phaseCouplage": cp.phaseCouplage,

        # Sclérose tissulaire détaillée
        "st_fibroseIndex": st.fibroseIndex,
        "st_zonesAtteintes": st.zonesAtteintes,
        "st_profondeur": st.profondeur,
        "st_revascularisation": st.revascularisation,
        "st_decompaction": st.decompaction,

        # Stockage global
        "stockage_niveau": s.niveau,
        "stockage_capacite": s.capacite,
        "stockage_tauxRestauration": s.tauxRestauration,
        "stockage_rendement": s.rendement,
    }

    try:
        resp = await make._client.post(make._push_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make push tore failed: {resp.text}")
        return {"success": True, "sessionKey": payload.session_key, "make_status": resp.status_code}
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{type(e).__name__}: {e}")


@router.post(
    "/pull",
    summary="Fetch stockage énergétique from Make.com by sessionKey",
    response_model=TorePullResponse,
)
async def pull_tore(
    payload: TorePullRequest,
    _: None = Depends(verify_token),
    make=Depends(get_make_service),
) -> TorePullResponse:
    """
    Retrieve previously stored stockage énergétique by session key.
    """
    body = {
        "sessionKey": payload.session_key,
        "datastoreId": DATASTORE_ID,
        "module": "TORE",
    }
    try:
        resp = await make._client.post(make._pull_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make pull tore failed: {resp.text}")
        raw = resp.text.strip()
        if not raw:
            return TorePullResponse(session_key=payload.session_key, found=False)
        try:
            data = resp.json()
        except Exception:
            return TorePullResponse(session_key=payload.session_key, found=False)
        if not data:
            return TorePullResponse(session_key=payload.session_key, found=False)

        tore = ChampToroidal(
            intensite=data.get("tore_intensite"),
            coherence=data.get("tore_coherence"),
            frequence=data.get("tore_frequence"),
            phase=data.get("tore_phase"),
        )
        glycemie = Glycemie(
            index=data.get("glyc_index"),
            balance=data.get("glyc_balance"),
            absorption=data.get("glyc_absorption"),
            resistanceScore=data.get("glyc_resistanceScore"),
        )
        sclerose = Sclerose(
            score=data.get("scl_score"),
            densite=data.get("scl_densite"),
            elasticite=data.get("scl_elasticite"),
            permeabilite=data.get("scl_permeabilite"),
        )
        sclerose_tiss = ScleroseTissulaire(
            fibroseIndex=data.get("st_fibroseIndex"),
            zonesAtteintes=data.get("st_zonesAtteintes"),
            profondeur=data.get("st_profondeur"),
            revascularisation=data.get("st_revascularisation"),
            decompaction=data.get("st_decompaction"),
        )
        couplage = CouplageToreGlycemie(
            correlationTG=data.get("cp_correlationTG"),
            correlationTS=data.get("cp_correlationTS"),
            correlationGS=data.get("cp_correlationGS"),
            scoreCouplage=data.get("cp_scoreCouplage"),
            fluxNet=data.get("cp_fluxNet"),
            phaseCouplage=data.get("cp_phaseCouplage"),
            scleroseTissulaire=sclerose_tiss,
        )
        stockage = StockageEnergetique(
            tore=tore,
            glycemie=glycemie,
            sclerose=sclerose,
            couplage=couplage,
            niveau=data.get("stockage_niveau"),
            capacite=data.get("stockage_capacite"),
            tauxRestauration=data.get("stockage_tauxRestauration"),
            rendement=data.get("stockage_rendement"),
        )

        return TorePullResponse(
            session_key=payload.session_key,
            stockage=stockage,
            found=True,
            timestamp=data.get("timestamp"),
        )
    except MakeServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{type(e).__name__}: {e}")
