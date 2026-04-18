# Data Model vlbh-energy

**Version** : 0.2
**Date** : 2026-04-17
**Auteur** : Patrick Bays + Claude (Cowork)
**Statut** : Draft en itération — ajout data residency géo-fragmentée
**Fichier compagnon** : `data-model-vlbh.mermaid`

---

## Changelog

| Version | Date | Auteur | Changements |
|---------|------|--------|-------------|
| 0.1 | 2026-04-17 | PB + Claude | Première synthèse : trois zones, SVLBH_Identifier pivot, classification juridique, cadre pédagogique, protocole incident |
| 0.2 | 2026-04-17 | PB + Claude | Ajout de la **résidence des données** (data residency) suivant la résidence déclarée de l'utilisatrice. Z2 et Z3 deviennent géo-fragmentées : CH (Suisses), EU (Européens), CA (Canadiens). Z1 reste en monorégion UE. Introduction de la table `svlbh_residency_directory` comme annuaire neutre hébergé en Suisse |

Convention de versioning : SemVer-like — les évolutions mineures de wording incrémentent le patch (0.1.1), les ajouts de structure incrémentent le mineur (0.2), les refontes majeures incrémentent le majeur (1.0).

---

## 1. Contexte et objectifs

vlbh-energy opère un écosystème à trois niveaux de maturité relationnelle avec ses utilisatrices :

- Un flux d'entrée volumétrique via WhatsApp (visiteuses)
- Un parcours de formation certifiante de 15 mois (étudiantes)
- Un réseau de praticiennes certifiées qui reçoivent leurs propres patientes via l'app SVLBH-Palette de Lumière

Chaque niveau implique des exigences distinctes en matière de protection des données (nLPD Suisse + RGPD UE), d'hébergement, d'authentification et de modélisation. L'audit en cours a fait apparaître une confusion dans le niveau de filtre à appliquer par zone. Ce document pose le cadre de référence.

---

## 2. Les trois zones — classification juridique

### Zone 1 — Visiteuses

| Dimension | Valeur |
|---|---|
| Sujet | Prospect/visiteuse curieuse entrant via WhatsApp (95%) ou landing page |
| Volume cible | Plusieurs millions de contacts |
| Données collectées | WhatsApp ID, prénom, LID (WhatsApp Linked ID) |
| Qualification juridique | Donnée personnelle pseudonymisée — **pas sensible** |
| Base légale | Intérêt légitime + consentement implicite (la visiteuse initie le contact) |
| Hébergement | Supabase EU (Francfort), Make.com orchestrateur |
| 2FA | Non requis |
| DPIA | Non requise |

### Zone 1bis — Invitation TestFlight SVLBH Colorpicker

| Dimension | Valeur |
|---|---|
| Sujet | Visiteuse Z1 qui demande à tester l'app pendant 14 jours |
| Données supplémentaires | Email, Apple ID ou Google ID |
| Qualification juridique | Relation pré-contractuelle (art. 6.1.b RGPD) |
| Base légale | **Consentement explicite horodaté** obligatoire |
| Hébergement | Supabase EU — datastore Make svlbh-apple-identity #156475 en transition |

### Zone 2 — Étudiantes en formation (15 mois)

| Dimension | Valeur |
|---|---|
| Sujet | Visiteuse Z1 passée à la séance découverte CHF 59 puis inscrite au parcours 15 mois |
| Cadre juridique | **Contrat de formation pédagogique**, pas contrat de soin |
| Données collectées | Identité étudiante (standard), paiements Postfinance, signatures vibratoires VLBH (outils pédagogiques), progression pédagogique |
| Qualification juridique | Donnée personnelle standard — **pas art. 9** |
| Base légale | Contrat de formation |
| Hébergement | Supabase EU |
| 2FA | Recommandé (pas obligatoire juridiquement) |
| DPIA | Non requise dans le cadre actuel |

### Zone 3 — Praticiennes certifiées et leurs patientes

| Dimension | Valeur |
|---|---|
| Sujet | Étudiante diplômée après 15 mois, exerce en autonomie avec ses patientes via SVLBH-Palette de Lumière |
| Données collectées | Identité praticienne (B2B), facturation/redevances, identité patientes, signatures vibratoires des patientes, historique séances |
| Qualification juridique | **Données sensibles art. 9 RGPD / art. 5c nLPD** |
| Base légale | Consentement explicite patiente + contrat thérapeutique |
| Hébergement | **Suisse** (Infomaniak ou Exoscale) |
| 2FA | **Obligatoire** |
| DPIA | **Obligatoire** |
| Co-responsabilité art. 26 RGPD | Contrat requis avec chaque praticienne certifiée |

---

## 3. Principes juridiques structurants

### 3.1 Pas de données médicales ni d'arbre généalogique

Le travail VLBH utilise des outils pédagogiques propriétaires (Rose des Vents, Scores de Lumière, hDOM, Sephiroth, Phantom Matrix). **Aucun arbre généalogique n'est transmis par l'étudiante.** Aucune donnée médicale n'est collectée. Les perceptions vibratoires sont exprimées dans un vocabulaire VLBH, pas dans un vocabulaire médical.

### 3.3 Pédagogique ≠ thérapeutique

La formation 15 mois est un contrat pédagogique. Patrick intervient comme formateur et superviseur, pas comme thérapeute. L'étudiante effectue son propre travail perceptif à l'aide des outils pédagogiques VLBH. Cette qualification est la clé qui maintient Zone 2 hors art. 9. Elle doit être tenue dans les faits, dans le contrat, dans la communication et dans le modèle de données.

### 3.4 Signatures vibratoires = vocabulaire VLBH

Les signatures énergétiques décodées sont exprimées dans un vocabulaire VLBH propriétaire (Rose des Vents, Scores de Lumière, hDOM, Sephiroth, Phantom Matrix) et non dans un vocabulaire médical. Ce choix lexical protège la qualification pédagogique et constitue une différenciation cohérente avec l'identité de marque.

### 3.5 Data residency — les données suivent la résidence de l'utilisatrice

**Z2 et Z3 sont géo-fragmentées** en trois shards régionaux selon la résidence déclarée de l'utilisatrice au moment de la signature du contrat de formation (Z2) ou du consentement patient (Z3) :

- **Shard CH** — Suisses, hébergement Suisse (Infomaniak ou Exoscale)
- **Shard EU** — Européens, hébergement UE (Supabase Francfort)
- **Shard CA** — Canadiens (y compris Québec Loi 25), hébergement Canada (Supabase Toronto ou OVH Canada)

**Z1 reste en monorégion UE** : le volume (millions de contacts) et la pseudonymisation rendent la géo-fragmentation disproportionnée, et la résidence réelle de la visiteuse est encore imprécise à ce stade (l'indicatif WhatsApp n'est pas fiable comme preuve de résidence).

Le **détermination de la résidence** se fait par déclaration formelle à l'entrée Z2 (adresse de résidence principale ou domicile fiscal), enregistrée dans le contrat de formation. Un changement de résidence en cours de formation déclenche un processus de migration explicite avec nouveau consentement.

### 3.6 Principe de souveraineté du patient en Z3

En Zone 3, la résidence qui détermine l'hébergement est celle de la **patiente**, pas de la praticienne. Si une praticienne suisse traite une patiente canadienne, la donnée de la patiente vit au Canada. La praticienne y accède par flux transfrontalier encadré contractuellement (SCC ou équivalent adéquation Suisse↔CA). Cette règle protège la patiente comme sujet premier du traitement art. 9.

---

## 4. Le SVLBH_Identifier — single source of truth

### 4.1 Principe

Identifiant unique opaque (UUID v4 ou ULID) généré lors de l'entrée en Zone 1. Persiste à travers toutes les zones pour la même personne. Sert de clé étrangère unique dans toutes les tables.

### 4.2 Propriétés

- **Opaque** : non dérivé de données sources (remplace l'actuel hash 256 tronqué 28 qui est réversible par force brute)
- **Stable** : une personne = un identifiant, pour la vie de sa relation avec vlbh-energy
- **Pseudonymisant** au sens art. 4.5 RGPD
- **Confidentiel** : jamais exposé côté client ni dans les logs exportables
- **Pivot** : toutes les tables de zone portent ce FK

### 4.3 Structure des tables — aperçu

```
-- TABLE PIVOT (globale, hébergement Suisse neutre)
svlbh_identifier_registry
  svlbh_id              : UUID (PK)
  created_at            : timestamp
  current_zone          : enum(Z1, Z2, Z3)
  zone_history          : array of {zone, transition_date}

-- ANNUAIRE DE RÉSIDENCE (globale, hébergement Suisse neutre)
svlbh_residency_directory
  svlbh_id              : UUID (FK)
  declared_residency    : enum(CH, EU, CA)
  declared_at           : timestamp
  declared_source       : enum(contrat_formation, consentement_patient, migration)
  country_code          : ISO-3166-1 alpha-2  -- précision sous-régionale (FR, DE, QC, etc.)
  migration_history     : array of {from, to, date, reason}

-- ZONE 1
visitor_contact
  svlbh_id              : UUID (FK)
  whatsapp_id           : encrypted
  first_name            : string
  lid                   : string
  pseudonym_hash_legacy : string  -- à déprécier

apple_identity          -- Z1bis
  svlbh_id              : UUID (FK)
  email                 : encrypted
  apple_id OR google_id : string
  testflight_invite_sent_at : timestamp
  consent_email_timestamp   : timestamp
  consent_text_version      : string

-- ZONE 2
student_profile
  svlbh_id              : UUID (FK)
  civil_identity        : object
  formation_start       : date
  formation_stage       : enum
  contract_signed_at    : timestamp
  contract_version      : string
  -- CONTRAINTE : aucun champ de santé ou diagnostic médical


billing_student
  svlbh_id              : UUID (FK)
  session_type          : enum(decouverte_59, formation_mois_X, ...)
  amount_chf            : number
  postfinance_ref       : string
  paid_at               : timestamp

-- ZONE 3 (Suisse)
praticienne_profile
  svlbh_id              : UUID (FK)
  certification_date    : date
  certification_level   : enum
  twofa_enabled         : boolean (required TRUE)

billing_praticien       -- COMMERCIAL B2B UNIQUEMENT
  svlbh_id              : UUID (FK)
  redevance_amount      : number
  billing_period        : string

patient_record          -- ART. 9 SENSIBLE
  patient_id            : UUID (PK)
  praticienne_svlbh_id  : UUID (FK)
  civil_identity        : object
  consent_art9_signed_at : timestamp
  consent_version       : string

patient_vibrational_signatures  -- ART. 9 SENSIBLE
  signature_id          : UUID (PK)
  patient_id            : UUID (FK)
  pattern               : string
  decoded_at            : timestamp
  session_id            : UUID
```

### 4.4 Contraintes techniques de base de données

- **`student_profile`** : aucun champ médical ou diagnostique. Seul le vocabulaire VLBH pédagogique est autorisé.
- **`patient_record`** et **`patient_vibrational_signatures`** : RLS (Row Level Security) strict limitant chaque praticienne à ses propres patientes uniquement.
- Chiffrement au repos AES-256 pour toutes les tables.
- Backups point-in-time sur les tables Z3 avec rétention 30 jours chiffrée.

### 4.5 Règle applicative complémentaire

Les formulaires étudiante (UI back-office, Colorpicker) n'offrent **aucun champ** pour saisir un diagnostic médical. La possibilité n'existe pas dans l'interface — la prévention est autant comportementale que technique.

---

## 5. Décisions d'hébergement

| Zone / Shard | Juridiction | Fournisseur recommandé | Raison |
|---|---|---|---|
| **Pivot global** (directory + residency) | Suisse neutre | Infomaniak managed Postgres | Métadonnée minimale, point de routage, juridiction forte |
| **Z1** (monorégion) | UE | Supabase EU (Francfort) + Make orchestrateur | Volume élevé, pseudonymisation, résidence imprécise à ce stade |
| **Z1bis** (monorégion) | UE | Idem | Email + Apple/Google ID standard |
| **Z2-CH** | Suisse | Infomaniak OU Exoscale | Étudiantes résidant en Suisse |
| **Z2-EU** | UE | Supabase EU (Francfort) | Étudiantes résidant en UE |
| **Z2-CA** | Canada | Supabase Toronto OU OVH Canada | Étudiantes résidant au Canada (y compris Québec) |
| **Z3-CH** | Suisse | Infomaniak OU Exoscale (même infra que Z2-CH) | Patientes résidant en Suisse — art. 9 |
| **Z3-EU** | UE | Supabase EU (Francfort) | Patientes résidant en UE — art. 9 |
| **Z3-CA** | Canada | Supabase Toronto OU OVH Canada | Patientes résidant au Canada — art. 9 + Loi 25 Québec |

**Note infra** : en Suisse comme au Canada, il est raisonnable de **co-héberger Z2 et Z3** sur la même infrastructure, en distinguant les niveaux de sécurité par schéma / RLS / 2FA. Cela évite la multiplication des fournisseurs tout en respectant la souveraineté régionale.

### Transitions à opérer

Les datastores Make actuels sont en transition vers le modèle cible :

- **svlbh-whatsapp-contacts #157329** → Supabase EU, table `visitor_contact` (Z1 monorégion)
- **svlbh-apple-identity #156475** → Supabase EU, table `apple_identity` (Z1bis monorégion)
- **billing_praticien #156396** → **à éclater** selon deux axes :
  - Axe fonctionnel : B2B commercial (table `billing_praticien`) vs patientes (tables `patient_record` + `patient_vibrational_signatures`)
  - Axe géographique : chaque partie répartie selon la résidence de la praticienne (B2B) ou de la patiente (Z3)

Les datastores Make restent pertinents comme **buffer d'orchestration** (scénarios entrants et sortants), mais ne constituent plus le système d'enregistrement canonique.

### Flux transfrontaliers à encadrer

- **Suisse ↔ UE** : décision d'adéquation mutuelle reconnue, peu de formalités.
- **UE ↔ Canada** : adéquation partielle Canada (secteur commercial privé via PIPEDA). SCC recommandés pour art. 9.
- **Suisse ↔ Canada** : pas de décision d'adéquation formelle. **SCC obligatoires** pour tout flux art. 9 transfrontalier.
- **Québec (Loi 25)** : depuis septembre 2023, obligations renforcées — PIA (privacy impact assessment) pour tout transfert hors Québec, DPO désigné, consentement explicite pour usage secondaire.

---

## 6. Protocole de gestion des incidents de données santé

Même si Z2 n'est pas en art. 9 par conception, il arrive qu'une étudiante transmette spontanément des documents de santé (ex : analyses sanguines). Protocole en cinq étages.

### Étage 1 — Prévention contractuelle

Clause explicite dans le contrat de formation : « Les canaux de formation (WhatsApp, email, téléphone) ne sont pas conçus pour la transmission de documents médicaux. L'étudiante s'engage à ne pas y transmettre d'analyses de laboratoire, diagnostics médicaux, imageries, ordonnances, ou autres documents de santé. »

### Étage 2 — Réponse automatique standardisée

À la détection (pièce jointe + mots-clés : « analyse », « résultat », « bilan », « diagnostic », nom de laboratoire), réponse-type envoyée immédiatement rappelant le cadre et demandant la suppression bilatérale.

### Étage 3 — Suppression effective sous 48h

Script automatisé de purge sur bridge WhatsApp + appareils liés. Log horodaté de chaque suppression. La politique actuelle « vidange 12-15 jours » est resserrée à 48h pour les documents santé reçus hors cadre.

### Étage 4 — Registre des incidents

Journal non-identifiant : date, type de document, action, délai. Preuve de conformité en cas d'audit PFPDT.

### Étage 5 — Politique de backup

Désactivation du backup iCloud/Google Drive de WhatsApp sur les appareils recevant les messages formation, ou usage d'un compte WhatsApp Business dédié avec contrôle backups.

### Extension Z3

Le protocole est reproduit à l'identique dans chaque installation SVLBH-Palette de Lumière des praticiennes certifiées. Enseignement intégré au curriculum de certification — chaque praticienne apprend à gérer les documents santé reçus de ses patientes.

---

## 7. Questions ouvertes

1. **Choix définitif de l'hébergeur Suisse** (Z2-CH + Z3-CH) : Infomaniak vs Exoscale vs autre ? Décision à prendre avant déploiement de la première Palette de Lumière en production.
2. **Choix définitif de l'hébergeur Canada** (Z2-CA + Z3-CA) : Supabase Toronto vs OVH Canada vs autre ? À cadrer quand les premières utilisatrices canadiennes arrivent.
3. **Déclenchement formel de la DPIA Z3** par shard régional : une DPIA par région, ou une DPIA globale avec annexes régionales ?
4. **Contrat de co-responsabilité art. 26 RGPD** avec chaque praticienne certifiée : modèle à rédiger, adapté au shard régional.
5. **Migration des datastores Make vers Supabase** : calendrier, mapping des données existantes, période transitoire.
6. **Middleware de détection santé** sur le bridge WhatsApp vlbh-energy-mcp : architecture à spécifier.
7. **Politique de conservation Z2** post-formation : durée d'archivage (proposition : 10 ans après fin de formation, alignée sur obligations pro santé CH, avec droit à l'effacement).
8. **SVLBH Colorpicker** (app TestFlight) : produit-elle des données qui atterrissent en base ? Si oui, catégorie/zone et routage régional ?
9. **Rétroactivité** : que faire des données actuellement dans Make au format hash 256 tronqué 28 ? Re-pseudonymisation vers SVLBH_Identifier natif + affectation régionale ?
10. **Flux transfrontalier praticienne ↔ patiente** : modèle de SCC pour les cas où la praticienne d'une région traite une patiente d'une autre région. Particulièrement Suisse ↔ Canada (sans adéquation formelle).
11. **Cas du déménagement d'une étudiante ou patiente** entre régions : processus de migration de données, nouveau consentement, bascule du shard d'hébergement.
12. **Loi 25 du Québec** : si les Canadiennes incluent des Québécoises, obligations supplémentaires (DPO, PIA, consentement explicite usage secondaire). À cadrer spécifiquement.

---

## 8. Prochaines itérations prévues

- **v0.2** — Spec détaillée du schéma Supabase (DDL SQL concret)
- **v0.3** — Contenu juridique complet du contrat de formation (clauses, consentements)
- **v0.4** — Architecture Zone 3 Swiss hosting (choix fournisseur, infra, DPIA)
- **v0.5** — Spec middleware détection santé WhatsApp bridge

---

## Avertissement

Ce document est un draft de travail issu d'une discussion architecturale. Les qualifications juridiques proposées sont des interprétations à soumettre à un conseil nLPD/RGPD spécialisé avant mise en production. Les clauses contractuelles mentionnées sont des orientations, pas des textes validés.
