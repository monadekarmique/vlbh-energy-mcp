"""Shared test fixtures — iTherapeut 6.0.

Mocks Supabase + Make.com so tests run without external services.
"""
from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Set required env vars BEFORE importing app
os.environ.setdefault("MAKE_WEBHOOK_PUSH_URL", "https://hook.test/push")
os.environ.setdefault("MAKE_WEBHOOK_PULL_URL", "https://hook.test/pull")
os.environ.setdefault("VLBH_TOKEN", "test-token-12345")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")

# ---------------------------------------------------------------------------
# Mock Supabase client
# ---------------------------------------------------------------------------

class MockSupabaseResponse:
    """Mimics supabase PostgREST response."""
    def __init__(self, data=None, count=None):
        self.data = data or []
        self.count = count or len(self.data)


class MockQueryBuilder:
    """Chainable mock that returns MockSupabaseResponse at .execute()."""

    def __init__(self, data=None):
        self._data = data or []

    def select(self, *a, **kw):   return self
    def insert(self, data):       self._data = [data] if isinstance(data, dict) else data; return self
    def update(self, data):       return self
    def delete(self):             return self
    def eq(self, *a):             return self
    def neq(self, *a):            return self
    def or_(self, *a):            return self
    def order(self, *a, **kw):    return self
    def range(self, *a):          return self
    def limit(self, *a):          return self
    def execute(self):
        # For inserts, add an id and timestamps to mimic Supabase
        enriched = []
        for item in self._data:
            if isinstance(item, dict):
                item.setdefault("id", "00000000-0000-0000-0000-000000000001")
                item.setdefault("created_at", "2026-04-08T10:00:00+00:00")
                item.setdefault("updated_at", "2026-04-08T10:00:00+00:00")
            enriched.append(item)
        return MockSupabaseResponse(data=enriched, count=len(enriched))


class MockSupabase:
    """Mock supabase client."""
    def table(self, name: str) -> MockQueryBuilder:
        return MockQueryBuilder()


_mock_sb = MockSupabase()


@pytest.fixture(autouse=True)
def mock_supabase(monkeypatch):
    """Replace get_supabase() globally with mock."""
    monkeypatch.setattr("services.supabase_client.get_supabase", lambda: _mock_sb)
    yield _mock_sb

@pytest.fixture()
def client():
    """TestClient with mocked lifespan (no real Make.com connection)."""
    # Patch MakeService so lifespan doesn't fail
    with patch("main.MakeService") as MockMake:
        mock_make = MagicMock()
        mock_make.close = AsyncMock()
        MockMake.return_value = mock_make
        from main import app
        with TestClient(app) as c:
            yield c


HEADERS = {"X-VLBH-Token": "test-token-12345"}