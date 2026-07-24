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
from routers import auth
from routers import invite
from routers import digisha
from routers import comms
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
app.include_router(comms.router)
app.include_router(auth.router)
# praticienne invite-token — premier-lien Apple/Google (C4 Option B), prototype
app.include_router(invite.router)

# digiSha — tuteur formation « Les 26 ponts » + accompagnement (auth X-DigiSha-Token)
app.include_router(digisha.router)

mcp = FastApiMCP(app)
mcp.mount()


@app.get("/health", tags=["System"], summary="Render health check")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "vlbh-energy-mcp", "ts": int(time.time())})
