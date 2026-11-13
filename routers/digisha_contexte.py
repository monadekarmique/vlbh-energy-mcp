"""Ce que DiGiSha sait de la personne (fable, 19.10.2026, carte c4b0a17e ; migration 2026-10-19b, digisha_contexte).

Patrick, 19.10 : « avant du sparring des propositions - maintenant une voix qui répète bornée » ; « au lieu de prendre comme
base les dernières discussions de l'apprenante » ; « ça ne peut pas être que mes paroles tout ce que j'ai ou que l'apprenante
ont décodé / discuté pour elle doit être prise en compte ».

Mesuré au banc (19.10, messages réels de Giulia, ~/svlbh-exports/banc_digisha/) : la reprise d'avant ne rendait que les pages
DiGiSha du canal, relances comprises (51 « Mesure : » en 12 101 car.) et le modèle les imitait, 3/3, quel que soit le prompt ;
tout garder en disant « n'imite pas » : 2/3 et 3/3 ; tout garder SANS les relances : 0/3, et DiGiSha cite le décodage de Patrick.
D'où : la base rend tout (ses jours de fil, ses séances DiGiSha, les décodages posés sur sa fiche par une autre personne) ; ici
on retire des réponses de DiGiSha les seules relances — les lignes « Mesure : … » et les questions qui terminent une réponse.

13.11.2026 (fiche 3ce90fd5) — Anne, 10.11 16h40 : « Ton message de 10h38 n'est pas dans ce que je vois ». Sa page du jour
faisait 48 136 caractères en 20 échanges ; la reprise n'en gardait que la fin. Désormais le début d'une page DiGiSha qui
dépasse son budget est découpé en blocs alignés sur le début de la page (donc identiques d'un tour à l'autre tant que la
page ne fait que grandir), chaque bloc est résumé UNE fois, et la suite est rendue mot pour mot : plus de trou.
"""
import asyncio
import re

# Un paragraphe de réponse de DiGiSha dans une page : de « **DiGiSha :** » jusqu'à la prochaine prise de parole datée.
_REPONSE = re.compile(r"\*\*DiGiSha :\*\*.*?(?=\n\*\*[^*\n]{1,60} · \d\dh\d\d :\*\*|\Z)", re.S)
_MESURE = re.compile(r"(?m)^.*\bMesure ?:.*$\n?")
_FIN_QUESTION = re.compile(r"\?\s*(\*+|_+)?\s*(\S{1,3})?\s*$")

BUDGETS = {"decodage": 8000, "fil": 8000, "digisha": 6000}
# Le début d'une prise de parole datée d'une personne (« **Anne · 10h38 :** ») : là seulement une page se coupe.
_DEBUT_TOUR = re.compile(r"(?m)^(?=\*\*[^*\n]{1,60} · \d\dh\d\d :\*\*)")
_HEURE_TOUR = re.compile(r"(?m)^\*\*[^*\n]{1,60} · (\d\dh\d\d) :\*\*")
BLOC_CAR = 6000          # un bloc du début : au moins ce nombre de caractères, en échanges entiers
SUITE_CAR = 4000         # ce qui reste mot pour mot après le dernier bloc détaché : au moins ce nombre de caractères
MAX_DIGISHA_BASE = 120000    # ce qu'on demande à la base pour les séances DiGiSha : la page du jour entière
ENTIER = "_entier"       # une page déjà préparée (début résumé + suite mot pour mot) : mettre_en_forme ne la coupe plus
TITRES = {
    "decodage": "### Décodages posés pour elle par une autre personne (Patrick, sa mentor) — ils font foi : cite-les, ne les paraphrase pas",
    "fil": "### Ses dernières discussions (son fil : ce qu'elle et Patrick ont échangé et décodé)",
    "digisha": "### Ses séances DiGiSha — ce qu'elle a décodé ici",
}


def sans_relances(texte: str) -> str:
    """Retire des réponses de DiGiSha les relances : toute ligne « Mesure : … » et les lignes-questions qui terminent une réponse.
    Les paroles des personnes ne sont pas touchées."""
    def nettoyer(m: re.Match) -> str:
        bloc = _MESURE.sub("", m.group(0))
        lignes = bloc.rstrip().split("\n")
        while len(lignes) > 1 and _FIN_QUESTION.search(lignes[-1].strip()):
            lignes.pop()
        while len(lignes) > 1 and not lignes[-1].strip().strip("-—*_ "):
            lignes.pop()
        return "\n".join(lignes) + "\n"
    return _REPONSE.sub(nettoyer, texte or "")


def _fin(texte: str, n: int) -> str:
    return texte if len(texte) <= n else "…" + texte[-n:]


def decouper_page(corps: str, bloc: int = BLOC_CAR, queue: int = SUITE_CAR) -> tuple[list[str], str]:
    """→ (blocs du début à résumer, suite à garder mot pour mot). blocs + suite = corps, au caractère près.

    Les blocs se forment depuis le DÉBUT de la page, par échanges entiers, dès qu'ils atteignent `bloc` caractères ; un bloc
    n'est détaché que s'il reste après lui au moins `queue` caractères. Une page qui grandit par la fin garde donc les mêmes
    blocs d'un tour à l'autre (leurs résumés se relisent) et en détache un de plus de temps en temps."""
    tours = [t for t in _DEBUT_TOUR.split(corps or "") if t]
    blocs, courant, reste = [], "", len(corps or "")
    for t in tours:
        courant += t
        if len(courant) >= bloc:
            if reste - len(courant) < queue:
                break
            blocs.append(courant)
            reste -= len(courant)
            courant = ""
    return blocs, (corps or "")[len("".join(blocs)):]


def _heures(texte: str) -> str:
    h = _HEURE_TOUR.findall(texte)
    return f" ({h[0]}–{h[-1]})" if len(h) > 1 else (f" ({h[0]})" if h else "")


async def resumer_debuts(lignes: list | None, resumer, budget: int = BUDGETS["digisha"]) -> list | None:
    """Prépare la page DiGiSha la plus récente quand elle dépasse son budget : le début en résumés (un par bloc, par
    `resumer(texte) -> str | None`, appelés ensemble), la suite mot pour mot. Rend les lignes, cette page remplacée et
    marquée ENTIER. Une page qui tient en un bloc et sa suite (BLOC_CAR + SUITE_CAR) passe entière, sans résumé. Page déjà
    coupée par la base (« … » en tête), échange unique trop long ou résumé en échec : lignes inchangées — la page rendra sa
    fin, comme avant. Jamais bloquant."""
    if not lignes or resumer is None:
        return lignes
    i = max((k for k, l in enumerate(lignes) if isinstance(l, dict) and l.get("genre") == "digisha"), default=None)
    if i is None:
        return lignes
    corps = (lignes[i].get("corps") or "").strip()
    if corps.startswith("…") or len(sans_relances(corps).strip()) <= budget:
        return lignes
    blocs, suite = decouper_page(corps)
    if not blocs:
        if len(corps) > BLOC_CAR + SUITE_CAR:
            return lignes
        return lignes[:i] + [{**lignes[i], ENTIER: True}] + lignes[i + 1:]
    resumes = await asyncio.gather(*(resumer(sans_relances(b).strip()) for b in blocs), return_exceptions=True)
    if any(not isinstance(r, str) or not r.strip() for r in resumes):
        return lignes
    debut = "\n\n".join(f"[Résumé du début de la page, partie {k}/{len(blocs)}{_heures(b)}]\n{r.strip()}"
                         for k, (b, r) in enumerate(zip(blocs, resumes), 1))
    page = dict(lignes[i], corps=debut + "\n\n[Suite de la page, mot pour mot]\n" + suite.strip())
    page[ENTIER] = True
    return lignes[:i] + [page] + lignes[i + 1:]


def mettre_en_forme(lignes: list | None, budgets: dict | None = None) -> str:
    """Les lignes de digisha_contexte (jour, genre, auteur, titre, corps) → le bloc à donner au modèle. Chaque genre garde son
    budget APRÈS le retrait des relances ; les plus récentes d'abord, la page qui déborde rend sa fin."""
    if not lignes:
        return ""
    budgets = {**BUDGETS, **(budgets or {})}
    parts = []
    for genre in ("decodage", "fil", "digisha"):
        pages = [l for l in lignes if isinstance(l, dict) and l.get("genre") == genre]
        if not pages:
            continue
        rendues, reste = [], budgets[genre]
        for p in reversed(pages):                       # la base les rend du plus ancien au plus récent
            corps = (p.get("corps") or "").strip()
            if genre != "fil":
                corps = sans_relances(corps).strip()
            if not corps or reste <= 0:
                continue
            if not p.get(ENTIER):                       # une page préparée par resumer_debuts garde tout : pas de trou
                corps = _fin(corps, reste)
            reste -= len(corps)
            qui = f" — {p.get('auteur')}" if genre == "decodage" and p.get("auteur") else ""
            rendues.append(f"**{p.get('titre') or 'Sans titre'}** ({p.get('jour')}{qui})\n{corps}")
        if rendues:
            parts.append(TITRES[genre] + "\n\n" + "\n\n".join(reversed(rendues)))
    return "\n\n".join(parts)
