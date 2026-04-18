# Prompt Claude Code — Spec Middleware de détection santé WhatsApp Bridge

**Version** : 0.1
**Date** : 2026-04-17
**Usage** : à copier-coller dans Claude Code pour obtenir une spec technique détaillée
**Parent** : `data-model-vlbh.md` v0.2 — question ouverte n°6

---

## Comment utiliser ce prompt

Ouvre Claude Code à la racine du repo `vlbh-energy-mcp` (ou celui du bridge WhatsApp correspondant) et colle le prompt ci-dessous. Claude Code va lire les fichiers de référence, explorer la codebase, et produire une spec sous forme de fichier `.md` dans le dossier `spec/` ou équivalent.

---

## Le prompt à coller

```
Je travaille sur l'écosystème vlbh-energy : infrastructure technique et méthodologique
pour un réseau de praticiennes en Vibrational Light Body Healing. Nous avons défini une
architecture à trois zones (Visiteuses, Étudiantes en formation 15 mois, Patientes via
praticiennes certifiées) avec data residency géo-fragmentée CH/EU/CA.

Je veux que tu rédiges une SPEC TECHNIQUE DÉTAILLÉE pour un middleware de détection
et de purge automatique des données de santé transitant par le bridge WhatsApp
(vlbh-energy-mcp). Tu n'écris PAS le code. Tu écris une spec que l'équipe pourra
implémenter ensuite.

---

CONTEXTE MÉTIER

Nos utilisatrices (visiteuses Z1, étudiantes Z2, patientes Z3) nous contactent
massivement via WhatsApp. Notre cadre juridique est construit pour éviter l'usage de
WhatsApp comme canal de transmission de données de santé art. 9 RGPD / art. 5c nLPD :

- Z1 (visiteuses) : WhatsApp ID + prénom + LID, pseudonymisé, pas de santé
- Z2 (étudiantes) : cadre pédagogique explicite, décodage transgénérationnel sur
  ancêtres DÉFUNTS (hors RGPD), PAS de diagnostic sur l'étudiante vivante, CIM-11
  utilisée uniquement pour qualifier des événements d'ancêtres décédés
- Z3 (patientes) : art. 9 sensible, hébergement Suisse/EU/CA selon résidence
  patiente, accès via 2FA

Problème observé : il arrive qu'une étudiante ou patiente transmette spontanément
des documents santé (analyses sanguines, IRM, ordonnances, comptes-rendus médicaux)
via WhatsApp. Cette réception constitue un traitement de données art. 9 qui dépasse
le cadre prévu et crée un risque de conformité.

---

OBJECTIF DU MIDDLEWARE

Intercepter chaque message entrant sur le bridge WhatsApp, détecter la probabilité
qu'il contienne des données de santé, et déclencher un protocole en cinq étages :

1. Prévention contractuelle (déjà couvert par les contrats)
2. RÉPONSE AUTOMATIQUE STANDARDISÉE — le middleware en est responsable
3. SUPPRESSION EFFECTIVE SOUS 48H — le middleware en est responsable
4. REGISTRE D'INCIDENTS non-identifiant — le middleware l'alimente
5. Politique de backup (hors scope middleware)

---

DOCUMENTS DE RÉFÉRENCE À LIRE AVANT DE COMMENCER

Dans le repo courant :
- data-model-vlbh.md (architecture globale, §6 = protocole cinq étages)
- data-model-vlbh.mermaid (diagramme)
- drafts/04-contrat-coresponsabilite-art26.md (art. 9 et obligations)
- drafts/09-retroactivite-donnees-existantes.md (gestion legacy)

Cherche également dans le repo :
- Le code actuel du bridge WhatsApp MCP (fichiers *.ts ou *.py selon stack)
- Les scénarios Make.com qui interagissent avec le bridge
- Toute config d'orchestration existante

---

CONTRAINTES TECHNIQUES

- Le bridge actuel est le MCP WhatsApp vlbh-energy-mcp (compte patrickbays)
- Il s'intègre avec Make.com (scénarios team 630342)
- Latence cible : détection < 500ms par message (sinon UX dégradée)
- Faux positifs acceptables (on préfère ratisser large) ; faux négatifs à minimiser
- Doit fonctionner sur texte, pièces jointes (PDF, JPG, PNG), et audio (transcription optionnelle v2)
- Langues à détecter : français, anglais, allemand (utilisatrices multilingues)
- Vocabulaire VLBH légitime à NE PAS flagger : hDOM, Score de Lumière, Rose des Vents,
  Sephiroth, signature vibratoire, décodage transgénérationnel, fréquences vibratoires,
  CIM-11 appliquée à ancêtres (contexte : "mon arrière-grand-mère avait 6A70")

---

CE QUE LA SPEC DOIT COUVRIR

1. ARCHITECTURE GLOBALE
   - Point d'interception dans le pipeline WhatsApp (webhook, middleware MCP, etc.)
   - Synchrone vs asynchrone
   - Interface avec Make.com
   - Stockage du registre d'incidents (où, quel schéma)

2. MOTEUR DE DÉTECTION
   - Stratégie multi-couches : mots-clés + expressions régulières + classifieur ML léger ?
   - Liste initiale de patterns : noms de laboratoires (Unilabs, Dianalabs, Synlab, CERBA,
     Viollier, BioAnalytica, Risch), mots-clés (analyse, résultat, bilan, prise de sang,
     hémogramme, ferritine, cholestérol, CRP, TSH, vitamine D, diagnostic, ordonnance,
     prescription, IRM, scanner, échographie, biopsie), motifs CIM-11 (regex), patterns
     de dates dans les en-têtes de labo
   - Détection sur nom de fichier ET contenu (OCR sur image/PDF envisageable)
   - Règles de pondération et seuil de déclenchement
   - Gestion du vocabulaire VLBH (whitelist contextuelle pour éviter faux positifs)

3. RÉPONSE AUTOMATIQUE
   - Template multi-langue de réponse
   - Adaptation selon la zone de l'expéditeur (Z1/Z2/Z3 via svlbh_id lookup)
   - Tonalité : bienveillante, pas alarmante, rappel du cadre
   - Action attendue de la part de l'expéditrice : suppression de son côté

4. MÉCANISME DE PURGE 48H
   - Suppression côté bridge : API WhatsApp delete_message
   - Log horodaté de l'action
   - Gestion des échecs de suppression (retry, alerting)
   - Comment s'assurer que les backups éventuels du bridge sont aussi purgés

5. REGISTRE D'INCIDENTS
   - Schéma : timestamp, svlbh_id (optionnel), zone, type de document détecté,
     score de confiance, action prise, délai de purge, langue détectée
   - NON-identifiant : pas de nom, pas de contenu du message, pas d'extrait
   - Stockage : table Supabase (shard EU par défaut) ou table Make dédiée
   - Retention : indéfini (preuve de conformité)

6. MÉTRIQUES ET MONITORING
   - Nombre d'incidents par jour/semaine/mois
   - Taux de faux positifs (détection ajustée par feedback)
   - Latence moyenne de détection
   - Délai moyen de purge effective
   - Alerting si pic anormal ou échec de suppression

7. CONFIGURATION ET MAINTENANCE
   - Comment mettre à jour la liste de mots-clés sans redéploiement (config centralisée ?)
   - Processus de revue mensuelle des faux positifs/négatifs
   - Gouvernance : qui valide les changements de patterns

8. CAS D'USAGE ET EDGE CASES
   - Étudiante envoie la CIM-11 d'une ancêtre ("mon grand-père avait 6A70") → autoriser
   - Praticienne Z3 supervise une étudiante et reçoit incidemment un doc santé → distinguer
   - Vocabulaire médical utilisé en sens figuré (ex : "je me sens en dépression" sans
     transmission de doc) → pas de déclenchement
   - Document santé envoyé d'une Zone 3 légitime (une patiente vers sa praticienne
     dans le cadre prévu de SVLBH-Palette de Lumière) → NE PAS intercepter si flux Z3
   - Pièce jointe chiffrée ou compressée

9. TESTS ET VALIDATION
   - Jeu de tests : messages positifs (vraiment santé) et négatifs (vocabulaire VLBH,
     conversation normale)
   - Validation manuelle mensuelle par PB pendant les 3 premiers mois
   - Seuil d'acceptation avant mise en production

10. PLAN DE DÉPLOIEMENT
    - Phase shadow (détecte mais n'agit pas, juste log) — 2 semaines
    - Phase active (détecte + répond + purge) sur un sous-ensemble de contacts —
      2 semaines
    - Déploiement complet
    - Plan de rollback si effet indésirable

---

LIVRABLE ATTENDU

Un fichier `spec/whatsapp-health-middleware.md` dans le repo, structuré selon les
10 sections ci-dessus, avec :

- Des schémas ASCII ou mermaid pour l'architecture et les flux
- Du pseudocode pour les points clés (détection, purge, réponse)
- Des tableaux de config pour les mots-clés et les seuils
- Une estimation d'effort d'implémentation (jours de dev)
- Une liste de décisions à prendre avant implémentation

N'écris PAS le code de production. Écris la spec. Si tu rencontres des zones floues
techniquement, liste-les clairement à la fin dans une section "Questions ouvertes
pour Patrick".

Explore d'abord le repo pour comprendre l'architecture existante du bridge avant de
proposer quoi que ce soit. Lis les documents de référence listés plus haut. Pose des
questions si le contexte métier manque de clarté.
```

---

## Notes d'utilisation

1. **Contexte repo** : ce prompt suppose que Claude Code est ouvert dans le repo `vlbh-energy-mcp` ou l'équivalent où vivent les sources du bridge. Adapter si le repo est ailleurs.

2. **Fichiers de référence** : les quatre fichiers listés dans « DOCUMENTS DE RÉFÉRENCE À LIRE » doivent exister dans le repo ou à un chemin accessible. Si Claude Code ne les trouve pas, fournis-les en pièces jointes à la conversation Claude Code.

3. **Itération** : si la première spec est trop légère, relancer Claude Code avec « approfondis la section X » plutôt que de tout redemander.

4. **Revue** : la spec produite doit être relue par Patrick avant implémentation. Les « Questions ouvertes » sont le filtre principal pour vérifier que Claude Code n'a pas fait d'hypothèses cachées.

5. **Prompt compagnon** : une fois la spec validée, un second prompt Claude Code pourra implémenter le middleware en suivant la spec. Ce prompt sera une continuation (« Implémente maintenant la spec dans spec/whatsapp-health-middleware.md »).
