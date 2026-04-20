# VIFA v0.1 — Spec & Architecture

**Status** : Draft v0.1 — revue Blueprint Compliance-by-Design effectuée (§13) + requalification app T3 (§14). Architecture backend v0.1 confirmée par Patrick. Cascade Asana à confirmer : 2 gaps P1 restants (geo-sharding Z2 CH/EU/CA, SVLBH_Identifier).
**Auteur** : Patrick Bays (via miroir Claude SVLBH Release Train)
**Date** : 2026-04-20
**Repo canonique** : `vlbh-energy-mcp/docs/specs/vifa-v0.1-spec.md`
**Codename** : `VIFA` (validé Patrick 2026-04-20, ex-`SYMTRANS`)

---

## 0. Pre-flight (ADR SVLBH-02)

| Critère | Vérification | Statut |
|---|---|---|
| Date `env.today` | 2026-04-20 (lundi). PI-1 Sprint **S2** = Mer 15 → Mar 28 avril 2026 (convention mer→mar 14j confirmée Patrick 2026-04-20). Validation spec aujourd'hui → exécution démarre **S3** (Mer 29 avr → Mar 12 mai 2026). Pilotes F10/F11 = **S4** (Mer 13 → Mar 26 mai 2026). | ✅ |
| Vocabulaire miroir | Aucun "agent autonome" — facettes thématiques de Patrick uniquement | ✅ |
| Disjonction PO | Parent **PO-07 Infra** (Supabase Storage RLS + Pro upgrade), multi-homé Features → **PO-09 RGPD** (audit, consent, RSK-6), **PO-08 Data Quality** (audit dual-write svlbh-v2/billing), **PO-03 Palette** (intégration UI app SVLBH) | ✅ |
| Confiance | 88% (4 critères × 25 — voir §10) | ✅ ≥ 85% |

**Méta-principe** : Cette Feature est portée par Patrick — les PO sont des miroirs thématiques pour structurer l'expression du besoin et la décomposition SAFe.

---

## 1. Contexte et besoin

### 1.1 Problème observé

Les consultantes VLBH (formées MyShamanFamily, terrain Z1/Z2/Z3/ZA via WhatsApp) envoient régulièrement à Patrick des **photos de symboles** observés en séance ou rapportés par leurs patientes :

- symboles VLBH propres (Rose des Vents tracée, schéma hDOM, code Sephiroth 3 chiffres, niveau Phantom Matrix Dn) ;
- symboles MTC (méridien dessiné, kanji 鬼 / 神 / 氣 / 命, point d'acupuncture annoté) ;
- symboles ésotériques classiques (hexagramme Yi King, sceau, rune, planche géométrique) ;
- dessins libres patient (mandala, dessin enfant, schéma corporel, photo d'objet symbolique) ;
- **parties du corps** (zone douloureuse photographiée, posture spontanée, dermatose, organe désigné).

Aujourd'hui : Patrick **décode manuellement à la volée** dans WhatsApp, sans trace, sans cohérence inter-séances, sans capitalisation pour la base de connaissance consultantes.

### 1.2 Conséquences mesurées

- Service Level WhatsApp dégradé (cf. mémoire `feedback_error_po10_rtm_briefing_20260420.md`, SL 12% mesuré) ;
- Risque RGPD : photos circulent sur bridges WhatsApp non chiffrés au repos (mémoire `reference_whatsapp_bridges.md`) ;
- Pas de capitalisation : chaque décodage refait à zéro, pas d'apprentissage cross-consultante ;
- Pas de structuration : impossible à corréler avec billing_praticien ou audit svlbh-v2 (PO-08).

### 1.3 Vision

Un **traducteur unifié image → déséquilibres structurés** qui :

1. reçoit une image d'une consultante via webhook dédié ;
2. extrait le contenu sémiotique (Vision multimodal LLM) ;
3. mappe vers les deux référentiels VLBH cibles : **Rose des Vents (12 directions × 3 plans)** + **Phantom Matrix (D1–D11 + 5 portes MTC)** ;
4. retourne **trois sorties simultanées** : JSON Supabase pour audit/apprentissage, draft WhatsApp prêt à l'envoi pour la consultante, Markdown structuré pour le dossier patient anonymisé ;
5. trace tout dans Supabase Storage privé + RLS (RSK-6 compatible : données personnelles standard, hors Art. 9 RGPD).

---

## 2. Scope v0.1

### In-scope

- Webhook Make.com **dédié** `vifa` (router keyword `#symbole` sur les 3 bridges WhatsApp existants wa_z1/wa_z2et3/wa_za, isolé du DM-v03-P3 Middleware WhatsApp scénario 9085048) ;
- Pipeline : ingestion image → upload Supabase Storage → call **Mistral Pixtral Large** (fallback Claude Sonnet 4.7 via config) → parsing structuré → triple output ;
- Référentiels mapping : Rose des Vents (12 directions, 3 plans, 4 quadrants) + Phantom Matrix (D1–D11, 5 portes énergétiques) ;
- Anonymisation patient via `pg_hashids` (pseudonymisation cohérente) ;
- Audit table Supabase + politique de purge à 90 jours (cohérent §4bis privacy policy v0.2.5) ;
- Triple sortie : JSON / WhatsApp draft FR / Markdown ;
- Confiance score ≥ 85% pour envoi auto ; sinon escalade vers Patrick (revue manuelle).

**Périmètre géographique v0.1** : **étudiantes résidentes Suisse uniquement** (T3 CH). Décision Patrick 2026-04-20. Pas de fragmentation Z2 CH/EU/CA en v0.1 — monorégion Supabase eu-central-2 Zurich suffit. Extension UE/CA reportée v0.2+ (Open Q nouvelle dans §11).

### Out-of-scope v0.1

- Symboles MTC complets (kanjis ésotériques rares, hexagrammes Yi King) → mapping basique uniquement, raffinement v0.2 ;
- Sephiroth (10 mondes) → pas dans la cible v0.1, à ajouter v0.3 si besoin ;
- Corrélation transgénérationnelle automatique (skill `hdom-decoder` reste manuel) ;
- Réponse audio WhatsApp (text-to-speech) ;
- Application mobile dédiée pour les consultantes (un simple envoi WhatsApp suffit pour v0.1) ;
- Multi-langue d'output : **français uniquement** v0.1 (78% des consultantes CH+FR cf. mémoire `project_audience_geographique_legal.md`).

### Hors-scope définitif (RSK-6)

- Pas de qualification thérapeutique ni de diagnostic médical ;
- Pas de classification Art. 9 RGPD (data-model v0.6 §3.3) ;
- Pas de stockage long-terme image originale (purge 90 j max).

---

## 3. Architecture cible

### 3.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CONSULTANTE                                 │
│             (envoi photo + caption FR sur WhatsApp)                 │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ media (image/jpeg, image/png, image/webp)
                       │ + texte caption optionnel
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│   BRIDGE WhatsApp (wa_z1 / wa_z2et3 / wa_za) — Go+Python           │
│                  patricktest@vlbh                                   │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ POST forward (quand consultante = whitelist)
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│  WEBHOOK MAKE.COM dédié `vifa` (filtre keyword `#symbole`)          │
│  Scenario ID : à créer (proposé : VIFA-9099001)                 │
│  Trigger : Custom webhook gen2                                      │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼ Step 1 — Validation + anonymisation
┌─────────────────────────────────────────────────────────────────────┐
│  ROUTER + HASH                                                      │
│  - whitelist consultante (svlbh-v2 datastore)                       │
│  - pg_hashids(consultante_id, patient_id) → opaque tokens           │
│  - rejet si MIME ≠ image/* ou si > 8 Mo                             │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼ Step 2 — Upload Supabase Storage
┌─────────────────────────────────────────────────────────────────────┐
│  SUPABASE STORAGE bucket `symbols-private` (private + RLS)          │
│  Path : symbols/{consultante_hash}/{yyyy-mm-dd}/{ulid}.{ext}        │
│  TTL pg_cron : 90 jours (purge automatique RSK-6 §4bis)             │
│  Région : eu-central-2 (Zurich) — conforme nLPD-first               │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ signed URL (TTL 10 min)
                       ▼ Step 3 — Vision call
┌─────────────────────────────────────────────────────────────────────┐
│  VISION : Mistral Pixtral Large (fallback Claude Sonnet 4.7)        │
│  - Prompt système figé (cf. §5)                                     │
│  - Inputs : image signed URL + caption + consultante_context        │
│  - Output : JSON strict (function calling / structured output)      │
│  - Coût estimé : ~0.0015 $/image (Pixtral) / ~0.003 (Sonnet 4.7)    │
│  - Secrets API keys dans Supabase Vault                             │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ raw_response_json
                       ▼ Step 4 — Mapping référentiels
┌─────────────────────────────────────────────────────────────────────┐
│  MAPPING ENGINE                                                     │
│  - Rose des Vents : direction → angle/plan/quadrant/transgression  │
│  - Phantom Matrix : level Dn → porte/Wei Qi/heure Zi Wu             │
│  - Confiance score (0.0 – 1.0) calculé                              │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼ Step 5 — Triple output
┌─────────────────────────────────────────────────────────────────────┐
│  OUTPUT 1 : INSERT INTO symbol_translations (audit)                 │
│  OUTPUT 2 : WhatsApp draft FR (template selon confiance)            │
│  OUTPUT 3 : Markdown patient anonymisé → repo VLBH local            │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
       ┌───────────────┴──────────────┐
       ▼                              ▼
┌──────────────┐               ┌──────────────────────────────────┐
│  CONSULTANTE │               │  PATRICK (revue async)           │
│  WhatsApp    │               │  Notion mirror + Asana PO-08     │
│  réponse FR  │               │  alerte si confiance < 85%       │
└──────────────┘               └──────────────────────────────────┘
```

### 3.2 Composants — détail

| Composant | Tech | Réutilisation infra existante |
|---|---|---|
| Bridge WhatsApp | Go + Python (whatsapp-mcp) | wa_z1 / wa_z2et3 / wa_za déjà déployés |
| Webhook | Make.com Custom Webhook gen2 | Pattern identique à scenario 9085048 |
| Storage | Supabase Storage bucket `symbols-private` | Projet `czxefyiqxgpstdtydnfl` Zurich existant |
| Anonymisation | `pg_hashids` extension + salt dans Vault | Extension dispo, à activer |
| Vision LLM | Mistral Pixtral Large (primaire) + Claude Sonnet 4.7 (fallback) | 2 API keys dans Supabase Vault à provisionner |
| Audit DB | Table `symbol_translations` + RLS | Projet existant, schéma à migrer |
| Notion mirror | MCP Notion teamspace SVLBH | Hub Legal page existante |

### 3.3 Décisions architecture (ADR-mini)

**D1 — Webhook dédié vs réutilisation 9085048** : DÉDIÉ (choix Patrick). Rationale : isolation du flux DM-v03-P3 (qui est un middleware audit Z2 différent), facilite kill-switch, métriques séparées, et permet rollout indépendant.

**D2 — Stockage image source** : Supabase Storage privé + RLS, **pas** local repo ni `user/.../heritages-transgen`. Rationale : multi-device + RGPD conforme nLPD-first + RLS par consultante. **Bloquant : PO-07 Pro upgrade** (PITR + Network restrictions exigés avant traitement données personnelles à grande échelle).

**D3 — LLM Vision** : appel via **sub-processor Make.com** (DPA Celonis signé 2026-04-20 couvre la chaîne). Pas de DPA direct VLBH↔fournisseur. **Modèle v0.1 : Mistral Pixtral Large** (RGPD-first UE, français natif, ~0.0015 $/image). **Fallback Claude Sonnet 4.7** activable via config Make `vision_model` si accuracy insuffisante au pack de test.

**D4 — Référentiels v0.1 = Rose des Vents + Phantom Matrix uniquement** : choix Patrick. Sephiroth et hDOM restent manuels (skills existants). Pas d'auto-correction radiesthésique : Claude n'est pas radiesthésiste — la perception finale reste à Patrick.

**D5 — Anonymisation côté Make (étape 1) avant Vision** : aucune donnée nominative ne quitte la zone Suisse. Le `consultante_id` et `patient_id` sont hashés AVANT envoi au LLM Vision (Pixtral UE / Sonnet 4.7 sub-processor Make). Le caption WhatsApp est dépersonnalisé par regex (prénoms blacklistés via `unaccent`).

**D6 — Seuil de confiance 85%** : aligné mémoire `feedback_seuil_confiance_85.md`. Sous 85% → escalade Patrick obligatoire, **pas** d'envoi auto à la consultante.

---

## 4. Schéma de données Supabase

### 4.1 Table `symbol_translations`

```sql
create table public.symbol_translations (
  id              uuid primary key default gen_random_uuid(),
  created_at      timestamptz not null default now(),

  -- Identifiants pseudonymisés (pg_hashids appliqué au SVLBH_Identifier, jamais clair)
  -- consultante_hash = pg_hashids(svlbh_identifier_consultante, salt) — UUID pivot Blueprint §4
  -- patient_hash     = pg_hashids(svlbh_identifier_patient, salt) si patient existe en SVLBH, sinon NULL
  consultante_hash    text not null,
  patient_hash        text,

  -- Source
  source_bridge       text not null check (source_bridge in ('wa_z1','wa_z2et3','wa_za')),
  whatsapp_msg_id     text,
  storage_path        text not null,         -- symbols/{consultante_hash}/...
  mime_type           text not null,
  bytes               int  not null,

  -- Vision raw
  vision_model        text not null,         -- ex: 'pixtral-large-latest' | 'claude-sonnet-4-7'
  vision_raw_json     jsonb not null,
  caption_anonymized  text,

  -- Mapping Rose des Vents
  rdv_direction       text,                  -- 'NNE','NE','ENE',...
  rdv_angle_deg       numeric(5,2),          -- 0.00 - 360.00
  rdv_quadrant        text check (rdv_quadrant in ('Q I','Q II','Q III','Q IV','Q V')),
  rdv_plan            text check (rdv_plan in ('sagittal','coronal','transverse')),
  rdv_transgression   text,                  -- 'abus/viol' | 'meurtre/vol' | 'aucune'
  rdv_association     text,                  -- 'Qliphoth', 'Endométriose', etc.

  -- Mapping Phantom Matrix
  pm_level            text,                  -- 'D1'..'D11'
  pm_porte            text,                  -- 'nuque','plexus','sacrum','coeur','sommet'
  pm_porte_acupoint   text,                  -- 'GV16','CV12',...
  pm_zi_wu_window     text,                  -- '01h-03h', etc.

  -- Sortie
  whatsapp_draft_fr   text,
  markdown_summary    text,
  confidence_score    numeric(3,2) not null check (confidence_score between 0 and 1),
  auto_sent           boolean not null default false,

  -- Audit RGPD
  consent_caption     text,                  -- mention RSK-6 jointe à la consultante
  purge_at            timestamptz not null default (now() + interval '90 days')
);

-- RLS : chaque consultante ne voit que ses propres lignes
alter table public.symbol_translations enable row level security;

create policy consultante_self_read on public.symbol_translations
  for select using (consultante_hash = current_setting('app.consultante_hash', true));

-- Index opérationnels
create index on public.symbol_translations (consultante_hash, created_at desc);
create index on public.symbol_translations (purge_at) where auto_sent = false;
create index on public.symbol_translations using gin (vision_raw_json);
```

### 4.2 Bucket Storage

```
Bucket : symbols-private
Public  : false
RLS     : enforced (policy : consultante_hash = path[1])
Lifecycle pg_cron : DELETE storage.objects WHERE created_at < now() - interval '90 days'
```

### 4.3 Vault secrets

```
vault.secrets:
  - mistral_pixtral_api_key   (rotation 90j) — primaire
  - anthropic_sonnet_api_key  (rotation 90j) — fallback
  - hashids_salt            (jamais rotated)
  - whatsapp_bridge_tokens  (3 entries : wa_z1, wa_z2et3, wa_za)
```

---

## 5. Prompt Vision (figé v0.1)

```
SYSTÈME

Tu es un assistant de pré-décodage symbolique pour la pratique VLBH (Vibrational
Light Body Healing). Tu reçois une image envoyée par une consultante VLBH
formée. Ton rôle est UNIQUEMENT de décrire et structurer ce que tu observes
dans le cadre de DEUX référentiels :

  1. Rose des Vents du Hara (12 directions, 3 plans, 4 quadrants)
  2. Phantom Matrix (11 niveaux dimensionnels D1–D11, 5 portes énergétiques)

Tu ne poses pas de diagnostic médical. Tu ne fais pas de recommandation
thérapeutique. Tu ne fais pas de radiesthésie : la perception finale reste
à la consultante humaine.

CONTRAINTES STRICTES

- Sortie : JSON strict suivant le schéma fourni. Aucune prose hors JSON.
- Si l'image ne contient PAS un symbole interprétable dans ces référentiels,
  retourne `{"interpretable": false, "reason": "..."}`.
- Confiance : note de 0.0 à 1.0 sur ta certitude d'interprétation. Sous 0.6,
  privilégie `interpretable: false`.
- Aucune donnée nominative dans la sortie : pas de prénom, pas de lieu, pas
  d'âge mentionné même si visible dans l'image.

SCHÉMA DE SORTIE

{
  "interpretable": boolean,
  "reason": "string optionnel si interpretable=false",
  "description_fr": "1-3 phrases descriptives neutres",
  "rose_des_vents": {
    "detected": boolean,
    "direction": "N|NNE|NE|ENE|E|ESE|SE|SSE|S|SSO|SO|OSO|O|ONO|NO|NNO",
    "angle_deg": float,
    "quadrant": "Q I|Q II|Q III|Q IV|Q V",
    "plan": "sagittal|coronal|transverse",
    "transgression": "abus/viol|meurtre/vol|aucune",
    "association": "string libre courte",
    "rationale": "1 phrase pourquoi cette direction"
  },
  "phantom_matrix": {
    "detected": boolean,
    "level": "D1|D2|...|D11",
    "porte": "nuque|plexus|sacrum|coeur|sommet|aucune",
    "porte_acupoint": "GV16|CV12|GV4|CV17|GV20|null",
    "zi_wu_window": "23h-01h|01h-03h|...|aucune",
    "type_parasite": "string libre courte",
    "rationale": "1 phrase pourquoi ce niveau"
  },
  "confidence": float
}

CONTEXTE FOURNI

- Caption (texte WhatsApp anonymisé) : {caption_anonymized}
- Heure d'envoi (utile pour Zi Wu Liu Zhu) : {sent_at_local_tz}
- Niveau de formation consultante : {consultante_level} (T1..T4)

UTILISATEUR

[Image attachée + caption ci-dessus]
```

**Notes prompt** :
- Les valeurs autorisées de `direction`, `quadrant`, `plan`, `porte`, `porte_acupoint`, `zi_wu_window` sont exactement celles des skills `rose-des-vents-hara` et `phantom-matrix-parasites`. Source de vérité = ces skills.
- Le prompt est versionné dans Git (`docs/specs/prompts/symtrans-vision-v0.1.md`) pour tracking des évolutions.
- Évaluations : pack de 30 images de test à constituer (15 Rose des Vents, 10 Phantom Matrix, 5 inintelligibles) pour mesurer accuracy avant production.

---

## 6. Templates de sortie

### 6.1 WhatsApp draft FR (selon confiance)

**Confiance ≥ 85%** (envoi auto possible après validation Patrick PI-1) :

```
Bonjour {prenom_consultante},

Pré-décodage de l'image que tu m'as envoyée :

🧭 Rose des Vents : {direction} ({angle}°) — Plan {plan}, Quadrant {quadrant}
   Lecture : {transgression} — {association}

🌀 Phantom Matrix : {level} — Porte {porte} ({acupoint})
   Fenêtre Zi Wu : {zi_wu_window}

{description_fr}

À croiser avec ton ressenti radiesthésique. Si ça résonne, je te propose un
échange en visio cette semaine.

Patrick
```

**Confiance < 85%** (escalade Patrick) :

```
Bonjour {prenom_consultante},

Bien reçu ton image. Pré-lecture en cours — je te reviens dans la journée
avec mon décodage croisé.

Patrick
```

### 6.2 Markdown patient (anonymisé)

```markdown
# Décodage symbole — {date_iso} — patient_hash {patient_hash}

**Consultante** : {consultante_hash}
**Source** : WhatsApp {source_bridge}
**Confiance** : {confidence}

## Rose des Vents
- Direction : {direction} ({angle}°)
- Quadrant : {quadrant} — Plan : {plan}
- Transgression : {transgression}
- Association : {association}

## Phantom Matrix
- Niveau dimensionnel : {level}
- Porte : {porte} ({acupoint})
- Zi Wu Liu Zhu : {zi_wu_window}
- Type parasite : {type_parasite}

## Description (Vision LLM)
{description_fr}

## Pré-recommandations
- Skills VLBH à mobiliser : `rose-des-vents-hara`, `phantom-matrix-parasites`
- Croiser avec : `hdom-decoder`, `entites-familiales-s1` si SLA > 98%
```

### 6.3 JSON Make → Supabase

Direct INSERT dans `symbol_translations` (cf. §4.1).

---

## 7. RGPD / RSK-6 — Conformité

| Item | Conformité | Référence |
|---|---|---|
| Base légale | Exécution contrat (consultante) + intérêt légitime patiente (pseudonymisé) | nLPD art.6 + RGPD art.6.1.b/f |
| Catégories | **Données personnelles standard, hors Art. 9** | data-model v0.6 §3.3 + RSK-6 |
| Hébergement | Supabase Zurich eu-central-2 (CH) | Adéquate UE/CA |
| Sous-traitants | Make.com (DPA 2026-04-20) + Supabase (DPA 2026-04-19 ref KSDVA-YIVUJ-O2BST-TAMAY) + Mistral AI 🇫🇷 (sub-processor Make) + Anthropic (sub-processor Make, fallback) | Mistral natif UE, Anthropic Swiss-US DPF à vérifier (artefact F9) |
| Pseudonymisation | `pg_hashids` salt Vault, jamais d'IDs clairs sortis du périmètre | nLPD art.5(c) minimisation |
| Conservation | 90 jours, purge `pg_cron` | privacy policy v0.2.5 §4bis |
| Droits accès | RLS Supabase + procédure exercice (registre RGPD §droits) | Registre v1.0 |
| Audit | Table + GIN index → exportable pour DPIA si TR-06 active | TR-06 du registre |
| Consent caption | Mention insérée dans message d'onboarding consultante | À rédiger AP-005 (proposé) |

**À ajouter au registre RGPD art.30** :
- Nouveau traitement TR-07 « Symbol Translator — Pré-décodage symbolique consultantes »
- Mise à jour TR-06 (Middleware DM-v03-P3) pour décrire la coexistence

---

## 8. Décomposition SAFe (Epic + Features)

### Epic parent

**VIFA — Symbol Translator** | Owner : PO-07 Infra (Patrick miroir)
- Rationale : la dépendance bloquante est l'upgrade Pro Supabase + bucket privé + RLS. Le reste est consommateur.

### Features (sous-tâches Asana, multi-homées via `add_projects`)

| Feature | Owner principal | Multi-home | Effort | Sprint cible |
|---|---|---|---|---|
| F1 — Migration Supabase : extensions (pg_hashids, pg_cron, pg_net), table `symbol_translations`, RLS, bucket `symbols-private` *(pgvector retiré — décision Patrick 2026-04-20)* | PO-07 Infra | PO-09 RGPD | 1 j | **S3** (mer 29 avr → mar 12 mai 2026) |
| F2 — Vault secrets : Pixtral API key + Sonnet 4.7 fallback key, hashids salt, bridge tokens | PO-07 Infra | PO-09 RGPD | 0.5 j | **S3** |
| F3 — Scénario Make.com `VIFA-9099001` (router keyword `#symbole` sur 3 bridges existants) | PO-07 Infra | PO-08 DataQuality | 1 j | **S3** |
| F4 — Prompt Vision figé + pack 30 images de test (Pixtral Large primaire, fallback Sonnet 4.7) | PO-03 Palette | PO-08 DataQuality | 2 j | **S3** / début **S4** |
| F5 — Mapping engine (Rose des Vents + Phantom Matrix) | PO-03 Palette | — | 1.5 j | **S3** |
| F6 — Templates WhatsApp + Markdown + rejet auto si caption absente | PO-03 Palette | PO-10 RTM | 0.5 j | **S3** |
| F7 — Inscription TR-07 dans registre RGPD art.30 | PO-09 RGPD | — | 0.5 j | **S3** |
| F8 — Mention consent caption (onboarding consultantes Flavia + Anne) | PO-09 RGPD | PO-11 Onboarding | 0.5 j | **S3** |
| F9 — Confirmation chaîne sub-processor Make → Mistral / Anthropic (artefact à archiver) | PO-09 RGPD | — | 0.5 j | **S3** |
| F10 — Tests de bout-en-bout (2 consultantes pilotes : Flavia Guift + Anne Grangier Brito) | PO-08 DataQuality | PO-11 Onboarding | 1 j | **S4** (mer 13 → mar 26 mai 2026) |
| F11 — Hub Notion mirror (mode B+C : 1 page/escalade + digest hebdo dimanche) + commit Git + propagation 4 miroirs | PO-09 RGPD | — | 0.5 j | **S4** |

**Effort total** : ~9.5 j sur **S3 + S4** (réaliste si Pro upgrade fait avant fin S2 = mar 28 avril 2026).

### Bloquants externes

- **PO-07 Pro upgrade Supabase** (GID Asana `1214130459219524`) — bloquant pour F1, F2, F3
- **Artefact sub-processor chain Mistral + Anthropic** (F9) — bloquant pour go-live F10

---

## 9. Test plan

### 9.1 Pack d'évaluation (30 images)

| Catégorie | Nb | Source |
|---|---|---|
| Rose des Vents tracée à la main par Patrick | 10 | Patrick |
| Schéma Phantom Matrix annoté | 8 | Patrick |
| Photo de zone corporelle (parties du corps) | 5 | Patrick |
| Dessin libre patient (mandala / schéma) | 4 | Anonymisé archive |
| Image inintelligible (test rejet) | 3 | Web aléatoire |

**Métriques** :
- Accuracy direction Rose des Vents : ≥ 80% sur 10 images de test
- Accuracy niveau Phantom Matrix : ≥ 75% sur 8 images
- Faux positifs (interpretable=true alors que ne devrait pas) : ≤ 10%
- Latence p95 : ≤ 12 s end-to-end

### 9.2 Pilotes Z2 + ZA

- 2 consultantes pilotes (Flavia Guift + Anne Grangier Brito, via PO-11 Onboarding) sur 2 semaines (S4 = mer 13 → mar 26 mai 2026)
- Métriques humaines : taux de validation par Patrick après pré-décodage (cible ≥ 70% des envois ≥85% confiance déclenchent envoi auto sans correction)

### 9.3 Tests RGPD

- Vérifier purge automatique à 90 j (test pg_cron sur ligne synthétique back-datée)
- Vérifier RLS : se connecter en tant que consultante A, tenter SELECT sur lignes consultante B → doit échouer
- Vérifier qu'aucun ID nominatif ne fuit vers Mistral / Anthropic (logs Make + intercept)

---

## 10. Score de confiance pre-flight (4 × 25%)

| Critère | Score | Commentaire |
|---|---|---|
| Compréhension besoin | 23/25 | Univers symboles très large mais 2 référentiels cibles précis |
| Architecture cible | 23/25 | Make + Supabase + Vision = pattern éprouvé ; bloquant PO-07 connu |
| Format I/O | 22/25 | Triple sortie validée ; templates à itérer avec usage réel |
| Référentiels mapping | 20/25 | Rose des Vents bien défini ; Phantom Matrix plus subjectif → calibration via pack test |
| **Total** | **94/100** | ✅ ≥ 85% (révisé 2026-04-20 après tranchage des 10 open questions) |

---

## 11. Open questions (à trancher avec Patrick avant implémentation)

1. ~~**DPA OpenAI** : signer un DPA direct VLBH ↔ OpenAI, ou rester sub-processor via Make ?~~ **TRANCHÉ 2026-04-20 : sub-processor via Make** (DPA Celonis du 2026-04-20 couvre la chaîne).
2. ~~**Modèle Vision** : pas nécessairement OpenAI.~~ **TRANCHÉ 2026-04-20 : Pixtral Large par défaut v0.1, fallback Claude Sonnet 4.7** si accuracy insuffisante au pack de test. Routage défini en config Make (variable `vision_model`).
3. ~~**Whitelist consultantes** pilotes ?~~ **TRANCHÉ 2026-04-20 : Flavia Guift + Anne Grangier Brito** (les 2 consultantes pilote v0.1, F10 ajusté).
4. ~~**Trigger mode** : nouveau bridge dédié ou keyword sur bridge existant ?~~ **TRANCHÉ 2026-04-20 : keyword `#symbole` sur les 3 bridges existants** (wa_z1, wa_z2et3, wa_za). Pas de provisioning bridge supplémentaire. Le router Make filtre `caption.contains("#symbole")` avant d'invoquer le pipeline.
5. ~~**Caption obligatoire ?**~~ **TRANCHÉ 2026-04-20 : OUI obligatoire** — l'image seule est rejetée par le webhook (réponse WhatsApp auto : « Merci d'ajouter une légende décrivant ce que tu observes »).
6. ~~**Notion mirror** : 3 modes possibles, à trancher.~~ **TRANCHÉ 2026-04-20 : combinaison C + B** — page Notion individuelle créée à chaque escalade (confiance < 85%) + digest hebdo agrégé du dimanche soir avec métriques accuracy et top-N motifs récurrents.
7. ~~**Sephiroth + hDOM** : hors v0.1 ?~~ **TRANCHÉ 2026-04-20 : hDOM hors v0.1, ajout planifié v0.3.** Sephiroth reste hors scope sans date de réintroduction (skill manuel Patrick conservé).
8. ~~**Renaming** : codename `SYMTRANS` ou autre ?~~ **TRANCHÉ 2026-04-20 : codename `VIFA`** (ex-`SYMTRANS`). Propagé partout dans la spec, à propager dans Asana, MEMORY.md, hub Notion.
9. ~~**Formule sprint PI-1**~~ **TRANCHÉ 2026-04-20 : démarrage mercredi, 14j (mer→mar).** S2 = mer 15 → mar 28 avril 2026 ; S3 = mer 29 avr → mar 12 mai ; S4 = mer 13 → mar 26 mai. Numéros absolus restaurés dans la décomposition §8.
10. ~~**pgvector embeddings** : oui/non ?~~ **TRANCHÉ 2026-04-20 : NON.** Pas d'embeddings stockés. Extension `vector` retirée de la migration F1. Recherche inter-consultantes restera manuelle / SQL textuel sur `vision_raw_json` (GIN index suffit). Évite tout risque de réidentification indirecte par embedding.

---

## 11bis. Alternatives Vision (Open Q #2)

Tableau comparatif des modèles Vision multimodaux compatibles avec un appel via Make.com (HTTP/Vision module ou wrapper API), tous via sub-processor (DPA Make Celonis 2026-04-20) :

| Modèle | Fournisseur | Coût/image (estim.) | Hébergement | Forces VLBH | Limites VLBH |
|---|---|---|---|---|---|
| **Mistral Pixtral Large** | Mistral AI 🇫🇷 | ~0.0015 $ | UE (Paris) | RGPD-first natif, **français langue mère**, alignement nLPD parfait, sub-processor EU | OCR moins mature que GPT/Claude, peu de retours sur symboles ésotériques |
| **Claude Sonnet 4.6 Vision** | Anthropic 🇺🇸 | ~0.003 $ | US/EU selon endpoint | Excellent description nuancée, suit instructions FR très bien, zero-retention dispo, **Anthropic = sub-processor de Cowork déjà** | DPF Anthropic à vérifier (Swiss-US bridge) |
| **Claude Opus 4.6 Vision** | Anthropic 🇺🇸 | ~0.015 $ | idem | Top accuracy nuance + raisonnement multimodal | 5× plus cher, latence ~6s |
| **GPT-4o** (gpt-4o-2024-11-20) | OpenAI 🇺🇸 | ~0.01 $ | US (zero-retention possible) | Function calling structured output natif (sortie JSON garantie) | Coût moyen, OpenAI Swiss-US DPF à vérifier |
| **GPT-4.1** | OpenAI 🇺🇸 | ~0.012 $ | idem | Meilleure accuracy générale, idem function calling | Idem |
| **Gemini 2.5 Pro Vision** | Google 🇺🇸 | ~0.0025 $ | US/EU/Asie | 1M tokens contexte, OCR excellent (utile kanjis MTC), DPA Workspace EU | Sortie JSON moins fiable, latence variable |
| **Qwen2-VL 72B** | Alibaba 🇨🇳 | API : ~0.002 $ | Chine — **bloquant nLPD** | Performant kanji 鬼神氣, multilingue | **Hors UE/CH** → exclu RGPD/nLPD-first |
| **Llama 3.2 Vision 90B** | Meta (open weights) | self-host : infra | UE possible (Hetzner/OVH) | Contrôle 100%, contournement DPF, customisable | Infra à monter + maintenance, pas natif Make.com |
| **Pixtral 12B local** | Mistral (open weights) | self-host : infra | CH possible | Souveraineté max | Idem, pas natif Make.com |

**Recommandation par critère** :

| Critère prioritaire | Modèle conseillé |
|---|---|
| RGPD/nLPD-first **strict** | **Mistral Pixtral Large** (UE-native, français mère) |
| Meilleure qualité brute | **Claude Opus 4.6 Vision** ou **GPT-4.1** |
| Meilleur ratio qualité/prix | **Mistral Pixtral Large** ou **Claude Sonnet 4.6** |
| Sortie JSON la plus fiable | **GPT-4o** (function calling natif) |
| Souveraineté absolue | Self-host **Pixtral 12B** sur infra CH/UE |

**Recommandation Patrick (à arbitrer)** : *Mistral Pixtral Large* en v0.1 (alignement nLPD-first du stack legal + français natif + coût bas + pas de Swiss-US DPF à vérifier). Si accuracy insuffisante sur pack test, fallback **Claude Sonnet 4.6 Vision**. GPT garde l'avantage du function calling, mais on peut le simuler en post-processing JSON sur Pixtral.

---

## 11ter. Notion mirror — reformulation Open Q #6

La question initiale était floue. Reformulation : **chaque décodage doit-il créer une trace dans Notion, et si oui à quelle granularité ?**

| Mode | Description | Volume Notion | Charge Patrick | Recommandation |
|---|---|---|---|---|
| **A. Journal complet** | 1 page Notion par image décodée | Élevé (toutes les images) | Faible (Notion sert d'archive) | Bon pour traçabilité maximale, mais pollue le teamspace |
| **B. Journal sélectif** | 1 page Notion uniquement quand confiance < 85% (escalades) | Faible (~15-20% des cas) | Modérée (revue ciblée) | **Recommandé v0.1** — focus sur ce qui demande ton arbitrage |
| **C. Journal hebdo agrégé** | 1 page Notion / semaine résumant les N décodages + métriques accuracy | Très faible (52/an) | Faible (lecture hebdo) | Idéal pour pilotage, mais perd la traçabilité unitaire |

**Recommandation Patrick** : combiner **B + C** — page Notion individuelle pour chaque escalade (confiance < 85%), plus rapport hebdo agrégé du dimanche soir (digest cohérent avec daily-briefing du lundi matin).

---

## 12. Annexes

### 12.1 Source de vérité référentiels

- Rose des Vents : `~/.claude/skills/rose-des-vents-hara/SKILL.md` — 12 directions × 3 plans, table §"Tableau de Référence Rapide"
- Phantom Matrix : `~/.claude/skills/phantom-matrix-parasites/SKILL.md` — D1-D11 + 5 portes + Zi Wu Liu Zhu

### 12.2 Mémoires liées (auto-memory)

- `feedback_seuil_confiance_85.md` — règle des 85%
- `pre_flight.md` — checklist 4 critères
- `feedback_radiesthesie_not_medical.md` — RSK-6
- `project_supabase_dpa_signed.md` — DPA Supabase signé
- `reference_dm_v03_p3_infra.md` — pattern Make + Supabase existant
- `feedback_asana_mandatory_task_doc.md` — règle Asana obligatoire pour exécution
- `project_safe_dispatch_rule.md` — Epic chez owner, Features multi-homées via add_projects

### 12.3 Cascade de propagation post-validation

Si Patrick valide cette spec :

1. Création Epic Asana VIFA sous PO-07
2. Création F1–F11 sous-tâches multi-homées (`mcp__14e4900b...__create_tasks`)
3. Mise à jour `vlbh-energy-mcp/CLAUDE.md` (section nouvelle Symbol Translator)
4. Mise à jour `~/.claude/CLAUDE.md` (mention codename + scenario Make)
5. Mise à jour `MEMORY.md` (auto-memory) avec entrée projet
6. Création hub Notion miroir sous PO-09 (cohérent règle `feedback_notion_hub_sync_rule.md`)
7. Commit Git du présent fichier + mise à jour CLAUDE.md (cohérent règle hub)

---

## 13. Revue Compliance-by-Design (ajoutée 2026-04-20)

Cette section a été ajoutée après lecture de `blueprint-compliance-by-design.md` v0.1 (document fondateur, 2026-04-18). Elle confronte la spec VIFA v0.1 aux exigences du Blueprint et liste les écarts à arbitrer en v0.2.

### 13.0 Acronyme VIFA — précisé 2026-04-20

**`VIFA` = Vibration Fréquences Accumulation Intervalle** (nomenclature Patrick, clarifiée 2026-04-20).

L'acronyme n'a pas de conflit sémantique dans le corpus VLBH. La mention du Blueprint §6 / RSK-3 (« VIFA = auto-évaluation, pas wearable ») décrit la **nature** de la famille VIFA (mesurer/accumuler des signatures vibratoires sur un intervalle, sans appareillage wearable) — pas un produit spécifique. Le translator d'images s'inscrit pleinement dans cette famille : il accumule des signatures vibratoires (Rose des Vents, Phantom Matrix) à partir d'images transmises.

Cette section initialement ouverte comme alerte P0 (erreur d'interprétation Claude) est donc **retirée**. Pas d'action nécessaire. Le codename `VIFA` reste validé.

### 13.1 Mapping Tier (Blueprint §2)

VIFA opère sur des consultantes formées MyShamanFamily — **donc T3 (Formation) ou T4 (Pro)**. Les patientes derrière l'image sont en **T4 (Z3 géo-fragmenté)** dès lors que la consultante est certifiée Pro.

**Exigences T4 non couvertes par la spec actuelle** :

| Exigence Blueprint T4 | État spec v0.1 | Gap |
|---|---|---|
| 2FA obligatoire (consultante) | Non mentionné | À ajouter F8 ou F12 |
| **DPIA obligatoire** | Marqué "uniquement si TR-05 ou TR-06" | **TR-07 VIFA T4 = DPIA obligatoire** |
| **Geo-sharding CH/EU/CA** selon résidence patiente | **Monorégion eu-central-2 Zurich** | **Gap majeur** : router par résidence patiente, ou restreindre VIFA aux patientes CH+UE en v0.1 |
| RLS praticienne→patientes | Prévu sur consultante_hash | À étendre : RLS doit aussi isoler patient_hash par consultante |
| **Co-responsabilité art. 26 RGPD** | Non mentionné | **Contrat art. 26 obligatoire** entre Patrick (responsable principal) et chaque consultante T4 utilisant VIFA. Draft 04 disponible (§9). |
| **Backup PITR 30j chiffré** | Mentionné implicitement (Pro upgrade PO-07) | À expliciter dans F1 |
| Rétention post-fin | Spec dit "purge 90j" | **T4 = durée légale profession santé CH** (typiquement 10 ans). Conflit majeur. |

### 13.2 Régime juridique (Blueprint §3 + §7)

✅ **Conforme** : VIFA respecte RSK-6 (données radiesthésiques hors Art. 9). Pas de reclassification médicale. Vocabulaire VLBH propriétaire.

⚠️ **À préciser** : la spec doit expliciter que les données image elles-mêmes (zones corporelles photographiées) restent des **données personnelles standard non Art. 9** dès lors qu'aucune annotation médicale n'est rajoutée. Si la consultante ajoute « cancer du sein gauche » dans le caption, on bascule possiblement Art. 9. À traiter par filtre regex en pré-anonymisation.

### 13.3 SVLBH_Identifier (Blueprint §4)

**Gap** : la spec utilise un `consultante_hash` issu de `pg_hashids`. Le Blueprint §4 exige d'utiliser le **SVLBH_Identifier** (UUID pivot qui ne change jamais entre T0 et T4) comme identifiant unique.

**Action v0.2** : remplacer `consultante_hash` par `svlbh_id_consultante` (UUID Blueprint) + `svlbh_id_patient_hash` (pseudonymisé seulement, car patient peut ne pas être inscrit comme T0 SVLBH). La cohérence inter-systèmes (billing_praticien, svlbh-v2, VIFA) est prérequise.

### 13.4 Transition tier §4 — VIFA absent

VIFA n'apparaît dans aucune transition de tier du Blueprint. **À insérer en Blueprint v0.2** :

> Nouvelle ligne table §4 : `T4 (Pro) → usage VIFA` | événement = consultante envoie 1ère image #symbole | données créées = `vifa_translation` (table `symbol_translations`) | SVLBH_Identifier = consultante existante.

À porter en PR sur `blueprint-compliance-by-design.md` après validation.

### 13.5 Architecture apps §5 — VIFA pas dans la grille

VIFA n'est pas une app ASC standalone — c'est un workflow Make + LLM consommé par les apps T3/T4 (SVLBH Formation et SVLBH Pro). Il s'inscrit comme **service transverse**, à mentionner dans une nouvelle section §5bis du Blueprint :

> §5bis Services transverses : VIFA-translator, DM-v03-P3 Middleware WhatsApp, etc. Ne sont pas des apps mais des pipelines compliance-bound consommés par les tiers cibles.

### 13.6 Budget infra (ADR-05, Blueprint §6)

Enveloppe ADR-05 = CHF 200/mois. Estimation VIFA :
- Pixtral Large : ~0.0015 $/image × volume (à estimer)
- Si 100 images/mois (estim. 2 consultantes pilotes × ~50 images) : ~0.15 $/mois — négligeable
- Storage Supabase Pro : déjà couvert par PO-07
- Pas de surcoût significatif. ✅ ADR-05 respecté.

Si scaling à 1000 images/mois (10 consultantes Pro × 100 images) : ~1.5 $/mois Pixtral + bande passante Supabase à estimer. Toujours dans l'enveloppe.

### 13.7 Rétention conflit (Blueprint §3)

Spec actuelle dit `purge 90j` — alignée sur §4bis privacy policy v0.2.5 (caché middleware WhatsApp). Mais **Blueprint T4 = "Durée légale profession santé CH"** (~10 ans pour les consultations).

**Arbitrage requis** :
- Image source : 90j (non thérapeutique, juste pre-décodage technique)
- JSON décodé + Markdown (data utile au dossier patient) : durée légale profession santé CH = ~10 ans

**Proposition v0.2** : double rétention — image source purgée à 90j (pg_cron), métadonnées décodées conservées 10 ans dans `symbol_translations` avec colonne `medical_retention_until` calculée.

### 13.8 Mécanisme de consentement (Blueprint §3)

Spec dit "consent caption" + "mention onboarding consultantes". Insuffisant pour T4.

**Manquant** :
- Consentement explicite **patient** (la patiente sait qu'une photo d'elle/d'un symbole la concernant transite vers un LLM tiers)
- Acte du consentement archivé
- Mention dans le contrat thérapeutique consultante↔patient

**Action v0.2** : F8 doit produire (a) avenant au contrat thérapeutique consultante↔patient, (b) script WhatsApp pour la consultante demandant le consentement à la patiente avant 1er envoi, (c) registre des consentements dans `symbol_translations.consent_proof_id` (référence vers nouvelle table `vifa_consents`).

### 13.9 Récapitulatif — Gaps prioritaires v0.2

| Priorité | Gap | Effort estim. | Impact |
|---|---|---|---|
| 🔴 P0 | Conflit nommage VIFA (RSK-3) | 0.5 j refacto | Bloquant cascade Asana |
| 🔴 P0 | DPIA TR-07 obligatoire (T4) | 1 j rédaction | Bloquant go-live Pro |
| 🔴 P0 | Contrat art. 26 consultante↔Patrick | 0.5 j (réutilise draft 04) | Bloquant onboarding pilotes |
| 🟠 P1 | Geo-sharding ou restriction CH+UE | 1 j | Bloquant patientes CA |
| 🟠 P1 | SVLBH_Identifier vs consultante_hash | 0.5 j refacto schéma | Cohérence inter-systèmes |
| 🟠 P1 | Double rétention 90j / 10 ans | 0.5 j | Compliance santé CH |
| 🟠 P1 | Consentement patient explicite | 1 j (script + table) | Compliance T4 |
| 🟡 P2 | Filtre Art. 9 sur caption (annotations médicales) | 0.5 j | Robustesse RGPD |
| 🟡 P2 | Insertion VIFA dans Blueprint §4 + §5bis | 0.5 j PR | Cohérence doc |
| 🟡 P2 | 2FA consultante T4 | déjà PO-09 | Renforcement |

**Effort additionnel** : ~6 j → **spec v0.2 totale = ~15.5 j** (vs 9.5 j v0.1). Peut nécessiter un sprint supplémentaire S5 (mer 27 mai → mar 9 juin 2026).

### 13.10 Score de confiance révisé

Le Blueprint introduit 9 gaps. Score de confiance recalculé :

| Critère | Score v0.1 (avant Blueprint) | Score révisé |
|---|---|---|
| Compréhension besoin | 23/25 | 23/25 |
| Architecture cible | 23/25 | **17/25** (geo-sharding + SVLBH_Id manquants) |
| Format I/O | 22/25 | 22/25 |
| Référentiels mapping | 20/25 | 20/25 |
| Compliance T4 (Blueprint) | non évaluée | **15/25** (5 P0/P1 ouverts) |
| **Total révisé (5 critères × 25)** | n/a | **97/125 = 78%** |

**Statut** : ⚠️ **score retombé sous 85%** → **STOP cascade Asana**. Spec v0.2 requise avant exécution. Itération courte sur les 3 gaps P0 + arbitrage codename suffit pour repasser ≥ 85%.

---

## 14. Mapping Blueprint §5 — app T3 + arbitrages 2026-04-20

VIFA est **une des apps T3 Formation à développer** (précision Patrick 2026-04-20). L'architecture backend v0.1 (Make + Supabase + Pixtral/Sonnet + triple sortie) **reste valide telle quelle**. L'app front consommera ce backend en temps voulu.

### 14.1 Compliance T3 confirmée

- **Régime juridique** : contrat de formation pédagogique (pas contrat de soin). Pas de DPIA, pas de co-responsabilité art. 26, 2FA recommandé (pas obligatoire).
- **Rétention** : 10 ans post-formation (remplace "90j" de la spec initiale — régime simple). L'image source peut rester purgée à 90j par bonne pratique (minimisation) ; le JSON décodé + Markdown conservés 10 ans.

### 14.2 Arbitrages Patrick 2026-04-20 (débloquent la cascade)

| Gap | Décision Patrick | Impact spec |
|---|---|---|
| Geo-sharding CH/EU/CA | **T3 CH uniquement v0.1** | Monorégion Zurich confirmée. Whitelist consultantes = résidence CH. Extension v0.2+. |
| SVLBH_Identifier vs `consultante_hash` | **C'est le même concept** : `consultante_hash = pg_hashids(SVLBH_Identifier)` | Annoté dans le schéma SQL §4.1. Source du hash = UUID pivot Blueprint §4. Pas de référentiel parallèle. |

### 14.3 Score de confiance final

Critères × 25 :
- Compréhension : 24 (T3 CH, SVLBH_Id clarifié)
- Architecture : 22 (backend confirmé, monorégion v0.1)
- Format I/O : 22
- Référentiels : 20
- Compliance T3 : 23 (régime simple, gaps tranchés)
- **Total : 111/125 = 89%** ✅ ≥ 85%

**Statut** : ✅ **Cascade Asana débloquée**. Spec v0.1 prête pour exécution.

---

**Fin de spec v0.1 + Revue Blueprint + Mapping T3 + Arbitrages 2026-04-20** — Prêt pour cascade Asana sur S3 (29 avr → 12 mai 2026).
