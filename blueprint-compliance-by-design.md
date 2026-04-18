# Blueprint Compliance-by-Design SVLBH

**Version** : 0.1
**Date** : 2026-04-18
**Auteur** : Patrick Bays + Claude (Cowork)
**Statut** : Document fondateur — référence pour toute décision data model et architecture
**Documents liés** : `data-model-vlbh.md` (v0.2), ADR SVLBH-01, Charte v0.8

---

## 1. Philosophie

Le modèle SVLBH est un **parcours de progression humaine**, pas un catalogue d'applications. Chaque étape du parcours correspond à un niveau de maturité relationnelle entre la personne et l'écosystème VLBH. La compliance n'est pas une couche ajoutée a posteriori — elle est structurellement liée au tier de progression.

Le principe directeur : **plus la personne avance dans le parcours, plus la relation de confiance est profonde, plus les données échangées sont riches, et plus les protections sont fortes.**

---

## 2. Parcours utilisateur — les 5 tiers

### Tier 0 — Visiteuse (Zone 1)

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

### Tier 1 — Trial 14 jours (Zone 1bis → Zone 2)

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

### Tier 2 — ColorPicker payant (Zone 2)

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

### Tier 3 — Formation Shamane (Zone 2)

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

### Tier 4 — Shamane certifiée Pro (Zone 3)

| Dimension | Valeur |
|---|---|
| Qui | Shamane MyShamanFamily certifiée qui souhaite exercer en professionnel |
| Données supplémentaires | Identité praticienne B2B, données patients (identité + signatures vibratoires), historique séances |
| Billing | Abonnement mensuel + infrastructure minimale annuelle. **Première estimation : CHF 259 / trimestre** (infra + protection). Prix définitifs non encore fixés. |
| Apps | **4 apps SVLBH Pro** (Panel, MyShamanFamily, Palette de Lumière, + 1 à préciser) |
| Zone data | Z3 géo-fragmentée (CH/EU/CA selon résidence de la **patiente**, pas de la praticienne) |
| Base légale | Consentement explicite patiente + contrat thérapeutique |
| RGPD | **Attention nuancée post-RSK-6** : les données radiesthésiques ne sont pas Art. 9. Seules les données d'identité patient sont sous régime renforcé. RLS obligatoire (praticienne ne voit que ses patients). |
| 2FA | **Obligatoire** |
| DPIA | **Obligatoire** |
| Co-responsabilité | Contrat art. 26 RGPD requis avec chaque praticienne (draft 04 disponible) |

---

## 3. Matrice compliance par tier

| Exigence | T0 Visiteuse | T1 Trial | T2 ColorPicker | T3 Formation | T4 Pro |
|---|---|---|---|---|---|
| Consentement explicite | Non (implicite) | Oui (horodaté) | Oui (contrat) | Oui (contrat formation) | Oui (consentement patient) |
| Données Art. 9 | Non | Non | Non | Non | Non (RSK-6) |
| Données médicales | Non | Non | Non | Non (outils pédagogiques) | Non (vocabulaire VLBH) |
| 2FA | Non requis | Non requis | Non requis | Recommandé | Obligatoire |
| DPIA | Non | Non | Non | Non | Obligatoire |
| Geo-sharding | Non (monorégion UE) | Non | Non | Oui (CH/EU/CA) | Oui (CH/EU/CA) |
| Droit à l'effacement | Oui (contact) | Oui (contact + Apple ID) | Oui (contact + billing) | Oui (contact + billing) | Oui (praticienne) + art. 26 (patients) |
| Rétention post-fin | 24 mois inactivité (prop.) | 30 jours post-trial | Durée abonnement + 90j | 10 ans post-formation (prop.) | Durée légale profession santé CH |
| Backup chiffré | Standard | Standard | Standard | Standard | Point-in-time 30j chiffré |
| RLS (row-level security) | Non | Non | Non | Non | Obligatoire (praticienne→patients) |
| Middleware WhatsApp santé | Non | Non | Non | Oui (protocole 5 niveaux) | Oui (intégré au curriculum) |
| Co-responsabilité art. 26 | Non | Non | Non | Non | Oui (contrat requis) |

---

## 4. Transition entre tiers — événements déclencheurs

| Transition | Événement déclencheur | Données créées | SVLBH_Identifier |
|---|---|---|---|
| Entrée T0 | Visiteuse initie contact WhatsApp | visitor_contact | Créé (UUID) |
| T0 → T1 | Demande de test app | apple_identity + consentement horodaté | Même UUID |
| T1 → T2 | Paiement premier trimestre ColorPicker (CHF 29) | billing_student + préférences ColorPicker | Même UUID |
| T1 → T3 | Inscription directe en formation (séance découverte CHF 59 puis contrat) | student_profile + contract + billing | Même UUID |
| T2 → T3 | Inscription en formation après expérience ColorPicker | student_profile + contract + billing | Même UUID |
| T3 → T4 | Certification MyShamanFamily + demande statut Pro | praticienne_profile + billing_praticien + contrat art.26 | Même UUID |

**Règle fondamentale** : le SVLBH_Identifier ne change jamais. La personne progresse, ses données s'enrichissent, mais son identité pivot reste la même du premier contact WhatsApp jusqu'au statut Pro.

**Règle de fédération** : avant la transition T3 → T4 (certification), toutes les identités (WhatsApp, Apple ID, Google ID, email) doivent être fédérées sous le même SVLBH_Identifier. C'est un prérequis technique à la certification.

---

## 5. Architecture apps par tier

| Tier | App(s) | Bundle ID ASC | Zone | Owner |
|---|---|---|---|---|
| T0 | Aucune (WhatsApp) | — | Z1 | — |
| T1 | SVLBH Colorpicker (trial) | À définir | Z1bis→Z2 | PO-05 |
| T2 | 1 des 5 ColorPicker (Glycémie, Sommeil, etc.) | À définir ×5 | Z2 | PO-05 |
| T3 | SVLBH Formation | M100-LS100-DM85.SVLBH-Panel (actuel) | Z2 | PO-01 |
| T4 | 4 apps SVLBH Pro | À définir ×4 | Z3 | PO-02/03/04/06 + Patrick (Bash Certifiées) |

**Note ADR SVLBH-01** : le split en 7 apps ASC concerne l'architecture technique App Store (review Apple, TestFlight, CI/CD). Côté data model et parcours utilisateur, c'est le tier qui détermine les droits d'accès aux données, pas l'app.

---

## 6. Décisions intégrées (arbitrées depuis le 14/04)

| Référence | Décision | Impact blueprint |
|---|---|---|
| RSK-2 (15/04) | Consentement TestFlight accepté pour 6 testeuses beta | T1 : risk acceptance temporaire. Mécanisme in-app avant scaling. |
| RSK-3 (15/04) | VIFA = auto-évaluation, pas wearable | T2/T3 : pas de DPIA pour auto-évaluation. |
| RSK-4 (15/04) | PWA cookies techniques uniquement | T0 : pas de bandeau cookie complexe. |
| RSK-5 (15/04) | Escrow chiffrement B2B uniquement (ADR-04) | T4 uniquement. |
| RSK-6 (15/04) | Données radiesthésiques hors Art. 9 RGPD | Tous tiers : simplification majeure. DPA standard Supabase suffit. |
| ADR-01 (13/04, confirmé 15/04) | Données hDOM hors Art. 9 | Confirme RSK-6. |
| ADR-05 (13/04) | Budget infra CHF 200/mois | Enveloppe validée pour Supabase Pro + Make + Apple Dev. |
| ADR SVLBH-01 (18/04) | 7 apps ASC, Bash Certifiées hors grille | Architecture technique, pas data model. Tier détermine l'accès. |

---

## 7. Données radiesthésiques — qualification post-RSK-6

Depuis l'arbitrage RSK-6 (15 avril 2026), les données radiesthésiques VLBH sont qualifiées ainsi :

- **Scores de Lumière** (SLA, SLSA, SLPMO, SLM) → vocabulaire VLBH propriétaire, hors Art. 9
- **Signatures vibratoires** (Rose des Vents, hDOM, Sephiroth, Phantom Matrix) → vocabulaire VLBH, hors Art. 9
- **Données chromatiques** (Color Gels, teintes, fréquences) → données perceptuelles, hors Art. 9

**Conséquence** : les protections techniques (RLS, chiffrement, backup) sont maintenues par bonne pratique et par respect du patient en Z3, mais le régime juridique est celui des données personnelles standard, pas des données sensibles Art. 9.

---

## 8. Questions ouvertes spécifiques au blueprint

1. **5 apps ColorPicker** : quels sont les 5 thèmes exacts ? (Glycémie, Sommeil, ... ?)
2. **4 apps SVLBH Pro** : quelles sont les 4 apps exactes reçues par les certifiées Pro ?
3. **Pricing Pro définitif** : CHF 259/trimestre est une première estimation. Quand sera-t-il fixé ?
4. **Transition T2 → T3** : une consultante ColorPicker peut-elle s'inscrire directement en formation, ou faut-il repasser par une séance découverte ?
5. **Multi-ColorPicker** : une consultante peut-elle souscrire à plusieurs ColorPicker simultanément ?
6. **Hard paywall J14** (DEC-006) : après les 14 jours, c'est un blocage complet. Que se passe-t-il avec les données de la période trial si la personne ne souscrit pas ?

---

## 9. Prochaines itérations

- **v0.2** — Intégrer les réponses aux questions ouvertes §8
- **v0.3** — Aligner avec data-model-vlbh.md v0.3 (tables billing refactorisées par tier)
- **v0.4** — Contrats types par transition de tier (conditions générales, consentements, art. 26)

---

## Avertissement

Ce document est un draft de travail issu d'une discussion architecturale. Les qualifications juridiques sont des interprétations à soumettre à un conseil nLPD/RGPD spécialisé avant mise en production. Les tarifs mentionnés sont ceux communiqués par Patrick Bays le 18 avril 2026 et peuvent évoluer.
