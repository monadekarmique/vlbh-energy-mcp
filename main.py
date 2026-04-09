"""main.py — VLBH Energy MCP + iTherapeut 6.0

All routers consolidated on main.
"""
from __future__ import annotations
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from routers import slm, sla, session, lead, tore, billing, dashboard, workspace, flux_whatsapp
# --- iTherapeut 6.0 routers ---
from routers import patient, therapy_session, invoice, qrbill
from routers import tarif590, scores, rose_des_vents
from routers import stats, twint, pipeline
from routers import chromo, auth, tore_session
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
    version="2.3.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(dashboard.router)
app.include_router(slm.router)
app.include_router(sla.router)
app.include_router(session.router)
app.include_router(lead.router)
app.include_router(tore.router)
app.include_router(billing.router)
app.include_router(workspace.router)
app.include_router(flux_whatsapp.router)

# iTherapeut 6.0 routers (J1)
app.include_router(patient.router)
app.include_router(therapy_session.router)
app.include_router(invoice.router)
app.include_router(qrbill.router)

# iTherapeut 6.0 routers (J2)
app.include_router(tarif590.router)
app.include_router(scores.router)
app.include_router(rose_des_vents.router)

# iTherapeut 6.0 routers (J3)
app.include_router(stats.router)
app.include_router(twint.router)
app.include_router(pipeline.router)

# iTherapeut 6.0 routers (J4)
app.include_router(chromo.router)
app.include_router(auth.router)
app.include_router(tore_session.router)

mcp = FastApiMCP(app)
mcp.mount()


@app.get("/health", tags=["System"], summary="Render health check")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "vlbh-energy-mcp", "ts": int(time.time())})
