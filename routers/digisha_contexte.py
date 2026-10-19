"""Ce que DiGiSha sait de la personne (fable, 19.10.2026, carte c4b0a17e ; migration 2026-10-19b, digisha_contexte).

Patrick, 19.10 : « avant du sparring des propositions - maintenant une voix qui répète bornée » ; « au lieu de prendre comme
base les dernières discussions de l'apprenante » ; « ça ne peut pas être que mes paroles tout ce que j'ai ou que l'apprenante
ont décodé / discuté pour elle doit être prise en compte ».

Mesuré au banc (19.10, messages réels de Giulia, ~/svlbh-exports/banc_digisha/) : la reprise d'avant ne rendait que les pages
DiGiSha du canal, relances comprises (51 « Mesure : » en 12 101 car.) et le modèle les imitait, 3/3, quel que soit le prompt ;
tout garder en disant « n'imite pas » : 2/3 et 3/3 ; tout garder SANS les relances : 0/3, et DiGiSha cite le décodage de Patrick.
D'où : la base rend tout (ses jours de fil, ses séances DiGiSha, les décodages posés sur sa fiche par une autre personne) ; ici
on retire des réponses de DiGiSha les seules relances — les lignes « Mesure : … » et les questions qui terminent une réponse.
"""
import re

# Un paragraphe de réponse de DiGiSha dans une page : de « **DiGiSha :** » jusqu'à la prochaine prise de parole datée.
_REPONSE = re.compile(r"\*\*DiGiSha :\*\*.*?(?=\n\*\*[^*\n]{1,60} · \d\dh\d\d :\*\*|\Z)", re.S)
_MESURE = re.compile(r"(?m)^.*\bMesure ?:.*$\n?")
_FIN_QUESTION = re.compile(r"\?\s*(\*+|_+)?\s*(\S{1,3})?\s*$")

BUDGETS = {"decodage": 8000, "fil": 8000, "digisha": 6000}
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
            corps = _fin(corps, reste)
            reste -= len(corps)
            qui = f" — {p.get('auteur')}" if genre == "decodage" and p.get("auteur") else ""
            rendues.append(f"**{p.get('titre') or 'Sans titre'}** ({p.get('jour')}{qui})\n{corps}")
        if rendues:
            parts.append(TITRES[genre] + "\n\n" + "\n\n".join(reversed(rendues)))
    return "\n\n".join(parts)
