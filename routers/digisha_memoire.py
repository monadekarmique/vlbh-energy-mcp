"""Mémoire de conversation DiGiSha — résumé par blocs, mis en cache.

Mesuré le 07.09.2026 (console Anthropic, clé DiGiSha) : ~58 messages tuteur
= 30,55 USD sur sonnet, soit ≈ 0,53 USD le message ; le 09.09, la même
personne, même modèle, une douzaine de messages pour presque rien. Ce qui
change : une conversation continue de trois heures dont l'app renvoie les
30 derniers messages à chaque tour. Passé 30 messages la fenêtre glisse d'un
cran par tour, le préfixe change, le cache de l'historique ne sert plus, et
~25k tokens de réponses sont renvoyés et réécrits à chaque message.

Ici : au-delà de SEUIL messages, les tours anciens sont découpés en blocs de
BLOC messages alignés sur le début de la liste reçue ; chaque bloc est résumé
UNE fois (clé = empreinte de son contenu, cache LRU borné) et les résumés
entrent dans le bloc système avec cache_control. Seuls les RECENT_MIN à
RECENT_MIN+BLOC-1 derniers messages restent bruts. Un client dont la fenêtre
glisse d'un cran par tour décale les blocs à chaque tour : le résumé est alors
recalculé — coût voisin du renvoi brut, jamais pire. Un client qui fait glisser
sa fenêtre par blocs (Priv-1 depuis le 09.09) garde des blocs stables et paie
un résumé par dizaine de messages.
"""
from __future__ import annotations

import hashlib
import json
import logging
from collections import OrderedDict

import httpx

log = logging.getLogger("digisha")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
RESUME_MODEL = "claude-sonnet-4-6"
SEUIL = 20          # au-delà de ce nombre de messages, on résume
BLOC = 10           # taille d'un bloc résumé
RECENT_MIN = 10     # messages bruts conservés au minimum
CACHE_MAX = 512     # résumés gardés en mémoire (≈ 1 Mo au plus)

RESUME_SYSTEM = (
    "Tu résumes fidèlement, en français, un extrait d'échange entre DiGiSha "
    "(tuteur et accompagnement Digital Shaman, SVLBH) et une personne. Garde : "
    "ce qu'elle a demandé, ce qui lui a été expliqué, les décisions prises et "
    "les questions restées ouvertes, avec les termes SVLBH exacts (lignée, "
    "décodage, capsule, pont, stade…). Rien d'inventé, aucun commentaire, "
    "aucune salutation. 250 mots au plus."
)

_resumes: "OrderedDict[str, str]" = OrderedDict()


def empreinte(bloc: list[dict]) -> str:
    return hashlib.sha256(
        json.dumps(bloc, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def decouper(messages: list[dict]) -> tuple[list[list[dict]], list[dict]]:
    """→ (blocs à résumer, messages récents laissés bruts).

    La frontière n'avance que par pas de BLOC : tant que le début de la liste
    ne bouge pas, les blocs restent identiques d'un tour à l'autre et leurs
    résumés sortent du cache. Les messages bruts commencent toujours par un
    tour « user » (exigence de l'API)."""
    n = len(messages)
    if n <= SEUIL:
        return [], messages
    old_len = ((n - RECENT_MIN) // BLOC) * BLOC
    while old_len > 0 and messages[old_len].get("role") != "user":
        old_len -= 1
    if old_len < BLOC:
        return [], messages
    old = messages[:old_len]
    blocs = [old[i:i + BLOC] for i in range(0, len(old), BLOC)]
    return blocs, messages[old_len:]


def _rendu(bloc: list[dict]) -> str:
    return "\n\n".join(
        ("Elle : " if m.get("role") == "user" else "DiGiSha : ") + str(m.get("content", ""))
        for m in bloc
    )


async def resumer_bloc(client: httpx.AsyncClient, api_key: str, bloc: list[dict]) -> str | None:
    """Résumé d'un bloc, servi du cache si déjà calculé. None = échec (l'appelant
    renvoie alors l'historique brut, comme avant — jamais bloquant)."""
    key = empreinte(bloc)
    if key in _resumes:
        _resumes.move_to_end(key)
        return _resumes[key]
    try:
        r = await client.post(
            ANTHROPIC_URL,
            json={
                "model": RESUME_MODEL,
                "max_tokens": 500,
                "system": RESUME_SYSTEM,
                "messages": [{"role": "user", "content": "Résume cet extrait :\n\n" + _rendu(bloc)}],
            },
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            timeout=60,
        )
    except Exception as exc:  # réseau — on ne bloque pas la réponse principale
        log.warning("resume bloc impossible : %r", exc)
        return None
    if r.status_code != 200:
        log.warning("resume bloc refusé : HTTP %s %s", r.status_code, r.text[:200])
        return None
    data = r.json()
    texte = "".join(
        b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
    ).strip()
    if not texte:
        return None
    u = data.get("usage") or {}
    log.info(
        "usage endpoint=resume model=%s in=%s cache_w=%s cache_r=%s out=%s msgs=%d",
        RESUME_MODEL, u.get("input_tokens"), u.get("cache_creation_input_tokens"),
        u.get("cache_read_input_tokens"), u.get("output_tokens"), len(bloc),
    )
    _resumes[key] = texte
    while len(_resumes) > CACHE_MAX:
        _resumes.popitem(last=False)
    return texte


async def preparer_historique(
    client: httpx.AsyncClient, api_key: str, messages: list[dict]
) -> tuple[dict | None, list[dict], int]:
    """→ (bloc système « résumé » ou None, messages bruts à envoyer, nb de blocs résumés).

    Le bloc système porte cache_control : stable tant que les blocs le sont."""
    blocs, recents = decouper(messages)
    if not blocs:
        return None, messages, 0
    parties = []
    for i, bloc in enumerate(blocs, 1):
        resume = await resumer_bloc(client, api_key, bloc)
        if resume is None:
            return None, messages, 0
        parties.append(f"### Bloc {i} ({len(bloc)} messages)\n{resume}")
    texte = (
        "## Résumé des échanges précédents de cette conversation\n"
        "Ces tours ne sont pas répétés ci-dessous ; les messages qui suivent reprennent "
        "après ce résumé. Appuie-toi dessus comme sur ta propre mémoire de l'échange.\n\n"
        + "\n\n".join(parties)
    )
    return {"type": "text", "text": texte, "cache_control": {"type": "ephemeral"}}, recents, len(blocs)


def journaliser_usage(endpoint: str, mode: str, model: str, data: dict, n_msgs: int, n_blocs: int) -> None:
    """Une ligne INFO par appel : ce que la console Anthropic sait, lisible dans Render."""
    u = (data or {}).get("usage") or {}
    log.info(
        "usage endpoint=%s mode=%s model=%s in=%s cache_w=%s cache_r=%s out=%s msgs=%d blocs_resumes=%d",
        endpoint, mode, model, u.get("input_tokens"), u.get("cache_creation_input_tokens"),
        u.get("cache_read_input_tokens"), u.get("output_tokens"), n_msgs, n_blocs,
    )
