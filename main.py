from __future__ import annotations
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from routers import slm, sla, session
from services.make_service import MakeService


@asynccontextmanager
async def lifespan(app: FastAPI):
    push_url = os.environ["MAKE_WEBHOOK_PUSH_URL"]
    pull_url = os.environ["MAKE_WEBHOOK_PULL_URL"]
    app.state.make_service = MakeService(push_url=push_url, pull_url=pull_url)
    yield
    await app.state.make_service.close()


app = FastAPI(
    title="VLBH Energy MCP",
    description="MCP server for SVLBHPanel — Scores de Lumière sync via Make.com",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

app.include_router(slm.router)
app.include_router(sla.router)
app.include_router(session.router)


@app.get("/health", tags=["System"], summary="Render health check")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "vlbh-energy-mcp", "ts": int(time.time())})
