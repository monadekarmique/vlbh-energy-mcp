"""comms.py — Message queue between Claude sessions (patrickbays ↔ patricktest).

Lightweight mailbox: each side POSTs to /comms/send and polls /comms/inbox.
Storage is a JSON file on the instance disk — ephemeral across Render
redeploys by design: the durable archive for missions stays GitHub issues
(ArbreDeVie/COMMS.md); this channel carries the live dialogue.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from dependencies import verify_token

router = APIRouter(prefix="/comms", tags=["Comms"])

_STORE = Path("data/comms_messages.json")
_LOCK = threading.Lock()

Peer = Literal["patrickbays", "patricktest", "patricktest-a", "patricktest-b", "patricktest-c", "patricktest-d", "patrick"]


class CommsMessage(BaseModel):
    sender: Peer
    recipient: Peer
    type: Literal["mission", "info", "reponse", "question", "ack"] = "info"
    body: str = Field(..., min_length=1, max_length=20000)
    ref: Optional[str] = None  # e.g. "ArbreDeVie#1" or a commit sha


class AckRequest(BaseModel):
    recipient: Peer
    ids: list[int]


def _load() -> list[dict]:
    if not _STORE.exists():
        return []
    try:
        return json.loads(_STORE.read_text())
    except json.JSONDecodeError:
        return []


def _save(messages: list[dict]) -> None:
    _STORE.parent.mkdir(parents=True, exist_ok=True)
    _STORE.write_text(json.dumps(messages, ensure_ascii=False, indent=1))


@router.post("/send", status_code=status.HTTP_201_CREATED, summary="Post a message to the other Claude session")
async def send(msg: CommsMessage, _: None = Depends(verify_token)) -> dict:
    with _LOCK:
        messages = _load()
        new = {
            "id": (messages[-1]["id"] + 1) if messages else 1,
            "ts": int(time.time() * 1000),
            "read": False,
            **msg.model_dump(),
        }
        messages.append(new)
        _save(messages)
    return {"success": True, "id": new["id"], "ts": new["ts"]}


@router.get("/inbox", summary="Poll messages for a recipient")
async def inbox(
    recipient: Peer = Query(...),
    unread_only: bool = Query(True),
    since_id: int = Query(0, ge=0),
    _: None = Depends(verify_token),
) -> dict:
    with _LOCK:
        messages = _load()
    items = [
        m for m in messages
        if m["recipient"] == recipient
        and m["id"] > since_id
        and (not unread_only or not m["read"])
    ]
    return {"count": len(items), "messages": items}


@router.post("/ack", summary="Mark messages as read")
async def ack(req: AckRequest, _: None = Depends(verify_token)) -> dict:
    with _LOCK:
        messages = _load()
        acked = 0
        for m in messages:
            if m["id"] in req.ids and m["recipient"] == req.recipient and not m["read"]:
                m["read"] = True
                acked += 1
        _save(messages)
    if not acked and req.ids:
        raise HTTPException(status_code=404, detail="No matching unread messages")
    return {"success": True, "acked": acked}


@router.get("/health", summary="Channel health and queue depth")
async def health(_: None = Depends(verify_token)) -> dict:
    with _LOCK:
        messages = _load()
    unread = {}
    for m in messages:
        if not m["read"]:
            unread[m["recipient"]] = unread.get(m["recipient"], 0) + 1
    return {"total": len(messages), "unread_by_recipient": unread}
