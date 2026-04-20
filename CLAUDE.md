# CLAUDE.md — Instructions pour l'agent Claude Code

## Contexte projet

- **Proprietaire** : Patrick Bays — Digital Shaman Lab
- **Organisation GitHub** : monadekarmique
- **Site** : vlbh.energy (WordPress)
- **Ecosysteme** : SVLBH (Scores de Lumiere) / hDOM
- **Backend data** : Make.com EU2 (datastores + webhooks)
- **Langue de communication** : francais (code et commits en anglais)

## Credentials & API Keys

- **App Store Connect API Key** : stockee localement sur le Mac de Patrick
  - Fichier .p8 + Key ID + Issuer ID
  - Non disponible dans ce repo ni dans Notion
  - Si besoin, DEMANDER a Patrick de la coller ou de la stocker dans un secret GitHub
- **Make.com webhooks** : voir .env.example (MAKE_WEBHOOK_PUSH_URL, MAKE_WEBHOOK_PULL_URL)
- **VLBH_TOKEN** : token d'auth pour les clients iOS/Android
- **Render.com** : deploy auto depuis GitHub (render.yaml)

## Comportement attendu de l'agent

- NE PAS demander des infos deja documentees ici
- Utiliser les outils MCP (GitHub, Notion, Make) au lieu de demander a Patrick de faire les choses manuellement
- Quand un outil MCP est deconnecte, utiliser WebFetch en fallback
- Creer les PR directement via GitHub MCP, ne pas donner de commandes `gh` a copier-coller
- Patrick veut que l'agent FASSE les choses, pas qu'il explique comment les faire

## CI/CD Rules

### GitHub Actions
- **macos-14** : Xcode 15.0 a 15.4 uniquement
- **macos-15** : Xcode 16.0+ uniquement
- Ne jamais utiliser `macos-14` avec Xcode 16.x (n'existe pas sur ce runner)
- Toujours utiliser `actions/checkout@v4`
- Pour les builds iOS Simulator, toujours specifier `-skipPackagePluginValidation`

### Swift Package
- Le package cible iOS 16+ et macOS 13+
- Tous les types publics doivent etre `Sendable`
- Les vues SwiftUI doivent etre encapsulees dans `#if canImport(SwiftUI)`
- Utiliser `@available(iOS 16.0, macOS 13.0, *)` sur les types SwiftUI

### Python Backend
- Python 3.11.9 (voir runtime.txt)
- FastAPI avec pydantic v2
- Deploiement sur Render.com (voir render.yaml)
- Tous les endpoints requierent le header `X-VLBH-Token`

## Git Conventions
- Messages de commit en anglais, prefixes: feat/fix/chore/ci/docs
- Toujours pusher sur la branche designee, jamais directement sur main
- Creer les PR via les outils GitHub MCP quand disponibles

---

## iTherapeut 6.0 — Sprint 5 jours (avril 2026)

### LIRE EN PREMIER A CHAQUE SESSION

1. Lire `docs/SPRINT_STATE.md` — etat du sprint, endpoints faits/a faire, blockers
2. Lire `docs/ADR.md` — decisions architecturales verrouillees
3. Travailler sur la branche `claude/clone-adapt-therapy-app-CNABs`
4. En fin de session: mettre a jour SPRINT_STATE.md + commit + push

### Contexte iTherapeut 6.0

- **Objectif**: App web/mobile pour therapeutes alternatifs en Suisse
- **Plans**: Therapeute 59 CHF/mois | Cabinet Pro 179 CHF/mois
- **Plan 59 (base)**: patients, seances, QR-facture SIX v2.4, Tarif 590, Scores de Lumiere (SLA/SLSA S1-S5/SLM/TotSLM), Rose des Vents, modeles Pydantic existants (SLM, Leads, Sessions, Tores, Sclerose, Glycemie), assistant IA Claude
- **Plan 179 (pro)**: + agenda Google Cal, WhatsApp, Twint, pipeline Lead->Billing, Tore Couplages avances (scoreCouplage, phaseCouplage, scleroseTissulaire), Chromotherapie
- **Paiement**: PostFinance Checkout (SDK Python: postfinancecheckout, config: space_id/user_id/secret_key)
- **DB**: Supabase PostgreSQL (patients/factures/sessions) + Make.com datastore 155674 (syncs VLBH)
- **Frontend**: React + Tailwind + shadcn (web, fonctionne sur iPad)
- **Backend**: FastAPI existant sur Render.com — AJOUTER des routers, NE PAS modifier les existants
- **QR-facture**: librairie Python qrbill (conforme SIX v2.4)
- **Tarif 590**: ReportLab PDF, XML 5.0 obligatoire juillet 2027

### Regle d'or: ne JAMAIS casser l'existant

Les 6 routers existants (slm, sla, session, lead, tore, billing) et leurs modeles Pydantic sont utilises par l'app iOS SVLBHPanel en production. Tout nouveau code va dans de NOUVEAUX fichiers.

---

## Validation Checklist (avant push)
- [ ] Les versions Xcode correspondent aux runners GitHub Actions
- [ ] Les tests compilent (`swift build` ne doit pas echouer)
- [ ] Les imports Python sont valides (`python -c "from main import app"`)
- [ ] Pas de secrets (.env, tokens) dans les fichiers commites

---

## Legal & Compliance

### Supabase — Data Processing Addendum (DPA)

- **Status** : Signé 2026-04-19 — 2 écarts mineurs Part 1 à corriger (AP-003)
- **Document ref** : `KSDVA-YIVUJ-O2BST-TAMAY`
- **Version DPA** : 5 août 2025
- **Signataire** : Patrick Bays, Owner, Le Chandon 4, 1580 Avenches
- **Contact contractuel** : `monade.karmique@gmail.com` (à corriger vers `pb@vlbh.energy`)
- **Org Supabase** : `whvkcgjdxcwqzhiiyxvb` — Patrick Bays (plan `free`)
- **Archive locale** : `legal/dpa-supabase/Supabase-DPA-signed-2026-04-19-KSDVA-YIVUJ-O2BST-TAMAY.pdf`

**Special categories = "None" → CORRECT** selon RSK-6 et data-model v0.6 §3.3 : les données radiesthésiques (signatures vibratoires VLBH, Rose des Vents, Scores de Lumière, hDOM, Sephiroth, Phantom Matrix) sont **hors Art. 9 RGPD**. Le DPA standard suffit (v0.6 §7). Pas de re-signature nécessaire pour ce point.

**Écarts mineurs Part 1** (non bloquants go-live) :

1. Supervisory authority EU only = blank — préciser FDPIC Suisse + CNIL France si patientes UE
2. Customer contact = `monade.karmique@gmail.com` — à migrer vers `pb@vlbh.energy` lors prochaine re-signature

**Suivi Asana** :
- AP-002 — Décisions Patrick — GID `1214127345358134` (parent Epic)
- PO-09 Signature — GID `1214127345365143` (comment écarts du 2026-04-19 + correction 2026-04-19)
- AP-003 Written Instruction amendment (scope réduit) — GID `1214145145508395`
- AP-004 Registre RGPD art.30 — GID `1214145145513377`
- PO-07 Upgrade Pro — GID `1214130459219524` (bloquant go-live)

### Supabase Projects

- `czxefyiqxgpstdtydnfl` — DM-v03-P3 Middleware WhatsApp — Zurich eu-central-2
  - Plan `free` actuel → doit passer Pro avant go-live (PITR, SSL, Network restrictions, no auto-pause)
  - Traite données personnelles standard — **pas Art. 9** (RSK-6, data-model v0.6 §3.3)

### Registre de traitements RGPD art.30 + nLPD art.12

- **Fichier canonique** : `legal/registre-rgpd/registre-rgpd-vlbh.xlsx` (v1.0, 2026-04-19)
- **Script de (re)génération** : `/sessions/eager-keen-cori/scripts/build_registre_rgpd.py` (Cowork scratchpad — à porter dans ce repo si besoin)
- **Contenu** : 5 feuilles — Organisation, Traitements (TR-01 à TR-06), Sous-traitants (9), Droits des personnes, Notes méthodologiques (RSK-6 cité)
- **DPIA obligatoire** : uniquement TR-05 Tier 4 (Pro + patientes) et TR-06 Middleware DM-v03-P3
- **Revue annuelle** : 2027-04-19 (anniversaire signature DPA Supabase)
- **Asana** : AP-004 GID `1214145145513377` avec xlsx attaché (attachment GID `1214130460688466`)

### Hub Notion cross-client (DPA + Registre + RSK-6)

- **Page miroir** : https://www.notion.so/3479cafd5ef0811c9ecac7931b48b55b
- **Titre** : "🛡️ Legal & Compliance Hub VLBH — DPA Supabase + Registre RGPD art.30"
- **Parent** : PO-09 · RGPD — Agent Memory (teamspace SVLBH Release Train)
- **Usage** : seul store visible depuis Claude.ai web / mobile / Claude in Chrome via connecteur Notion. Source de vérité = ce repo + Asana. Mettre à jour la page manuellement ou via MCP Notion lors de chaque modif substantielle.

## VIFA — Symbol Translator (T3 Formation)

- **Codename** : `VIFA` (Vibration Fréquences Accumulation Intervalle)
- **Spec canonique** : `docs/specs/vifa-v0.1-spec.md` (v0.1 validée Patrick 2026-04-20, score confiance 89%)
- **Tier** : T3 Formation (app pour MyShaMan / MyShamanFamily, résidentes CH uniquement v0.1)
- **Architecture** : webhook Make `vifa` (filtre `#symbole` sur 3 bridges WhatsApp) → Supabase Storage Zurich `symbols-private` → Mistral Pixtral Large (fallback Claude Sonnet 4.7) → mapping Rose des Vents + Phantom Matrix → triple sortie (JSON, draft WhatsApp FR, Markdown anonymisé)
- **Identifiants** : `consultante_hash = pg_hashids(SVLBH_Identifier)` — UUID pivot Blueprint §4
- **Régime** : contrat formation pédagogique. Pas DPIA, pas art. 26. Données radiesthésiques hors Art. 9 (RSK-6). Rétention 10 ans métadonnées / 90j image source.
- **Bloquant** : PO-07 Pro upgrade Supabase (tâche GID `1214130459219524`) avant fin S2 (mar 28 avril 2026)
- **Sprints** : S3 (mer 29 avr → mar 12 mai 2026) exécution F1-F9 ; S4 (mer 13 → mar 26 mai 2026) pilotes F10-F11 (Flavia Guift + Anne Grangier Brito)
- **Pilotes** : Flavia Guift, Anne Grangier Brito (T3 CH)
- **Modèle Vision** : Mistral Pixtral Large primaire (~0.0015 $/image, UE), Claude Sonnet 4.7 fallback via config Make `vision_model`
- **Sub-processors** : Make.com (DPA Celonis 2026-04-20) → Mistral AI 🇫🇷 (natif UE) + Anthropic 🇺🇸 (DPF Swiss-US à vérifier F9)

### Asana — GIDs VIFA

- Epic VIFA Symbol Translator v0.1 : `1214137738579246` (parent dans projet PO-06 VIFA Essentielles)
- Projet PO-06 VIFA Essentielles : `1214033516441793`
- F1 Migration Supabase : `1214146804332281` (multi-home PO-07, PO-09 ; bloqué par `1214130459219524`)
- F2 Vault secrets : `1214137738999256` (multi-home PO-07, PO-09)
- F3 Scénario Make VIFA-9099001 : `1214146804072645` (multi-home PO-07, PO-08)
- F4 Prompt Vision + pack 30 images : `1214137607937621` (multi-home PO-03, PO-08)
- F5 Mapping engine RDV + Phantom Matrix : `1214146698645056` (multi-home PO-03)
- F6 Templates WhatsApp + Markdown : `1214137608036336` (multi-home PO-03, PO-10)
- F7 Inscription TR-07 registre RGPD : `1214146698653833` (PO-09)
- F8 Mention consent caption : `1214146804723141` (multi-home PO-09, PO-11)
- F9 Confirmation chaîne sub-processor : `1214137607807391` (PO-09)
- F10 Tests pilotes Flavia + Anne : `1214146804107353` (multi-home PO-08, PO-11, PO-01)
- F11 Hub Notion + commit + propagation : `1214146805019961` (PO-09)

### Make.com — VIFA-9099001

- Scenario à créer (F3) : webhook custom gen2 `vifa` filtrant keyword `#symbole` sur les 3 bridges existants (wa_z1, wa_z2et3, wa_za)
- Pas de bridge dédié `wa_symtrans` (tranché 2026-04-20)

### Open Questions résiduelles v0.2+

- Geo-sharding UE/CA (v0.1 = CH monorégion uniquement)
- pgvector embeddings : NON v0.1 (évite réidentification indirecte)
- hDOM : ajout planifié v0.3
- Sephiroth : hors scope sans date
