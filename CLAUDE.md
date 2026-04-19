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
