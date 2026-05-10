# Blueprint Compliance-by-Design SVLBH

**Version** : 0.4
**Date** : 2026-05-10
**Auteur** : Patrick Bays + Claude
**Statut** : Document fondateur — référence pour toute décision data model et architecture
**Documents liés** : `data-model-vlbh.md` (v0.8), ADR SVLBH-01, ADR SVLBH-03, Charte v0.8, registre RGPD v1.1, mémoire `reference_tier_mapping.md` (doctrine 4D)

---

## 0. Mapping doctrinal v0.3 (tier) → v0.4 (stage)

La version 0.4 introduit **6 stages explicites** (ST0..ST5) à la place des 5 tiers (T0..T4) de la v0.3. Le découplage `parcours_stage` (toll-gate stable) ↔ `tier_capacity` (capacité fluide) introduit en doctrine 4D le 2026-05-10 sépare désormais ces deux dimensions :

| v0.3 (legacy) | v0.4 (canonique) | Glissement sémantique |
|---|---|---|
| T0 Visiteuse | **ST0 Lead** | Lead anonyme avant signup (svlbh.com landing). Visiteuse logged-in est ST1. |
| T1 Trial 14j | **ST1 Visiteuse qualifiée** | Trial app + accès priv.svlbh.com `/lire` (lecture pédagogique). |
| T2 ColorPicker payant | **ST2 Apprentie** | Paiement premier produit chromatique, début engagement actif. |
| T3 Formation | **ST3 Certifiée Priv** | Formation MyShamanFamily + voie privée Priv-1. |
| T4 Pro | **ST4 Praticienne Pro** | Certifiée MyShamanFamily PRO + voie pro pwa.app.svlbh.com. |
| *(nouveau)* | **ST5 Superviseure / Enseignante** | Certification MyShaman + supervision Cercle de Lumière SR via cockpit.svlbh.com. |

**Source de vérité DB** : `consultante_record.parcours_stage` (enum T0..T5, T99) ; UI affichée ST0..ST5 via `stageLabel()` helper. La colonne `parcours_tier` legacy reste pendant la transition iOS, sera dropée après nettoyage (cf. `handoff_ios_parcours_tier_drop_final.md`).

**Dimension orthogonale** : `tier_capacity` (NULL initial sur 49/49 consultantes) capture la capacité fluide à recevoir T0↔T6 — distincte du stage administratif. Sera enrichie au cas par cas par les praticiennes.

---

## 1. Philosophie

Le modèle SVLBH est un **parcours de progression humaine**, pas un catalogue d'applications. Chaque étape du parcours correspond à un niveau de maturité relationnelle entre la personne et l'écosystème VLBH. La compliance n'est pas une couche ajoutée a posteriori — elle est structurellement liée au tier de progression.

Le principe directeur : **plus la personne avance dans le parcours, plus la relation de confiance est profonde, plus les données échangées sont riches, et plus les protections sont fortes.**

---

## 2. Parcours utilisateur — les 6 stages (ST0 → ST5)

### Stage 0 (ST0) — Lead WhatsApp (Zone 1)

| Dimension | Valeur |
|---|---|
| Qui | Personne curieuse, arrive via WhatsApp (95%) ou landing page vlbh.energy |
| Données | WhatsApp ID, prénom, LID |
| Billing | Aucun |
| Durée | Illimitée (tant que le contact est actif) |
| App | Aucune app — interaction WhatsApp uniquement |
| Zone data | Z1 monorégion UE |
| Base légale | Intérêt légitime + consentement implicite (la visiteuse initie le contact) |
| RGPD | Données personnelles pseudonymisées, pas sensibles. Pas d'Art. 9. |

### Stage 1 (ST1) — Visiteuse qualifiée / Trial 14 jours (Zone 1bis → Zone 2)

| Dimension | Valeur |
|---|---|
| Qui | Visiteuse qui demande à tester l'app SVLBH Colorpicker |
| Données supplémentaires | Email, Apple ID ou Google ID |
| Billing | **Zéro** — essai gratuit |
| Durée | 14 jours calendaires |
| Onboarding | 5 jours guidés par email pour explorer les fonctionnalités |
| App | 1 seule app de test (SVLBH Colorpicker trial) |
| Zone data | Z1bis → Z2 (relation pré-contractuelle art. 6.1.b RGPD) |
| Base légale | Consentement explicite horodaté (popup in-app) |
| RGPD | Donnée personnelle standard. Consentement TestFlight accepté comme base provisoire pour le groupe beta (RSK-2, 15/04). Mécanisme in-app à construire avant scaling. |

### Stage 2 (ST2) — Apprentie ColorPicker payant (Zone 2)

| Dimension | Valeur |
|---|---|
| Qui | Consultante ou son proche aidant qui a décidé de continuer après le trial |
| Données supplémentaires | Identité de facturation (Postfinance), préférences ColorPicker |
| Billing | **CHF 29 / trimestre** — la consultante choisit 1 des 5 apps ColorPicker (ex : Glycémie, Sommeil, etc.) |
| Durée | Renouvellement trimestriel |
| App | 1 app ColorPicker spécifique parmi 5 |
| Zone data | Z2 |
| Base légale | Contrat d'abonnement |
| RGPD | Données personnelles standard. Données radiesthésiques hors Art. 9 (RSK-6, 15/04). |
| Particularité | Les données ColorPicker sont des auto-évaluations personnelles, pas des diagnostics. Vocabulaire VLBH propriétaire. |

### Stage 3 (ST3) — Formation Shamane / Certifiée Priv (Zone 2)

| Dimension | Valeur |
|---|---|
| Qui | Consultante qui s'engage dans la formation certifiante |
| Données supplémentaires | Identité civile complète, signatures vibratoires VLBH, progression pédagogique |
| Durée et pricing | **Deux parcours :** |

**MyShaMan** (9 mois) :
- 99 CHF/mois × 9 mois
- ou 1 099 CHF payable en 3 fois
- ou 129 CHF/mois

**MyShamanFamily** (12 mois, inclut MyShaMan) :
- 1 999 CHF one-shot
- ou 179 CHF/mois × 12 mois

| App | 1 app SVLBH Formation (version dédiée aux étudiantes) |
| Zone data | Z2 géo-fragmentée (CH/EU/CA selon résidence déclarée) |
| Base légale | **Contrat de formation pédagogique** — pas contrat de soin |
| RGPD | Données personnelles standard. Données radiesthésiques hors Art. 9 (RSK-6). Aucune donnée médicale collectée — outils pédagogiques VLBH uniquement. |
| 2FA | Recommandé |
| DPIA | Non requise |

### Stage 4 (ST4) — Shamane certifiée Pro (Zone 3)

| Dimension | Valeur |
|---|---|
| Qui | Shamane MyShamanFamily certifiée qui exerce en professionnel et reçoit des **consultantes** (pas de "patientes" au sens RGPD) |
| Sujets travaillés | Consultantes (vivantes, sujets RGPD) qui viennent décoder les **mémoires électromagnétiques accumulées de défunts, de familles d'Âmes et de Monades de la consultante, qui se densifient dans la matière**. Aucun de ces sujets (défunts, familles d'Âmes, Monades, incarnations passées) n'est une personne physique vivante au sens RGPD art. 4.1 → hors RGPD. |
| Données supplémentaires | Identité praticienne B2B, identité civile consultante, consentement horodaté, historique des séances, signatures vibratoires décodées (portent sur les mémoires des défunts) |
| Billing | Abonnement mensuel + infrastructure minimale annuelle. **Première estimation : CHF 259 / trimestre** (infra + protection). Prix définitifs non encore fixés. |
| Apps | **4 apps ST4 Pro en satellites** (repo racine `monadekarmique/svlbh-pro` = SDK + specs + CI commune ; chaque app = son propre repo satellite, owner Patrick Bays) : **SVLBH Pro 1**, **AUDIT Pro 1**, **SVLBH Chromothérapie 1**, **SVLBH Protection 1** |
| Zone data | Z3 géo-fragmentée (CH/EU/CA selon résidence de la **consultante**, pas de la praticienne) |
| Base légale | Art. 6.1.b (contrat d'accompagnement pédagogique B2B + contrat consultante) + art. 6.1.a (consentement explicite consultante) + art. 26 (co-responsabilité) |
| RGPD | Consultante = donnée personnelle standard (pas Art. 9, RSK-6). Défunts + incarnations passées + mémoires accumulées ≠ sujets RGPD (art. 4.1). **Analogie ancestry.com** : service sur défunts sans régime renforcé médical. RLS obligatoire (praticienne ne voit que ses consultantes). |
| 2FA | **Obligatoire** |
| DPIA | **Non requise** (décision Patrick 2026-04-22 : pas d'Art. 9 via RSK-6, pas de large-scale, pas de profiling automatisé ; analogie ancestry.com) |
| Co-responsabilité | Contrat art. 26 RGPD requis avec chaque praticienne (draft 04 disponible) |

### Stage 5 (ST5) — Superviseure / Enseignante (Zone 3)

Nouveau stage introduit en v0.4 (cf. doctrine 4D 2026-05-10).

| Dimension | Valeur |
|---|---|
| Qui | Praticienne MyShaman (certification supérieure à MyShamanFamily) qui supervise les ST4 du Cercle de Lumière et enseigne la méthode |
| Données supplémentaires | Mêmes que ST4 + droits de supervision (lecture cross-praticiennes du Cercle, validation 4 mains, transmission de la méthode) |
| Billing | À définir (formation des praticiennes + supervision continue). Pas encore cadré au 2026-05-10. |
| Apps | Mêmes apps que ST4 + accès cockpit.svlbh.com (audit + suivi cercle + Si Zhu calendar) |
| Zone data | Z3 |
| Base légale | Mêmes bases que ST4 + contrat de supervision avec praticiennes ST4 supervisées |
| RGPD | Mêmes que ST4. Lecture étendue requiert RLS spécifique : `cockpit_access` whitelist OU `cercle_lumiere_sr=true` (cf. layout cockpit) |
| 2FA | **Obligatoire** |
| DPIA | Non requise (mêmes critères que ST4) |
| Membre Cercle SR | Typiquement oui (Cornelia Althaus = ST5 / MyShaman au 2026-05-10) |

---

## 3. Matrice compliance par stage

| Exigence | ST0 Lead | ST1 Visiteuse | ST2 ColorPicker | ST3 Formation | ST4 Pro | ST5 Superviseure |
|---|---|---|---|---|---|---|
| Consentement explicite | Non (implicite) | Oui (horodaté) | Oui (contrat) | Oui (contrat formation) | Oui (consentement consultante) | Oui (idem ST4) + contrat supervision |
| Données Art. 9 | Non | Non | Non | Non | Non (RSK-6) | Non (RSK-6) |
| Données médicales | Non | Non | Non | Non (outils pédagogiques) | Non (vocabulaire VLBH) | Non (vocabulaire VLBH) |
| 2FA | Non requis | Non requis | Non requis | Recommandé | Obligatoire | **Obligatoire** |
| DPIA | Non | Non | Non | Non | **Non requise** (décision 2026-04-22) | Non requise (idem ST4) |
| Geo-sharding | Non (monorégion UE) | Non | Non | Oui (CH/EU/CA) | Oui (CH/EU/CA) | Oui (CH/EU/CA) |
| Droit à l'effacement | Oui (contact) | Oui (contact + Apple ID) | Oui (contact + billing) | Oui (contact + billing) | Oui (praticienne) + art. 26 (consultantes) | Oui (praticienne + supervision logs) |
| Rétention post-fin | 24 mois inactivité (prop.) | 30 jours post-trial | Durée abonnement + 90j | 10 ans post-formation (prop.) | Durée légale profession santé CH | Durée légale (idem ST4) |
| Backup chiffré | Standard | Standard | Standard | Standard | Point-in-time 30j chiffré | Point-in-time 30j chiffré |
| RLS (row-level security) | Non | Non | Non | Non | Obligatoire (praticienne→consultantes) | RLS étendue (lecture Cercle SR) |
| Middleware WhatsApp santé | Non | Non | Non | Oui (protocole 5 niveaux) | Oui (intégré au curriculum) | Oui + audit transmission |
| Co-responsabilité art. 26 | Non | Non | Non | Non | Oui (contrat requis) | Oui (idem ST4) + contrat supervision |
| Cockpit access | Non | Non | Non | Whitelist `cockpit_access` | Oui si `cercle_lumiere_sr=true` | Oui (auto si Cercle SR) |

---

## 4. Transition entre stages — événements déclencheurs (toll-gates)

| Transition | Événement déclencheur | Données créées | SVLBH_Identifier |
|---|---|---|---|
| Entrée ST0 | Visiteuse initie contact WhatsApp | visitor_contact | Créé (UUID) |
| ST0 → ST1 | Demande de test app | apple_identity + consentement horodaté | Même UUID |
| ST1 → ST2 | Paiement premier trimestre ColorPicker (CHF 29) | billing_student + préférences ColorPicker | Même UUID |
| ST1 → ST3 | Inscription directe en formation (séance découverte CHF 59 puis contrat) | student_profile + contract + billing | Même UUID |
| ST2 → ST3 | Inscription en formation après expérience ColorPicker | student_profile + contract + billing | Même UUID |
| ST3 → ST4 | Certification MyShamanFamily + demande statut Pro | praticienne_profile + billing_praticien + contrat art.26 | Même UUID |
| ST4 → ST5 | Promotion MyShaman (capacité ≥ 300% sustained démontrée) | `certification_level=MYSHAMAN` + cooptation Cercle SR | Même UUID |

**Règle fondamentale** : le SVLBH_Identifier ne change jamais. La personne progresse, ses données s'enrichissent, mais son identité pivot reste la même du premier contact WhatsApp jusqu'au statut Pro.

**Règle de fédération** : avant la transition ST3 → ST4 (certification), toutes les identités (WhatsApp, Apple ID, Google ID, email) doivent être fédérées sous le même SVLBH_Identifier. C'est un prérequis technique à la certification.

---

## 5. Architecture apps par stage

| Stage | App(s) | Bundle ID ASC | Zone | Owner |
|---|---|---|---|---|
| ST0 | Aucune (WhatsApp + svlbh.com landing) | — | Z1 | — |
| ST1 | SVLBH Colorpicker (trial) + priv.svlbh.com `/lire` | À définir / Web | Z1bis→Z2 | PO-05 |
| ST2 | 1 des 5 ColorPicker (Glycémie, Sommeil, etc.) | À définir ×5 | Z2 | PO-05 |
| ST3 | SVLBH Formation (Cercle Lumière iOS) + priv.svlbh.com | M100-LS100-DM85.SVLBH-Panel | Z2 | PO-01 |
| ST4 | SVLBH Pro 1, AUDIT Pro 1, SVLBH Chromothérapie 1, SVLBH Protection 1 (satellites de `svlbh-pro`) + pwa.app.svlbh.com | À définir ×4 | Z3 | Patrick Bays |
| ST5 | Mêmes apps que ST4 + cockpit.svlbh.com (audit + supervision Cercle + Si Zhu calendar) | idem ST4 | Z3 | Patrick Bays |

**Note ADR SVLBH-01** : le split en 7 apps ASC concerne l'architecture technique App Store (review Apple, TestFlight, CI/CD). Côté data model et parcours utilisateur, c.est le stage qui détermine les droits d'accès aux données, pas l'app.

---

## 6. Décisions intégrées (arbitrées depuis le 14/04)

| Référence | Décision | Impact blueprint |
|---|---|---|
| RSK-2 (15/04) | Consentement TestFlight accepté pour 6 testeuses beta | ST1 : risk acceptance temporaire. Mécanisme in-app avant scaling. |
| RSK-3 (15/04) | VIFA = auto-évaluation, pas wearable | ST2/ST3 : pas de DPIA pour auto-évaluation. |
| RSK-4 (15/04) | PWA cookies techniques uniquement | ST0 : pas de bandeau cookie complexe. |
| RSK-5 (15/04) | Escrow chiffrement B2B uniquement (ADR-04) | ST4 uniquement. |
| RSK-6 (15/04) | Données radiesthésiques hors Art. 9 RGPD | Tous stages : simplification majeure. DPA standard Supabase suffit. |
| ADR-01 (13/04, confirmé 15/04) | Données hDOM hors Art. 9 | Confirme RSK-6. |
| ADR-05 (13/04) | Budget infra CHF 200/mois | Enveloppe validée pour Supabase Pro + Make + Apple Dev. |
| ADR SVLBH-01 (18/04) | 7 apps ASC, Bash Certifiées hors grille (legacy) | Architecture technique, pas data model. Stage détermine l.accès. |
| ADR SVLBH-03 (22/04) | `svlbh-pro` = SDK + specs + CI + 4 satellites ST4 Pro, aucune DPIA dedans | ST4 : 4 apps nommées (SVLBH Pro 1, AUDIT Pro 1, SVLBH Chromothérapie 1, SVLBH Protection 1). Registre RGPD TR-05 à décomposer en 4 traitements. |
| Décision 2026-04-22 (Patrick Bays) | ST4 Pro : pas de "patient" au sens RGPD. Praticienne reçoit des **consultantes** pour décoder les **mémoires électromagnétiques accumulées de défunts, de familles d'Âmes et de Monades de la consultante, qui se densifient dans la matière**. Mission de l'Âme = se libérer des mémoires de métaux lourds accumulées dans d'autres incarnations. Analogie ancestry.com : hors régime renforcé médical. Argument de facto : « Je ne traite jamais le patient vivant mais les mémoires accumulées. » | DPIA ST4 passe de **Obligatoire** à **Non requise** (matrice §3 mise à jour). Décomposition TR-05 en TR-05a/b/c/d avec DPIA Non requise pour les 4 (registre RGPD v1.1). Data-model v0.7 → v0.8 : rename `patient_record` → `consultante_record`, `patient_vibrational_signatures` → `lineage_vibrational_signatures`. |

---

## 7. Données radiesthésiques — qualification post-RSK-6

Depuis l'arbitrage RSK-6 (15 avril 2026), les données radiesthésiques VLBH sont qualifiées ainsi :

- **Scores de Lumière** (SLA, SLSA, SLPMO, SLM) → vocabulaire VLBH propriétaire, hors Art. 9
- **Signatures vibratoires** (Rose des Vents, hDOM, Sephiroth, Phantom Matrix) → vocabulaire VLBH, hors Art. 9
- **Données chromatiques** (Color Gels, teintes, fréquences) → données perceptuelles, hors Art. 9

**Conséquence** : les protections techniques (RLS, chiffrement, backup) sont maintenues par bonne pratique et par respect de la consultante en Z3, mais le régime juridique est celui des données personnelles standard, pas des données sensibles Art. 9.

### Refinement 2026-04-22 — ontologie VLBH ST4 (décision Patrick Bays)

**Vocabulaire canonique** : le travail VLBH Stage 4 (ST4) consiste à **décoder les mémoires électromagnétiques accumulées de défunts, de familles d'Âmes et de Monades de la consultante, qui se densifient dans la matière**. La **mission de l'Âme** de la consultante est de se libérer de ces mémoires — notamment des **mémoires de métaux lourds** — qu'elle a accumulées dans d'**autres incarnations**.

**Sujets travaillés en ST4** (aucun n'est une personne physique vivante au sens RGPD art. 4.1) :

- **Défunts** — ancêtres de la consultante ou incarnations passées de son Âme.
- **Familles d'Âmes** de la consultante.
- **Monades** de la consultante.
- **Mémoires électromagnétiques accumulées** et **mémoires de métaux lourds** densifiées dans la matière.

**Conséquence RGPD** :

- La **consultante** (personne physique vivante, utilisatrice de l'app praticienne) est seule sujet RGPD/nLPD en ST4 — donnée personnelle standard, pas Art. 9 (RSK-6).
- Tous les autres sujets travaillés (défunts, familles d'Âmes, Monades, incarnations passées, mémoires accumulées) sont **hors RGPD** (pas de personnes physiques art. 4.1).
- **Analogie ancestry.com** : service qui opère sur les défunts sans régime RGPD renforcé au-delà du traitement standard des données de ses utilisateurs vivants. Même logique pour VLBH ST4.
- **Argument de facto** (Patrick 2026-04-22) : « Je ne traite de facto jamais le patient vivant mais les mémoires accumulées de ses familles d'Âmes ou de ses Monades. »

**DPIA art. 35 non déclenchée** pour ST4 :

- (a) Profiling systématique et extensif → Non (séances individualisées, pas de décision algorithmique).
- (b) Large-scale traitement Art. 9 → Non (RSK-6 hors Art. 9, pas de donnée médicale).
- (c) Monitoring systématique → Non.

→ **DPIA Non requise** pour les 4 traitements ST4 (TR-05a/b/c/d registre RGPD v1.1, 2026-04-22).

### Méthodologie canonique VLBH ST4 — révocation des clés chromatiques

**Patrick Bays 2026-04-22** : « La priorité de tout soin est de **révoquer les clés des portes** qui permettent aux mémoires électromagnétiques de pénétrer la structure énergétique du patient vivant [consultante]. Ces clés sont **chromatiques**. »

Cette méthodologie structure la grille des 4 apps ST4 Pro :

- **SVLBH Pro 1** (flagship) — orchestration globale, dossier consultante, historique des révocations de clés chromatiques, facturation.
- **AUDIT Pro 1** — traçabilité des actes de révocation (métadonnées : quelle clé chromatique, quand, par quelle praticienne) pour conformité nLPD/RGPD.
- **SVLBH Chromothérapie 1** — cœur opératoire de la méthodologie : révocation des clés chromatiques via Color Gels par méridien, teintes, fréquences.
- **SVLBH Protection 1** — protection énergétique pendant la révocation (contre Qliphoth, égrégores, entités qui tentent de rétablir les clés).

**Conséquence data model** : les "signatures vibratoires" décodées sont en fait des **clés chromatiques** identifiées avant révocation — d'où la suggestion `lineage_vibrational_signatures` ou `chromatic_keys` comme nom de table dans data-model v0.8.

---

## 8. Questions ouvertes spécifiques au blueprint

1. **5 apps ColorPicker** : quels sont les 5 thèmes exacts ? (Glycémie, Sommeil, ... ?)
2. ~~**4 apps SVLBH Pro** : quelles sont les 4 apps exactes reçues par les certifiées Pro ?~~ **Résolu 2026-04-22 (ADR SVLBH-03)** : SVLBH Pro 1, AUDIT Pro 1, SVLBH Chromothérapie 1, SVLBH Protection 1 — satellites GitHub de `monadekarmique/svlbh-pro`.
3. **Pricing Pro définitif** : CHF 259/trimestre est une première estimation. Quand sera-t-il fixé ?
4. **Transition ST2 → ST3** : une consultante ColorPicker peut-elle s'inscrire directement en formation, ou faut-il repasser par une séance découverte ?
5. **Multi-ColorPicker** : une consultante peut-elle souscrire à plusieurs ColorPicker simultanément ?
6. **Hard paywall J14** (DEC-006) : après les 14 jours, c'est un blocage complet. Que se passe-t-il avec les données de la période trial si la personne ne souscrit pas ?

---

## 9. Prochaines itérations

- ~~**v0.2** — Intégrer les réponses aux questions ouvertes §8~~ ✅ 2026-04-22 (ADR SVLBH-03) : 4 apps ST4 nommées, architecture satellites verrouillée.
- ~~**v0.3** — Aligner avec data-model-vlbh.md v0.7~~ ✅ 2026-04-22 (décision Patrick) : refonte vocabulaire ST4 "consultante" + ontologie (défunts, familles d'Âmes, Monades, mémoires accumulées, mission de l'Âme, métaux lourds, incarnations) ; DPIA ST4 passe à **Non requise** (analogie ancestry.com) ; cascade data-model v0.8 (rename tables) ; décomposition TR-05 registre RGPD v1.1.
- ~~**v0.4** — Notation T → ST + introduction ST5 Superviseure + découplage stage/capacity~~ ✅ 2026-05-10 (doctrine 4D Patrick) :
  - Renommage T0..T4 → ST0..ST4 dans tous les libellés UI/doc
  - Nouveau stage ST5 Superviseure (MyShaman, access cockpit, supervision Cercle de Lumière SR)
  - Découplage `parcours_stage` (toll-gate stable) ↔ `tier_capacity` (capacité fluide T0↔T6)
  - Toll-gate ST4 → ST5 ajouté à la matrice §4
  - Matrice §3 compliance enrichie (ligne Cockpit access)
  - Architecture apps §5 enrichie (priv.svlbh.com, pwa.app.svlbh.com, cockpit.svlbh.com)
  - Migration DB additive : `parcours_stage` + `tier_capacity` ajoutées, `parcours_tier` deprecated en attente de cleanup iOS
  - Web migré (priv-web `4619883`, pro-web `123ca36` puis cleanup `83b5941`, RPCs `rpc_leads_drop_parcours_tier_fallback`)
  - iOS migré (svlbh-pro-1 `feature/macos-polish-pages`, 4 commits, C2/C3/C4 ✅ Patrick)
- **v0.5** — Contrats types par transition de stage (conditions générales, consentements, art. 26) — à aligner avec vocabulaire "consultante" ST4 et nouvelle dimension `tier_capacity`

---

## Avertissement

Ce document est un draft de travail issu d'une discussion architecturale. Les qualifications juridiques sont des interprétations à soumettre à un conseil nLPD/RGPD spécialisé avant mise en production. Les tarifs mentionnés sont ceux communiqués par Patrick Bays le 18 avril 2026 et peuvent évoluer.
