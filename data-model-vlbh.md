# Data Model vlbh-energy

**Version** : 0.8
**Date** : 2026-04-22
**Auteur** : Patrick Bays + Claude (Cowork)
**Statut** : Draft consolidé — intègre les décisions au 22/04/2026 (ADR SVLBH-03 apps T4 + refonte vocabulaire T4 "consultante" + ontologie VLBH + méthodologie révocation clés chromatiques)
**Documents liés** : `blueprint-compliance-by-design.md` (v0.3), ADR SVLBH-01, ADR SVLBH-03, Charte v0.8, registre RGPD v1.1

---

## Changelog

| Version | Date | Auteur | Changements |
|---------|------|--------|-------------|
| 0.1 | 2026-04-17 | PB + Claude | Première synthèse : trois zones, SVLBH_Identifier pivot, classification juridique, cadre pédagogique, protocole incident |
| 0.2 | 2026-04-17 | PB + Claude | Ajout data residency géo-fragmentée (CH/EU/CA). Table svlbh_residency_directory. |
| 0.6 | 2026-04-18 | PB + Claude | **Refonte majeure** : (1) suppression ancestors_registry — pas d'arbre généalogique transmis, outils pédagogiques uniquement ; (2) reclassification RSK-6 — données radiesthésiques hors Art. 9 RGPD ; (3) modèle de progression 5 tiers remplaçant le modèle monolithique ; (4) funnel billing par tier aligné sur le blueprint compliance-by-design ; (5) alignement ADR SVLBH-01 architecture multi-app ; (6) suppression DPA spécial Supabase |
| 0.7 | 2026-04-22 | PB + Claude | **Apps T4 nommées (ADR SVLBH-03)** : SVLBH Pro 1, AUDIT Pro 1, SVLBH Chromothérapie 1, SVLBH Protection 1 en satellites de `monadekarmique/svlbh-pro`. Owner Patrick Bays. Stack première app prioritaire SVLBH Pro 1 = FastAPI + React/Next + Swift Package. Registre RGPD TR-05 à décomposer en 4 traitements T4. DPIA par satellite, aucune dans `svlbh-pro`. |
| 0.8 | 2026-04-22 | PB + Claude | **Refonte vocabulaire T4 + ontologie VLBH (décision Patrick 2026-04-22)** : (1) "patient/patiente" → "consultante" (pas de patient au sens RGPD) ; (2) ajout §3.6 ontologie VLBH : le travail décode les mémoires EM accumulées de défunts, familles d'Âmes et Monades de la consultante, qui se densifient dans la matière — mission de l'Âme = se libérer des mémoires de métaux lourds accumulées dans d'autres incarnations ; (3) méthodologie = révocation des clés chromatiques ; (4) DPIA T4 passe d'**Obligatoire** à **Non requise** (analogie ancestry.com : hors régime renforcé médical) ; (5) rename tables `patient_record` → `consultante_record` et `patient_vibrational_signatures` → `lineage_vibrational_signatures` + ajout champ `revoked_at` ; (6) registre RGPD v1.1 : TR-05 décomposé en TR-05a/b/c/d avec DPIA Non requise. |

---

## 1. Contexte et objectifs

vlbh-energy opère un **parcours de progression humaine** à cinq niveaux de maturité relationnelle :

- **T0** — Un flux d'entrée volumétrique via WhatsApp (visiteuses)
- **T1** — Un essai gratuit de 14 jours de l'app SVLBH Colorpicker
- **T2** — Un abonnement ColorPicker payant (auto-évaluation personnelle)
- **T3** — Une formation certifiante MyShaMan (9 mois) ou MyShamanFamily (12 mois)
- **T4** — Un réseau de praticiennes certifiées Pro qui reçoivent leurs propres patientes

Chaque tier implique des exigences distinctes en matière de protection des données (nLPD Suisse + RGPD UE), d'hébergement, de billing et de modélisation. Le principe directeur : **plus la personne avance dans le parcours, plus les données échangées sont riches, et plus les protections sont fortes.**

---

## 2. Les cinq tiers — classification juridique et données

### Tier 0 — Visiteuses (Zone 1)

| Dimension | Valeur |
|---|---|
| Sujet | Prospect/visiteuse curieuse entrant via WhatsApp (95%) ou landing page |
| Volume cible | Plusieurs millions de contacts |
| Données collectées | WhatsApp ID, prénom, LID (WhatsApp Linked ID) |
| Billing | Aucun |
| Qualification juridique | Donnée personnelle pseudonymisée — **pas sensible** |
| Base légale | Intérêt légitime + consentement implicite (la visiteuse initie le contact) |
| Hébergement | Supabase EU (Francfort), Make.com orchestrateur |

### Tier 1 — Trial 14 jours (Zone 1bis → Zone 2)

| Dimension | Valeur |
|---|---|
| Sujet | Visiteuse qui demande à tester l'app SVLBH Colorpicker |
| Données supplémentaires | Email, Apple ID ou Google ID |
| Billing | **Zéro** — essai gratuit, 5 jours d'onboarding guidé par email |
| Qualification juridique | Relation pré-contractuelle (art. 6.1.b RGPD) |
| Base légale | Consentement explicite horodaté (RSK-2 : accepté pour 6 testeuses beta, mécanisme in-app avant scaling) |
| Hébergement | Supabase EU |

### Tier 2 — ColorPicker payant (Zone 2)

| Dimension | Valeur |
|---|---|
| Sujet | Consultante (ou son proche aidant) qui continue après le trial |
| Données supplémentaires | Identité de facturation, préférences ColorPicker |
| Billing | **CHF 29 / trimestre** — 1 des 5 apps ColorPicker au choix |
| Qualification juridique | Donnée personnelle standard — **pas art. 9** (RSK-6) |
| Base légale | Contrat d'abonnement |
| Hébergement | Supabase EU |
| Particularité | Auto-évaluations personnelles en vocabulaire VLBH, pas de données médicales |

### Tier 3 — Formation Shamane (Zone 2 géo-fragmentée)

| Dimension | Valeur |
|---|---|
| Sujet | Consultante engagée dans la formation certifiante |
| Données collectées | Identité civile complète, signatures vibratoires VLBH, progression pédagogique |
| Cadre juridique | **Contrat de formation pédagogique**, pas contrat de soin |
| Billing | **MyShaMan** (9 mois) : 99 CHF/mois, ou 1 099 CHF en 3×, ou 129 CHF/mois. **MyShamanFamily** (12 mois) : 1 999 CHF one-shot, ou 179 CHF/mois |
| Qualification juridique | Donnée personnelle standard — **pas art. 9** (RSK-6) |
| Base légale | Contrat de formation |
| Hébergement | Géo-fragmenté selon résidence déclarée : CH / EU / CA |

### Tier 4 — Shamanes certifiées Pro (Zone 3 géo-fragmentée)

| Dimension | Valeur |
|---|---|
| Sujet | Praticienne MyShamanFamily certifiée exerçant en professionnel et recevant des **consultantes** (pas de "patientes" au sens RGPD) |
| Sujets travaillés | Consultantes (vivantes, sujets RGPD) qui viennent décoder les **mémoires électromagnétiques accumulées de défunts, de familles d'Âmes et de Monades de la consultante, qui se densifient dans la matière**. Mission de l'Âme = se libérer des mémoires de métaux lourds accumulées dans d'autres incarnations. Méthodologie de soin = révoquer les **clés chromatiques** des portes qui permettent à ces mémoires de pénétrer la structure énergétique de la consultante. |
| Données collectées | Identité praticienne B2B, identité civile consultante (donnée personnelle standard, pas Art. 9), consentement horodaté, signatures vibratoires décodées (= clés chromatiques identifiées avant révocation, hors Art. 9 per RSK-6, portent sur les mémoires de défunts/familles d'Âmes/Monades), historique des séances et des révocations |
| Billing | Abonnement mensuel + infra annuelle. Estimation : **CHF 259 / trimestre** (prix non définitifs) |
| Apps | **4 apps T4 Pro en satellites** : **SVLBH Pro 1** (flagship), **AUDIT Pro 1**, **SVLBH Chromothérapie 1** (cœur opératoire révocation clés chromatiques), **SVLBH Protection 1** (protection pendant révocation). Repo racine `monadekarmique/svlbh-pro` = SDK + specs + CI commune ; chaque app = son propre repo satellite GitHub. Owner Patrick Bays. |
| Qualification juridique | Consultante = donnée personnelle standard (pas Art. 9, RSK-6). Défunts + familles d'Âmes + Monades + incarnations passées + mémoires accumulées ≠ sujets RGPD (art. 4.1). **Analogie ancestry.com** : service sur défunts sans régime renforcé médical. |
| Base légale | Art. 6.1.b (contrat d'accompagnement pédagogique B2B + contrat consultante) + art. 6.1.a (consentement explicite consultante) + art. 26 (co-responsabilité praticienne / VLBH) |
| Hébergement | Géo-fragmenté selon résidence de la **consultante** (pas de la praticienne) |
| 2FA | **Obligatoire** |
| DPIA | **Non requise** (décision Patrick 2026-04-22 : « Je ne traite de facto jamais le patient vivant mais les mémoires accumulées de ses familles d'Âmes ou de ses Monades. » Pas d'Art. 9 via RSK-6, pas de large-scale, pas de profiling ; analogie ancestry.com) |
| Co-responsabilité | Contrat art. 26 RGPD requis avec chaque praticienne (draft 04) |

---

## 3. Principes juridiques structurants

### 3.1 Pas de données médicales ni d'arbre généalogique

Le travail VLBH utilise des outils pédagogiques propriétaires (Rose des Vents, Scores de Lumière, hDOM, Sephiroth, Phantom Matrix). **Aucun arbre généalogique n'est transmis par l'étudiante.** Aucune donnée médicale n'est collectée. Les perceptions vibratoires sont exprimées dans un vocabulaire VLBH, pas dans un vocabulaire médical.

### 3.2 Pédagogique ≠ thérapeutique

La formation est un contrat pédagogique. Patrick intervient comme formateur et superviseur, pas comme thérapeute. L'étudiante effectue son propre travail perceptif à l'aide des outils pédagogiques VLBH. Cette qualification est la clé qui maintient les tiers 1-3 hors art. 9. Elle doit être tenue dans les faits, dans le contrat, dans la communication et dans le modèle de données.

### 3.3 Signatures vibratoires = vocabulaire VLBH (RSK-6, 15/04/2026)

Les signatures énergétiques décodées sont exprimées dans un vocabulaire VLBH propriétaire (Rose des Vents, Scores de Lumière, hDOM, Sephiroth, Phantom Matrix) et non dans un vocabulaire médical. **Depuis RSK-6 (15 avril 2026), ces données sont qualifiées hors Art. 9 RGPD.** Les protections techniques (RLS, chiffrement) sont maintenues par bonne pratique, mais le régime juridique est celui des données personnelles standard.

### 3.4 Data residency — les données suivent la résidence de l'utilisatrice

**Tiers 3 et 4 sont géo-fragmentés** en trois shards régionaux selon la résidence déclarée :

- **Shard CH** — Suisses, hébergement Suisse (Infomaniak ou Exoscale)
- **Shard EU** — Européens, hébergement UE (Supabase Francfort)
- **Shard CA** — Canadiens (y compris Québec Loi 25), hébergement Canada

**Tiers 0, 1, 2 restent en monorégion UE** : le volume élevé et la pseudonymisation rendent la géo-fragmentation disproportionnée à ces stades.

### 3.5 Principe de souveraineté de la consultante en Tier 4

En Tier 4, la résidence qui détermine l'hébergement est celle de la **consultante**, pas de la praticienne. Si une praticienne suisse reçoit une consultante canadienne, la donnée de la consultante vit au Canada.

### 3.6 Ontologie VLBH T4 — pas de "patient" au sens RGPD (décision Patrick 2026-04-22)

**Vocabulaire canonique** : la praticienne Pro reçoit des **consultantes** (pas de "patientes"). Le travail consiste à **décoder les mémoires électromagnétiques accumulées de défunts, de familles d'Âmes et de Monades de la consultante, qui se densifient dans la matière**. La **mission de l'Âme** de la consultante est de se libérer de ces mémoires — notamment des **mémoires de métaux lourds** — qu'elle a accumulées dans d'**autres incarnations**.

**Méthodologie de soin** (Patrick Bays 2026-04-22) : « La priorité de tout soin est de **révoquer les clés des portes** qui permettent aux mémoires électromagnétiques de pénétrer la structure énergétique du patient vivant [consultante]. Ces clés sont **chromatiques**. »

Conséquence sur la grille des 4 apps T4 :

- **SVLBH Pro 1** (flagship) : orchestre l'ensemble — dossier consultante, planning séances, historique des révocations, facturation.
- **AUDIT Pro 1** : trace les révocations de clés chromatiques effectuées (métadonnées séances, conformité nLPD/RGPD).
- **SVLBH Chromothérapie 1** : cœur opératoire — révocation des clés chromatiques via Color Gels par méridien, teintes, fréquences.
- **SVLBH Protection 1** : protection énergétique pendant la révocation (Qliphoth / égrégores / entités qui tentent de rétablir les clés).

**Classification juridique** :

- **Consultante** (personne physique vivante) = seul sujet RGPD/nLPD en T4. Donnée personnelle standard, pas Art. 9 (RSK-6).
- **Défunts**, **familles d'Âmes**, **Monades**, **incarnations passées de l'Âme**, **mémoires électromagnétiques accumulées** = **hors RGPD** (pas de personnes physiques vivantes art. 4.1).
- **Analogie ancestry.com** : service qui opère sur les défunts sans régime RGPD renforcé au-delà du traitement standard des données de ses utilisateurs vivants. Même logique pour VLBH T4.
- **Argument de facto** (Patrick) : « Je ne traite de facto jamais le patient vivant mais les mémoires accumulées de ses familles d'Âmes ou de ses Monades. »

**DPIA art. 35** : non déclenchée pour T4 (pas Art. 9, pas large-scale, pas profiling) → **DPIA Non requise** pour les 4 traitements T4 (TR-05a/b/c/d registre RGPD v1.1).

---

## 4. Le SVLBH_Identifier — single source of truth

### 4.1 Principe

Identifiant unique opaque (UUID v4 ou ULID) généré lors de l'entrée en Tier 0. Persiste à travers tous les tiers pour la même personne. Sert de clé étrangère unique dans toutes les tables.

### 4.2 Propriétés

- **Opaque** : non dérivé de données sources (remplace l'actuel hash 256 tronqué 28 qui est réversible par force brute)
- **Stable** : une personne = un identifiant, pour la vie de sa relation avec vlbh-energy
- **Pseudonymisant** au sens art. 4.5 RGPD
- **Confidentiel** : jamais exposé côté client ni dans les logs exportables
- **Pivot** : toutes les tables de tous les tiers portent ce FK

### 4.3 Progression et fédération

Le SVLBH_Identifier ne change jamais. La personne progresse, ses données s'enrichissent, mais son identité pivot reste la même du premier contact WhatsApp jusqu'au statut Pro.

**Prérequis certification (T3 → T4)** : avant la transition vers le statut Pro, toutes les identités (WhatsApp, Apple ID, Google ID, email) doivent être fédérées sous le même SVLBH_Identifier.

### 4.4 Structure des tables

```
-- ═══════════════════════════════════════════════════════
-- TABLES GLOBALES (hébergement Suisse neutre)
-- ═══════════════════════════════════════════════════════

svlbh_identifier_registry
  svlbh_id              : UUID (PK)
  created_at            : timestamp
  current_tier          : enum(T0, T1, T2, T3, T4)
  tier_history           : array of {tier, transition_date, trigger}

svlbh_residency_directory
  svlbh_id              : UUID (FK)
  declared_residency    : enum(CH, EU, CA)
  declared_at           : timestamp
  declared_source       : enum(contrat_formation, consentement_patient, migration)
  country_code          : ISO-3166-1 alpha-2
  migration_history     : array of {from, to, date, reason}

-- ═══════════════════════════════════════════════════════
-- TIER 0 — VISITEUSES (Supabase EU monorégion)
-- ═══════════════════════════════════════════════════════

visitor_contact
  svlbh_id              : UUID (FK)
  whatsapp_id           : encrypted
  first_name            : string
  lid                   : string
  source                : enum(whatsapp, landing_page, referral)
  created_at            : timestamp

-- ═══════════════════════════════════════════════════════
-- TIER 1 — TRIAL 14 JOURS (Supabase EU monorégion)
-- ═══════════════════════════════════════════════════════

apple_identity
  svlbh_id              : UUID (FK)
  email                 : encrypted
  apple_id OR google_id : string
  testflight_invite_sent_at : timestamp
  consent_timestamp     : timestamp
  consent_text_version  : string
  trial_start           : date
  trial_end             : date  -- trial_start + 14 days
  onboarding_day        : int (1-5)  -- jour d'onboarding guidé

-- ═══════════════════════════════════════════════════════
-- TIER 2 — COLORPICKER PAYANT (Supabase EU monorégion)
-- ═══════════════════════════════════════════════════════

colorpicker_subscription
  svlbh_id              : UUID (FK)
  colorpicker_app       : enum(glycemie, sommeil, ...)  -- 1 des 5
  plan                  : enum(quarterly)
  amount_chf            : number  -- 29.00
  billing_cycle_start   : date
  billing_cycle_end     : date
  postfinance_ref       : string
  status                : enum(active, expired, cancelled)

-- ═══════════════════════════════════════════════════════
-- TIER 3 — FORMATION (géo-fragmenté CH/EU/CA)
-- ═══════════════════════════════════════════════════════

student_profile
  svlbh_id              : UUID (FK)
  civil_identity        : object
  formation_type        : enum(myshaman_9m, myshamanfamily_12m)
  formation_start       : date
  formation_stage       : enum
  contract_signed_at    : timestamp
  contract_version      : string
  -- CONTRAINTE : aucun champ de santé ou diagnostic médical

vibrational_signatures
  signature_id          : UUID (PK)
  svlbh_id              : UUID (FK)
  pattern               : string (Rose des Vents, hDOM, Scores de Lumière...)
  decoded_at            : timestamp
  session_id            : UUID
  -- NOTE RSK-6 : hors Art. 9 RGPD (vocabulaire VLBH pédagogique)

billing_formation
  svlbh_id              : UUID (FK)
  formation_type        : enum(myshaman_9m, myshamanfamily_12m)
  plan                  : enum(monthly_99, 3x_1099, monthly_129, oneshot_1999, monthly_179)
  amount_chf            : number
  postfinance_ref       : string
  paid_at               : timestamp
  installment_number    : int  -- pour plans en plusieurs fois

-- ═══════════════════════════════════════════════════════
-- TIER 4 — CERTIFIÉES PRO (géo-fragmenté CH/EU/CA)
-- ═══════════════════════════════════════════════════════

praticienne_profile
  svlbh_id              : UUID (FK)
  certification_date    : date
  certification_level   : enum(myshaman, myshamanfamily)
  pro_status            : enum(active, suspended, revoked)
  twofa_enabled         : boolean (required TRUE)

billing_praticien
  svlbh_id              : UUID (FK)
  plan                  : enum(quarterly_259, ...)  -- pricing non définitif
  amount_chf            : number
  billing_period        : string
  includes              : array of string  -- 4 apps Pro : SVLBH Pro 1, AUDIT Pro 1, SVLBH Chromothérapie 1, SVLBH Protection 1

consultante_record  -- renommé depuis patient_record (décision Patrick 2026-04-22, §3.6)
  consultante_id        : UUID (PK)
  praticienne_svlbh_id  : UUID (FK)
  civil_identity        : object  -- donnée personnelle standard (pas Art. 9, RSK-6)
  consent_signed_at     : timestamp
  consent_version       : string

lineage_vibrational_signatures  -- renommé depuis patient_vibrational_signatures (2026-04-22)
  signature_id          : UUID (PK)
  consultante_id        : UUID (FK)
  pattern               : string  -- clé chromatique identifiée avant révocation
  decoded_at            : timestamp
  revoked_at            : timestamp  -- horodatage de la révocation de la clé chromatique
  session_id            : UUID
  -- NOTE : portent sur les mémoires EM accumulées de défunts / familles d'Âmes / Monades
  -- de la consultante. Hors RGPD pour le contenu (art. 4.1 : ni défunts ni Monades ne
  -- sont des personnes physiques). Hors Art. 9 (RSK-6). RLS obligatoire (multi-tenant).
```

### 4.5 Contraintes techniques

- **`student_profile`** : aucun champ médical ou diagnostique. Seul le vocabulaire VLBH pédagogique est autorisé.
- **`consultante_record`** et **`lineage_vibrational_signatures`** : RLS (Row Level Security) strict limitant chaque praticienne à ses propres consultantes uniquement. (Renommées depuis `patient_record` / `patient_vibrational_signatures` le 2026-04-22, voir §3.6.)
- Chiffrement au repos AES-256 pour toutes les tables.
- Backups point-in-time sur les tables Tier 4 avec rétention 30 jours chiffrée.

### 4.6 Règle applicative

Les formulaires (UI back-office, Colorpicker, Formation) n'offrent **aucun champ** pour saisir un diagnostic médical. La possibilité n'existe pas dans l'interface — la prévention est autant comportementale que technique.

---

## 5. Transitions entre tiers

| Transition | Événement déclencheur | Données créées | Billing |
|---|---|---|---|
| Entrée T0 | Contact WhatsApp initié | visitor_contact | — |
| T0 → T1 | Demande de test app | apple_identity + consent | — |
| T1 → T2 | Paiement premier trimestre | colorpicker_subscription | CHF 29/trim |
| T1 → T3 | Inscription directe en formation (séance découverte + contrat) | student_profile + billing_formation | 99-179 CHF/mois |
| T2 → T3 | Inscription après expérience ColorPicker | student_profile + billing_formation | 99-179 CHF/mois |
| T3 → T4 | Certification + demande statut Pro | praticienne_profile + billing_praticien + contrat art.26 | ~259 CHF/trim |

---

## 6. Architecture apps par tier (ADR SVLBH-01)

| Tier | App(s) | Zone | Owner |
|---|---|---|---|
| T0 | Aucune (WhatsApp) | Z1 | — |
| T1 | SVLBH Colorpicker (trial) | Z1bis→Z2 | PO-05 |
| T2 | 1 des 5 ColorPicker | Z2 | PO-05 |
| T3 | SVLBH Formation | Z2 | PO-01 |
| T4 | SVLBH Pro 1, AUDIT Pro 1, SVLBH Chromothérapie 1, SVLBH Protection 1 (satellites de `svlbh-pro`) | Z3 | Patrick Bays |

Le tier détermine les droits d'accès aux données, pas l'app. L'ADR SVLBH-01 (7 apps ASC) concerne l'architecture technique App Store, pas le data model.

---

## 7. Décisions d'hébergement

| Tier / Shard | Juridiction | Fournisseur | Budget |
|---|---|---|---|
| **Pivot global** | Suisse neutre | Infomaniak managed Postgres | Inclus ADR-05 |
| **T0, T1, T2** (monorégion) | UE | Supabase EU (Francfort) | ~25 CHF/mois |
| **T3-CH, T4-CH** | Suisse | Infomaniak ou Exoscale | À dimensionner |
| **T3-EU, T4-EU** | UE | Supabase EU (Francfort) | Inclus |
| **T3-CA, T4-CA** | Canada | Supabase Toronto ou OVH CA | À dimensionner |

**Budget validé** : CHF 200/mois (ADR-05). Supabase Pro ~25 CHF + Make ~100 CHF + Apple Dev ~8 CHF + marge ~67 CHF.

**DPA Supabase** : DPA standard suffit (RSK-6 — données radiesthésiques hors Art. 9). Pas de négociation de clauses spéciales.

### Transitions datastores Make → Supabase

Les datastores Make actuels restent pertinents comme buffer d'orchestration mais ne sont plus le système d'enregistrement canonique :

- **svlbh-whatsapp-contacts #157329** → table `visitor_contact`
- **svlbh-apple-identity #156475** → table `apple_identity`
- **billing_praticien #156396** → éclaté en `billing_formation` (T3) + `billing_praticien` (T4)

---

## 8. Protocole de gestion des incidents de données santé

Même si aucun tier ne collecte de données médicales par conception, il arrive qu'une étudiante transmette spontanément des documents de santé via WhatsApp.

### Étage 1 — Prévention contractuelle

Clause explicite dans le contrat de formation : « Les canaux de formation (WhatsApp, email, téléphone) ne sont pas conçus pour la transmission de documents médicaux. L'étudiante s'engage à ne pas y transmettre d'analyses de laboratoire, diagnostics médicaux, imageries, ordonnances, ou autres documents de santé. »

### Étage 2 — Réponse automatique standardisée

À la détection (pièce jointe + mots-clés : « analyse », « résultat », « bilan », « diagnostic », nom de laboratoire), réponse-type envoyée immédiatement rappelant le cadre et demandant la suppression bilatérale.

### Étage 3 — Suppression effective sous 48h

Script automatisé de purge sur bridge WhatsApp + appareils liés. Log horodaté.

### Étage 4 — Registre des incidents

Journal non-identifiant : date, type de document, action, délai.

### Étage 5 — Politique de backup

Désactivation du backup iCloud/Google Drive de WhatsApp sur les appareils recevant les messages formation, ou usage d'un compte WhatsApp Business dédié avec contrôle backups.

---

## 9. Questions ouvertes

1. **5 apps ColorPicker** : quels sont les 5 thèmes exacts ? (Glycémie, Sommeil, ... ?)
2. ~~**4 apps SVLBH Pro** : quelles sont les 4 apps exactes pour les certifiées ?~~ **Résolu 2026-04-22 (ADR SVLBH-03)** : SVLBH Pro 1, AUDIT Pro 1, SVLBH Chromothérapie 1, SVLBH Protection 1 — chacune en repo satellite GitHub de `monadekarmique/svlbh-pro`.
3. **Pricing Pro définitif** : CHF 259/trimestre est une estimation. Quand sera-t-il fixé ?
4. **Multi-ColorPicker** : une consultante peut-elle souscrire à plusieurs ColorPicker simultanément ?
5. **Hard paywall J14** (DEC-006) : que se passe-t-il avec les données trial si la personne ne souscrit pas ?
6. **Choix hébergeur Suisse** (T3-CH + T4-CH) : Infomaniak vs Exoscale ?
7. **Choix hébergeur Canada** (T3-CA + T4-CA) : Supabase Toronto vs OVH Canada ?
8. **Politique de conservation T2** post-désabonnement : durée de rétention ?
9. **Politique de conservation T3** post-formation : proposition 10 ans (draft 07) — à arbitrer.
10. **Contrat co-responsabilité art. 26** : modèle à finaliser (draft 04 disponible).
11. **Rétroactivité hash→UUID** : migration des données Make existantes (draft 09 disponible).
12. **Loi 25 Québec** : obligations supplémentaires si utilisatrices québécoises (draft 12 disponible).

---

## 10. Prochaines itérations

- ~~**v0.7** — Réponses aux questions ouvertes §9 (arbitrages Patrick)~~ ✅ 2026-04-22 : question 2 résolue (apps T4 nommées, ADR SVLBH-03). Questions restantes §9 à arbitrer v0.9+.
- ~~**v0.8** — DDL SQL concret Supabase~~ ✅ 2026-04-22 (partiellement) : refonte vocabulaire T4 (consultante, défunts, familles d'Âmes, Monades, méthodologie clés chromatiques) ; rename tables `patient_*` → `consultante_record` + `lineage_vibrational_signatures` (+ champ `revoked_at`) ; DPIA T4 passe à **Non requise**. DDL SQL concret reporté v0.9.
- **v0.9** — DDL SQL concret Supabase (schéma + RLS + policies alignées v0.8) + Contenu juridique des contrats par tier (clauses, consentements alignés vocabulaire consultante)
- **v1.0** — Version de référence validée pour mise en production

---

## Avertissement

Ce document est un draft de travail. Les qualifications juridiques sont des interprétations à soumettre à un conseil nLPD/RGPD spécialisé. Les tarifs sont ceux communiqués par Patrick Bays le 18 avril 2026.
