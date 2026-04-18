# Draft 12 — Conformité Loi 25 du Québec

**Version** : 0.1
**Date** : 2026-04-17
**Statut** : Draft pour revue par conseil juridique québécois spécialisé
**Parent** : `data-model-vlbh.md` v0.2 — question ouverte n°12
**Périmètre** : utilisatrices et patientes résidant au Québec (sous-ensemble du shard CA)

---

## Changelog

| Version | Date | Changements |
|---|---|---|
| 0.1 | 2026-04-17 | Draft initial — cartographie des obligations, comparaison avec RGPD/nLPD, actions à mettre en œuvre |

---

## 1. Contexte juridique

### 1.1 La Loi 25 — vue d'ensemble

La **Loi modernisant des dispositions législatives en matière de protection des renseignements personnels** (couramment appelée Loi 25, anciennement projet de loi 64) a été adoptée par l'Assemblée nationale du Québec le 21 septembre 2021 et est entrée en vigueur **progressivement** :

- **22 septembre 2022** : première vague — désignation d'un responsable de la protection des renseignements personnels, notification des incidents, registre des incidents
- **22 septembre 2023** : deuxième vague — consentement, communication hors Québec, droit à l'oubli, anonymisation, automatisation décisionnelle, évaluation des facteurs relatifs à la vie privée (EFVP)
- **22 septembre 2024** : troisième vague — droit à la portabilité

La loi s'applique à toute organisation qui collecte, détient, utilise ou communique des renseignements personnels de résidents québécois, **indépendamment de la localisation de l'organisation**. vlbh-energy, opérant depuis la Suisse, est donc concernée dès qu'elle a une utilisatrice résidant au Québec.

### 1.2 Autorité de contrôle

**Commission d'accès à l'information du Québec (CAI)** — pouvoir d'enquête, d'ordonnance, et de sanction administrative pécuniaire jusqu'à 10 millions CAD ou 2% du chiffre d'affaires mondial, le plus élevé des deux.

---

## 2. Obligations applicables à vlbh-energy

### 2.1 Responsable de la protection des renseignements personnels (art. 3.1)

**Obligation** : désigner une personne responsable, dont les coordonnées sont publiées sur le site web.

**Application VLBH** :
- Désignation obligatoire dès qu'une utilisatrice québécoise entre en base
- Peut être Patrick Bays lui-même, ou un tiers délégué
- Publication sur vlbh.energy/vie-privee avec email dédié (ex : rpvp@vlbh.energy)
- Fonction : traiter les demandes d'accès, rectification, effacement, portabilité ; notifier les incidents ; superviser les EFVP

### 2.2 Évaluation des facteurs relatifs à la vie privée — EFVP (art. 3.3)

**Obligation** : réaliser une EFVP pour :
- Tout projet d'acquisition, développement ou refonte d'un système d'information impliquant des renseignements personnels
- Toute communication hors Québec de renseignements personnels

**Application VLBH** :
- **EFVP obligatoire** pour l'hébergement Supabase Toronto / OVH Canada si transit par d'autres juridictions
- **EFVP obligatoire** pour tout flux vers le `svlbh_identifier_registry` suisse (directory neutre)
- **EFVP obligatoire** pour le bridge WhatsApp (Meta hors Québec)
- Documenter : finalités, nécessité, proportionnalité, risques, mesures d'atténuation

### 2.3 Consentement (art. 14 et suivants)

**Obligation** : consentement « manifeste, libre, éclairé et donné à des fins spécifiques ». Le consentement doit être demandé **séparément** pour chaque finalité distincte. Valable pour la durée nécessaire, révocable à tout moment.

**Application VLBH** :
- Consentement granulaire pour : communication WhatsApp, stockage de l'identité, participation à la formation, test TestFlight, décodage transgénérationnel, etc.
- Pas de consentement « forfaitaire » pour plusieurs finalités en une case cochée
- Mention explicite du droit de retrait et des modalités
- Interface de gestion des consentements accessible à l'utilisatrice (espace personnel)

### 2.4 Communication hors Québec (art. 17)

**Obligation** : évaluation préalable du caractère adéquat de la protection dans la juridiction réceptrice. Si adéquate, la communication est permise. Sinon, encadrement contractuel (équivalent SCC).

**Application VLBH** :
- Transfert vers la Suisse (directory neutre) : la Suisse bénéficie d'une décision d'adéquation européenne et est généralement considérée comme offrant une protection équivalente. **À confirmer** formellement pour la CAI.
- Transfert accessoire vers l'UE (si jamais) : similaire.
- Transfert vers Meta (WhatsApp) : plus complexe — requiert un DPA avec mesures contractuelles renforcées.
- Chaque flux transfrontalier doit faire l'objet d'une EFVP (§2.2).

### 2.5 Automatisation décisionnelle (art. 12.1)

**Obligation** : informer la personne concernée lorsqu'une décision est fondée exclusivement sur un traitement automatisé, lui permettre de présenter ses observations, et de demander la révision par un humain.

**Application VLBH** :
- Si un algorithme trie automatiquement les nouvelles visiteuses (Claude en orientation), informer qu'une IA est utilisée
- Si un score automatisé détermine l'éligibilité à la formation, prévoir un mécanisme de révision humaine
- Pas de décision purement automatisée sur des données sensibles (toujours validation humaine)

### 2.6 Droit à la portabilité (art. 27, en vigueur 22 sept. 2024)

**Obligation** : fournir à la personne qui le demande ses renseignements personnels dans un format technologique structuré et couramment utilisé.

**Application VLBH** :
- Export JSON ou CSV des données de la personne via l'espace utilisatrice
- Inclure : student_profile, billing_student, vibrational_signatures (anonymisé si demandé), consentements
- Délai de fourniture : 30 jours

### 2.7 Droit à l'oubli / désindexation (art. 28.1)

**Obligation** : cesser la diffusion et procéder à la désindexation/ré-anonymisation lorsque la diffusion cause un préjudice grave.

**Application VLBH** :
- Processus d'effacement prévu dans le Draft 07 (politique de conservation Z2) applicable ici
- Spécificité QC : le critère « préjudice grave » ouvre des demandes plus larges que l'effacement classique RGPD

### 2.8 Anonymisation qualifiée (art. 23)

**Obligation** : l'anonymisation n'est reconnue que lorsqu'elle est « faite selon les meilleures pratiques généralement reconnues » et de manière « irréversible ». Seuil **plus strict** que le RGPD.

**Application VLBH** :
- Le standard d'anonymisation appliqué est celui du Québec (le plus strict) de manière uniforme (cf. Draft 07 §4.3)
- Pas de mapping conservé post-anonymisation
- Conservation uniquement de statistiques agrégées

### 2.9 Notification des incidents (art. 3.5)

**Obligation** : notifier la CAI et les personnes concernées « sans délai » en cas d'incident de confidentialité présentant un risque de préjudice sérieux. Tenir un registre des incidents (même ceux non notifiables).

**Application VLBH** :
- Intégré au protocole du Draft 04 (co-responsabilité)
- Registre d'incidents conforme art. 3.8 — déjà prévu §6 du data-model-vlbh
- Délai interne : 24h pour notification interne, analyse risque sous 48h, notification CAI sous 72h si risque sérieux

---

## 3. Comparaison avec RGPD et nLPD

| Obligation | RGPD | nLPD CH | Loi 25 QC |
|---|---|---|---|
| DPO / Responsable | Si conditions art. 37 | Recommandé | **Obligatoire systématique** |
| PIA / EFVP | Si risque élevé art. 35 | Non obligatoire | **Obligatoire systématique** pour SI et transfert hors QC |
| Consentement | Libre, spécifique, éclairé, univoque | Similaire | **Manifeste**, granulaire par finalité |
| Communication transfrontalière | Décision d'adéquation, SCC | Liste PFPDT + garanties | **EFVP préalable** + évaluation caractère adéquat |
| Droit à l'oubli | Art. 17, conditions listées | Art. 32 | Critère « préjudice grave » — plus ouvert |
| Portabilité | Art. 20 | Art. 28 | Art. 27, entré en vigueur sept. 2024 |
| Anonymisation | Décentrale, non définie strictement | Similaire RGPD | **Standard strict** : irréversibilité + meilleures pratiques |
| Sanction max | 20M€ ou 4% CA | 250k CHF | **10M CAD ou 2% CA mondial** |
| Décision automatisée | Art. 22 | Art. 21 | Art. 12.1 — droit à la révision humaine explicite |
| Délai notification incident | 72h | Sans délai excessif | Sans délai |

**Conclusion opérationnelle** : la Loi 25 est, sur plusieurs aspects, **plus stricte** que le RGPD (EFVP systématique, DPO systématique, anonymisation qualifiée, sanctions proportionnellement plus sévères). Appliquer le standard Loi 25 de manière uniforme dans le shard CA + une partie (anonymisation) à tous les shards est une stratégie robuste.

---

## 4. Actions à mettre en œuvre

### 4.1 Court terme (avant première utilisatrice QC)

- [ ] Désigner formellement le Responsable de la protection des renseignements personnels
- [ ] Publier l'identité et les coordonnées du Responsable sur vlbh.energy/vie-privee
- [ ] Rédiger le document d'information Loi 25 (version QC de la politique de confidentialité)
- [ ] Créer les formulaires de consentement granulaire pour QC
- [ ] Établir le registre d'incidents conforme art. 3.8
- [ ] Consulter un conseil juridique québécois pour validation

### 4.2 Moyen terme (phase 5 de la migration — shard CA)

- [ ] Réaliser l'EFVP globale pour l'infrastructure vlbh vis-à-vis des données QC
- [ ] Contractualiser avec Supabase Toronto (ou OVH Canada) — DPA conforme Loi 25
- [ ] Documenter l'évaluation d'adéquation pour les transferts vers la Suisse (directory)
- [ ] Contractualiser avec Meta pour le bridge WhatsApp — mesures renforcées
- [ ] Implémenter l'interface de gestion des consentements dans l'espace utilisatrice

### 4.3 Long terme (22 septembre 2024+)

- [ ] Implémenter la fonctionnalité d'export portabilité dans l'espace utilisatrice
- [ ] Mettre en place le mécanisme de révision humaine pour toute décision automatisée
- [ ] Audit annuel de conformité Loi 25 avec un conseil québécois

---

## 5. Détection et routage des utilisatrices québécoises

### 5.1 Identification

L'affectation au shard CA se fait via la résidence déclarée. Pour distinguer **Québec** de reste du Canada :
- Dans `svlbh_residency_directory.country_code`, utiliser un sous-code `CA-QC` vs `CA-ON`, `CA-BC`, etc.
- Déclenchement automatique du régime renforcé Loi 25 si `country_code = 'CA-QC'`

### 5.2 Déclenchement automatique

Dès qu'une utilisatrice déclare une résidence QC :
- Affichage du document d'information Loi 25 (version QC)
- Demande de consentement granulaire Loi 25 (pas le consentement générique)
- Flag `loi25_applicable = true` dans toutes les tables la concernant
- Activation des contrôles spécifiques (EFVP déjà faite, log d'accès renforcé, etc.)

### 5.3 Migration d'un contact existant

Si une utilisatrice actuelle déclare ultérieurement une résidence QC :
- Bascule du shard d'hébergement (EU → CA)
- Application rétroactive des mesures Loi 25
- Nouveau consentement granulaire demandé
- EFVP associée déjà couverte par l'EFVP globale §4.2

---

## 6. Décisions à valider

- **Choix du Responsable** : Patrick personnellement ou délégation à un tiers (avocat québécois, service externalisé) ?
- **Distinction CA-QC vs autre Canada** : granularité nécessaire dès la v1.0 ou acceptable de traiter tout le Canada avec le standard Loi 25 par défaut (safer) ?
- **Hébergeur Toronto vs OVH Canada** : critère de sélection (conformité Loi 25 explicite dans le DPA ?) à clarifier
- **Seuil de premier utilisateur QC** : à quel moment déclenche-t-on la mise en place complète — avant la première, ou au premier signal ?

---

## 7. Annexes prévues

- **Annexe A** — Document d'information Loi 25 (à rédiger en collaboration avec conseil québécois)
- **Annexe B** — Formulaires de consentement granulaire version QC
- **Annexe C** — Modèle d'EFVP (template pour usage répété)
- **Annexe D** — Registre d'incidents type art. 3.8
