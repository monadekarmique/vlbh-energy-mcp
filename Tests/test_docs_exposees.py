"""Documentation de l'API servie seulement en développement (EXPOSE_API_DOCS=1) ; /mcp n'en dépend pas."""
import asyncio

from mcp import types

import main


def test_sans_variable_pas_de_documentation(client):
    assert main.app.openapi_url is None
    for chemin in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(chemin).status_code == 404, chemin


def test_la_variable_rouvre_la_documentation():
    assert main.docs_urls({"EXPOSE_API_DOCS": "1"}) == {
        "docs_url": "/docs", "redoc_url": "/redoc", "openapi_url": "/openapi.json"}
    assert main.docs_urls({"EXPOSE_API_DOCS": "0"})["openapi_url"] is None
    assert main.docs_urls({})["docs_url"] is None


def test_mcp_garde_ses_outils_sans_openapi_json(client):
    """fastapi-mcp lit les routes de l'app, pas l'URL /openapi.json : ses outils restent là, /mcp reste monté."""
    assert main.app.openapi_url is None
    assert any(getattr(r, "path", "") == "/mcp" for r in main.app.routes)
    noms = {t.name for t in main.mcp.tools}
    assert len(noms) > 10
    assert any("digisha_chat" in n for n in noms) and any("health" in n for n in noms)
    handler = main.mcp.server.request_handlers[types.ListToolsRequest]
    res = asyncio.run(handler(types.ListToolsRequest(method="tools/list")))
    assert {t.name for t in res.root.tools} == noms
