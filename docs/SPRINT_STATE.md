# SPRINT STATE — iTherapeut 6.0 (5 jours)

> **CE FICHIER EST LA SOURCE DE VERITE.**
> Chaque session Claude DOIT lire ce fichier en premier et le mettre a jour en fin de session.
> Format: etat actuel + ce qui a ete fait + ce qui reste + decisions prises.

## Etat global

| Jour | Statut | Date |
|------|--------|------|
| J1 — Fondations (DB + API + QR-facture) | DONE | 2026-04-08 |
| J2 — Tarif 590 + Scores + Rose des Vents | EN ATTENTE | |
| J3 — Finition plan 59 + debut plan 179 | EN ATTENTE | |
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
| `POST /invoices/{id}/twint` | POST | TwintLink | routers/invoice.py | 179 | J3 | TODO |
| `GET /stats/dashboard` | GET | DashboardStats | routers/stats.py | 59 | J3 | TODO |
| `POST /tarif590/generate` | POST | Tarif590PDF | routers/tarif590.py | 59 | J2 | TODO |
| `POST /auth/register` | POST | — | Supabase Auth | tous | J4 | TODO |
| `POST /auth/magic-link` | POST | — | Supabase Auth | tous | J4 | TODO |
| `GET /pipeline/leads` | GET | PipelineView | routers/pipeline.py | 179 | J3 | TODO |
| `PUT /pipeline/leads/{id}` | PUT | PipelineUpdate | routers/pipeline.py | 179 | J3 | TODO |

## Decisions prises en cours de sprint

> Ajouter ici toute decision prise PENDANT le sprint (pas dans ADR.md qui est pour les decisions architecturales).

- J1: Supabase client via lru_cache singleton (services/supabase_client.py)
- J1: Invoice numbers auto-generated as ITH-YYYY-NNNN
- J1: QR-bill returns SVG (native qrbill library output) — PDF conversion possible en J2 si besoin
- J1: main.py updated to v2.0.0, 4 new routers added after existing ones
- J1: Structured addresses only (SIX v2.4 mandatory since Nov 2025) — no combined address support
- J1: RLS disabled for now (will be enabled J4 with Supabase Auth)

## Blockers / Questions ouvertes

- [ ] Patrick a-t-il un compte PostFinance e-Commerce? (necessaire J4)
- [ ] Export CSV depuis FileMaker: Patrick doit le faire manuellement (le Runtime ne supporte pas l'export programmatique)
- [ ] Domaine final: app.itherapeut.ch ou app.vlbh.energy/itherapeut?
- [x] Compte Supabase: a creer J1 matin — SUPABASE_URL et SUPABASE_SERVICE_KEY requis dans .env

## Fin de session — Checklist handover

A faire a CHAQUE fin de session Claude:

1. `git add docs/SPRINT_STATE.md && git commit -m "chore: update sprint state [JX end]"`
2. Mettre a jour le tableau "Etat global" avec le statut du jour
3. Mettre a jour le registre API (marquer les endpoints DONE)
4. Mettre a jour la liste "Fichiers crees / modifies"
5. Ajouter les decisions prises dans la section "Decisions en cours de sprint"
6. Push la branche
