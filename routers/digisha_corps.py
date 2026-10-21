"""Taille du corps des requêtes DiGiSha bornée AVANT l'authentification et avant la lecture du JSON.

Middleware ASGI pur, placé devant FastAPI : l'authentification vit dans les routes, et FastAPI lit et valide le JSON avant
d'y entrer. Ici, rien n'est encore lu :
  · un Content-Length au-delà de la borne → 413 tout de suite, sans lire un octet ;
  · sans Content-Length (envoi par morceaux) → on lit en comptant ; 413 dès que la borne est franchie, et l'application
    ne voit rien ; sous la borne, le corps lu lui est rejoué tel quel.
La borne par défaut (32 Mo) est celle au-delà de laquelle le fournisseur de modèle refuse la requête de toute façon.
DIGISHA_CORPS_MAX_OCTETS la change sans toucher au code."""
from __future__ import annotations

import json
import os

PREFIXE = "/digisha"
CORPS_MAX_DEFAUT = 32 * 1024 * 1024
MESSAGE_413 = "Message trop volumineux pour DiGiSha — allège les pièces jointes et réessaie."


def corps_max() -> int:
    try:
        v = int(os.environ.get("DIGISHA_CORPS_MAX_OCTETS", ""))
    except ValueError:
        return CORPS_MAX_DEFAUT
    return v if v > 0 else CORPS_MAX_DEFAUT


def _content_length(scope) -> int | None:
    for nom, valeur in scope.get("headers") or []:
        if nom.lower() == b"content-length":
            try:
                return int(valeur)
            except ValueError:
                return None
    return None


async def _refuser(send) -> None:
    corps = json.dumps({"detail": MESSAGE_413}, ensure_ascii=False).encode()
    await send({"type": "http.response.start", "status": 413,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(corps)).encode())]})
    await send({"type": "http.response.body", "body": corps})


class LimiteCorpsDigisha:
    def __init__(self, app, prefixe: str = PREFIXE):
        self.app = app
        self.prefixe = prefixe

    def _concerne(self, chemin: str) -> bool:
        return chemin == self.prefixe or chemin.startswith(self.prefixe + "/")

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or not self._concerne(scope.get("path") or ""):
            await self.app(scope, receive, send)
            return
        borne = corps_max()
        longueur = _content_length(scope)
        if longueur is not None:
            if longueur > borne:
                await _refuser(send)
                return
            await self.app(scope, receive, send)
            return
        morceaux, total = [], 0
        while True:
            message = await receive()
            if message["type"] != "http.request":           # déconnexion : on laisse l'application la voir
                rejoue = [message]
                break
            morceau = message.get("body", b"")
            total += len(morceau)
            if total > borne:
                await _refuser(send)
                return
            morceaux.append(morceau)
            if not message.get("more_body", False):
                rejoue = [{"type": "http.request", "body": b"".join(morceaux), "more_body": False}]
                break

        async def rejouer():
            if rejoue:
                return rejoue.pop(0)
            return await receive()

        await self.app(scope, rejouer, send)
