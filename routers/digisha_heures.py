"""L'heure de chaque intervention, pour que Patrick et DiGiSha se réfèrent au même tour (fable, 07.11.2026).

Patrick, 07.11 vers 21h50, en décodant : « Dans DiGiSha j'aurais besoin de voir l'heure de tes interventions quand je code
avec toi que nous puissions discuter valablement ». La réponse porte son heure (« 21h36 ») ; l'app l'affiche sous la bulle et
la renvoie avec l'historique (champ facultatif « heure » d'un tour) ; le serveur la place entre crochets en tête du tour pour
le modèle, qui peut alors citer « ma réponse de 21h36 ». Une app qui n'envoie pas d'heure ne change rien.
"""
import re

_HEURE = re.compile(r"(?:T|\b)(?P<h>[01]?\d|2[0-3])\s*[h:]\s*(?P<m>[0-5]\d)")


def normaliser(heure: str | None) -> str | None:
    """« 21:36 », « 21h36 », « 2026-11-07T21:36:00+01:00 » → « 21h36 » ; illisible → None."""
    m = _HEURE.search(heure or "")
    return f"{int(m.group('h')):02d}h{m.group('m')}" if m else None


def avec_heures(messages: list[dict]) -> list[dict]:
    """Retire le champ « heure » de chaque tour (l'API du modèle ne le connaît pas) et le place en tête du texte : « [21h36] »."""
    sortie = []
    for m in messages or []:
        m = dict(m)
        h = normaliser(m.pop("heure", None))
        if h:
            c = m.get("content")
            if isinstance(c, str):
                m["content"] = f"[{h}] {c}"
            elif isinstance(c, list):
                m["content"] = [{"type": "text", "text": f"[{h}]"}] + list(c)
        sortie.append(m)
    return sortie


def heure_cadre(maintenant: str) -> str:
    return (
        "## L'heure\n"
        f"Il est {maintenant} à Zurich. Quand l'app la donne, chaque message de la conversation porte son heure entre crochets "
        "(« [21h36] ») : c'est ainsi que Patrick et toi vous référez à une intervention (« ta réponse de 21h36 »). Tu peux "
        "citer ces heures ; tu n'en écris pas toi-même en tête de ta réponse — l'app affiche la sienne.\n"
    )


_EN_TETE = re.compile(r"^\s*\[\s*(?:[01]?\d|2[0-3])\s*[h:]\s*[0-5]\d\s*\]\s*")


def sans_heure_en_tete(texte: str) -> str:
    """Si le modèle imite les crochets en tête de sa réponse, on les retire : l'heure de la réponse est celle du serveur."""
    return _EN_TETE.sub("", texte or "", count=1)
