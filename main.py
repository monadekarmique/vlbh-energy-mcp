"""main.py — updated for iTherapeut 6.0 J3.

This file shows the ADDITIONS to main.py. Do NOT replace the existing file —
add the new imports and router includes AFTER the existing ones.
"""
from __future__ import annotations
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from routers import slm, sla, session, lead, tore, billing
# --- NEW J1 routers ---
from routers import patient, therapy_session, invoice, qrbill
# --- NEW J2 routers ---
from routers import tarif590, scores, rose_des_vents
# --- NEW J3 routers ---
from routers import stats, twint, pipeline
from services.make_service import MakeService
from fastapi_mcp import FastApiMCP


@asynccontextmanager
async def lifespan(app: FastAPI):
    push_url = os.environ["MAKE_WEBHOOK_PUSH_URL"]
    pull_url = os.environ["MAKE_WEBHOOK_PULL_URL"]
    app.state.make_service = MakeService(push_url=push_url, pull_url=pull_url)
    yield
    await app.state.make_service.close()


app = FastAPI(
    title="VLBH Energy MCP",
    description="MCP server for SVLBHPanel — Scores de Lumière sync via Make.com + iTherapeut 6.0",
    version="2.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

# Existing routers (DO NOT TOUCH)
app.include_router(slm.router)
app.include_router(sla.router)
app.include_router(session.router)
app.include_router(lead.router)
app.include_router(tore.router)
app.include_router(billing.router)

# NEW iTherapeut 6.0 routers (J1)
app.include_router(patient.router)
app.include_router(therapy_session.router)
app.include_router(invoice.router)
app.include_router(qrbill.router)

# NEW iTherapeut 6.0 routers (J2)
app.include_router(tarif590.router)
app.include_router(scores.router)
app.include_router(rose_des_vents.router)

# NEW iTherapeut 6.0 routers (J3)
app.include_router(stats.router)
app.include_router(twint.router)
app.include_router(pipeline.router)

mcp = FastApiMCP(app)
mcp.mount()


@app.get("/health", tags=["System"], summary="Render health check")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "vlbh-energy-mcp", "ts": int(time.time())})
