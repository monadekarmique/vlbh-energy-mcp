from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class ShamanePending(BaseModel):
    code: str
    name: str
    soins: int = 0
    recherche: int = 0
    total: int = 0
    records: list[str] = []


class ShamanesPendingResponse(BaseModel):
    shamanes: list[ShamanePending]
    total_soins: int
    total_recherche: int
    total: int
