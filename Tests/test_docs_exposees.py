"""Documentation de l'API servie seulement en développement (EXPOSE_API_DOCS=1) ; /mcp monté seulement avec EXPOSE_MCP=1."""
import asyncio

from fastapi import FastAPI
from mcp import types

import main
from routers import digisha


def test_sans_variable_pas_de_documentation(client):
    assert main.app.openapi_url is None
    for chemin in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(chemin).status_code == 404, chemin


def test_la_variable_rouvre_la_documentation():
    assert main.docs_urls({"EXPOSE_API_DOCS": "1"}) == {
        "docs_url": "/docs", "redoc_url": "/redoc", "openapi_url": "/openapi.json"}
    assert main.docs_urls({"EXPOSE_API_DOCS": "0"})["openapi_url"] is None
    assert main.docs_urls({})["docs_url"] is None


def test_sans_variable_pas_de_mcp(client):
    """Production : aucune route /mcp, aucun serveur MCP construit."""
    assert main.mcp is None
    assert not any(getattr(r, "path", "").startswith("/mcp") for r in main.app.routes)
    assert client.get("/mcp").status_code == 404
    assert main.monter_mcp(FastAPI(), {}) is None
    assert main.monter_mcp(FastAPI(), {"EXPOSE_MCP": "0"}) is None


def test_la_variable_monte_mcp_avec_ses_outils_sans_openapi_json():
    """Développement (EXPOSE_MCP=1) : /mcp monté ; fastapi-mcp lit les routes, pas l'URL /openapi.json fermée."""
    app = FastAPI(**main.docs_urls({}))
    app.include_router(digisha.router)
    serveur = main.monter_mcp(app, {"EXPOSE_MCP": "1"})
    assert serveur is not None and app.openapi_url is None
    assert any(getattr(r, "path", "") == "/mcp" for r in app.routes)
    noms = {t.name for t in serveur.tools}
    assert any("digisha_chat" in n for n in noms)
    handler = serveur.server.request_handlers[types.ListToolsRequest]
    res = asyncio.run(handler(types.ListToolsRequest(method="tools/list")))
    assert {t.name for t in res.root.tools} == noms
