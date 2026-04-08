# Deploy Checklist — iTherapeut 6.0

## Pre-deploy

- [ ] Execute SQL migrations in order in Supabase SQL Editor:
  - `docs/001_create_tables.sql` (patients, therapy_sessions, invoices)
  - `docs/002_j2_tables.sql` (tarif590, scores, rose_des_vents)
  - `docs/003_j3_tables.sql` (twint_payments, pipeline_leads)
  - `docs/004_j4_tables.sql` (chromo_sessions, tore_sessions)
- [ ] Configure environment variables on Render.com:
  - `SUPABASE_URL` — Project URL from Supabase dashboard
  - `SUPABASE_SERVICE_KEY` — Service role key (Settings > API)
  - `SUPABASE_ANON_KEY` — Anon/public key (Settings > API)
  - `MAKE_WEBHOOK_TWINT_URL` — Make.com webhook for WhatsApp Twint
- [ ] Verify existing env vars still set:
  - `MAKE_WEBHOOK_PUSH_URL`
  - `MAKE_WEBHOOK_PULL_URL`
  - `VLBH_TOKEN`

## Deploy

- [ ] Merge branch `claude/clone-adapt-therapy-app-CNABs` into main
- [ ] Render.com auto-deploys from main (verify in dashboard)
- [ ] Wait for build to complete (~2-3 min)
- [ ] Check health endpoint: `curl https://vlbh-energy-mcp.onrender.com/health`

## Post-deploy verification

- [ ] Verify /docs (Swagger UI) loads with all new endpoints
- [ ] Test auth flow: POST /auth/register with test account
- [ ] Test patient CRUD: POST /patients, GET /patients
- [ ] Test chromo reference: GET /chromo/reference (14 meridians)
- [ ] Test existing endpoints still work: POST /slm/push, /sla/push
- [ ] Verify SVLBH Demandes iOS app connects to backend

## Supabase Auth setup

- [ ] Enable email auth provider (Authentication > Providers)
- [ ] Configure SMTP for magic links (Settings > Auth > SMTP)
- [ ] Set Site URL for redirect: https://app.vlbh.energy (or chosen domain)
- [ ] Enable RLS policies on new tables (after verifying app works)

## Pending items (not blockers for deploy)

- [ ] PostFinance e-Commerce account for real Twint payments
- [ ] FileMaker CSV patient data export + import script
- [ ] Domain choice: app.itherapeut.ch vs app.vlbh.energy/itherapeut
- [ ] Patrick's RCC number for Tarif 590 default config
- [ ] Capacitor wrapper for iOS/Android (ADR-002)