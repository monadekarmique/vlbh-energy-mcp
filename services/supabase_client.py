"""Supabase client singleton for iTherapeut 6.0.

Uses SUPABASE_URL and SUPABASE_SERVICE_KEY env vars.
Row Level Security (RLS) is enforced at the DB level (ADR-001).
"""
from __future__ import annotations

import os
from functools import lru_cache

from supabase import create_client, Client


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a cached Supabase client instance."""
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)
