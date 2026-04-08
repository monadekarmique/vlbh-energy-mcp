# SPRINT STATE — iTherapeut 6.0 (5 jours)

> **CE FICHIER EST LA SOURCE DE VERITE.**
> Chaque session Claude DOIT lire ce fichier en premier et le mettre a jour en fin de session.
> Format: etat actuel + ce qui a ete fait + ce qui reste + decisions prises.

## Etat global

| Jour | Statut | Date |
|------|--------|------|
| J1 — Fondations (DB + API + QR-facture) | DONE | 2026-04-08 |
| J2 — Tarif 590 + Scores + Rose des Vents | DONE | 2026-04-08 |
| J3 — Finition plan 59 + debut plan 179 | DONE | 2026-04-08 |
| J4 — Tore Couplages + Chromo + Auth | EN ATTENTE | |
| J5 — Deploy + tests + mobile | EN ATTENTE | |

## Branche Git

`claude/clone-adapt-therapy-app-CNABs`

## Fichiers crees / modifies

| Fichier | Statut | Jour |
|---------|--------|------|
| docs/ADR.md | CREE | J0 (prep) |
| docs/SPRINT_STATE.md | CREE | J0 (prep) |
| services/supabase_client.py | CREE | J1 |
| models/patient.py | CREE | J1 |
| models/therapy_session.py | CREE | J1 |
| models/invoice.py | CREE | J1 |
| routers/patient.py | CREE | J1 |
| routers/therapy_session.py | CREE | J1 |
| routers/invoice.py | CREE | J1 |
| routers/qrbill.py | CREE | J1 |
| docs/001_create_tables.sql | CREE | J1 |
| main.py | MODIFIE | J1 |
| requirements.txt | MODIFIE | J1 |
| models/tarif590.py | CREE | J2 |
| routers/tarif590.py | CREE | J2 |
| models/scores.py | CREE | J2 |
| routers/scores.py | CREE | J2 |
| models/rose_des_vents.py | CREE | J2 |
| routers/rose_des_vents.py | CREE | J2 |
| docs/002_j2_tables.sql | CREE | J2 |
| main.py | MODIFIE | J2 |
| models/stats.py | CREE | J3 |
| routers/stats.py | CREE | J3 |
| models/twint.py | CREE | J3 |
| routers/twint.py | CREE | J3 |
| models/pipeline.py | CREE | J3 |
| routers/pipeline.py | CREE | J3 |
| docs/003_j3_tables.sql | CREE | J3 |
| main.py | MODIFIE | J3 |

## API Contract Registry

> Tout endpoint cree est documente ici. NE JAMAIS modifier un endpoint existant sans mettre a jour ce registre.

### Endpoints EXISTANTS (NE PAS TOUCHER)

| Route | Methode | Modele | Router |
|-------|---------|--------|--------|
| `/slm/push` | POST | SLMPushRequest | routers/slm.py |
| `/slm/pull` | POST | SLMPullResponse | routers/slm.py |
| `/sla/push` | POST | SLAPushRequest | routers/sla.py |
| `/sla/pull` | POST | SLAPullResponse | routers/sla.py |
| `/session/push` | POST | SessionPushRequest | routers/session.py |
| `/session/pull` | POST | SessionPullResponse | routers/session.py |
| `/lead/push` | POST | LeadPushRequest | routers/lead.py |
| `/lead/pull` | POST | LeadPullResponse | routers/lead.py |
| `/tore/push` | POST | TorePushRequest | routers/tore.py |
| `/tore/pull` | POST | TorePullResponse | routers/tore.py |
| `/billing/list` | GET | BillingListResponse | routers/billing.py |
| `/health` | GET | — | main.py |

### Endpoints NOUVEAUX (a creer J1+)

| Route | Methode | Modele | Router | Plan | Jour | Statut |
|-------|---------|--------|--------|------|------|--------|
| `POST /patients` | POST | PatientCreate | routers/patient.py | 59 | J1 | DONE |
| `GET /patients` | GET | PatientList | routers/patient.py | 59 | J1 | DONE |
| `GET /patients/{id}` | GET | Patient | routers/patient.py | 59 | J1 | DONE |
| `PUT /patients/{id}` | PUT | PatientUpdate | routers/patient.py | 59 | J1 | DONE |
| `POST /therapy-sessions` | POST | TherapySessionCreate | routers/therapy_session.py | 59 | J1 | DONE |
| `GET /therapy-sessions` | GET | TherapySessionList | routers/therapy_session.py | 59 | J1 | DONE |
| `GET /therapy-sessions/{id}` | GET | TherapySession | routers/therapy_session.py | 59 | J1 | DONE |
| `POST /invoices` | POST | InvoiceCreate | routers/invoice.py | 59 | J1 | DONE |
| `GET /invoices` | GET | InvoiceList | routers/invoice.py | 59 | J1 | DONE |
| `GET /invoices/{id}` | GET | Invoice | routers/invoice.py | 59 | J1 | DONE |
| `GET /invoices/{id}/pdf` | GET | PDF binary | routers/invoice.py | 59 | J1 | DONE |
| `POST /qrbill/generate` | POST | QRBillSVG | routers/qrbill.py | 59 | J1 | DONE |
| `POST /tarif590/generate` | POST | Tarif590PDF | routers/tarif590.py | 59 | J2 | DONE |
| `POST /tarif590/generate/json` | POST | Tarif590Response | routers/tarif590.py | 59 | J2 | DONE |
| `POST /scores` | POST | SessionScoresCreate | routers/scores.py | 59 | J2 | DONE |
| `GET /scores` | GET | SessionScoresList | routers/scores.py | 59 | J2 | DONE |
| `GET /scores/{id}` | GET | SessionScores | routers/scores.py | 59 | J2 | DONE |
| `PUT /scores/{id}` | PUT | SessionScoresUpdate | routers/scores.py | 59 | J2 | DONE |
| `GET /scores/trend/{patient_id}` | GET | ScoreTrendResponse | routers/scores.py | 59 | J2 | DONE |
| `POST /rose-des-vents` | POST | RoseDesVentsCreate | routers/rose_des_vents.py | 59 | J2 | DONE |
| `GET /rose-des-vents` | GET | RoseDesVentsList | routers/rose_des_vents.py | 59 | J2 | DONE |
| `GET /rose-des-vents/{id}` | GET | RoseDesVents | routers/rose_des_vents.py | 59 | J2 | DONE |
| `PUT /rose-des-vents/{id}` | PUT | RoseDesVentsUpdate | routers/rose_des_vents.py | 59 | J2 | DONE |
| `GET /rose-des-vents/reference` | GET | DirectionReference | routers/rose_des_vents.py | 59 | J2 | DONE |
| `GET /stats/dashboard` | GET | DashboardStats | routers/stats.py | 59 | J3 | DONE |
| `POST /invoices/{id}/twint` | POST | TwintLink | routers/twint.py | 179 | J3 | DONE |
| `GET /pipeline/leads` | GET | PipelineView | routers/pipeline.py | 179 | J3 | DONE |
| `POST /pipeline/leads` | POST | PipelineLead | routers/pipeline.py | 179 | J3 | DONE |
| `GET /pipeline/leads/{id}` | GET | PipelineLead | routers/pipeline.py | 179 | J3 | DONE |
| `PUT /pipeline/leads/{id}` | PUT | PipelineLead | routers/pipeline.py | 179 | J3 | DONE |
| `DELETE /pipeline/leads/{id}` | DELETE | — | routers/pipeline.py | 179 | J3 | DONE |
| `POST /auth/register` | POST | — | Supabase Auth | tous | J4 | TODO |
| `POST /auth/magic-link` | POST | — | Supabase Auth | tous | J4 | TODO |

## Decisions prises en cours de sprint

> Ajouter ici toute decision prise PENDANT le sprint (pas dans ADR.md qui est pour les decisions architecturales).

- J1: Supabase client via lru_cache singleton (services/supabase_client.py)
- J1: Invoice numbers auto-generated as ITH-YYYY-NNNN
- J1: QR-bill returns SVG (native qrbill library output) — PDF conversion possible en J2 si besoin
- J1: main.py updated to v2.0.0, 4 new routers added after existing ones
- J1: Structured addresses only (SIX v2.4 mandatory since Nov 2025) — no combined address support
- J1: RLS disabled for now (will be enabled J4 with Supabase Auth)
- J2: Tarif 590 numbers auto-generated as T590-YYYY-NNNN
- J2: Tarif 590 PDF via ReportLab (meme lib que invoices) — layout officiel tarif590.ch
- J2: Tarif 590 metadata stored in tarif590_invoices table (PDF streamed, not stored)
- J2: Session scores stored as JSONB (patient_scores, therapist_scores) — flexible pour evolution schema
- J2: Rose des Vents: 12 directions + N(0°) = 13 total, JSONB primary/secondary
- J2: DIRECTION_MAP static dict dans models/rose_des_vents.py — reference table pour le frontend
- J2: Endpoint /rose-des-vents/reference retourne la table complete (13 directions avec associations)
- J2: ScoreSnapshot inclut SLPMO (Score Lumiere Projet Monadique Originel) — ajout vs modele SLM existant
- J2: Endpoint /scores/trend/{patient_id} pour courbes evolution SLA/SLSA/SLPMO/SLM
- J2: main.py updated to v2.1.0, 3 new routers (tarif590, scores, rose_des_vents)
- J3: Dashboard stats = aggregation endpoint (pas de table dediee) — queries patients/sessions/invoices/scores
- J3: Twint payment links stored in twint_payments table, deep-link format twint://payment?amount=&currency=CHF
- J3: Twint URL est un deep-link P2P pour l'instant — integration PostFinance e-Commerce prevue J4 si compte dispo
- J3: Twint links expirent en 48h par defaut
- J3: WhatsApp delivery via Make.com webhook (MAKE_WEBHOOK_TWINT_URL env var)
- J3: Pipeline CRM avec 6 stages (new→contacted→scheduled→in_treatment→completed→lost)
- J3: Pipeline leads supporte sync Close CRM via close_lead_id
- J3: Pipeline GET retourne stage_counts pour affichage kanban board
- J3: Twint router monte sur /invoices/{id}/twint (sous-ressource de invoice, pas nouveau prefix)
- J3: main.py updated to v2.2.0, 3 new routers (stats, twint, pipeline)

## Blockers / Questions ouvertes

- [ ] Patrick a-t-il un compte PostFinance e-Commerce? (necessaire J4)
- [ ] Export CSV depuis FileMaker: Patrick doit le faire manuellement (le Runtime ne supporte pas l'export programmatique)
- [ ] Domaine final: app.itherapeut.ch ou app.vlbh.energy/itherapeut?
- [x] Compte Supabase: a creer J1 matin — SUPABASE_URL et SUPABASE_SERVICE_KEY requis dans .env
- [ ] Numero RCC de Patrick pour Tarif 590 par defaut?
- [ ] Migration 002_j2_tables.sql: a executer dans Supabase SQL Editor
- [ ] Migration 003_j3_tables.sql: a executer dans Supabase SQL Editor
- [ ] MAKE_WEBHOOK_TWINT_URL: a configurer dans Make.com pour envoi WhatsApp Twint

## Fin de session — Checklist handover

A faire a CHAQUE fin de session Claude:

1. `git add docs/SPRINT_STATE.md && git commit -m "chore: update sprint state [JX end]"`
2. Mettre a jour le tableau "Etat global" avec le statut du jour
3. Mettre a jour le registre API (marquer les endpoints DONE)
4. Mettre a jour la liste "Fichiers crees / modifies"
5. Ajouter les decisions prises dans la section "Decisions en cours de sprint"
6. Push la branche
