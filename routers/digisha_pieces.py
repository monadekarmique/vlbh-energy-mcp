"""Pièces jointes DiGiSha — une photo (depuis Photos, ou collée depuis WhatsApp) ou un document (PDF) dans la saisie.

Patrick, 17.10.2026 09h2x (fenêtre de fable) : « j'aimerais pouvoir ajouter une photo depuis photo ou attacher un
documer ou copier une photo depuis whatsapp et la coller dans la fenêtre de saisie DiGiSha ».

Le tour reste un `ChatTurn` ; son `content` est soit le texte d'avant (rien ne change pour les apps d'aujourd'hui),
soit une liste de blocs au format de l'API Anthropic — `text`, `image` (base64 jpeg/png/gif/webp, 5 Mo au plus),
`document` (base64 PDF, 10 Mo au plus) — passés tels quels au modèle, qui voit la photo et lit le document.
Partout où le serveur a besoin du TEXTE d'un tour (dépôt dans le fil, journal, banque Q/R, passages du fil),
`texte_de()` le rend : une pièce y devient « [photo] » ou « [document : titre] ». La pièce elle-même n'est pas
déposée dans le fil (à faire : la ranger dans un bucket et la lier à la page du jour).
"""
from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, field_validator

IMAGES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
DOCUMENTS = {"application/pdf"}
IMAGE_MAX_OCTETS = 5 * 1024 * 1024       # la limite de l'API pour une image
DOCUMENT_MAX_OCTETS = 10 * 1024 * 1024   # l'API admet 32 Mo ; on borne le corps HTTP d'un tour
PIECES_MAX = 4                           # pièces par message


def octets(b64: str) -> int:
    """Taille décodée approchée d'une chaîne base64 (sans la décoder)."""
    return len(b64) * 3 // 4


class SourceBase64(BaseModel):
    type: Literal["base64"] = "base64"
    media_type: str
    data: str = Field(min_length=1)


class BlocTexte(BaseModel):
    type: Literal["text"]
    text: str


class BlocImage(BaseModel):
    type: Literal["image"]
    source: SourceBase64

    @field_validator("source")
    @classmethod
    def _image_admise(cls, s: SourceBase64) -> SourceBase64:
        if s.media_type not in IMAGES:
            raise ValueError(f"image : type « {s.media_type} » non admis (jpeg, png, gif, webp)")
        if octets(s.data) > IMAGE_MAX_OCTETS:
            raise ValueError("image : plus de 5 Mo — la réduire avant l'envoi")
        return s


class BlocDocument(BaseModel):
    type: Literal["document"]
    source: SourceBase64
    title: str | None = None

    @field_validator("source")
    @classmethod
    def _document_admis(cls, s: SourceBase64) -> SourceBase64:
        if s.media_type not in DOCUMENTS:
            raise ValueError(f"document : type « {s.media_type} » non admis (pdf)")
        if octets(s.data) > DOCUMENT_MAX_OCTETS:
            raise ValueError("document : plus de 10 Mo")
        return s


Bloc = Annotated[Union[BlocTexte, BlocImage, BlocDocument], Field(discriminator="type")]
Contenu = Union[str, list[Bloc]]


def valider_contenu(contenu: Contenu) -> Contenu:
    """Un tour en blocs porte au moins un bloc et au plus PIECES_MAX pièces."""
    if isinstance(contenu, str):
        return contenu
    if not contenu:
        raise ValueError("un tour en blocs porte au moins un bloc")
    if compter_pieces(contenu) > PIECES_MAX:
        raise ValueError(f"au plus {PIECES_MAX} pièces par message")
    return contenu


def _champ(b, nom: str):
    return b.get(nom) if isinstance(b, dict) else getattr(b, nom, None)


def compter_pieces(contenu: Contenu | None) -> int:
    if not isinstance(contenu, list):
        return 0
    return sum(1 for b in contenu if _champ(b, "type") in ("image", "document"))


def texte_de(contenu: Contenu | None) -> str:
    """Le texte d'un tour : tel quel pour une chaîne ; pour des blocs, les textes et une marque par pièce."""
    if contenu is None:
        return ""
    if isinstance(contenu, str):
        return contenu
    parts: list[str] = []
    for b in contenu:
        t = _champ(b, "type")
        if t == "text":
            parts.append(str(_champ(b, "text") or ""))
        elif t == "image":
            parts.append("[photo]")
        elif t == "document":
            titre = _champ(b, "title")
            parts.append(f"[document : {titre}]" if titre else "[document]")
    return "\n".join(p for p in parts if p).strip()


def marquer_cache(content):
    """Le point de cache sur le dernier bloc d'un tour (texte ou liste), sans modifier l'original."""
    if isinstance(content, str):
        return [{"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}]
    if isinstance(content, list) and content:
        out = [dict(b) for b in content]
        out[-1] = {**out[-1], "cache_control": {"type": "ephemeral"}}
        return out
    return content
