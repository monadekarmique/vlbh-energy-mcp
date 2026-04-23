"""Typed Supabase service for iTherapeut 6.0.

Provides generic CRUD operations and domain-specific methods for migrating
the 5 Make.com datastore 155674 (svlbh-v2) routers to direct Supabase PostgreSQL.

Tables mapped:
  - praticiennes        (practitioners)
  - consultantes        (patients/clients)
  - vlbh_sessions       (SVLBH therapy sessions — Make.com SESSION module)
  - leads               (pipeline — Make.com LEAD module)
  - billing_praticien   (practitioner billing)
  - tores               (tore couplages — Make.com TORE module)
  - slm_scores          (SLM scores — Make.com SLM module)
  - sla_scores          (SLA scores — Make.com SLA module)

Uses SUPABASE_URL and SUPABASE_SERVICE_KEY env vars.
RLS is enforced at the DB level (ADR-001); the service key bypasses RLS
but all queries include mobile_hash / practitioner_id filters to respect
the same row-scoping.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Generic, Optional, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from supabase import Client

from services.supabase_client import get_supabase

logger = logging.getLogger("vlbh.supabase_service")

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SupabaseServiceError(Exception):
    """Raised when a Supabase operation fails."""

    def __init__(self, detail: str, *, status_code: int = 500):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _raise_http(error: SupabaseServiceError) -> None:
    """Convert a SupabaseServiceError to a FastAPI HTTPException."""
    raise HTTPException(status_code=error.status_code, detail=error.detail)


# ---------------------------------------------------------------------------
# Generic CRUD helper
# ---------------------------------------------------------------------------

class CrudTable(Generic[T]):
    """Generic CRUD wrapper around a single Supabase table.

    Usage::

        patients = CrudTable[Patient]("consultantes", Patient)
        row = patients.get_by_id("some-uuid")
        rows = patients.select(filters={"mobile_hash": "abc123"})
        new = patients.insert({"first_name": "Marie", ...})
        patients.update("some-uuid", {"phone": "+41..."})
        patients.delete("some-uuid")
    """

    def __init__(self, table: str, model: type[T], *, client: Client | None = None):
        self._table = table
        self._model = model
        self._client = client or get_supabase()

    # -- helpers --

    def _q(self):  # noqa: ANN202 – postgrest query builder
        return self._client.table(self._table)

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    # -- read --

    def get_by_id(self, row_id: str, *, id_col: str = "id") -> T:
        """Fetch a single row by primary key. Raises 404 if not found."""
        try:
            resp = self._q().select("*").eq(id_col, row_id).execute()
        except Exception as exc:
            raise SupabaseServiceError(f"select failed: {exc}") from exc

        if not resp.data:
            raise SupabaseServiceError(
                f"{self._table} {row_id} not found",
                status_code=404,
            )
        return self._model.model_validate(resp.data[0])

    def select(
        self,
        *,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        ascending: bool = True,
        limit: int = 100,
        offset: int = 0,
        columns: str = "*",
    ) -> list[T]:
        """Select rows with optional equality filters, ordering and pagination."""
        try:
            q = self._q().select(columns)
            for col, val in (filters or {}).items():
                q = q.eq(col, val)
            if order_by:
                q = q.order(order_by, desc=not ascending)
            q = q.range(offset, offset + limit - 1)
            resp = q.execute()
        except Exception as exc:
            raise SupabaseServiceError(f"select failed: {exc}") from exc

        return [self._model.model_validate(row) for row in (resp.data or [])]

    def count(self, *, filters: dict[str, Any] | None = None) -> int:
        """Return count of rows matching filters."""
        try:
            q = self._q().select("*", count="exact")
            for col, val in (filters or {}).items():
                q = q.eq(col, val)
            resp = q.execute()
        except Exception as exc:
            raise SupabaseServiceError(f"count failed: {exc}") from exc
        return resp.count or 0

    # -- write --

    def insert(self, data: dict[str, Any]) -> T:
        """Insert a single row and return the created record."""
        try:
            resp = self._q().insert(data).execute()
        except Exception as exc:
            raise SupabaseServiceError(f"insert failed: {exc}") from exc

        if not resp.data:
            raise SupabaseServiceError("insert returned no data", status_code=500)
        return self._model.model_validate(resp.data[0])

    def upsert(self, data: dict[str, Any], *, on_conflict: str = "id") -> T:
        """Upsert a single row (insert or update on conflict)."""
        try:
            resp = self._q().upsert(data, on_conflict=on_conflict).execute()
        except Exception as exc:
            raise SupabaseServiceError(f"upsert failed: {exc}") from exc

        if not resp.data:
            raise SupabaseServiceError("upsert returned no data", status_code=500)
        return self._model.model_validate(resp.data[0])

    def update(self, row_id: str, data: dict[str, Any], *, id_col: str = "id") -> T:
        """Update a single row by primary key."""
        try:
            resp = self._q().update(data).eq(id_col, row_id).execute()
        except Exception as exc:
            raise SupabaseServiceError(f"update failed: {exc}") from exc

        if not resp.data:
            raise SupabaseServiceError(
                f"{self._table} {row_id} not found for update",
                status_code=404,
            )
        return self._model.model_validate(resp.data[0])

    def delete(self, row_id: str, *, id_col: str = "id") -> bool:
        """Delete a single row by primary key. Returns True if deleted."""
        try:
            resp = self._q().delete().eq(id_col, row_id).execute()
        except Exception as exc:
            raise SupabaseServiceError(f"delete failed: {exc}") from exc
        return bool(resp.data)


# ---------------------------------------------------------------------------
# Row models for svlbh-v2 domain tables (Supabase-side)
# ---------------------------------------------------------------------------

class PraticienneRow(BaseModel):
    """Row in the praticiennes table."""
    id: str | None = None
    mobile_hash: str
    code: str
    nom_praticien: str | None = None
    role: str | None = None          # certifiee | superviseur
    statut: str | None = None        # active | inactive
    formation_max: str | None = None
    compteur_max_patient: int = 0
    compteur: int = 0
    quota_libre: int = 0
    quota_libre_pct: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class ConsultanteRow(BaseModel):
    """Row in the consultantes table (patients/clients)."""
    id: str | None = None
    mobile_hash: str                 # links to praticienne
    patient_id: str
    prenom: str
    nom: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class VlbhSessionRow(BaseModel):
    """Row in the vlbh_sessions table (Make.com SESSION module equivalent)."""
    id: str | None = None
    session_key: str                 # PP-patientId-sessionNum-praticienCode
    mobile_hash: str | None = None
    patient_id: str
    session_num: str
    program_code: str
    practitioner_code: str
    therapist_name: str | None = None
    status: str = "ACTIVE"
    event_count: int = 0
    liberated_count: int = 0
    platform: str = "android"
    timestamp: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class LeadRow(BaseModel):
    """Row in the leads table (Make.com LEAD module equivalent)."""
    id: str | None = None
    shamane_code: str
    mobile_hash: str | None = None
    prenom: str
    nom: str | None = None
    tier: str = "CERTIFIEE"          # LEAD | FORMATION | CERTIFIEE | SUPERVISEUR
    status: str = "ACTIVE"           # ACTIVE | WAITING | COMPLETED
    session_key: str | None = None
    platform: str = "android"
    timestamp: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class BillingRow(BaseModel):
    """Row in the billing_praticien table."""
    id: str | None = None
    mobile_hash: str
    code: str | None = None
    nom_praticien: str | None = None
    role: str | None = None
    statut: str | None = None
    formation_max: str | None = None
    compteur_max_patient: int = 0
    compteur: int = 0
    quota_libre: int = 0
    quota_libre_pct: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class ToreRow(BaseModel):
    """Row in the tores table (Make.com TORE module equivalent).

    Flat structure mirroring the Make.com datastore fields.
    """
    id: str | None = None
    session_key: str
    mobile_hash: str | None = None
    therapist_name: str | None = None
    platform: str = "android"
    timestamp: int | None = None
    # Champ toroidal
    tore_intensite: int | None = None
    tore_coherence: int | None = None
    tore_frequence: float | None = None
    tore_phase: str | None = None
    # Glycemie
    glyc_index: int | None = None
    glyc_balance: int | None = None
    glyc_absorption: int | None = None
    glyc_resistance_score: int | None = None
    # Sclerose
    scl_score: int | None = None
    scl_densite: int | None = None
    scl_elasticite: int | None = None
    scl_permeabilite: int | None = None
    # Couplage
    cp_correlation_tg: int | None = None
    cp_correlation_ts: int | None = None
    cp_correlation_gs: int | None = None
    cp_score_couplage: int | None = None
    cp_flux_net: int | None = None
    cp_phase_couplage: str | None = None
    # Sclerose tissulaire
    st_fibrose_index: int | None = None
    st_zones_atteintes: int | None = None
    st_profondeur: int | None = None
    st_revascularisation: int | None = None
    st_decompaction: int | None = None
    # Stockage global
    stockage_niveau: int | None = None
    stockage_capacite: int | None = None
    stockage_taux_restauration: int | None = None
    stockage_rendement: float | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SlmScoreRow(BaseModel):
    """Row in the slm_scores table (Make.com SLM module equivalent)."""
    id: str | None = None
    session_key: str
    mobile_hash: str | None = None
    therapist_name: str | None = None
    platform: str = "android"
    timestamp: int | None = None
    # Therapist scores
    sla_t: int | None = None
    slsa_t: int | None = None
    slsa_s1_t: int | None = None
    slsa_s2_t: int | None = None
    slsa_s3_t: int | None = None
    slsa_s4_t: int | None = None
    slsa_s5_t: int | None = None
    slm_t: int | None = None
    tot_slm_t: int | None = None
    # Patrick scores
    sla_p: int | None = None
    slsa_p: int | None = None
    slsa_s1_p: int | None = None
    slsa_s2_p: int | None = None
    slsa_s3_p: int | None = None
    slsa_s4_p: int | None = None
    slsa_s5_p: int | None = None
    slm_p: int | None = None
    tot_slm_p: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SlaScoreRow(BaseModel):
    """Row in the sla_scores table (Make.com SLA module equivalent)."""
    id: str | None = None
    session_key: str
    mobile_hash: str | None = None
    therapist_name: str | None = None
    platform: str = "android"
    timestamp: int | None = None
    sla_t: int | None = None
    sla_p: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


# ---------------------------------------------------------------------------
# SupabaseService — domain-level facade
# ---------------------------------------------------------------------------

class SupabaseService:
    """High-level service wrapping all Supabase operations for SVLBH domain.

    This service is designed to eventually replace MakeService calls in the
    5 CRUD routers (slm, sla, session, lead, tore, billing) without modifying
    the existing router files.

    Usage in a new router::

        from services.supabase_service import SupabaseService

        svc = SupabaseService()
        row = svc.sessions.get_by_key("00-12-002-0301")
    """

    def __init__(self, client: Client | None = None):
        self._client = client or get_supabase()

        # Generic CRUD tables
        self.praticiennes = CrudTable[PraticienneRow](
            "praticiennes", PraticienneRow, client=self._client,
        )
        self.consultantes = CrudTable[ConsultanteRow](
            "consultantes", ConsultanteRow, client=self._client,
        )
        self.sessions = CrudTable[VlbhSessionRow](
            "vlbh_sessions", VlbhSessionRow, client=self._client,
        )
        self.leads = CrudTable[LeadRow](
            "leads", LeadRow, client=self._client,
        )
        self.billing = CrudTable[BillingRow](
            "billing_praticien", BillingRow, client=self._client,
        )
        self.tores = CrudTable[ToreRow](
            "tores", ToreRow, client=self._client,
        )
        self.slm_scores = CrudTable[SlmScoreRow](
            "slm_scores", SlmScoreRow, client=self._client,
        )
        self.sla_scores = CrudTable[SlaScoreRow](
            "sla_scores", SlaScoreRow, client=self._client,
        )

    # ------------------------------------------------------------------
    # Domain helpers — SLM
    # ------------------------------------------------------------------

    def push_slm(
        self,
        session_key: str,
        therapist_scores: dict[str, Any],
        patrick_scores: dict[str, Any],
        *,
        therapist_name: str | None = None,
        platform: str = "android",
        mobile_hash: str | None = None,
    ) -> SlmScoreRow:
        """Upsert SLM scores for a session (replaces MakeService.push_slm)."""
        data: dict[str, Any] = {
            "session_key": session_key,
            "therapist_name": therapist_name,
            "platform": platform,
            "timestamp": CrudTable._now_ms(),
            # Therapist
            "sla_t": therapist_scores.get("sla"),
            "slsa_t": therapist_scores.get("slsa"),
            "slsa_s1_t": therapist_scores.get("slsaS1"),
            "slsa_s2_t": therapist_scores.get("slsaS2"),
            "slsa_s3_t": therapist_scores.get("slsaS3"),
            "slsa_s4_t": therapist_scores.get("slsaS4"),
            "slsa_s5_t": therapist_scores.get("slsaS5"),
            "slm_t": therapist_scores.get("slm"),
            "tot_slm_t": therapist_scores.get("totSlm"),
            # Patrick
            "sla_p": patrick_scores.get("sla"),
            "slsa_p": patrick_scores.get("slsa"),
            "slsa_s1_p": patrick_scores.get("slsaS1"),
            "slsa_s2_p": patrick_scores.get("slsaS2"),
            "slsa_s3_p": patrick_scores.get("slsaS3"),
            "slsa_s4_p": patrick_scores.get("slsaS4"),
            "slsa_s5_p": patrick_scores.get("slsaS5"),
            "slm_p": patrick_scores.get("slm"),
            "tot_slm_p": patrick_scores.get("totSlm"),
        }
        if mobile_hash:
            data["mobile_hash"] = mobile_hash
        return self.slm_scores.upsert(data, on_conflict="session_key")

    def pull_slm(self, session_key: str) -> SlmScoreRow | None:
        """Fetch SLM scores by session_key. Returns None if not found."""
        rows = self.slm_scores.select(filters={"session_key": session_key}, limit=1)
        return rows[0] if rows else None

    # ------------------------------------------------------------------
    # Domain helpers — SLA
    # ------------------------------------------------------------------

    def push_sla(
        self,
        session_key: str,
        sla_therapist: int | None,
        sla_patrick: int | None,
        *,
        therapist_name: str | None = None,
        platform: str = "android",
        mobile_hash: str | None = None,
    ) -> SlaScoreRow:
        """Upsert SLA scores for a session (replaces MakeService.push_sla)."""
        data: dict[str, Any] = {
            "session_key": session_key,
            "therapist_name": therapist_name,
            "platform": platform,
            "timestamp": CrudTable._now_ms(),
            "sla_t": sla_therapist,
            "sla_p": sla_patrick,
        }
        if mobile_hash:
            data["mobile_hash"] = mobile_hash
        return self.sla_scores.upsert(data, on_conflict="session_key")

    def pull_sla(self, session_key: str) -> SlaScoreRow | None:
        """Fetch SLA scores by session_key."""
        rows = self.sla_scores.select(filters={"session_key": session_key}, limit=1)
        return rows[0] if rows else None

    # ------------------------------------------------------------------
    # Domain helpers — Sessions
    # ------------------------------------------------------------------

    def push_session(
        self,
        session_key: str,
        patient_id: str,
        session_num: str,
        program_code: str,
        practitioner_code: str,
        *,
        therapist_name: str | None = None,
        status: str = "ACTIVE",
        event_count: int = 0,
        liberated_count: int = 0,
        platform: str = "android",
        mobile_hash: str | None = None,
    ) -> VlbhSessionRow:
        """Upsert a VLBH session (replaces MakeService.push_session)."""
        data: dict[str, Any] = {
            "session_key": session_key,
            "patient_id": patient_id,
            "session_num": session_num,
            "program_code": program_code,
            "practitioner_code": practitioner_code,
            "therapist_name": therapist_name,
            "status": status,
            "event_count": event_count,
            "liberated_count": liberated_count,
            "platform": platform,
            "timestamp": CrudTable._now_ms(),
        }
        if mobile_hash:
            data["mobile_hash"] = mobile_hash
        return self.sessions.upsert(data, on_conflict="session_key")

    def pull_session(self, session_key: str) -> VlbhSessionRow | None:
        """Fetch a session by session_key."""
        rows = self.sessions.select(filters={"session_key": session_key}, limit=1)
        return rows[0] if rows else None

    # ------------------------------------------------------------------
    # Domain helpers — Leads
    # ------------------------------------------------------------------

    def push_lead(
        self,
        shamane_code: str,
        prenom: str,
        *,
        nom: str | None = None,
        tier: str = "CERTIFIEE",
        lead_status: str = "ACTIVE",
        session_key: str | None = None,
        platform: str = "android",
        mobile_hash: str | None = None,
    ) -> LeadRow:
        """Upsert a lead (replaces MakeService.push_lead)."""
        data: dict[str, Any] = {
            "shamane_code": shamane_code,
            "prenom": prenom,
            "nom": nom,
            "tier": tier,
            "status": lead_status,
            "session_key": session_key,
            "platform": platform,
            "timestamp": CrudTable._now_ms(),
        }
        if mobile_hash:
            data["mobile_hash"] = mobile_hash
        return self.leads.upsert(data, on_conflict="shamane_code")

    def pull_lead(self, shamane_code: str) -> LeadRow | None:
        """Fetch a lead by shamane_code."""
        rows = self.leads.select(filters={"shamane_code": shamane_code}, limit=1)
        return rows[0] if rows else None

    # ------------------------------------------------------------------
    # Domain helpers — Tores
    # ------------------------------------------------------------------

    def push_tore(self, session_key: str, tore_data: dict[str, Any]) -> ToreRow:
        """Upsert tore stockage energetique (replaces Make tore push)."""
        tore_data["session_key"] = session_key
        tore_data["timestamp"] = CrudTable._now_ms()
        return self.tores.upsert(tore_data, on_conflict="session_key")

    def pull_tore(self, session_key: str) -> ToreRow | None:
        """Fetch tore data by session_key."""
        rows = self.tores.select(filters={"session_key": session_key}, limit=1)
        return rows[0] if rows else None

    # ------------------------------------------------------------------
    # Domain helpers — Billing
    # ------------------------------------------------------------------

    def list_active_praticiens(self) -> list[BillingRow]:
        """List active certified/supervisor practitioners."""
        try:
            resp = (
                self._client.table("billing_praticien")
                .select("*")
                .eq("statut", "active")
                .in_("role", ["certifiee", "superviseur"])
                .execute()
            )
        except Exception as exc:
            raise SupabaseServiceError(f"billing list failed: {exc}") from exc
        return [BillingRow.model_validate(r) for r in (resp.data or [])]

    def get_praticien_by_hash(self, mobile_hash: str) -> BillingRow | None:
        """Fetch a single practitioner by mobile_hash."""
        rows = self.billing.select(filters={"mobile_hash": mobile_hash}, limit=1)
        return rows[0] if rows else None

    # ------------------------------------------------------------------
    # Domain helpers — Consultantes (patients scoped by mobile_hash)
    # ------------------------------------------------------------------

    def list_consultantes(self, mobile_hash: str) -> list[ConsultanteRow]:
        """List all consultantes for a practitioner (by mobile_hash)."""
        return self.consultantes.select(
            filters={"mobile_hash": mobile_hash},
            order_by="created_at",
            ascending=False,
        )

    def get_consultante(self, mobile_hash: str, patient_id: str) -> ConsultanteRow | None:
        """Fetch a single consultante scoped by mobile_hash."""
        rows = self.consultantes.select(
            filters={"mobile_hash": mobile_hash, "patient_id": patient_id},
            limit=1,
        )
        return rows[0] if rows else None

    # ------------------------------------------------------------------
    # Utility — batch & mobile_hash scoping
    # ------------------------------------------------------------------

    def sessions_for_hash(
        self,
        mobile_hash: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[VlbhSessionRow]:
        """List sessions scoped to a mobile_hash (RLS pattern)."""
        return self.sessions.select(
            filters={"mobile_hash": mobile_hash},
            order_by="timestamp",
            ascending=False,
            limit=limit,
            offset=offset,
        )

    def scores_for_hash(
        self,
        mobile_hash: str,
        *,
        limit: int = 50,
    ) -> list[SlmScoreRow]:
        """List SLM scores scoped to a mobile_hash."""
        return self.slm_scores.select(
            filters={"mobile_hash": mobile_hash},
            order_by="timestamp",
            ascending=False,
            limit=limit,
        )
