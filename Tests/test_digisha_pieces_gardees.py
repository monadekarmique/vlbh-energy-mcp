"""Les pièces jointes sont gardées (fiche c51ff989) : chaque photo ou PDF du tour part dans le seau « digisha-pieces » sous sa
séance, et sa référence s'ajoute à la page ; un tour sans pièce ou sans séance ne fait rien."""
import asyncio
import base64
import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import routers.digisha as d  # noqa: E402
from routers.digisha import ChatTurn  # noqa: E402

PNG = base64.b64encode(b"\x89PNG petit").decode()
SEANCE = "54719345-ecac-56ce-7e40-7dee232658fc"


def test_photo_et_pdf_ranges_sous_la_seance(monkeypatch):
    monkeypatch.setenv("DIGISHA_SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("DIGISHA_SUPABASE_SERVICE_KEY", "k")
    envois, rpc = [], []

    class Client:
        async def post(self, url, content=None, headers=None, timeout=None, **kw):
            envois.append((url, headers["Content-Type"], content))
            return httpx.Response(200, json={"Key": "ok"})
    monkeypatch.setattr(d, "_http", lambda: Client())

    async def faux_service(nom, corps, timeout=10):
        rpc.append((nom, corps))
        return 1
    monkeypatch.setattr(d, "_rpc_service", faux_service)
    t = ChatTurn(role="user", content=[{"type": "text", "text": "regarde"},
                                       {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": PNG}},
                                       {"type": "document", "title": "bilan.pdf", "source": {"type": "base64", "media_type": "application/pdf", "data": PNG}}])
    assert asyncio.run(d.ranger_pieces(SEANCE, t.content)) == 2
    assert envois[0][0].startswith(f"https://x.supabase.co/storage/v1/object/digisha-pieces/{SEANCE}/") and envois[0][0].endswith(".png")
    assert envois[0][2] == b"\x89PNG petit" and envois[1][1] == "application/pdf"
    nom, corps = rpc[0]
    assert nom == "digisha_page_pieces_ajouter" and corps["p_session"] == SEANCE
    assert [p["genre"] for p in corps["p_pieces"]] == ["photo", "document"] and corps["p_pieces"][1]["titre"] == "bilan.pdf"


def test_rien_sans_seance_ni_piece():
    assert asyncio.run(d.ranger_pieces(None, [])) == 0
    assert asyncio.run(d.ranger_pieces(SEANCE, "texte seul")) == 0
