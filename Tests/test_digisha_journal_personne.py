"""Le tour du tuteur porte la personne dans digisha_chat_log, comme celui de l'accompagnement (13.11.2026).

Mesuré le 13.11.2026 : 100 tours « formation_m1 » en 7 jours sans svlbh_id — le moniteur /admin/digisha ne pouvait les
rattacher à personne. La route /chat connaissait pourtant la personne (gate_subscription) et ne la passait pas au journal."""
import asyncio
import importlib.util
from pathlib import Path

from routers import digisha as d

# Le banc du journal (fixture « journal », _chat, _accompagnement) est repris tel quel du test voisin.
_spec = importlib.util.spec_from_file_location("banc_journal", Path(__file__).with_name("test_digisha_journal.py"))
_banc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_banc)
journal, _chat, _accompagnement = _banc.journal, _banc._chat, _banc._accompagnement

PATRICK = "52adbc98-d2b0-4444-b89c-b1311a02a983"


def _capter(monkeypatch):
    vus = []

    async def log_exchange(*a, **k):
        vus.append(k)
    monkeypatch.setattr(d, "log_exchange", log_exchange)
    return vus


def test_le_tour_du_tuteur_porte_la_personne(journal, monkeypatch):
    vus = _capter(monkeypatch)
    asyncio.run(_chat())
    assert [k.get("svlbh_id") for k in vus] == [PATRICK]


def test_le_tour_d_accompagnement_porte_la_personne(journal, monkeypatch):
    vus = _capter(monkeypatch)
    asyncio.run(_accompagnement())
    assert [k.get("svlbh_id") for k in vus] == [PATRICK]
