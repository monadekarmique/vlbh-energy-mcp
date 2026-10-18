"""Le jeton statique SEUL ne suffit plus (fiche 271f6a10, 19.10.2026) ; DIGISHA_JETON_SEUL=oui le rouvre."""
import asyncio
import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routers import digisha as d  # noqa: E402


class _Req:
    def __init__(self):
        self.headers = {"user-agent": "test", "x-forwarded-for": "1.2.3.4"}
        self.url = type("U", (), {"path": "/digisha/chat"})()
        self.client = None


async def _sans_session(authorization):
    return None


async def _avec_session(authorization):
    return "uid-1"


async def _rien(*a, **k):
    return None


def test_sans_session_refuse_meme_avec_le_bon_jeton(monkeypatch):
    monkeypatch.setattr(d, "resolve_uid", _sans_session)
    monkeypatch.setenv("DIGISHA_TOKEN", "le-bon")
    monkeypatch.delenv("DIGISHA_JETON_SEUL", raising=False)
    with pytest.raises(HTTPException) as e:
        asyncio.run(d.authorize_caller(_Req(), "le-bon", None))
    assert e.value.status_code == 401


def test_le_filet_rouvre_le_jeton(monkeypatch):
    monkeypatch.setattr(d, "resolve_uid", _sans_session)
    monkeypatch.setattr(d, "_quota", _rien)
    monkeypatch.setenv("DIGISHA_TOKEN", "le-bon")
    monkeypatch.setenv("DIGISHA_JETON_SEUL", "oui")
    assert asyncio.run(d.authorize_caller(_Req(), "le-bon", None)) is None
    with pytest.raises(HTTPException):
        asyncio.run(d.authorize_caller(_Req(), "mauvais", None))


def test_une_session_passe_sans_jeton(monkeypatch):
    monkeypatch.setattr(d, "resolve_uid", _avec_session)
    monkeypatch.setattr(d, "_quota", _rien)
    monkeypatch.delenv("DIGISHA_JETON_SEUL", raising=False)
    assert asyncio.run(d.authorize_caller(_Req(), None, "Bearer x")) == "uid-1"
