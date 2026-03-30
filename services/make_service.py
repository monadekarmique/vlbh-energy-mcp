from __future__ import annotations
import time
import httpx
from typing import Optional
from models.slm import ScoresLumiere, SLMPushRequest, SLMPullResponse

DATASTORE_ID = 155674
TIMEOUT = 15.0


class MakeServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        super().__init__(detail)


class MakeService:
    """
    Client for Make.com webhooks → datastore svlbh-v2 (ID 155674).
    Region: eu2 (hook.eu2.make.com)
    """

    def __init__(self, push_url: str, pull_url: str):
        self._push_url = push_url
        self._pull_url = pull_url
        self._client = httpx.AsyncClient(timeout=TIMEOUT)

    async def push_slm(self, payload: SLMPushRequest) -> dict:
        t = payload.therapist
        p = payload.patrick

        body = {
            "sessionKey": payload.session_key,
            "datastoreId": DATASTORE_ID,
            "module": "SLM",
            "therapistName": payload.therapist_name,
            "platform": payload.platform,
            "timestamp": int(time.time() * 1000),

            # Therapist scores
            "SLA_T": t.sla,
            "SLSA_T": t.slsa_effective,
            "SLSA_S1_T": t.slsaS1,
            "SLSA_S2_T": t.slsaS2,
            "SLSA_S3_T": t.slsaS3,
            "SLSA_S4_T": t.slsaS4,
            "SLSA_S5_T": t.slsaS5,
            "SLM_T": t.slm,
            "TotSLM_T": t.totSlm,

            # Patrick scores
            "SLA_P": p.sla,
            "SLSA_P": p.slsa_effective,
            "SLSA_S1_P": p.slsaS1,
            "SLSA_S2_P": p.slsaS2,
            "SLSA_S3_P": p.slsaS3,
            "SLSA_S4_P": p.slsaS4,
            "SLSA_S5_P": p.slsaS5,
            "SLM_P": p.slm,
            "TotSLM_P": p.totSlm,
        }

        resp = await self._client.post(self._push_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make push failed: {resp.text}")
        return {"ok": True, "make_status": resp.status_code}

    async def pull_slm(self, session_key: str) -> SLMPullResponse:
        body = {
            "sessionKey": session_key,
            "datastoreId": DATASTORE_ID,
            "module": "SLM",
        }

        resp = await self._client.post(self._pull_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make pull failed: {resp.text}")

        raw = resp.text
        try:
            data = resp.json()
        except Exception:
            raise MakeServiceError(0, f"Make pull returned non-JSON: {raw[:500]!r}")

        if not data:
            return SLMPullResponse(session_key=session_key, found=False)

        def parse_scores(prefix: str) -> Optional[ScoresLumiere]:
            sla_key = f"SLA_{prefix}"
            if data.get(sla_key) is None and data.get(f"SLM_{prefix}") is None:
                return None
            return ScoresLumiere(
                sla=data.get(f"SLA_{prefix}"),
                slsa=data.get(f"SLSA_{prefix}"),
                slsaS1=data.get(f"SLSA_S1_{prefix}"),
                slsaS2=data.get(f"SLSA_S2_{prefix}"),
                slsaS3=data.get(f"SLSA_S3_{prefix}"),
                slsaS4=data.get(f"SLSA_S4_{prefix}"),
                slsaS5=data.get(f"SLSA_S5_{prefix}"),
                slm=data.get(f"SLM_{prefix}"),
                totSlm=data.get(f"TotSLM_{prefix}"),
            )

        return SLMPullResponse(
            session_key=session_key,
            therapist=parse_scores("T"),
            patrick=parse_scores("P"),
            found=True,
            timestamp=data.get("timestamp"),
        )

    async def close(self):
        await self._client.aclose()
