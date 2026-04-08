from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard", response_class=HTMLResponse, summary="Sprint planning dashboard")
async def dashboard(request: Request):
    """Serve the sprint planning dashboard UI."""
    return templates.TemplateResponse("dashboard.html", {"request": request})
