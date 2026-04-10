# SPRINT STATE — iSVLBHTherapeut 6.1 (replan, 3 jours)

> **CE FICHIER EST LA SOURCE DE VERITE.**
> Chaque session Claude DOIT lire ce fichier en premier et le mettre a jour en fin de session.
> Format: etat actuel + ce qui a ete fait + ce qui reste + decisions prises.

## Etat global — Sprint v6.0 (archive)

| Jour | Statut | Date |
|------|--------|------|
| J1 — Fondations (DB + API + QR-facture) | DONE | 2026-04-08 |
| J2 — Tarif 590 + Scores + Rose des Vents | DONE | 2026-04-08 |
| J3 — Finition plan 59 + debut plan 179 | DONE | 2026-04-08 |
| J4 — Tore Couplages + Chromo + Auth | DONE | 2026-04-08 |
| J5 — Deploy + tests + mobile | DONE | 2026-04-08 |
| POST-SPRINT — Multi-praticien | DONE | 2026-04-08 |

## Etat global — Sprint v6.1 (replan 3 jours)

| Jour | Statut | Date | Focus |
|------|--------|------|-------|
| J1 v6.1 — Apple Sign In `/auth/apple-native` | DONE | 2026-04-09 | iOS auth |
| J2 v6.1 — Multi-praticien + schema FileMaker | DONE | 2026-04-09 | practitioners router |
| J3 v6.1 — Consolidation CNABs = main + v2.5.0 | DONE | 2026-04-10 | merge, bump, tests, deploy |
| J4 v6.1 — iOS client Swift (OpenAPI codegen) | TODO | 2026-04-11 | PatientService, ScoresService, ChromoService |
| J5 v6.1 — Polish, import CSV, TestFlight v6.1.0 | TODO | 2026-04-12 | handover + TF release |

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
| models/chromo.py | CREE | J4 |
| routers/chromo.py | CREE | J4 |
| models/auth.py | CREE | J4 |
| routers/auth.py | CREE | J4 |
| models/tore_session.py | CREE | J4 |
| routers/tore_session.py | CREE | J4 |
| docs/004_j4_tables.sql | CREE | J4 |
| main.py | MODIFIE | J4 |
| Tests/conftest.py | CREE | J5 |
| Tests/test_models.py | CREE | J5 |
| Tests/test_health.py | CREE | J5 |
| Tests/test_patients.py | CREE | J5 |
| Tests/test_chromo.py | CREE | J5 |
| Tests/test_tore_sessions.py | CREE | J5 |
| Tests/test_pipeline.py | CREE | J5 |
| Tests/test_scores.py | CREE | J5 |
| Tests/test_rose_des_vents.py | CREE | J5 |
| pytest.ini | CREE | J5 |
| render.yaml | MODIFIE | J5 |
| requirements.txt | MODIFIE | J5 |
| models/tarif590.py | MODIFIE | J5 |
| docs/005_deploy_checklist.md | CREE | J5 |
| models/practitioner.py | CREE | POST-SPRINT |
| routers/practitioner.py | CREE | POST-SPRINT |
| docs/006_practitioners.sql | CREE | POST-SPRINT |
| main.py | MODIFIE | POST-SPRINT (v2.4.0) |
| models/invoice.py | MODIFIE | POST-SPRINT (practitioner_id) |
| models/tarif590.py | MODIFIE | POST-SPRINT (practitioner_id) |
| routers/invoice.py | MODIFIE | POST-SPRINT (auto-fill creditor) |
| routers/tarif590.py | MODIFIE | POST-SPRINT (auto-fill therapeute) |

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
| `POST /auth/register` | POST | RegisterResponse | routers/auth.py | tous | J4 | DONE |
| `POST /auth/login` | POST | LoginResponse | routers/auth.py | tous | J4 | DONE |
| `POST /auth/magic-link` | POST | MagicLinkResponse | routers/auth.py | tous | J4 | DONE |
| `POST /auth/refresh` | POST | LoginResponse | routers/auth.py | tous | J4 | DONE |
| `GET /auth/me` | GET | TokenVerifyResponse | routers/auth.py | tous | J4 | DONE |
| `POST /chromo` | POST | ChromoSession | routers/chromo.py | 59/179 | J4 | DONE |
| `GET /chromo` | GET | ChromoSessionList | routers/chromo.py | 59/179 | J4 | DONE |
| `GET /chromo/{id}` | GET | ChromoSession | routers/chromo.py | 59/179 | J4 | DONE |
| `PUT /chromo/{id}` | PUT | ChromoSession | routers/chromo.py | 59/179 | J4 | DONE |
| `GET /chromo/reference` | GET | ChromoReferenceResponse | routers/chromo.py | 59/179 | J4 | DONE |
| `POST /tore-sessions` | POST | ToreSession | routers/tore_session.py | 179 | J4 | DONE |
| `GET /tore-sessions` | GET | ToreSessionList | routers/tore_session.py | 179 | J4 | DONE |
| `GET /tore-sessions/{id}` | GET | ToreSession | routers/tore_session.py | 179 | J4 | DONE |
| `PUT /tore-sessions/{id}` | PUT | ToreSession | routers/tore_session.py | 179 | J4 | DONE |
| `POST /practitioners` | POST | PractitionerCreate | routers/practitioner.py | tous | POST | DONE |
| `GET /practitioners` | GET | PractitionerList | routers/practitioner.py | tous | POST | DONE |
| `GET /practitioners/{id}` | GET | Practitioner | routers/practitioner.py | tous | POST | DONE |
| `PUT /practitioners/{id}` | PUT | PractitionerUpdate | routers/practitioner.py | tous | POST | DONE |

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
- J4: Chromo model = 12 Color Gels Dinshah × 14 meridiens MTC × 5 Elements, mapping tonify/sedate/neutral
- J4: MERIDIEN_ELEMENT_MAP dict statique dans models/chromo.py — reference pour frontend prescription UI
- J4: GET /chromo/reference retourne la table complete (14 meridiens + 12 gels + 5 elements)
- J4: Prescriptions chromo stockees en JSONB (array de ChromoPrescriptionItem) — flexible pour N items/session
- J4: protocol_source enum: 5_elements | hdom | spectro_chrome | custom
- J4: Auth via Supabase GoTrue (anon key) — register, login, magic-link, refresh, me
- J4: Auth router SANS verify_token (public endpoints) — utilise Bearer token pour /auth/me
- J4: _get_anon_client() separe du get_supabase() service key — RLS-compatible
- J4: Tore sessions = CRUD historique avec before/after snapshots (JSONB) + rendement_delta compute
- J4: tore_sessions complemente /tore/push et /tore/pull existants (Make.com sync)
- J4: main.py updated to v2.3.0, 3 new routers (chromo, auth, tore_session)
- J5: 39 tests pytest (17 model validation + 22 integration via TestClient)
- J5: Fix tarif590.py Pydantic 2.12 / Python 3.14 compat (date field name clash with type annotation)
- J5: render.yaml augmente avec SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ANON_KEY, MAKE_WEBHOOK_TWINT_URL
- J5: pytest.ini avec import-mode=importlib (requis macOS case-insensitive + Tests dir)
- J5: Deploy checklist complete dans docs/005_deploy_checklist.md
- POST-SPRINT: Table practitioners ajoutee — chaque praticien a son propre profil (RCC, IBAN, adresse, methode)
- POST-SPRINT: practitioner_id optionnel sur invoices et tarif590 — auto-fill creditor/therapeute depuis le profil
- POST-SPRINT: Cabinet Pro (Plan 179) supporte multi-praticien via cabinet_id
- POST-SPRINT: Migration 006_practitioners.sql ajoute aussi practitioner_id FK sur invoices, tarif590_invoices, therapy_sessions, patients
- POST-SPRINT: main.py updated to v2.4.0, 1 new router (practitioner)

### Sprint v6.1 — J3 (2026-04-10)

- J3v6.1: Replan confirme avec Patrick apres constat que v6.0 J1-J5 + POST-SPRINT sont DONE
- J3v6.1: Fast-forward merge `main` -> `claude/clone-adapt-therapy-app-CNABs` (5cceede..6d5c1bc) — aucune divergence a resoudre
- J3v6.1: CNABs contient maintenant tout: 21 routers, practitioner, apple-native, schema FileMaker
- J3v6.1: Bump main.py a v2.5.0 — titre iSVLBHTherapeut 6.1 (rebrand interne)
- J3v6.1: 39/39 tests pytest passent (aucune regression apres merge)
- J3v6.1: Render env vars verifies — SUPABASE_URL/ANON_KEY/SERVICE_KEY OK, MAKE_WEBHOOK_TWINT_URL absent mais twint.py degrade proprement (retourne False)
- J3v6.1: Migrations SQL 001 a 006 confirmees EXECUTEES par Patrick (hors repo)
- J3v6.1: v2.5.0 balance tracking / Barzahlung / KVG-VVG-UVG-IVG-MVG reste isolee sur branche `claude/prepare-conversation-context-BIJbE` — NON mergee v6.1, a decider plus tard si on l'integre
- J3v6.1: Plan J4 = iOS client Swift via OpenAPI codegen (PatientService, ScoresService, ChromoService, RoseDesVentsService)
- J3v6.1: Plan J5 = import CSV FileMaker (manuel) + TestFlight v6.1.0 pour 6 testeurs (Flavia, Cornelia, Anne, Patrick x2, Chloe)

## Blockers / Questions ouvertes

- [ ] Patrick a-t-il un compte PostFinance e-Commerce? (decale post-v6.1)
- [ ] Export CSV depuis FileMaker: Patrick doit le faire manuellement (le Runtime ne supporte pas l'export programmatique) — J5v6.1
- [ ] Domaine final: app.itherapeut.ch ou app.vlbh.energy/itherapeut? — a lock J5v6.1 sur `app.vlbh.energy/itherapeut`
- [x] Compte Supabase: a creer J1 matin — SUPABASE_URL et SUPABASE_SERVICE_KEY requis dans .env
- [ ] Numero RCC de Patrick pour Tarif 590 par defaut?
- [x] Migration 002_j2_tables.sql: EXECUTEE (confirme par Patrick J3v6.1)
- [x] Migration 003_j3_tables.sql: EXECUTEE (confirme par Patrick J3v6.1)
- [ ] MAKE_WEBHOOK_TWINT_URL: a configurer dans Make.com pour envoi WhatsApp Twint (degrade, non-bloquant)
- [x] Migration 004_j4_tables.sql: EXECUTEE (confirme par Patrick J3v6.1)
- [x] SUPABASE_ANON_KEY: configure sur Render (confirme J3v6.1)
- [x] Migration 006_practitioners.sql: EXECUTEE (confirme par Patrick J3v6.1)
- [ ] Decider integration v2.5.0 balance/Barzahlung dans v6.1 ou v6.2 (branche prepare-conversation-context-BIJbE)

## Fin de session — Checklist handover

A faire a CHAQUE fin de session Claude:

1. `git add docs/SPRINT_STATE.md && git commit -m "chore: update sprint state [JX end]"`
2. Mettre a jour le tableau "Etat global" avec le statut du jour
3. Mettre a jour le registre API (marquer les endpoints DONE)
4. Mettre a jour la liste "Fichiers crees / modifies"
5. Ajouter les decisions prises dans la section "Decisions en cours de sprint"
6. Push la branche
