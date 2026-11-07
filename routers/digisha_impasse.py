"""« Impasse » : le mot code de Patrick quand DiGiSha l'emmène dans un cul-de-sac (fable, 07.11.2026 ; migration 2026-11-07a).

Patrick, 07.11 vers 21h45, en décodant (Cornelia, Arlette) : « J'ai vraiment besoin que nous puissions avoir un mode
apprentissage où DiGiSha puisse m'épauler et ne pas me guider plusieurs fois dans un cul de sac », puis « le mot code va
être : Impasse ». Mesuré le soir même (digisha_a_apprendre, 21h36) : il demandait l'axe Foie–Vésicule biliaire ; les
savoirs ne portent pas la Vésicule ; DiGiSha l'a noté comme un manque, puis a répondu par la paire voisine Po→Hun
(Poumon–Foie). Combler un trou par le voisin, c'est ce qui fait tourner en rond.

Quand Patrick écrit « Impasse », DiGiSha abandonne le chemin qu'il vient de proposer, le nomme, et termine sa réponse par
⟦Impasse : chemin — pourquoi⟧. Le serveur retire la ligne et la garde (digisha_impasse_noter) ; les chemins fermés lui sont
rappelés aux tours suivants — dans les échanges de Patrick, et pour le même cas quand une fiche est en contexte. Si le mot
est là et que la ligne manque, le serveur garde quand même l'impasse : le début de la réponse précédente, et ses mots.
"""
import re

IMPASSE_CADRE = (
    "## Quand Patrick écrit « Impasse »\n"
    "« Impasse » est son mot code : le chemin que tu viens de lui proposer ne mène nulle part. Tu ne le défends pas, tu ne "
    "le reformules pas, et tu n'y reviens plus — ni dans cette conversation, ni plus tard. Tu nommes en une ligne ce que tu "
    "abandonnes, puis tu proposes UNE autre direction, ou tu dis ce qui te manque et tu le lui demandes. Termine ta réponse "
    "par une ligne :\n"
    "⟦Impasse : <le chemin abandonné, en quelques mots> — <pourquoi, avec ses mots>⟧\n"
    "Elle n'est pas montrée : le serveur la garde, et ce chemin te sera rappelé comme fermé.\n"
    "Ce qui te manque se dit ; il ne se comble pas avec ce qui est voisin (une autre paire, un autre organe, une autre "
    "table). Une lecture à mesurer ne vient que d'un savoir des apps, avec sa source, ou de Patrick : sinon, tu lui demandes "
    "quoi mesurer.\n"
)
# 07.11.2026 vers 21h55 — Patrick : « je souhaiterais pouvoir demander à résumer ce qui a été dit au moyen du mot de code
# Compte-rendu ». Rien n'est gardé : c'est une façon de répondre, pas une mémoire.
COMPTE_RENDU_CADRE = (
    "## Quand Patrick écrit « Compte-rendu »\n"
    "C'est son mot code : tu fais le compte-rendu de ce qui a été dit depuis le début de cette conversation (le résumé des "
    "échanges précédents compris), sans rien ajouter de nouveau — ni hypothèse, ni lecture à mesurer de ton cru. En listes "
    "courtes :\n"
    "1. Ce qui est établi — chaque point avec l'heure du tour où il a été posé, quand elle est donnée (« [21h36] ») ;\n"
    "2. Ce que Patrick a corrigé, avec ses mots ;\n"
    "3. Les impasses (les chemins fermés) ;\n"
    "4. Ce qui manque encore ou reste ouvert ;\n"
    "5. Les prochaines mesures que Patrick a annoncées — seulement les siennes.\n"
)
IMPASSES_CADRE = (
    "## Chemins que Patrick a marqués « Impasse » — fermés\n"
    "Tu ne les reproposes pas, même reformulés. Si la question y ramène, dis-le et cherche ailleurs, ou demande-lui.\n\n"
)

_MOT = re.compile(r"\bimpasse\b", re.I)
_IMPASSE = re.compile(r"\n?[ \t]*⟦\s*Impasse\s*:\s*(?P<chemin>[^⟧\n]{1,160}?)(?:\s+[—–-]\s+(?P<raison>[^⟧\n]{0,600}))?\s*⟧[ \t]*")
MAX_IMPASSES = 20


def dit_impasse(message: str) -> bool:
    """Le dernier message de Patrick porte-t-il son mot code ?"""
    return bool(_MOT.search(message or ""))


def extraire_impasse(texte: str) -> tuple[str, list[tuple[str, str]]]:
    """(le texte sans les lignes ⟦Impasse : …⟧, [(chemin, pourquoi)]) — deux au plus, sans doublon."""
    impasses: list[tuple[str, str]] = []
    for m in _IMPASSE.finditer(texte or ""):
        c = m.group("chemin").strip().strip("«»\"' ")
        if c and c.lower() not in {x.lower() for x, _ in impasses} and len(impasses) < 2:
            impasses.append((c, (m.group("raison") or "").strip()))
    return _IMPASSE.sub("", texte or "").rstrip(), impasses


def impasse_de_secours(message: str, reponse_precedente: str) -> tuple[str, str]:
    """Quand le mot est là sans la ligne : le chemin = le début de la réponse précédente de DiGiSha ; pourquoi = ses mots."""
    lignes = [l.strip(" *#-•>") for l in (reponse_precedente or "").splitlines() if l.strip(" *#-•>")]
    chemin = (lignes[0] if lignes else "la réponse précédente")[:160]
    raison = _MOT.sub("", message or "", count=1).strip(" :—–-.,\n\t") or "Patrick : « Impasse »"
    return chemin, raison[:600]


async def noter_impasses(rpc_service, impasses, auteur: str | None, consultante: str | None, message: str) -> list:
    """Chaque impasse est gardée avec SES mots (la base refuse tout autre auteur que le propriétaire)."""
    if not auteur:
        return []
    return [await rpc_service("digisha_impasse_noter",
                              {"p_auteur": auteur, "p_consultante": consultante, "p_chemin": c,
                               "p_raison": r or None, "p_message": (message or "").strip()[:2000]})
            for c, r in impasses]


def bloc_impasses(lignes) -> str:
    if not isinstance(lignes, list):
        return ""
    entrees = [f"- {l.get('chemin')}" + (f" — {l.get('raison')}" if l.get("raison") else "") + (f" ({l.get('le')})" if l.get("le") else "")
               for l in lignes[:MAX_IMPASSES] if isinstance(l, dict) and l.get("chemin")]
    return (IMPASSES_CADRE + "\n".join(entrees)) if entrees else ""


async def impasses(rpc_service, auteur: str | None, consultante: str | None) -> str:
    """Les chemins fermés de cet auteur : les siens sans fiche, et ceux de la fiche en contexte. Panne → rien."""
    if not auteur:
        return ""
    return bloc_impasses(await rpc_service("digisha_impasses", {"p_auteur": auteur, "p_consultante": consultante}))
