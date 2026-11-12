"""Le sondage WhatsApp que DiGiSha prépare (mother bee apple mac, 13.11.2026, carte 280b0b5a ; migration 2026-11-13a).

Patrick, 21.10.2026 : « ok on incorpore ça dans la voix DiGiSha c'est qqch à préparer ».
Patrick, 11.11.2026 05h10, à la question « à quoi sert le premier sondage » : « Valider la clé chromatique du jour ».
Patrick, 12.11.2026 : « C'est moi ou une ST5 - actuellement Anne qui la valide ».
Patrick, 13.11.2026 00h22 : « Les deux en même temps donc je peux dans DiGiSha ajouter une de mes clés décodées ».

Trois temps, et DiGiSha n'envoie jamais rien lui-même :
  1. Patrick joint une de ses clés à son message — l'app écrit ⟦Clé chromatique : nom — teintes⟧ dans le tour ;
  2. DiGiSha termine sa réponse par ⟦Sondage pour <prénom> : question | option | option⟧ ; le serveur retire la ligne,
     range la PROPOSITION en base (pont_sondage_proposer : état « propose », rien ne part) et montre ce qui partira ;
  3. Patrick écrit « envoie » : le serveur fait passer la proposition en file (pont_sondage_envoyer) sans appeler le
     modèle ; l'agent du Mac la porte au pont. Une proposition de plus de 30 minutes ne part plus.
Celle qui reçoit est désignée par la base : Patrick ou une ST5 active, par son prénom, à son numéro — jamais un groupe
(DEC 09.11.2026). Tout ceci n'existe que pour le propriétaire.
"""
import re
import unicodedata

# Patrick, 12.11.2026 : « actuellement Anne ». À changer ici le jour où il en nomme une autre.
VALIDATRICE_DU_JOUR = "Anne"
QUESTION_PAR_DEFAUT = "Valider la clé chromatique du jour"

SONDAGE_CADRE = (
    "## Un sondage WhatsApp, à faire valider\n"
    "Patrick peut te demander de préparer un sondage WhatsApp — d'abord pour faire valider la clé chromatique du jour. Celle "
    f"qui valide est Patrick lui-même ou une ST5 ; aujourd'hui c'est {VALIDATRICE_DU_JOUR}. S'il ne nomme personne, tu "
    f"l'adresses à {VALIDATRICE_DU_JOUR} ; s'il dit « à moi », tu écris « moi ».\n"
    "Une clé chromatique qu'il joint à son message s'écrit ⟦Clé chromatique : <nom> — <ses teintes, niveau par niveau>⟧ : "
    "c'est une de ses clés décodées, tu la lis telle quelle (un niveau scellé ne se réécrit pas). Le serveur l'enverra, mot "
    "pour mot, juste avant le sondage : tu ne la recopies pas.\n"
    "Tu ne peux rien envoyer toi-même. Quand il te demande un sondage, tu termines ta réponse par UNE ligne :\n"
    "⟦Sondage pour <prénom> : <la question> | <option 1> | <option 2>⟧\n"
    f"Sans autre consigne : la question « {QUESTION_PAR_DEFAUT} », les options « Validée » et « À reprendre ». S'il donne "
    "sa question ou ses options, tu prends les siennes, mot pour mot (de 2 à 12 options, un seul choix).\n"
    "Le serveur retire cette ligne, range la proposition et affiche sous ta réponse ce qui partira : ne le répète pas. Rien "
    "ne part tant qu'il n'a pas écrit « envoie ». Tu n'écris jamais qu'un sondage est parti, ni qu'il a été reçu."
)

_SONDAGE = re.compile(r"\n?[ \t]*⟦\s*Sondage(?:\s+pour\s+(?P<pour>[^:⟧\n]{1,60}?))?\s*:\s*(?P<corps>[^⟧\n]{1,1600})⟧[ \t]*")
_CLE = re.compile(r"⟦\s*Clé chromatique\s*:\s*(?P<cle>[^⟧]{1,1500}?)\s*⟧")
_ENVOIE = re.compile(r"^(oui )?envoie( le| la)?( sondage)?$")


def extraire_sondage(texte: str) -> tuple[str, dict | None]:
    """(le texte sans les lignes ⟦Sondage …⟧, la première proposition lisible ou None).
    Une proposition = {pour, question, options} ; `pour` vaut la validatrice du jour si la ligne ne nomme personne."""
    proposition = None
    for m in _SONDAGE.finditer(texte or ""):
        morceaux = [x.strip().strip("«»\"' ") for x in m.group("corps").split("|")]
        question, options = (morceaux[0] if morceaux else ""), [o for o in morceaux[1:] if o]
        if proposition is None and question:
            pour = (m.group("pour") or "").strip().strip("«»\"' ") or VALIDATRICE_DU_JOUR
            proposition = {"pour": pour, "question": question, "options": options}
    return _SONDAGE.sub("", texte or "").rstrip(), proposition


def cle_jointe(tours: list[tuple[str, str]]) -> str | None:
    """La dernière clé chromatique jointe par la PERSONNE dans la conversation : `tours` = [(rôle, texte)], du plus ancien
    au plus récent. Une marque dans une réponse de DiGiSha ne compte pas."""
    for role, texte in reversed(tours or []):
        if role != "user":
            continue
        trouvees = _CLE.findall(texte or "")
        if trouvees:
            return " ".join(trouvees[-1].split())
    return None


def message_avant(cle: str | None) -> str | None:
    """Le message WhatsApp qui précède le sondage : la clé, telle que Patrick l'a jointe."""
    return f"Clé chromatique : {cle}" if cle else None


def _plat(t: str) -> str:
    sans = "".join(c for c in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z]+", " ", sans).split())


def est_envoie(texte: str) -> bool:
    """« envoie », « Envoie. », « envoie-le », « oui envoie », « envoie le sondage » — et rien d'autre."""
    return bool(_ENVOIE.match(_plat(texte)))


def _refus(r, pour: str) -> str:
    """Pourquoi la proposition n'a pas été rangée, en une phrase."""
    debut = "Je n'ai pas préparé le sondage : "
    if not isinstance(r, dict):
        return debut + "la base n'a pas répondu. Redemande-le-moi dans un instant."
    raison = r.get("raison")
    if raison in ("inconnue", "ambigu"):
        qui = ", ".join(str(x) for x in (r.get("validatrices") or []))
        return debut + f"« {r.get('pour') or pour} » n'est pas parmi celles et ceux qui valident ({qui}). Dis-moi à qui il va."
    if raison == "sans_numero":
        return debut + f"la base ne connaît pas de numéro WhatsApp pour {r.get('pour') or pour}."
    if raison == "options":
        return debut + "il faut de 2 à 12 options différentes."
    if raison == "longueur":
        return debut + "la question tient en 255 caractères, chaque option en 100."
    if raison == "auteur":
        return debut + "seul Patrick peut en préparer un."
    return debut + f"la base l'a refusé ({raison})."


def bloc_propose(r: dict, avant: str | None) -> str:
    """Ce qui partira, tel que la base l'a rangé."""
    lignes = ["**Sondage prêt — rien n'est parti.**", "", f"- Pour : {r.get('pour')} (pont {r.get('pont')})"]
    if avant:
        lignes.append(f"- Juste avant, ce message : {avant}")
    lignes.append(f"- Question : {r.get('question')}")
    lignes.append("- Options : " + " · ".join(str(o) for o in (r.get("options") or [])))
    lignes += ["", "Écris « envoie » pour qu'il parte. Il reste prêt 30 minutes ; une autre proposition le remplace."]
    return "\n".join(lignes)


async def proposer_sondage(rpc_service, svlbh: str | None, proposition: dict, cle: str | None) -> str:
    """Range la proposition (rien ne part) et rend le bloc à montrer sous la réponse — ou la raison du refus."""
    avant = message_avant(cle)
    r = await rpc_service("pont_sondage_proposer", {
        "p_auteur": svlbh, "p_pour": proposition.get("pour"), "p_question": proposition.get("question"),
        "p_options": proposition.get("options") or [], "p_avant": avant})
    if not isinstance(r, dict) or r.get("ok") is not True:
        return _refus(r, str(proposition.get("pour") or ""))
    return bloc_propose(r, avant if r.get("avant") else None)


async def envoyer_sur_son_mot(rpc_personne, rpc_service, authorization: str | None, svlbh: str | None,
                              message: str) -> str | None:
    """Le dernier message est « envoie » et le propriétaire a un sondage en suspens : il passe en file, et la réponse est
    cette phrase — sans appel au modèle. None dans tous les autres cas : le tour suit son cours habituel."""
    if not svlbh or not est_envoie(message):
        return None
    if await rpc_personne(authorization, "is_owner_st6", {}) is not True:
        return None
    r = await rpc_service("pont_sondage_envoyer", {"p_auteur": svlbh})
    if not isinstance(r, dict) or not r.get("n"):
        return None
    return (f"Le sondage « {r.get('question')} » est remis au pont {r.get('pont')} pour {r.get('pour')}. Il part dans la "
            "minute ; les votes se lisent dans la conversation WhatsApp.")
