# Draft 04 — Contrat de co-responsabilité art. 26 RGPD
### Entre vlbh-energy et chaque Praticienne Certifiée

**Version** : 0.1
**Date** : 2026-04-17
**Statut** : Draft pour revue par conseil juridique spécialisé nLPD/RGPD
**Parent** : `data-model-vlbh.md` v0.2 — question ouverte n°4
**Destinataire prévu** : Praticiennes certifiées MyShamanFamily / SVLBH-Palette de Lumière

---

## Changelog

| Version | Date | Changements |
|---|---|---|
| 0.1 | 2026-04-17 | Draft initial — structure type art. 26 RGPD, adapté au contexte VLBH à trois shards régionaux |

---

## Avertissement

Ce document est un **modèle de travail**. Il n'a pas de valeur contractuelle en l'état. Il doit être revu et adapté par un avocat spécialisé en protection des données (nLPD Suisse, RGPD UE, Loi 25 Québec) avant toute signature. Les clauses marquées `[À VALIDER]` appellent une décision spécifique.

---

## Préambule

Attendu que :

- **vlbh-energy** (ci-après « vlbh ») opère une infrastructure technique et méthodologique permettant à des praticiennes certifiées d'accompagner leurs patientes selon la méthode VLBH (Vibrational Light Body Healing), notamment via l'application SVLBH-Palette de Lumière.
- **La Praticienne** (ci-après « la Praticienne ») a été certifiée par vlbh à l'issue d'un parcours de formation de 15 mois et exerce son art en accompagnement direct avec ses patientes.
- La relation thérapeutique s'établit entre la Praticienne et chacune de ses patientes, tandis que l'infrastructure technique de traitement des données est fournie et maintenue par vlbh.
- Les données traitées incluent des **données de santé au sens de l'article 9 RGPD et de l'article 5 let. c nLPD** (ci-après « données sensibles »).
- Les Parties reconnaissent qu'elles déterminent conjointement les finalités et les moyens du traitement et sont par conséquent **responsables conjointes du traitement** au sens de l'article 26 du RGPD.

Les Parties conviennent ce qui suit.

---

## Article 1 — Objet

Le présent contrat définit la répartition des responsabilités des Parties en matière de protection des données personnelles traitées dans le cadre de l'activité de la Praticienne sur l'infrastructure vlbh, conformément à l'article 26 RGPD et aux dispositions équivalentes de la nLPD.

Il couvre l'ensemble des traitements effectués via l'application SVLBH-Palette de Lumière, le réseau de praticiennes MyShamanFamily, et tout canal de communication lié (WhatsApp, email, visioconférence).

---

## Article 2 — Finalités du traitement conjoint

Les Parties déterminent conjointement les finalités suivantes :

- Accompagnement thérapeutique individualisé des patientes selon la méthode VLBH
- Tenue du dossier énergétique et vibratoire des patientes
- Suivi longitudinal des séances
- Facturation et gestion commerciale de la relation praticienne↔patiente
- Supervision et contrôle qualité du réseau de praticiennes par vlbh
- Amélioration méthodologique à partir de données anonymisées [À VALIDER — finalité secondaire nécessite consentement explicite séparé]

---

## Article 3 — Données traitées

Catégories de données traitées dans le cadre du présent contrat :

- **Identifiants** : SVLBH_Identifier de la patiente, nom, coordonnées
- **Données contractuelles** : consentement signé, date, version
- **Données vibratoires VLBH** : hDOM, Scores de Lumière, Rose des Vents, Sephiroth, signatures énergétiques (vocabulaire VLBH propriétaire, non médical)
- **Données relatives aux lignées ancestrales** : registre des ancêtres (défunts — hors scope RGPD/nLPD selon considérant 27 RGPD)
- **Données de facturation** : Twint, Postfinance, références de paiement
- **Métadonnées de séance** : date, durée, modalité (présentiel/distance)

Les Parties s'engagent à ne traiter **aucun diagnostic médical** établi sur la patiente par la Praticienne, la méthode VLBH étant de nature énergétique et perceptive, non médicale.

---

## Article 4 — Répartition des responsabilités

### 4.1 Responsabilités de vlbh

- Fournir et maintenir l'infrastructure technique (serveurs, base de données, application, chiffrement, sauvegardes)
- Garantir l'hébergement dans la juridiction de résidence déclarée de la patiente (Suisse, UE ou Canada selon le shard applicable)
- Mettre en œuvre les mesures techniques et organisationnelles appropriées (chiffrement AES-256 au repos et en transit, RLS, 2FA obligatoire, audit log immuable, backups point-in-time)
- Réaliser et maintenir à jour la DPIA globale de l'infrastructure
- Assurer la conformité des sous-traitants techniques (Infomaniak, Supabase, etc.) via des DPA signés au sens de l'art. 28 RGPD
- Fournir à la Praticienne des outils permettant l'exercice des droits des personnes concernées (export, rectification, effacement)
- Notifier la Praticienne de toute violation de données affectant l'infrastructure dans un délai de 24h

### 4.2 Responsabilités de la Praticienne

- Recueillir le consentement explicite de chaque patiente conformément à l'art. 9.2.a RGPD avant toute saisie de données sensibles, à l'aide du formulaire fourni par vlbh
- Tenir à jour les dossiers patientes de manière exacte et proportionnée
- N'enregistrer dans le système que les données strictement nécessaires à l'accompagnement
- Ne jamais introduire de codes CIM-11, diagnostics médicaux ou recommandations pharmacologiques
- Former ses propres collaborateurs éventuels aux règles du présent contrat
- Appliquer le protocole de gestion des incidents de données santé fourni par vlbh (détection, purge 48h, registre)
- Notifier vlbh de toute violation de données ou incident suspect dans un délai de 24h
- Répondre aux demandes d'exercice des droits de ses patientes dans les délais légaux (30 jours RGPD, 30 jours nLPD)

### 4.3 Matrice de responsabilité

| Obligation RGPD/nLPD | vlbh | Praticienne |
|---|---|---|
| Registre des activités de traitement (art. 30) | Tenue du registre global | Contribution pour son périmètre |
| DPIA (art. 35) | Responsable | Consultée |
| Sécurité technique (art. 32) | Responsable | Application des règles |
| Notification de violation à l'autorité (art. 33) | Responsable | Informe vlbh |
| Notification aux personnes concernées (art. 34) | Appui technique | Responsable du contact direct |
| Consentement des patientes (art. 7) | Fournit le formulaire | Recueille et conserve |
| Droits d'accès/rectification/effacement (art. 15-17) | Fournit les outils | Point de contact opérationnel |
| Portabilité (art. 20) | Fournit l'export | Transmet à la patiente |
| Transfert transfrontalier (art. 44+) | Responsable (SCC, adéquation) | Informée |
| Sous-traitants (art. 28) | Responsable (signe les DPA) | Sans délégation |

---

## Article 5 — Point de contact unique

Conformément à l'art. 26.1 RGPD, les Parties conviennent que **vlbh-energy est désignée comme point de contact unique** pour les personnes concernées souhaitant exercer leurs droits.

La Praticienne relaie sans délai à vlbh toute demande reçue directement d'une patiente.

**[À VALIDER]** : La patiente conserve néanmoins le droit d'exercer ses droits auprès de chacune des Parties (art. 26.3 RGPD) et ce droit ne peut être limité par le présent contrat.

---

## Article 6 — Information des patientes

Les Parties conviennent d'un texte d'information unique, remis à chaque patiente avant le début de l'accompagnement, précisant :

- L'identité et les coordonnées des deux responsables conjoints
- La répartition des responsabilités (essentiel du présent contrat)
- Les finalités et la base légale de chaque traitement
- Les destinataires éventuels des données
- La durée de conservation
- Les droits de la patiente et les modalités d'exercice
- Le droit d'introduire une réclamation auprès de l'autorité de contrôle compétente (PFPDT en Suisse, CNIL/autorité du pays de résidence en UE, CAI au Québec)

Le texte d'information est annexé au présent contrat (Annexe A — à rédiger).

---

## Article 7 — Sous-traitance technique

La Praticienne reconnaît que vlbh recourt aux sous-traitants suivants pour l'hébergement et les services techniques :

- **Shard CH** : Infomaniak SA (Genève) ou Exoscale AG (Lausanne) — à confirmer v0.4
- **Shard EU** : Supabase Inc. (via DPA), infrastructure AWS Francfort
- **Shard CA** : Supabase Inc. (Toronto) ou OVH Canada — à confirmer v0.4
- **Orchestration** : Make.com s.r.o. (République tchèque) — buffer d'orchestration uniquement
- **Canal de communication** : Meta WhatsApp Business (avec DPA spécifique)

vlbh s'engage à n'ajouter aucun nouveau sous-traitant sans information préalable de la Praticienne et droit d'opposition dans un délai de 15 jours.

---

## Article 8 — Hébergement et résidence des données

Conformément au principe de souveraineté de la patiente retenu dans l'architecture VLBH, **les données des patientes sont hébergées dans la juridiction de résidence déclarée de la patiente** :

- Patientes résidant en Suisse → Shard CH
- Patientes résidant en UE → Shard EU
- Patientes résidant au Canada → Shard CA (traitement spécifique pour le Québec conformément à la Loi 25)

Si la Praticienne et la patiente résident dans des juridictions différentes, vlbh assure l'encadrement du flux transfrontalier (SCC, décision d'adéquation, ou autre mécanisme de l'art. 44+ RGPD).

---

## Article 9 — Incidents et violations de données

### 9.1 Définition

Toute violation, fuite, perte, altération ou accès non autorisé à des données personnelles traitées dans le cadre du présent contrat.

### 9.2 Notification interne

La partie qui détecte l'incident notifie l'autre dans les **24 heures**.

### 9.3 Notification à l'autorité de contrôle

vlbh est responsable de la notification à l'autorité de contrôle compétente dans les 72 heures (art. 33 RGPD), sur la base des éléments fournis par la Praticienne.

### 9.4 Notification aux personnes concernées

En cas de risque élevé pour les personnes concernées, la Praticienne notifie directement ses patientes, avec l'appui opérationnel de vlbh (art. 34 RGPD).

### 9.5 Cas particulier — réception accidentelle de documents santé

Lorsqu'une patiente transmet spontanément un document médical (analyse, IRM, ordonnance) hors du cadre prévu, la Praticienne applique le protocole en cinq étages défini dans `data-model-vlbh.md` §6 : prévention contractuelle, réponse automatique standardisée, suppression sous 48h, registre d'incident, politique de backup.

---

## Article 10 — Durée, suspension, résiliation

### 10.1 Durée

Le présent contrat entre en vigueur à la date de certification de la Praticienne et court tant que la Praticienne exerce sous la méthode VLBH.

### 10.2 Suspension

vlbh peut suspendre l'accès de la Praticienne à l'infrastructure en cas de violation caractérisée du présent contrat, après mise en demeure restée sans effet pendant 15 jours.

### 10.3 Résiliation

Chaque Partie peut résilier le contrat avec un préavis de 3 mois. En cas de résiliation :

- La Praticienne dispose d'un délai de 60 jours pour informer ses patientes et leur proposer les options de transfert vers une autre praticienne VLBH ou d'export/effacement de leurs données.
- Au terme de ce délai, les dossiers patientes restants sont anonymisés ou supprimés selon la politique de conservation.
- La Praticienne cesse immédiatement d'utiliser la marque, les outils et la méthode VLBH au-delà du préavis.

---

## Article 11 — Droit applicable et juridiction

Le présent contrat est régi par le **droit suisse**. Tout litige relève de la compétence exclusive des tribunaux ordinaires du canton de [siège vlbh].

**[À VALIDER]** : pour les Praticiennes canadiennes, clause d'arbitrage international ou prorogation au droit local ?

---

## Annexes prévues

- **Annexe A** — Texte d'information aux patientes (modèle unique multi-juridiction)
- **Annexe B** — Formulaire de consentement patiente (avec variantes QC/UE/CH)
- **Annexe C** — Protocole de gestion des incidents de données santé (extrait de `data-model-vlbh.md` §6)
- **Annexe D** — Liste à jour des sous-traitants techniques
- **Annexe E** — Matrice des droits des personnes et procédure opérationnelle

---

## Signatures

Pour vlbh-energy : _______________________

Pour la Praticienne : _______________________

Date : _______________________ Lieu : _______________________
