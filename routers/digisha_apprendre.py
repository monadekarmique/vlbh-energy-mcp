"""Ce que DiGiSha ne comprend pas, et ce que Patrick lui apprend (fable, 19.10.2026, carte 6f1ef080 ; migration 2026-10-19c).

Patrick, 19.10 : « je veux que DiGiSha nous rapporte ce qu'elle ne comprend pas que nous puissions lui permettre d'apprendre à
expliquer les décodages ». Cas d'origine : Giulia, 19.10 03h36, « le noed coex que patrick a décoder » ; DiGiSha a inventé.

DiGiSha termine sa réponse par une ligne ⟦À apprendre : terme — ce qui manque⟧ quand un terme lui échappe ; le serveur la retire
avant tout affichage, dépôt ou journal, et la range en base (digisha_a_apprendre_noter). Patrick répond dans le Kanban ; ses
réponses reviennent ici par digisha_lexique() et sont données au modèle à chaque tour.
"""
import re
import time
import unicodedata

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
    "retenu une définition dans le lexique sans cette ligne.\n\n"
    "## Quand Patrick te corrige\n"
    "Si c'est Patrick qui, dans ce dernier message, corrige ce que tu as dit ou ce que tu sais — une explication, une "
    "correspondance, une table, un point, une lecture (souvent il commence par « Correction », « non », « c'est faux ») — tu "
    "reprends avec SA correction, sans te justifier, et tu termines ta réponse par une ligne :\n"
    "⟦Corrigé : <le sujet, en quelques mots> — <ce qui est juste désormais, en une phrase, avec ses mots>⟧\n"
    "Le serveur range alors SON message, tel quel, avec cette phrase, dans ton lexique : cela fait foi ensuite, pour toutes. "
    "Une correction par sujet, deux au plus. Tu n'écris jamais que tu as retenu une correction sans cette ligne.\n"
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


# 06.11.2026 — Patrick : « comment puis-je corriger ce que DiGiSha me dit en live pour qu'il consolide ce savoir ? ». Mesuré
# ce matin-là (06h55) : « Correction : pour l'absinthe la Tables des Dark entities - Rose des Vents - HVLBH Priv-6 … » ; rien
# ne la gardait, elle se perdait avec la conversation. La ligne ⟦Corrigé : sujet — ce qui est juste⟧ la range dans le lexique.
_CORRIGE = re.compile(r"\n?[ \t]*⟦\s*Corrigé\s*:\s*(?P<sujet>[^⟧\n]{1,120}?)(?:\s+[—–-]\s+(?P<juste>[^⟧\n]{0,600}))?\s*⟧[ \t]*")


def extraire_corrige(texte: str) -> tuple[str, list[tuple[str, str]]]:
    """(le texte sans les lignes ⟦Corrigé : …⟧, [(sujet, ce qui est juste)]) — deux au plus, sans doublon."""
    corrections: list[tuple[str, str]] = []
    for m in _CORRIGE.finditer(texte or ""):
        s = m.group("sujet").strip().strip("«»\"' ")
        if s and cle(s) and cle(s) not in {cle(x) for x, _ in corrections} and len(corrections) < 2:
            corrections.append((s, (m.group("juste") or "").strip()))
    return _CORRIGE.sub("", texte or "").rstrip(), corrections


def texte_de_correction(message: str, juste: str, jour: str) -> str:
    """SES mots d'abord, tels quels ; la phrase de DiGiSha ensuite, marquée comme la sienne."""
    t = f"Correction de Patrick du {jour} : « {(message or '').strip()} »"
    return t + (f" — retenu : {juste}" if juste else "")


async def corriger_en_seance(rpc_service, corrections, svlbh: str | None, message: str, jour: str) -> list:
    """Chaque correction devient l'entrée de son sujet dans le lexique (la base refuse tout autre que Patrick)."""
    if not svlbh or not (message or "").strip():
        return []
    sorties = [await rpc_service("digisha_a_apprendre_appris_en_seance",
                                 {"p_terme": s, "p_texte": texte_de_correction(message, j, jour), "p_svlbh": svlbh})
               for s, j in corrections]
    _cache["t"] = 0.0          # le lexique se relit au tour suivant, pas cinq minutes plus tard
    return sorties


async def apprendre_en_seance(rpc_service, termes, svlbh: str | None, message: str) -> list:
    """Le message de Patrick, TEL QUEL, devient la réponse de chaque terme (la base refuse tout autre que lui)."""
    if not svlbh or not (message or "").strip():
        return []
    return [await rpc_service("digisha_a_apprendre_appris_en_seance", {"p_terme": t, "p_texte": message, "p_svlbh": svlbh})
            for t in termes]


_cache: dict = {"t": 0.0, "bloc": "", "illus": {}}

# 04.11.2026 (migration 2026-11-04c, carte 0eceae35) — Patrick : « y-a-t-il possibilité d'ajouter des images ou des stickers à
# cette explication ? ». Un terme du lexique peut porter une illustration (seau « digisha-pieces », dossier lexique/) ; DiGiSha
# la désigne par une ligne ⟦Montrer : terme⟧, retirée comme les autres, et la réponse rend l'image à côté du texte.
MONTRER_CADRE = (
    "## Montrer une illustration\n"
    "Quelques termes du lexique portent une illustration de Patrick (marqués « illustration : ⟦Montrer : <terme>⟧ »). Quand ta "
    "réponse explique un de ces termes, termine-la par cette ligne, telle quelle (deux au plus). Elle n'est pas montrée : l'app "
    "affiche l'image sous ta réponse, et tu peux y renvoyer (« regarde l'illustration sous ma réponse »). Tu ne décris pas "
    "l'image au-delà de ce que dit le lexique. Pour un terme sans illustration, pas de ligne.\n\n"
)
_MONTRER = re.compile(r"\n?[ \t]*⟦\s*Montrer\s*:\s*(?P<terme>[^⟧\n]{1,120}?)\s*⟧[ \t]*")


def cle(terme: str) -> str:
    """La clé large d'un terme, comme digisha_terme_cle_large en base : sans accents, minuscules, lettres et chiffres seuls."""
    t = unicodedata.normalize("NFD", terme or "")
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn").lower())


def extraire_montrer(texte: str) -> tuple[str, list[str]]:
    """(le texte sans les lignes ⟦Montrer : …⟧, [termes]) — deux au plus, sans doublon."""
    termes: list[str] = []
    for m in _MONTRER.finditer(texte or ""):
        t = m.group("terme").strip().strip("«»\"' ")
        if t and cle(t) and cle(t) not in {cle(x) for x in termes} and len(termes) < 2:
            termes.append(t)
    return _MONTRER.sub("", texte or "").rstrip(), termes


def illustrations(termes, heure: str) -> list[dict]:
    """Les images des termes désignés, dans la forme d'une pièce gardée (heure, genre, chemin, media_type, titre)."""
    sortie, vus = [], set()
    for t in termes or []:
        for p in _cache["illus"].get(cle(t), []):
            if p.get("chemin") and p["chemin"] not in vus:
                vus.add(p["chemin"])
                sortie.append({"heure": heure, "genre": "photo", "chemin": p["chemin"], "media_type": p.get("media_type"),
                               "titre": p.get("titre") or t})
    return sortie


def marques(pieces) -> str:
    """Les lignes-marques du tour déposé : « [illustration : Gui] » — l'app y rattache l'image à la relecture."""
    return "\n".join(f"[illustration : {p['titre']}]" for p in pieces or [])


def _illustrations_par_cle(lignes) -> dict:
    par_cle: dict = {}
    for l in lignes if isinstance(lignes, list) else []:
        if isinstance(l, dict) and l.get("terme") and l.get("chemin"):
            par_cle.setdefault(cle(l["terme"]), []).append(l)
    return par_cle


def bloc_lexique(lignes, illus: dict | None = None) -> str:
    if not isinstance(lignes, list):
        return ""
    illus = illus or {}
    entrees = [f"- **{l.get('terme')}** : {l.get('explication')}"
               + (f" (illustration : ⟦Montrer : {l.get('terme')}⟧)" if cle(l.get("terme")) in illus else "")
               for l in lignes if isinstance(l, dict) and l.get("terme") and l.get("explication")]
    if not entrees:
        return ""
    return (MONTRER_CADRE if any(cle(l.get("terme")) in illus for l in lignes if isinstance(l, dict)) else "") \
        + LEXIQUE_CADRE + "\n".join(entrees)


async def lexique(rpc_service, ttl: int = 300) -> str:
    """Le lexique de Patrick, relu au plus toutes les 5 minutes (une réponse dans l'app sert au plus 5 minutes plus tard)."""
    if time.monotonic() - _cache["t"] < ttl:
        return _cache["bloc"]
    lignes = await rpc_service("digisha_lexique", {})
    if lignes is None:
        return _cache["bloc"]                     # panne : on garde le dernier lexique connu
    illus = await rpc_service("digisha_lexique_illustrations", {})
    if illus is not None:                         # panne : on garde les dernières illustrations connues
        _cache["illus"] = _illustrations_par_cle(illus)
    _cache.update(t=time.monotonic(), bloc=bloc_lexique(lignes, _cache["illus"]))
    return _cache["bloc"]


async def noter(rpc_service, termes, svlbh: str | None, consultante: str | None, question: str, reponse: str) -> list:
    extrait = (question or "")[:700] + "\n— DiGiSha : " + (reponse or "")[:600]
    sorties = []
    for terme, manque in termes:
        sorties.append(await rpc_service("digisha_a_apprendre_noter",
                                         {"p_svlbh": svlbh, "p_consultante": consultante, "p_terme": terme,
                                          "p_manque": manque or None, "p_extrait": extrait}))
    return sorties
