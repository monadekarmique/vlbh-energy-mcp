"""Le numéro de release DiGiSha rendu avec chaque réponse (fable, carte 9331e3e6, migration 2026-10-19e).

Patrick, 19.10.2026 : « nous devrions ajouter le numéro de release de DiGiSha dans la fenêtre et informer chaque fois qu'une
nouvelle release est mise à jour celles qui le demandent ». La release vit en base (digisha_release) ; le serveur la relit au
plus toutes les 5 minutes et la rend dans « release ». Jamais bloquant : sans base, sans fonction, la réponse part sans numéro."""
from __future__ import annotations

import time

_cache: dict = {"t": -1e9, "numero": None}


async def release_courante(rpc_service, ttl: int = 300) -> str | None:
    if time.monotonic() - _cache["t"] < ttl:
        return _cache["numero"]
    lignes = await rpc_service("digisha_release_courante", {})
    _cache["t"] = time.monotonic()               # panne ou fonction absente : on réessaie dans 5 minutes, pas à chaque tour
    if isinstance(lignes, list) and lignes and isinstance(lignes[0], dict) and lignes[0].get("numero"):
        _cache["numero"] = str(lignes[0]["numero"])
    return _cache["numero"]                      # panne : le dernier numéro connu
