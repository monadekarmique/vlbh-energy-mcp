"""Recherche sémantique dans le fil — le vecteur de la QUESTION, calculé ici (carte Kanban b8d68119, 24.09.2026).

Les vecteurs des fils sont calculés la nuit sur le Mac de Patrick (~/svlbh-exports/embeddings_nocturnes.py) et
rangés dans public.fil_embedding. Pour chercher, il faut le vecteur de la question dans LE MÊME espace : même
modèle, même fichier de poids, même tokenizer, même pooling — d'où `embed_minilm.py`, copie octet pour octet de
celui du Mac (vérifier par shasum), et les empreintes SHA-256 ci-dessous : si Hugging Face changeait un fichier,
le chargement échouerait plutôt que de produire des vecteurs d'un autre espace.

Le texte de la question ne sort pas de chez nous : il est encodé ici ; seul le vecteur va en base.

Mémoire mesurée sur le Mac (24.09) : sentencepiece +67 Mo, session ONNX quint8 +133 Mo — le service tourne à
~100 Mo sur 512. Coupe-circuit sans code : DIGISHA_SEMANTIQUE=0 → recherche lexicale seule, comme avant.
Tout échec (téléchargement, empreinte, chargement) retombe sur la recherche lexicale : le mode fil ne casse
jamais à cause de ce module.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import pathlib
import time

import httpx

log = logging.getLogger("digisha")

REVISION = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"   # dépôt HF sentence-transformers, épinglé le 24.09.2026
BASE_HF = ("https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/"
           + REVISION + "/")
EMPREINTES = {
    "sentencepiece.bpe.model": "cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865",
    "onnx/model_quint8_avx2.onnx": "98a01d88b7de996cdea58c32ca71208c09968d143798814b2ea09d3439dc334f",
}
DOSSIER = pathlib.Path(os.environ.get("DIGISHA_MODELE_DIR", "/tmp/svlbh-minilm"))
NOUVEL_ESSAI_APRES_S = 600

_encodeur = None
_echec_le: float | None = None
_verrou: asyncio.Lock | None = None


def actif() -> bool:
    return os.environ.get("DIGISHA_SEMANTIQUE", "1") != "0"


def _sha256(chemin: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def _telecharger_et_charger():
    for nom, attendu in EMPREINTES.items():
        cible = DOSSIER / nom
        if cible.exists() and _sha256(cible) == attendu:
            continue
        cible.parent.mkdir(parents=True, exist_ok=True)
        provisoire = cible.with_suffix(cible.suffix + ".part")
        with httpx.stream("GET", BASE_HF + nom, follow_redirects=True, timeout=120) as r:
            r.raise_for_status()
            with open(provisoire, "wb") as f:
                for bloc in r.iter_bytes(1 << 20):
                    f.write(bloc)
        obtenu = _sha256(provisoire)
        if obtenu != attendu:
            provisoire.unlink(missing_ok=True)
            raise RuntimeError(f"empreinte de {nom} : {obtenu[:12]} ≠ {attendu[:12]} — autre fichier que celui du Mac")
        provisoire.replace(cible)
    from routers.embed_minilm import Encodeur   # import tardif : le service démarre même sans onnxruntime
    return Encodeur(str(DOSSIER), fils=1)


async def encodeur():
    """L'encodeur, chargé une fois (en arrière-plan, hors de la boucle), ou None s'il n'est pas disponible."""
    global _encodeur, _echec_le, _verrou
    if not actif():
        return None
    if _encodeur is not None:
        return _encodeur
    if _echec_le and time.time() - _echec_le < NOUVEL_ESSAI_APRES_S:
        return None
    if _verrou is None:
        _verrou = asyncio.Lock()
    async with _verrou:
        if _encodeur is None:
            t0 = time.time()
            try:
                _encodeur = await asyncio.to_thread(_telecharger_et_charger)
                _echec_le = None
                log.info("digisha — recherche sémantique prête en %.1fs (%s)", time.time() - t0, DOSSIER)
            except Exception as exc:   # jamais bloquant, jamais muet
                _echec_le = time.time()
                log.warning("digisha — recherche sémantique indisponible, lexicale seule : %r", exc)
    return _encodeur


async def precharger() -> None:
    """Appelé au démarrage du service : la première question n'attend pas le téléchargement."""
    await encodeur()


async def vecteur_question(question: str) -> str | None:
    enc = await encodeur()
    if enc is None or not (question or "").strip():
        return None
    from routers.embed_minilm import vecteur_texte
    v = await asyncio.to_thread(enc.encoder, [question])
    return vecteur_texte(v[0])
