"""Unit tests for Pydantic models — validation rules."""
import pytest
from pydantic import ValidationError

from models.chromo import (
    ChromoPrescriptionItem, ChromoSessionCreate, ColorGel,
    Meridien, Element, MERIDIEN_ELEMENT_MAP,
)
from models.tore_session import ToreSnapshot, ToreSessionCreate
from models.auth import RegisterRequest, LoginRequest
from models.pipeline import PipelineLeadCreate


class TestChromoModels:
    def test_meridien_element_map_complete(self):
        """All 14 meridians must be in the map."""
        assert len(MERIDIEN_ELEMENT_MAP) == 14
        for m in Meridien:
            assert m.value in MERIDIEN_ELEMENT_MAP

    def test_color_gels_count(self):
        assert len(ColorGel) == 12

    def test_elements_count(self):
        assert len(Element) == 5
    def test_prescription_valid(self):
        p = ChromoPrescriptionItem(
            meridien="poumon", color_gel="indigo",
            action="tonify", duration_seconds=180,
        )
        assert p.meridien == Meridien.POUMON

    def test_prescription_invalid_action(self):
        with pytest.raises(ValidationError):
            ChromoPrescriptionItem(
                meridien="poumon", color_gel="indigo",
                action="BOOM", duration_seconds=180,
            )

    def test_prescription_duration_bounds(self):
        with pytest.raises(ValidationError):
            ChromoPrescriptionItem(
                meridien="poumon", color_gel="indigo",
                action="tonify", duration_seconds=5,  # min 30
            )

    def test_session_empty_prescriptions(self):
        with pytest.raises(ValidationError):
            ChromoSessionCreate(
                therapy_session_id="00000000-0000-0000-0000-000000000010",
                patient_id="00000000-0000-0000-0000-000000000020",
                prescriptions=[],
            )

class TestToreModels:
    def test_snapshot_valid(self):
        s = ToreSnapshot(tore_intensite=5000, tore_coherence=45)
        assert s.tore_intensite == 5000

    def test_snapshot_coherence_max(self):
        with pytest.raises(ValidationError):
            ToreSnapshot(tore_coherence=999)

    def test_snapshot_phase_enum(self):
        s = ToreSnapshot(tore_phase="CHARGE")
        assert s.tore_phase == "CHARGE"

    def test_snapshot_invalid_phase(self):
        with pytest.raises(ValidationError):
            ToreSnapshot(tore_phase="INVALID")


class TestAuthModels:
    def test_register_valid(self):
        r = RegisterRequest(
            email="test@example.com",
            password="secure123",
            full_name="Test User",
            role="patient",
        )
        assert r.role == "patient"

    def test_register_short_password(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="t@t.com", password="short")

    def test_register_invalid_role(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="t@t.com", password="secure123", role="admin",
            )

class TestPipelineModels:
    def test_lead_valid(self):
        lead = PipelineLeadCreate(
            first_name="Jean", last_name="Martin",
            stage="new", source="website", priority=1,
        )
        assert lead.stage == "new"

    def test_lead_invalid_stage(self):
        with pytest.raises(ValidationError):
            PipelineLeadCreate(
                first_name="Bad", last_name="Stage",
                stage="INVALID",
            )

    def test_lead_priority_bounds(self):
        with pytest.raises(ValidationError):
            PipelineLeadCreate(
                first_name="Bad", last_name="Priority",
                priority=5,
            )