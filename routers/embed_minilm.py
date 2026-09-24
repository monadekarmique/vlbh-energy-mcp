"""Embeddings MiniLM multilingue — LE MÊME FICHIER sur le Mac (la nuit, les fils) et sur Render (la question).

Carte Kanban b8d68119 (DEC Patrick 15.09 « oui nous avons besoin de embeddings », modèle nommé le 24.09 :
paraphrase-multilingual-MiniLM-L12-v2). Rien ne sort de chez nous : le modèle tourne en local, seuls les
vecteurs montent en base.

Choix mesurés le 24.09 sur ce Mac (Intel, AVX2) — ne pas les défaire sans remesurer :
· Poids : `onnx/model_quint8_avx2.onnx` du dépôt officiel (118 Mo). Render starter = 512 Mo dont ~100 utilisés ;
  les poids fp32 seuls font 470 Mo. Fidélité face au fp32 : cosinus 0,995–0,998 par phrase, corrélation des
  similarités croisées 0,997.
· Tokenizer : `sentencepiece` sur `sentencepiece.bpe.model` (+67 Mo résidents) et NON la bibliothèque
  `tokenizers` sur tokenizer.json (+372 Mo résidents : vocabulaire de 250 000 entrées). Sur les 9 964 textes du
  corpus réel, les identifiants sont identiques à 99,4 % ; les 0,6 % restants sont des variantes de
  segmentation de même longueur. La cohérence entre le Mac et Render vient de ce que les DEUX côtés passent
  par CETTE fonction — pas d'une équivalence avec l'autre tokenizer.
· ONNX : prepacking laissé actif (le couper a fait passer la session de +133 à +262 Mo).
· Pooling : moyenne des tokens (1_Pooling/config.json), puis normalisation L2 ; la base cherche en cosinus.

⚠️ Copie exacte attendue dans vlbh-energy-mcp (routers/embed_minilm.py). `shasum embed_minilm.py` doit donner
la même empreinte des deux côtés.
"""
from __future__ import annotations

import os
import re
from typing import Iterable

import numpy as np
import onnxruntime as ort
import sentencepiece as spm

MODELE = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FICHIERS = ("sentencepiece.bpe.model", "onnx/model_quint8_avx2.onnx")
DIMENSION = 384
MAX_TOKENS = 128          # sentence_bert_config.json : max_seq_length (<s> et </s> compris)
FENETRE_TOKENS = 120      # un morceau reste sous la limite
RECOUVREMENT_MOTS = 8     # contexte partagé entre deux morceaux voisins (20 donnait 56 000 morceaux, mesuré 24.09)

# XLM-RoBERTa : identifiants « fairseq » = identifiant sentencepiece + 1, sauf les spéciaux.
_BOS, _PAD, _EOS, _UNK = 0, 1, 2, 3


class Encodeur:
    def __init__(self, dossier: str, fils: int | None = None):
        self.sp = spm.SentencePieceProcessor(model_file=os.path.join(dossier, FICHIERS[0]))
        so = ort.SessionOptions()
        if fils:
            so.intra_op_num_threads = fils
        self.session = ort.InferenceSession(os.path.join(dossier, FICHIERS[1]), so,
                                            providers=["CPUExecutionProvider"])
        self.entrees = {i.name for i in self.session.get_inputs()}

    def _ids(self, texte: str) -> list[int]:
        return [(i + 1) if i != 0 else _UNK for i in self.sp.encode(texte or "")]

    def nb_tokens(self, texte: str) -> int:
        return len(self._ids(texte)) + 2

    def encoder(self, textes: list[str], lot: int = 32) -> np.ndarray:
        """(n, 384) float32, normalisés L2. Ordre conservé."""
        sorties = []
        for i in range(0, len(textes), lot):
            seqs = [[_BOS] + self._ids(t)[:MAX_TOKENS - 2] + [_EOS] for t in textes[i:i + lot]]
            longueur = max(len(s) for s in seqs)
            ids = np.full((len(seqs), longueur), _PAD, dtype=np.int64)
            masque = np.zeros((len(seqs), longueur), dtype=np.int64)
            for k, s in enumerate(seqs):
                ids[k, :len(s)] = s
                masque[k, :len(s)] = 1
            flux = {"input_ids": ids, "attention_mask": masque}
            if "token_type_ids" in self.entrees:
                flux["token_type_ids"] = np.zeros_like(ids)
            jetons = self.session.run(None, flux)[0]            # (b, t, 384)
            m = masque[..., None].astype(np.float32)
            moyenne = (jetons * m).sum(axis=1) / np.clip(m.sum(axis=1), 1e-9, None)
            norme = np.linalg.norm(moyenne, axis=1, keepdims=True)
            sorties.append((moyenne / np.clip(norme, 1e-12, None)).astype(np.float32))
        return np.vstack(sorties) if sorties else np.zeros((0, DIMENSION), np.float32)

    def decouper(self, titre: str | None, corps: str) -> list[str]:
        """Découpe déterministe en morceaux de ≤ FENETRE_TOKENS tokens, titre en tête de chacun.

        Rend [(texte_à_encoder, debut, fin)] où [debut, fin[ est la plage de CARACTÈRES du morceau dans
        `corps` (indices Python, base 0). La base ne garde que ces bornes, jamais le texte une seconde fois :
        l'extrait est relu dans le fil lui-même.
        Même texte ⇒ mêmes morceaux, dans le même ordre : c'est ce qui rend le calcul de nuit incrémental.
        """
        tete = (titre or "").strip()
        tete = f"{tete} — " if tete else ""
        spans = [(m.start(), m.end()) for m in re.finditer(r"\S+", corps or "")]
        if not spans:
            return []
        mots = [corps[a:b] for a, b in spans]
        budget = max(FENETRE_TOKENS - (self.nb_tokens(tete) - 2 if tete else 0), 40)
        taille = [len(self._ids(m)) for m in mots]           # tokens par mot, calculés une fois
        morceaux, debut = [], 0
        while debut < len(mots):
            total, fin = 0, debut
            while fin < len(mots) and (total + taille[fin] <= budget or fin == debut):
                total += taille[fin]
                fin += 1
            morceaux.append((tete + " ".join(mots[debut:fin]), spans[debut][0], spans[fin - 1][1]))
            if fin >= len(mots):
                break
            debut = max(fin - min(RECOUVREMENT_MOTS, (fin - debut) // 4), debut + 1)
        return morceaux


def vecteur_texte(v: Iterable[float]) -> str:
    """Forme littérale pgvector : '[0.1,0.2,…]' (8 décimales suffisent pour un vecteur normalisé)."""
    return "[" + ",".join(f"{x:.8f}" for x in v) + "]"
