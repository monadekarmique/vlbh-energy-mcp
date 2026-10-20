"""Ce que DiGiSha ne comprend pas, et ce que Patrick lui apprend (fable, 19.10.2026, carte 6f1ef080 ; migration 2026-10-19c).

Patrick, 19.10 : « je veux que DiGiSha nous rapporte ce qu'elle ne comprend pas que nous puissions lui permettre d'apprendre à
expliquer les décodages ». Cas d'origine : Giulia, 19.10 03h36, « le noed coex que patrick a décoder » ; DiGiSha a inventé.

DiGiSha termine sa réponse par une ligne ⟦À apprendre : terme — ce qui manque⟧ quand un terme lui échappe ; le serveur la retire
avant tout affichage, dépôt ou journal, et la range en base (digisha_a_apprendre_noter). Patrick répond dans le Kanban ; ses
réponses reviennent ici par digisha_lexique() et sont données au modèle à chaque tour.
"""
import re
import time

APPRENDRE_CADRE = (
    "## Ce que tu ne sais pas expliquer\n"
    "Quand un terme, une abréviation, une mesure ou un décodage cité t'échappe — il n'est ni dans ce que tu sais d'elle, ni "
    "dans le lexique de Patrick — tu ne l'inventes pas et tu ne le paraphrases pas pour donner le change. Tu le dis simplement "
    "(« je ne sais pas encore l'expliquer ; je le demande à Patrick ») et tu continues avec ce que tu sais. Puis, À LA TOUTE FIN "
    "de ta réponse, une ligne par terme (deux au plus) :\n"
    "⟦À apprendre : <le terme> — <ce qui te manque pour l'expliquer>⟧\n"
    "Cette ligne n'est pas montrée : elle part à Patrick, qui te l'apprendra.\n\n"
    "## Quand Patrick te donne lui-même une définition\n"
    "Si c'est Patrick qui, dans ce dernier message, te donne lui-même le sens d'un terme (souvent un terme que tu viens de dire "
    "ne pas savoir), termine ta réponse par une ligne :\n"
    "⟦Appris : <le terme>⟧\n"
    "Le serveur range alors SON message, tel quel, dans ton lexique, et ferme la question. Tu n'écris jamais que tu as rangé ou "
    "retenu une définition dans le lexique sans cette ligne.\n"
)
LEXIQUE_CADRE = (
    "## Lexique de Patrick — ce qu'il t'a appris (fait foi)\n"
    "Explique ces termes avec ses mots ; ne les redemande pas.\n\n"
)

_LIGNE = re.compile(r"\n?[ \t]*⟦\s*À apprendre\s*:\s*(?P<terme>[^⟧\n]{1,120}?)(?:(?:\s+[—–-]\s+|\s*:\s+)(?P<manque>[^⟧\n]{0,600}))?\s*⟧[ \t]*")


def extraire(texte: str) -> tuple[str, list[tuple[str, str]]]:
    """(le texte sans les lignes ⟦À apprendre…⟧, [(terme, ce qui manque)]) — deux termes au plus, sans doublon."""
    termes: list[tuple[str, str]] = []
    vus = set()
    for m in _LIGNE.finditer(texte or ""):
        t = m.group("terme").strip().strip("«»\"' ")
        if t and t.lower() not in vus and len(termes) < 2:
            vus.add(t.lower())
            termes.append((t, (m.group("manque") or "").strip()))
    propre = _LIGNE.sub("", texte or "").rstrip()
    return propre, termes


# 20.10.2026 (migration 2026-10-20j) — Patrick : « je viens de répondre dans une carte à égo errant et en revoila une autre ».
# Il avait défini le terme DANS DiGiSha ; elle avait écrit « rangé dans ton lexique » sans que rien ne soit écrit.
_APPRIS = re.compile(r"\n?[ \t]*⟦\s*Appris\s*:\s*(?P<terme>[^⟧\n]{1,120}?)\s*⟧[ \t]*")


def extraire_appris(texte: str) -> tuple[str, list[str]]:
    """(le texte sans les lignes ⟦Appris : …⟧, [termes]) — deux au plus, sans doublon."""
    termes: list[str] = []
    for m in _APPRIS.finditer(texte or ""):
        t = m.group("terme").strip().strip("«»\"' ")
        if t and t.lower() not in {x.lower() for x in termes} and len(termes) < 2:
            termes.append(t)
    return _APPRIS.sub("", texte or "").rstrip(), termes


async def apprendre_en_seance(rpc_service, termes, svlbh: str | None, message: str) -> list:
    """Le message de Patrick, TEL QUEL, devient la réponse de chaque terme (la base refuse tout autre que lui)."""
    if not svlbh or not (message or "").strip():
        return []
    return [await rpc_service("digisha_a_apprendre_appris_en_seance", {"p_terme": t, "p_texte": message, "p_svlbh": svlbh})
            for t in termes]


_cache: dict = {"t": 0.0, "bloc": ""}


def bloc_lexique(lignes) -> str:
    if not isinstance(lignes, list):
        return ""
    entrees = [f"- **{l.get('terme')}** : {l.get('explication')}" for l in lignes
               if isinstance(l, dict) and l.get("terme") and l.get("explication")]
    return (LEXIQUE_CADRE + "\n".join(entrees)) if entrees else ""


async def lexique(rpc_service, ttl: int = 300) -> str:
    """Le lexique de Patrick, relu au plus toutes les 5 minutes (une réponse dans l'app sert au plus 5 minutes plus tard)."""
    if time.monotonic() - _cache["t"] < ttl:
        return _cache["bloc"]
    lignes = await rpc_service("digisha_lexique", {})
    if lignes is None:
        return _cache["bloc"]                     # panne : on garde le dernier lexique connu
    _cache.update(t=time.monotonic(), bloc=bloc_lexique(lignes))
    return _cache["bloc"]


async def noter(rpc_service, termes, svlbh: str | None, consultante: str | None, question: str, reponse: str) -> list:
    extrait = (question or "")[:700] + "\n— DiGiSha : " + (reponse or "")[:600]
    sorties = []
    for terme, manque in termes:
        sorties.append(await rpc_service("digisha_a_apprendre_noter",
                                         {"p_svlbh": svlbh, "p_consultante": consultante, "p_terme": terme,
                                          "p_manque": manque or None, "p_extrait": extrait}))
    return sorties
