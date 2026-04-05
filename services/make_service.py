from __future__ import annotations
import time
import httpx
from typing import Optional
from models.slm import ScoresLumiere, SLMPushRequest, SLMPullResponse
from models.lead import LeadPushRequest, LeadPullResponse
from models.session import SessionPushRequest, SessionPullResponse
from models.sla import SLAPushRequest, SLAPullResponse

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

        raw = resp.text.strip()
        if not raw:
            return SLMPullResponse(session_key=session_key, found=False)

        try:
            data = resp.json()
        except Exception:
            # Make.com returns "Accepted" when the pull scenario has no Webhook Response module
            return SLMPullResponse(session_key=session_key, found=False)

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

    async def push_lead(self, payload: LeadPushRequest) -> dict:
        body = {
            "shamaneCode": payload.shamane_code,
            "datastoreId": DATASTORE_ID,
            "module": "LEAD",
            "prenom": payload.prenom,
            "nom": payload.nom,
            "tier": payload.tier,
            "status": payload.status,
            "sessionKey": payload.session_key,
            "platform": payload.platform,
            "timestamp": int(time.time() * 1000),
        }
        resp = await self._client.post(self._push_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make push lead failed: {resp.text}")
        return {"ok": True, "make_status": resp.status_code}

    async def pull_lead(self, shamane_code: str) -> LeadPullResponse:
        body = {
            "shamaneCode": shamane_code,
            "datastoreId": DATASTORE_ID,
            "module": "LEAD",
        }
        resp = await self._client.post(self._pull_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make pull lead failed: {resp.text}")
        raw = resp.text.strip()
        if not raw:
            return LeadPullResponse(shamane_code=shamane_code, found=False)
        try:
            data = resp.json()
        except Exception:
            return LeadPullResponse(shamane_code=shamane_code, found=False)
        if not data:
            return LeadPullResponse(shamane_code=shamane_code, found=False)
        return LeadPullResponse(
            shamane_code=shamane_code,
            prenom=data.get("prenom"),
            nom=data.get("nom"),
            tier=data.get("tier"),
            status=data.get("status"),
            session_key=data.get("sessionKey"),
            found=True,
            timestamp=data.get("timestamp"),
        )

    async def push_session(self, payload: SessionPushRequest) -> dict:
        body = {
            "sessionKey": payload.session_key,
            "datastoreId": DATASTORE_ID,
            "module": "SESSION",
            "patientId": payload.patient_id,
            "sessionNum": payload.session_num,
            "programCode": payload.program_code,
            "practitionerCode": payload.practitioner_code,
            "therapistName": payload.therapist_name,
            "status": payload.status,
            "eventCount": payload.event_count,
            "liberatedCount": payload.liberated_count,
            "platform": payload.platform,
            "timestamp": int(time.time() * 1000),
        }
        resp = await self._client.post(self._push_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make push session failed: {resp.text}")
        return {"ok": True, "make_status": resp.status_code}

    async def pull_session(self, session_key: str) -> SessionPullResponse:
        body = {
            "sessionKey": session_key,
            "datastoreId": DATASTORE_ID,
            "module": "SESSION",
        }
        resp = await self._client.post(self._pull_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make pull session failed: {resp.text}")
        raw = resp.text.strip()
        if not raw:
            return SessionPullResponse(session_key=session_key, found=False)
        try:
            data = resp.json()
        except Exception:
            return SessionPullResponse(session_key=session_key, found=False)
        if not data:
            return SessionPullResponse(session_key=session_key, found=False)
        return SessionPullResponse(
            session_key=session_key,
            patient_id=data.get("patientId"),
            session_num=data.get("sessionNum"),
            program_code=data.get("programCode"),
            practitioner_code=data.get("practitionerCode"),
            therapist_name=data.get("therapistName"),
            status=data.get("status"),
            event_count=data.get("eventCount"),
            liberated_count=data.get("liberatedCount"),
            found=True,
            timestamp=data.get("timestamp"),
        )

    async def push_sla(self, payload: SLAPushRequest) -> dict:
        body = {
            "sessionKey": payload.session_key,
            "datastoreId": DATASTORE_ID,
            "module": "SLA",
            "therapistName": payload.therapist_name,
            "platform": payload.platform,
            "timestamp": int(time.time() * 1000),
            "SLA_T": payload.sla_therapist,
            "SLA_P": payload.sla_patrick,
        }
        resp = await self._client.post(self._push_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make push SLA failed: {resp.text}")
        return {"ok": True, "make_status": resp.status_code}

    async def pull_sla(self, session_key: str) -> SLAPullResponse:
        body = {
            "sessionKey": session_key,
            "datastoreId": DATASTORE_ID,
            "module": "SLA",
        }
        resp = await self._client.post(self._pull_url, json=body)
        if resp.status_code not in range(200, 300):
            raise MakeServiceError(resp.status_code, f"Make pull SLA failed: {resp.text}")
        raw = resp.text.strip()
        if not raw:
            return SLAPullResponse(session_key=session_key, found=False)
        try:
            data = resp.json()
        except Exception:
            return SLAPullResponse(session_key=session_key, found=False)
        if not data:
            return SLAPullResponse(session_key=session_key, found=False)
        return SLAPullResponse(
            session_key=session_key,
            sla_therapist=data.get("SLA_T"),
            sla_patrick=data.get("SLA_P"),
            found=True,
            timestamp=data.get("timestamp"),
        )

    async def close(self):
        await self._client.aclose()
