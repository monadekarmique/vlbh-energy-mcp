"""Les savoirs des apps, que DiGiSha va chercher lui-même (fable, 06.11.2026).

Patrick, 06.11 : « je trouve que DiGiSha n'utilise pas encore assez les savoirs croisés de mes app » ; « comment puis-je lui
donner des instructions d'aller chercher de l'info ? » ; « oui tu construis la marque corrigé et les 5 savoirs ».
Mesuré ce jour-là : la consigne active (digisha-v2.5) ne nommait ni méridien, ni Palette, ni hDOM, ni Phantom ; DiGiSha n'a
aucun outil et ne sait que ce qu'on lui donne à chaque tour.

Les cinq savoirs les plus croisés des apps sont extraits TELS QUELS par scripts/extraire_savoirs_apps.mjs dans
data/savoirs_apps.json. DiGiSha les consulte par un outil, `chercher_savoir`, quand la question les touche ou quand on le
lui demande (« va chercher NNO dans la Rose des Vents »). Chaque version porte le stade de l'app qui la montre ; une personne
ne lit que les versions de son stade et des stades en dessous (Patrick : « ils sont le savoir au stade ST2, ST3 et ST4 »).
"""
import json
import logging
import re
import unicodedata
from pathlib import Path

log = logging.getLogger("digisha")

_FICHIER = Path(__file__).resolve().parent.parent / "data" / "savoirs_apps.json"
try:
    SAVOIRS: dict = json.loads(_FICHIER.read_text(encoding="utf-8"))["savoirs"]
except (OSError, ValueError, KeyError) as exc:          # jamais bloquant : DiGiSha répond sans l'outil
    log.error("digisha — savoirs des apps illisibles (%s) : l'outil chercher_savoir est retiré", exc)
    SAVOIRS = {}

MAX_TOURS_OUTIL = 2            # deux recherches au plus par réponse : la latence et le coût restent bornés
MAX_CAR_RESULTAT = 7000        # ce que rend une recherche, au plus
MAX_RESULTATS = 6

OUTIL_NOM = "chercher_savoir"
DERNIERE_PASSE = ("(Plus de recherche possible pour cette réponse : réponds maintenant à la question, avec ce que les "
                  "recherches ont rendu, et dis ce qui manque s'il manque quelque chose.)")


def stade_de(stx: str | None, proprietaire: bool = False) -> int:
    """« ST4 » → 4 ; le propriétaire lit tout ; illisible → 0 (aucune version)."""
    if proprietaire:
        return 9
    m = re.match(r"\s*ST\s*(\d+)", stx or "", re.I)
    return int(m.group(1)) if m else 0


def _plat(t: str) -> str:
    t = unicodedata.normalize("NFD", t or "")
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def _mots(requete: str) -> list[str]:
    vus, sortie = set(), []
    for m in re.findall(r"[0-9a-z][0-9a-z\-]*", _plat(requete)):
        m = m.strip("-")
        if len(m) >= 2 and m not in vus and m not in _VIDES:
            vus.add(m)
            sortie.append(m)
    return sortie


_VIDES = {"le", "la", "les", "de", "des", "du", "un", "une", "et", "ou", "en", "dans", "sur", "pour", "par", "avec", "que",
          "qui", "quoi", "est", "sont", "au", "aux", "ce", "cette", "ces", "son", "sa", "ses", "mon", "ma", "mes", "the", "of"}


def versions_lisibles(savoir: dict, stade: int) -> list[dict]:
    return [v for v in savoir.get("versions", []) if int(v.get("stade") or 99) <= stade]


def outil(stade: int) -> dict | None:
    """La définition de l'outil pour ce stade — None si aucune version ne lui est lisible."""
    lisibles = {k: s for k, s in SAVOIRS.items() if versions_lisibles(s, stade)}
    if not lisibles:
        return None
    liste = "\n".join(f"- {k} : {s['titre']} — {s['description']}" for k, s in lisibles.items())
    return {
        "name": OUTIL_NOM,
        "description": (
            "Cherche dans les savoirs des apps de Patrick (tables codées dans ses apps, données telles quelles). "
            "Donne le savoir et ce que tu cherches : une direction (NNO), un type (KI-DE-03), une séphirah (Hod), un esprit "
            "(Hun), une paire (hun→shen), un point (GV4), une dimension (D8), un organe, une émotion, une teinte (#660033)… "
            "Requête vide : la liste des entrées du savoir.\n" + liste),
        "input_schema": {
            "type": "object",
            "properties": {
                "savoir": {"type": "string", "enum": list(lisibles)},
                "requete": {"type": "string", "description": "Ce que tu cherches, en quelques mots ou une clé."},
            },
            "required": ["savoir", "requete"],
        },
    }


SAVOIRS_CADRE = (
    "## Les savoirs des apps de Patrick — va les chercher\n"
    "Tu as un outil, `chercher_savoir`, qui ouvre les tables codées dans les apps de Patrick : la Rose des Vents du Hara, les "
    "types DE de la Lignée masculine, l'arbre des Séphiroth chromatique et les Tores de Lumière, les Wu Shen et la "
    "DynaPathoMu, les chakras hDOM par dimension et les portes Phantom. Dès qu'une question touche l'un de ces savoirs — une "
    "direction, un type, une séphirah, une teinte, un esprit, une cascade, un chakra, une dimension, une porte, un point — "
    "tu vas y chercher AVANT de répondre, et tu croises : un savoir en appelle souvent un autre (un type Lmasc renvoie à une "
    "direction, une séphirah, une porte). Quand Patrick ou la personne te dit d'aller chercher, tu le fais.\n"
    "Ce que l'outil rend fait foi pour le contenu des apps : tu le cites avec sa source (« Rose des Vents, Priv 4 VIFA »), "
    "tu n'y ajoutes rien qu'il ne dit pas, et s'il ne trouve rien tu le dis. Tu n'annonces pas ta recherche : tu réponds. "
    "Le lexique et les corrections de Patrick passent avant les apps."
)


def _entrees(savoir: dict, stade: int) -> list[tuple[dict, dict]]:
    """(version, entrée) lisibles. Un savoir `memes_cles` (le même type Lmasc dans VIFA et dans Chroma 2) n'en garde qu'une
    par clé : celle du stade le plus haut ; ailleurs, chaque version garde les siennes (ce sont d'autres tables)."""
    par_cle: dict[str, tuple[dict, dict]] = {}
    for v in sorted(versions_lisibles(savoir, stade), key=lambda v: int(v.get("stade") or 0)):
        for e in v.get("entrees", []):
            par_cle[str(e.get("cle")) if savoir.get("memes_cles") else f"{v.get('nom')}|{e.get('cle')}"] = (v, e)
    return list(par_cle.values())


def chercher(savoir_id: str, requete: str, stade: int) -> str:
    """Le résultat de l'outil, en JSON compact borné."""
    savoir = SAVOIRS.get(savoir_id)
    if not savoir or not versions_lisibles(savoir, stade):
        return json.dumps({"erreur": f"savoir inconnu ou fermé à ce stade : {savoir_id}", "savoirs": [
            k for k, s in SAVOIRS.items() if versions_lisibles(s, stade)]}, ensure_ascii=False)
    paires = _entrees(savoir, stade)
    mots = _mots(requete)
    if not mots:
        return _borne({"savoir": savoir["titre"], "versions": [
            {"nom": v["nom"], "stade": f"ST{v['stade']}", "app": v["app"],
             "cles": [e.get("cle") for e in v.get("entrees", [])]} for v in versions_lisibles(savoir, stade)]})
    notes = []
    for v, e in paires:
        texte = _plat(json.dumps(e, ensure_ascii=False))
        cle = _plat(str(e.get("cle") or ""))
        note = 0.0
        for m in mots:
            if m == cle or (len(m) >= 3 and cle.startswith(m + " ")):
                note += 10
            elif re.search(rf"(?<![0-9a-z]){re.escape(m)}(?![0-9a-z])", cle):
                note += 6
            n = len(re.findall(rf"(?<![0-9a-z]){re.escape(m)}(?![0-9a-z])", texte))
            if n:
                note += 2 + min(n, 4) * 0.5
            elif len(m) >= 5 and m in texte:
                note += 1
        if note > 0:
            notes.append((note, v, e))
    notes.sort(key=lambda t: -t[0])
    resultats = [{"source": f"{v['app']} · {v['nom']} (ST{v['stade']})", "entree": e} for _, v, e in notes[:MAX_RESULTATS]]
    return _borne({"savoir": savoir["titre"], "requete": requete, "trouves": len(notes), "resultats": resultats},
                  [e for _, _, e in notes[:40]])


def _titre(e: dict) -> str:
    for k in ("nom_fr", "nom", "name", "label", "titre", "emotion", "qualite", "concept", "assoc", "theme"):
        if e.get(k):
            return str(e[k])[:80]
    return ""


def _borne(objet: dict, toutes: list[dict] | None = None) -> str:
    """Au-delà de la borne, on garde les premières entrées entières et on nomme les autres (clé + titre) : DiGiSha peut les
    redemander par leur clé — mesuré au banc le 06.11 : un type Lmasc pèse 4 à 6 000 car., la liste s'arrêtait sans le dire."""
    texte = json.dumps(objet, ensure_ascii=False)
    if len(texte) <= MAX_CAR_RESULTAT:
        return texte
    if "resultats" in objet:
        while len(objet["resultats"]) > 1 and len(json.dumps(objet, ensure_ascii=False)) > MAX_CAR_RESULTAT - 1500:
            objet["resultats"].pop()
        gardees = {json.dumps(r["entree"], ensure_ascii=False, sort_keys=True) for r in objet["resultats"]}
        objet["autres_a_redemander_par_cle"] = [
            f"{e.get('cle')} · {_titre(e)}".rstrip(" ·") for e in (toutes or [])
            if json.dumps(e, ensure_ascii=False, sort_keys=True) not in gardees][:30]
        texte = json.dumps(objet, ensure_ascii=False)
    return texte[:MAX_CAR_RESULTAT]


def executer(nom: str, entree: dict, stade: int) -> str:
    if nom != OUTIL_NOM or not isinstance(entree, dict):
        return json.dumps({"erreur": f"outil inconnu : {nom}"}, ensure_ascii=False)
    return chercher(str(entree.get("savoir") or ""), str(entree.get("requete") or ""), stade)


def _additionner(total: dict, usage: dict) -> None:
    for k, v in (usage or {}).items():
        if isinstance(v, (int, float)):
            total[k] = total.get(k, 0) + v


async def appeler_avec_savoirs(poster, payload: dict, stade: int) -> tuple[dict, list[str]]:
    """Appelle le modèle avec l'outil ; tant qu'il cherche (deux fois au plus), exécute et rappelle. Rend la DERNIÈRE réponse,
    son usage additionné sur tous les appels (le coût journalisé est le vrai), et les recherches faites (pour le journal).
    `poster(payload) -> dict` fait un appel au modèle et lève en cas d'erreur, comme avant."""
    definition = outil(stade)
    if not definition:
        return await poster(payload), []
    payload["tools"] = [definition]
    usage: dict = {}
    faites: list[str] = []
    data = await poster(payload)
    _additionner(usage, data.get("usage"))
    tours = 0
    while data.get("stop_reason") == "tool_use":
        appels = [b for b in data.get("content", []) if b.get("type") == "tool_use"]
        if not appels:
            break
        tours += 1
        resultats = []
        for b in appels:
            e = b.get("input") or {}
            faites.append(f"{e.get('savoir')}:{str(e.get('requete'))[:40]}")
            resultats.append({"type": "tool_result", "tool_use_id": b.get("id"),
                              "content": executer(b.get("name"), e, stade)})
        if tours >= MAX_TOURS_OUTIL:
            # Dernière passe : plus d'outil, et on le lui DIT — mesuré au banc le 06.11 (sonnet 5.5) : avec tool_choice « none »
            # seul, il rendait un bloc de réflexion et aucun texte (il voulait encore chercher).
            payload["tool_choice"] = {"type": "none"}
            resultats.append({"type": "text", "text": DERNIERE_PASSE})
        payload["messages"] = list(payload["messages"]) + [
            {"role": "assistant", "content": data.get("content")},
            {"role": "user", "content": resultats},
        ]
        data = await poster(payload)
        _additionner(usage, data.get("usage"))
    data = dict(data)
    data["usage"] = usage or data.get("usage") or {}
    return data, faites
