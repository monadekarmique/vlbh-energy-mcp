"""pdf.engine — moteur PDF standard des documents praticiennes (DEC Patrick 2026-08-08).

WeasyPrint est LE moteur : HTML + CSS → PDF, polices embarquées par le moteur
(toute police résolue est incorporée au fichier). Module PORTABLE à dessein —
la DEC dit « le service vivra dans le FastAPI qui servira les factures, pas
encore connu » : ce dossier `pdf/` (engine + templates) se déplace tel quel.
"""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES)),
    autoescape=select_autoescape(["html"]),
)


def render_pdf(template_name: str, context: dict) -> bytes:
    """Rend un template Jinja2 en PDF (bytes). Lève si WeasyPrint est absent —
    jamais de repli silencieux vers un autre moteur : WeasyPrint est le standard."""
    # Import local : le serveur démarre même si les libs système (pango/cairo)
    # manquent — seul l'endpoint PDF échoue alors, explicitement.
    from weasyprint import HTML

    html = _env.get_template(template_name).render(**context)
    return HTML(string=html, base_url=str(_TEMPLATES)).write_pdf()
