"""Une réponse DiGiSha coupée en route se redemande sans être recalculée (fable, 06.11.2026).

Patrick, 06.11 07h0x : « pourquoi y a-t-il des problèmes de connexions sur le DiGiSha de mon mac ? ». Mesuré dans le journal
de Chroma 5 Mac (iMac) : 06h57:51 envoi de 19 415 octets ; le serveur répond 200 en 7 s (journal Render 06h57:59) ; l'app ne
reçoit que 1 214 octets et finit en -1005 « connexion réseau perdue » — connexion HTTP/3 réutilisée après 2 min 14 s, Wi-Fi
de l'iMac qui change de chemin chaque minute. Un POST n'est jamais relancé par le système : Patrick voit « problème de
connexion » alors que sa réponse est écrite et déposée.

L'app envoie une clé par message (en-tête X-DiGiSha-Envoi, un UUID) et, sur une coupure, redemande UNE fois avec la même clé.
Ici, la même clé du même appelant rend la même réponse : sans nouvel appel au modèle, sans second dépôt dans le fil. Si la
première est encore en calcul, la seconde l'attend. Gardé en mémoire 10 minutes (un seul processus sur Render)."""
import asyncio
import hashlib
import time
from collections import OrderedDict

DUREE = 600            # secondes
TAILLE = 500           # réponses gardées au plus
ATTENTE = 150          # une redemande attend la première au plus ce temps (le modèle a 120 s par appel)

_faites: "OrderedDict[tuple[str, str], tuple[float, object]]" = OrderedDict()
_en_cours: dict[tuple[str, str], asyncio.Future] = {}


def _cle(appelant: str | None, envoi: str | None) -> tuple[str, str] | None:
    envoi = (envoi or "").strip()
    if not envoi or len(envoi) > 80 or not appelant:
        return None
    return hashlib.sha256(appelant.encode()).hexdigest()[:24], envoi


def _purger(maintenant: float) -> None:
    while _faites and (maintenant - next(iter(_faites.values()))[0] > DUREE or len(_faites) > TAILLE):
        _faites.popitem(last=False)


async def une_seule_fois(appelant: str | None, envoi: str | None, calcul):
    """Rend `await calcul()` une seule fois par (appelant, clé d'envoi) ; sans clé, calcule simplement.
    `appelant` = ce qui identifie l'appel (le jeton) — deux personnes ne partagent jamais une réponse."""
    k = _cle(appelant, envoi)
    if k is None:
        return await calcul()
    maintenant = time.monotonic()
    _purger(maintenant)
    if k in _faites:
        return _faites[k][1]
    if k in _en_cours:
        return await asyncio.wait_for(asyncio.shield(_en_cours[k]), ATTENTE)
    futur = asyncio.get_running_loop().create_future()
    _en_cours[k] = futur
    try:
        reponse = await calcul()
    except BaseException as exc:
        if not futur.done():
            futur.set_exception(exc)
            futur.exception()            # lue : pas d'avertissement « exception never retrieved »
        raise
    else:
        _faites[k] = (time.monotonic(), reponse)
        if not futur.done():
            futur.set_result(reponse)
        return reponse
    finally:
        _en_cours.pop(k, None)
