"""signaler_difficulte — le signalement silencieux de DiGiSha, porté du site Pro web au serveur (fable, 15.11.2026).

Patrick, 15.11.2026 à 12h19 (carte 38e837cf) : « Porte-le sur le serveur ». L'outil n'existait que sur Pro web
(svlbh-pro-web, api/ai/chat et src/lib/ai/signalement.ts) : 3 signalements en tout, le dernier le 27.10. Depuis que Pro web
passe par ce serveur (carte b4e26384), aucune surface ne l'avait plus — alors que la consigne active (digisha-v2.5) dit à
DiGiSha de « déposer un signalement discret via l'outil signaler_difficulte ». Même outil, mêmes bornes, même texte :

- Plafond par compte : 3 par heure pleine, 10 sur 24 heures. Le compteur est celui du quota (digisha_appel_heure, migration
  2026-10-18m) sous la clé « signaler:<uid> » — LE MÊME que Pro web — ; chaque tentative compte. Base muette : une fenêtre en
  mémoire du process, à partir des signalements acceptés.
- Texte borné : motif sur une ligne, 500 caractères au plus ; motif + extrait, 2 000 au plus. Au-delà on coupe, on ne refuse
  pas : un signalement de vigilance légitime arrive quand même.
- L'auteur vient de la SESSION (l'identité rendue par gate_subscription), jamais de l'entrée du modèle.
- Silencieux : rien n'en paraît dans la réponse ; le journal du service ne dit que « déposé » ou « refusé », jamais le
  motif (il peut nommer une personne vivante).

Les fonctions pures sont prouvées par Tests/test_digisha_signalement.py ; `deposer` reçoit ses appels à la base en paramètre.
"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

log = logging.getLogger("digisha")

OUTIL_NOM = "signaler_difficulte"
PAR_HEURE = 3
PAR_JOUR = 10
MOTIF_MAX = 500
TEXTE_MAX = 2000
_COUPE = " […]"
# Caractères de contrôle, sauf tabulation et retour à la ligne (gardés dans l'extrait).
_CONTROLES = re.compile("[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f  ]")

OUTIL = {
    "name": OUTIL_NOM,
    "description": (
        "Dépose DISCRÈTEMENT un signalement dans la file de formation quand une situation mérite une formation de la "
        "participante (par ex. une personne VIVANTE possiblement en danger réel, ou une confusion de méthode qui pourrait "
        "l'égarer). N'en parle JAMAIS à l'utilisatrice, ne dévie pas la conversation : tu signales en coulisse et tu "
        "continues normalement."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "motif": {"type": "string", "maxLength": MOTIF_MAX,
                      "description": "Raison du signalement, en une phrase, pour la formation."},
            "extrait": {"type": "string", "maxLength": TEXTE_MAX - MOTIF_MAX,
                        "description": "Court extrait / contexte pertinent (anonymisé si possible)."},
        },
        "required": ["motif"],
        "additionalProperties": False,
    },
}


def borner(texte: str, maximum: int) -> str:
    """Coupe à `maximum` caractères (points de code), marque de coupe comprise."""
    if len(texte) <= maximum:
        return texte
    if maximum <= len(_COUPE):
        return texte[:max(maximum, 0)]
    return texte[:maximum - len(_COUPE)].rstrip() + _COUPE


def valider(entree) -> tuple[bool, dict | str]:
    """L'entrée du modèle : motif (texte non vide, une ligne) et extrait facultatif (texte). Rien d'autre n'est lu."""
    if not isinstance(entree, dict):
        return False, "entrée invalide : objet { motif, extrait? } attendu"
    motif, extrait = entree.get("motif"), entree.get("extrait")
    if not isinstance(motif, str):
        return False, "motif requis (texte)"
    if extrait is not None and not isinstance(extrait, str):
        return False, "extrait : texte attendu"
    # Le motif tient sur une ligne : ni retour à la ligne ni contrôle, pour qu'il ne puisse pas imiter l'en-tête.
    m = borner(re.sub(r"\s+", " ", _CONTROLES.sub(" ", motif)).strip(), MOTIF_MAX)
    if not m:
        return False, "motif requis (texte non vide)"
    e = _CONTROLES.sub("", extrait.replace("\r\n", "\n").replace("\r", "\n")).strip() if isinstance(extrait, str) else ""
    return True, {"motif": m, "extrait": borner(e, TEXTE_MAX - len(m)) if e else None}


def composer_commentaire(s: dict, compte_sans_fiche: str | None = None) -> str:
    """Le texte de feedback_queue.comment — le même que Pro web. `compte_sans_fiche` : l'uid quand la session n'a pas de
    svlbh_id ; il entre alors dans l'en-tête, pour que la ligne porte son auteur."""
    entete = f"[DiGiSha · signalement auto · compte {compte_sans_fiche}]" if compte_sans_fiche else "[DiGiSha · signalement auto]"
    return f"{entete} {s['motif']}" + (f"\n— {s['extrait']}" if s.get("extrait") else "")


def signalements_sur_le_jour(lignes, par_heure: int = PAR_HEURE) -> int:
    """Les signalements des 24 heures, d'après les lignes horaires du compteur. Une heure pleine ne peut en avoir laissé
    passer plus de `par_heure` : les tentatives refusées au-delà ne comptent pas pour la journée."""
    total = 0
    for ligne in lignes or []:
        n = ligne.get("n") if isinstance(ligne, dict) else None
        if isinstance(n, bool) or not isinstance(n, (int, float)) or n != n:
            continue
        total += min(max(0, int(n)), par_heure)
    return total


def plafond(heure: int, jour: int) -> str | None:
    """None = sous les deux plafonds ; sinon celui qui est dépassé. `heure` et `jour` incluent la tentative en cours."""
    if heure > PAR_HEURE:
        return "heure"
    if jour > PAR_JOUR:
        return "jour"
    return None


def compter_en_memoire(acceptes: list[float], maintenant: float) -> tuple[list[float], int, int]:
    """Repli quand la base ne répond pas : (acceptés encore dans les 24 h, heure, jour), tentative en cours comprise."""
    gardes = [t for t in acceptes if maintenant - t < 86_400]
    return gardes, sum(1 for t in gardes if maintenant - t < 3_600) + 1, len(gardes) + 1


_acceptes: dict[str, list[float]] = {}


async def plafond_du_signalement(uid: str, rpc_service, lire_service, maintenant: float) -> str | None:
    cle = f"signaler:{uid}"
    gardes, heure_mem, jour_mem = compter_en_memoire(_acceptes.get(uid, []), maintenant)
    r = await rpc_service("digisha_appel_heure_incr", {"p_cle": cle, "p_limite": PAR_HEURE}, timeout=5)
    n = r.get("n") if isinstance(r, dict) else None
    if isinstance(n, bool) or not isinstance(n, (int, float)):
        log.warning("digisha — signaler_difficulte : compteur en base indisponible, repli en mémoire")
        p = plafond(heure_mem, jour_mem)
    elif n > PAR_HEURE:
        p = "heure"
    else:
        depuis = (datetime.fromtimestamp(maintenant, timezone.utc) - timedelta(days=1)).isoformat()
        lignes = await lire_service(f"digisha_appel_heure?select=n&cle=eq.{quote(cle, safe='')}&heure=gt.{quote(depuis, safe='')}")
        if not isinstance(lignes, list):
            log.warning("digisha — signaler_difficulte : journée comptée en mémoire")
            p = plafond(int(n), jour_mem)
        else:
            p = plafond(int(n), signalements_sur_le_jour(lignes))
    _acceptes[uid] = gardes if p else gardes + [maintenant]
    return p


def _resultat(**champs) -> str:
    return json.dumps(champs, ensure_ascii=False)


async def deposer(entree, ident: dict | None, *, rpc_service, lire_service, inserer_service,
                  maintenant: float | None = None) -> str:
    """Exécute l'outil : valide, compte, dépose dans feedback_queue. Rend le contenu du tool_result (texte JSON). Ne lève
    jamais : un échec se dit au modèle, qui continue normalement sans en parler."""
    ok, valeur = valider(entree)
    if not ok:
        return _resultat(erreur=str(valeur))
    uid = str((ident or {}).get("uid") or "") or None
    svlbh = str((ident or {}).get("svlbh_id") or "") or None
    if not uid:
        return _resultat(erreur="signalement impossible sans compte : rien n'est déposé ; n'en parle pas et continue normalement")
    p = await plafond_du_signalement(uid, rpc_service, lire_service, time.time() if maintenant is None else maintenant)
    if p:
        log.info("digisha — signalement refusé : plafond %s", p)
        borne = f"{PAR_HEURE} par heure" if p == "heure" else f"{PAR_JOUR} sur 24 heures"
        return _resultat(erreur=f"plafond de signalements atteint ({borne}) : rien n'est déposé ; n'en parle pas et continue normalement")
    erreur = await inserer_service("feedback_queue", {
        "author_svlbh_id": svlbh,
        "author_stx": (ident or {}).get("stx") or None,
        "comment": composer_commentaire(valeur, None if svlbh else uid),
        "status": "pending",
        "source": "digisha-auto",
    })
    if erreur:
        log.warning("digisha — signalement non déposé : %s", erreur)
        return _resultat(erreur="le signalement n'a pas pu être déposé ; n'en parle pas et continue normalement")
    log.info("digisha — signalement déposé (feedback_queue, source digisha-auto)")
    return _resultat(ok=True)
