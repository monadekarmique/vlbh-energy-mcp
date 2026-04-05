from __future__ import annotations
import os
import re
import httpx
from fastapi import APIRouter, Depends, HTTPException
from dependencies import verify_token
from models.shamanes import ShamanePending, ShamanesPendingResponse

router = APIRouter(prefix="/shamanes", tags=["Shamanes"])

SHAMANES = {
    "0300": "Cornelia Althaus",
    "0301": "Flavia Carriero",
    "0302": "Anne Grangier Bays",
    "0303": "Chloé P.Bays",
    "455000": "Patrick Bays",
}

MAKE_API_BASE = "https://eu2.make.com/api/v2"
DATASTORE_ID = 155674

# Key format: {prefix}-{patientId}-{sessionNum}-{sourceCode}
KEY_PATTERN = re.compile(r"^(\d{2})-(.+)-(.+)-(\d{3,6})$")


@router.get("/pending", response_model=ShamanesPendingResponse, summary="Soins en attente par shamane")
async def get_pending(token: None = Depends(verify_token)):
    api_token = os.environ.get("MAKE_API_TOKEN", "")
    if not api_token:
        raise HTTPException(status_code=500, detail="MAKE_API_TOKEN not configured")

    async with httpx.AsyncClient(timeout=20.0) as client:
        records = []
        # Paginate (Make.com max 100 per page)
        for offset in range(0, 500, 100):
            resp = await client.get(
                f"{MAKE_API_BASE}/data-stores/{DATASTORE_ID}/data",
                headers={"Authorization": f"Token {api_token}"},
                params={"pg[limit]": 100, "pg[offset]": offset},
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Make.com API error: {resp.status_code}")
            page = resp.json()
            if not page:
                break
            records.extend(page)
            if len(page) < 100:
                break

    # Group by shamane code
    pending: dict[str, ShamanePending] = {}
    for code, name in SHAMANES.items():
        pending[code] = ShamanePending(code=code, name=name)

    for rec in records:
        key = rec.get("key", "")
        data = rec.get("data", {})
        payload = data.get("payload", "")

        # Skip READ, empty, non-session records
        if not payload or payload == "READ":
            continue
        if not payload.startswith("SVLBH") and not payload.startswith("PIN:"):
            continue

        m = KEY_PATTERN.match(key)
        if not m:
            continue

        prefix, _pid, _sess, source_code = m.groups()

        if source_code not in pending:
            continue

        entry = pending[source_code]
        if prefix == "00":
            entry.soins += 1
        elif prefix == "01":
            entry.recherche += 1
        entry.total = entry.soins + entry.recherche
        entry.records.append(key)

    shamanes_list = sorted(pending.values(), key=lambda s: s.total, reverse=True)
    return ShamanesPendingResponse(
        shamanes=shamanes_list,
        total_soins=sum(s.soins for s in shamanes_list),
        total_recherche=sum(s.recherche for s in shamanes_list),
        total=sum(s.total for s in shamanes_list),
    )
