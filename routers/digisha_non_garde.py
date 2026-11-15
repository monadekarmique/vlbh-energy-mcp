"""Ce qu'un tour DiGiSha n'a pas pu garder se dit dans la réponse (fable, 15.11.2026, carte ac79ce6b).

Le 09.11.2026, Anne a fait 14 tours « À propos de » une fiche créée le jour même : la base a refusé les 14 dépôts
(« cette fiche n'est pas la tienne à relire »), l'app a affiché chaque réponse, le serveur n'a écrit qu'un WARNING au
journal, et rien de sa séance n'a été gardé. La cause en base est corrigée (migration 2026-11-10a). Ici, le prochain dépôt
qui ne se fait pas — quel qu'il soit — se VOIT : la réponse de /digisha/chat et de /digisha/accompagnement porte

    non_garde         booléen : vrai quand quelque chose de ce tour n'a pas été gardé, faux sinon ;
    non_garde_motif   la phrase à afficher sous la réponse, en français ; null quand tout est gardé.

Une app qui ne lit pas ces champs ne voit rien changer.

Ce qui se dit :
  · le tour (la page DiGiSha du jour, ou la page « Relecture ») que la base a refusé, auquel elle n'a pas répondu, ou
    qu'elle a rendu sans séance pour une question qui n'est pas un message d'ouverture de l'app ;
  · une pièce jointe (photo, PDF) qui n'est pas arrivée dans le seau, ou n'a pas été rattachée à la page ;
  · les consignes d'un tour « À propos de » qui ne sont pas posées : refusées, base muette, réponse coupée, ou prénom
    de la fiche illisible (une fiche neuve, avant sa première séance) ;
  · les images du lexique montrées avec la réponse, quand elles n'ont pas été rattachées à la page.
Ce qui ne se dit pas : le message d'ouverture écrit par l'app (« 🎓 … »), que la base ne garde jamais ; un compte de
revue (réponse fixe, sans page) ; digisha_chat_log et le journal des coûts, qui sont des compteurs et non la séance.

« Voir comme » ne se dit PAS ici, et ce n'est pas un oubli (contre-épreuve du 15.11.2026) : ce serveur appelle la base
sans l'en-tête de surface de l'app, donc coach_view_target() y est toujours nul — la base ne le voit jamais « en vue »,
et la garde « on regarde, on n'écrit pas » de digisha_fil_deposer (17.10) ne joue pas pour un tour passé par ici. Une
branche qui ne peut pas se produire ne s'écrit pas ; le sujet a sa propre carte.

Le motif ne recopie JAMAIS le message de la base : il peut porter un identifiant, ou la ligne d'une autre personne. Le
message est reconnu parmi ceux que les fonctions de dépôt lèvent (relus dans pg_proc le 15.11.2026) et rendu par une
phrase fixe ; le détail reste au journal, où `extrait_journal` masque les identifiants.

Le suivi vit le temps d'un appel (ContextVar) : `_rpc_personne` et `fil_digisha_deposer` gardent ainsi leur signature —
les bancs d'essai les remplacent tels quels — et la route le relit au moment d'écrire sa réponse.
"""
from __future__ import annotations

import json
import logging
import re
from contextvars import ContextVar
from dataclasses import dataclass, field

log = logging.getLogger("digisha")

# Espace insécable : ni « : » ni un guillemet seul en début de ligne quand la phrase passe à la ligne dans une bulle.
_I = "\N{NO-BREAK SPACE}"
_TOUR = f"Ce tour n'a pas été gardé{_I}: "

# genre → la phrase que l'écran affiche. Le genre va au journal ; la phrase, à la personne. Elle dit ce qui s'est passé,
# jamais « tu n'as pas le droit » : le 09.11 c'est la porte de la base qui se trompait, pas Anne.
MOTIFS_TOUR = {
    "droit": _TOUR + "l'enregistrement sur cette fiche a été refusé.",
    "fiche_soi": _TOUR + "tu n'as pas encore de fiche à ton nom pour le recevoir.",
    "fiche_introuvable": _TOUR + "cette fiche est introuvable.",
    "canal": _TOUR + "le canal du soin n'est pas reconnu.",
    "session": _TOUR + "ta session n'a pas été reconnue. Reconnecte-toi dans l'app.",
    "refus": _TOUR + "l'enregistrement a été refusé.",
    # « probablement » : sur un délai dépassé, le serveur ne sait pas si la base a fini d'écrire après lui.
    "panne": f"Ce tour n'a probablement pas été gardé{_I}: la base de données n'a pas répondu.",
}
MOTIF_CONSIGNES = "Les consignes de ce tour n'ont pas été enregistrées."
MOTIF_ILLUSTRATIONS = "Les images montrées avec cette réponse n'ont pas été rattachées à la page."

# Les messages que digisha_fil_deposer et digisha_relecture_deposer lèvent (pg_proc, 15.11.2026). Reconnus sans dépendre
# d'une lettre accentuée ni d'une espace insécable : la forme exacte des octets en base n'est pas garantie.
_MESSAGES_CONNUS = (
    (re.compile(r"pas la tienne"), "droit"),
    (re.compile(r"aucune fiche «\s*soi\s*»"), "fiche_soi"),
    (re.compile(r"fiche introuvable"), "fiche_introuvable"),
    (re.compile(r"canal inconnu"), "canal"),
    (re.compile(r"non authentifi|\bjwt\b", re.I), "session"),
)


# Les deux formes de question que la base ne garde jamais (digisha_fil_page_ajouter et digisha_relecture_deposer, relues
# dans pg_proc le 15.11.2026) : le message d'ouverture écrit par l'app, pas par la personne. Mêmes motifs, même portée
# (« . » y prend aussi un saut de ligne, comme dans la base).
_ARTEFACTS_APP = (re.compile(r'^\s*[«"]?\s*🎓'), re.compile(r"Module 1 .{0,80}ouvert pour", re.S))


def est_artefact_app(question) -> bool:
    """La question est-elle un message d'ouverture de l'app, que la base ne garde pas ?"""
    return isinstance(question, str) and any(m.search(question) for m in _ARTEFACTS_APP)


def motif_pieces(manquantes: int, jointes: int) -> str:
    """La phrase pour des pièces jointes non gardées, alors que le tour, lui, l'est."""
    if jointes <= 1:
        return "La pièce jointe de ce tour n'a pas été gardée."
    if manquantes >= jointes:
        return f"Les {jointes} pièces jointes de ce tour n'ont pas été gardées."
    return f"{manquantes} des {jointes} pièces jointes de ce tour " + ("n'a pas été gardée." if manquantes == 1 else "n'ont pas été gardées.")


def genre_du_refus(code: int | None, corps: str | None) -> str:
    """Pourquoi un dépôt n'a pas abouti, d'après la réponse de la base. `code` None = pas de réponse (réseau, délai).
    Pur : ne rend qu'un genre de MOTIFS_TOUR, jamais un mot du corps."""
    if code is None or code == 408 or code == 429 or code >= 500:
        return "panne"
    message = corps or ""
    try:
        lu = json.loads(message)
        if isinstance(lu, dict):
            message = str(lu.get("message") or "")
    except ValueError:
        pass
    for motif, genre in _MESSAGES_CONNUS:
        if motif.search(message):
            return genre
    return "session" if code == 401 else "refus"


@dataclass
class Suivi:
    """Ce que le tour en cours n'a pas pu garder."""
    manques: list[tuple[str, str]] = field(default_factory=list)        # (quoi, phrase), dans l'ordre où c'est arrivé
    dernier_echec: tuple[str, str] | None = None                        # (rpc, genre) du dernier appel à la base en échec

    def noter(self, quoi: str, phrase: str, genre: str = "") -> None:
        """Une chose de ce tour n'a pas été gardée. Une ligne au journal, sans rien de la personne ; « non_garde= » se
        cherche tel quel dans le journal Render (sans tiret long ni accent, que son filtre de texte ne trouve pas)."""
        if any(q == quoi for q, _ in self.manques):
            return
        self.manques.append((quoi, phrase))
        log.warning("digisha — non_garde=%s genre=%s", quoi, genre or "-")

    def champs(self) -> dict:
        """Les champs à poser sur la réponse : rien quand tout est gardé (non_garde reste faux, le motif absent)."""
        if not self.manques:
            return {}
        return {"non_garde": True, "non_garde_motif": " ".join(phrase for _, phrase in self.manques)}


_suivi: ContextVar[Suivi | None] = ContextVar("digisha_non_garde", default=None)


def ouvrir() -> Suivi:
    """Ouvre le suivi de l'appel en cours ; la route le garde et le relit en écrivant sa réponse."""
    suivi = Suivi()
    _suivi.set(suivi)
    return suivi


def echec_rpc(nom: str, code: int | None, corps: str | None) -> None:
    """Un appel à la base, avec le jeton de la personne, a échoué : on en retient le genre — jamais le corps."""
    suivi = _suivi.get()
    if suivi is not None:
        suivi.dernier_echec = (nom, genre_du_refus(code, corps))


def tour_non_depose(nom: str, question=None) -> None:
    """Le dépôt `nom` n'a pas rendu de séance. Si le tour devait être gardé, le suivi de l'appel le dit, avec sa raison.

    Trois issues (fonctions relues dans pg_proc le 15.11.2026) : la base a refusé ou n'a pas répondu — l'appel a
    échoué, son genre est dans le suivi ; la base a répondu sans rien écrire parce que la question est un artefact de
    l'app (le message d'ouverture « 🎓 … »), qu'elle ne garde jamais : celui-là ne se dit pas, personne n'a rien écrit ;
    ou elle a répondu sans séance pour une vraie question, sans raison connue d'ici : ce tour n'est pas gardé, on le dit."""
    suivi = _suivi.get()
    if suivi is None:
        return
    echec, suivi.dernier_echec = suivi.dernier_echec, None
    if echec is not None and echec[0] == nom:
        suivi.noter("tour", MOTIFS_TOUR[echec[1]], echec[1])
        return
    if est_artefact_app(question):
        # Rien à l'écran, mais une trace : c'est la base qui décide de ne pas garder ce message.
        log.info("digisha — depot_sans_seance=%s : message d'ouverture de l'app, que la base ne garde pas", nom)
        return
    # Ni refus, ni panne, ni artefact : si la base gagne un jour une autre façon de ne rien écrire, elle ne restera pas muette.
    suivi.noter("tour", MOTIFS_TOUR["refus"], "sans_seance")
