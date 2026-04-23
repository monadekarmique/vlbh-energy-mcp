# Make.com → Supabase Migration Plan

Migration of 5 CRUD routers (slm, sla, session, lead, tore) + billing
from Make.com datastore 155674 (svlbh-v2) to direct Supabase PostgreSQL.

## Architecture

```
Before:  iOS → FastAPI → Make.com webhook → datastore 155674
After:   iOS → FastAPI → SupabaseService → Supabase PostgreSQL
```

The 6 existing routers are NOT modified. New routers (v2) will use
`SupabaseService` and coexist until the iOS clients are updated.

## DDL — 8 tables

### 1. praticiennes

```sql
CREATE TABLE IF NOT EXISTS praticiennes (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    mobile_hash text NOT NULL UNIQUE,
    code        text NOT NULL UNIQUE,
    nom_praticien text,
    role        text CHECK (role IN ('certifiee', 'superviseur')),
    statut      text DEFAULT 'active' CHECK (statut IN ('active', 'inactive')),
    formation_max text,
    compteur_max_patient int DEFAULT 0,
    compteur    int DEFAULT 0,
    quota_libre int DEFAULT 0,
    quota_libre_pct int DEFAULT 0,
    created_at  timestamptz DEFAULT now(),
    updated_at  timestamptz DEFAULT now()
);

CREATE INDEX idx_praticiennes_mobile_hash ON praticiennes (mobile_hash);
CREATE INDEX idx_praticiennes_statut ON praticiennes (statut);
```

### 2. consultantes

```sql
CREATE TABLE IF NOT EXISTS consultantes (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    mobile_hash text NOT NULL REFERENCES praticiennes(mobile_hash) ON DELETE CASCADE,
    patient_id  text NOT NULL,
    prenom      text NOT NULL,
    nom         text,
    email       text,
    phone       text,
    notes       text,
    created_at  timestamptz DEFAULT now(),
    updated_at  timestamptz DEFAULT now(),
    UNIQUE (mobile_hash, patient_id)
);

CREATE INDEX idx_consultantes_mobile_hash ON consultantes (mobile_hash);
CREATE INDEX idx_consultantes_patient_id ON consultantes (patient_id);
```

### 3. vlbh_sessions

```sql
CREATE TABLE IF NOT EXISTS vlbh_sessions (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_key       text NOT NULL UNIQUE,
    mobile_hash       text REFERENCES praticiennes(mobile_hash),
    patient_id        text NOT NULL,
    session_num       text NOT NULL,
    program_code      text NOT NULL,
    practitioner_code text NOT NULL,
    therapist_name    text,
    status            text DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'WAITING', 'COMPLETED')),
    event_count       int DEFAULT 0,
    liberated_count   int DEFAULT 0,
    platform          text DEFAULT 'android',
    "timestamp"       bigint,
    created_at        timestamptz DEFAULT now(),
    updated_at        timestamptz DEFAULT now()
);

CREATE INDEX idx_vlbh_sessions_mobile_hash ON vlbh_sessions (mobile_hash);
CREATE INDEX idx_vlbh_sessions_patient_id ON vlbh_sessions (patient_id);
CREATE INDEX idx_vlbh_sessions_status ON vlbh_sessions (status);
```

### 4. leads

```sql
CREATE TABLE IF NOT EXISTS leads (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    shamane_code text NOT NULL UNIQUE,
    mobile_hash  text REFERENCES praticiennes(mobile_hash),
    prenom       text NOT NULL,
    nom          text,
    tier         text DEFAULT 'CERTIFIEE' CHECK (tier IN ('LEAD', 'FORMATION', 'CERTIFIEE', 'SUPERVISEUR')),
    status       text DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'WAITING', 'COMPLETED')),
    session_key  text,
    platform     text DEFAULT 'android',
    "timestamp"  bigint,
    created_at   timestamptz DEFAULT now(),
    updated_at   timestamptz DEFAULT now()
);

CREATE INDEX idx_leads_mobile_hash ON leads (mobile_hash);
CREATE INDEX idx_leads_tier ON leads (tier);
CREATE INDEX idx_leads_status ON leads (status);
```

### 5. billing_praticien

```sql
CREATE TABLE IF NOT EXISTS billing_praticien (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    mobile_hash text NOT NULL UNIQUE,
    code        text,
    nom_praticien text,
    role        text CHECK (role IN ('certifiee', 'superviseur')),
    statut      text DEFAULT 'active' CHECK (statut IN ('active', 'inactive')),
    formation_max text,
    compteur_max_patient int DEFAULT 0,
    compteur    int DEFAULT 0,
    quota_libre int DEFAULT 0,
    quota_libre_pct int DEFAULT 0,
    created_at  timestamptz DEFAULT now(),
    updated_at  timestamptz DEFAULT now()
);

CREATE INDEX idx_billing_mobile_hash ON billing_praticien (mobile_hash);
CREATE INDEX idx_billing_statut ON billing_praticien (statut);
```

### 6. tores

```sql
CREATE TABLE IF NOT EXISTS tores (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_key     text NOT NULL UNIQUE,
    mobile_hash     text REFERENCES praticiennes(mobile_hash),
    therapist_name  text,
    platform        text DEFAULT 'android',
    "timestamp"     bigint,
    -- Champ toroidal
    tore_intensite  int CHECK (tore_intensite BETWEEN 0 AND 100000),
    tore_coherence  int CHECK (tore_coherence BETWEEN 0 AND 100),
    tore_frequence  numeric(8,2) CHECK (tore_frequence BETWEEN 0.01 AND 1000),
    tore_phase      text CHECK (tore_phase IN ('REPOS', 'CHARGE', 'DECHARGE', 'EQUILIBRE')),
    -- Glycemie
    glyc_index             int CHECK (glyc_index BETWEEN 0 AND 500),
    glyc_balance           int CHECK (glyc_balance BETWEEN 0 AND 100),
    glyc_absorption        int CHECK (glyc_absorption BETWEEN 0 AND 100),
    glyc_resistance_score  int CHECK (glyc_resistance_score BETWEEN 0 AND 1000),
    -- Sclerose
    scl_score        int CHECK (scl_score BETWEEN 0 AND 1000),
    scl_densite      int CHECK (scl_densite BETWEEN 0 AND 100),
    scl_elasticite   int CHECK (scl_elasticite BETWEEN 0 AND 100),
    scl_permeabilite int CHECK (scl_permeabilite BETWEEN 0 AND 100),
    -- Couplage
    cp_correlation_tg   int CHECK (cp_correlation_tg BETWEEN -100 AND 100),
    cp_correlation_ts   int CHECK (cp_correlation_ts BETWEEN -100 AND 100),
    cp_correlation_gs   int CHECK (cp_correlation_gs BETWEEN -100 AND 100),
    cp_score_couplage   int CHECK (cp_score_couplage BETWEEN 0 AND 10000),
    cp_flux_net          int CHECK (cp_flux_net BETWEEN -100000 AND 100000),
    cp_phase_couplage    text CHECK (cp_phase_couplage IN ('SYNERGIQUE', 'ANTAGONISTE', 'NEUTRE', 'TRANSITOIRE')),
    -- Sclerose tissulaire
    st_fibrose_index      int CHECK (st_fibrose_index BETWEEN 0 AND 1000),
    st_zones_atteintes    int CHECK (st_zones_atteintes BETWEEN 0 AND 50),
    st_profondeur         int CHECK (st_profondeur BETWEEN 0 AND 10),
    st_revascularisation  int CHECK (st_revascularisation BETWEEN 0 AND 100),
    st_decompaction       int CHECK (st_decompaction BETWEEN 0 AND 100),
    -- Stockage global
    stockage_niveau            int CHECK (stockage_niveau BETWEEN 0 AND 100000),
    stockage_capacite          int CHECK (stockage_capacite BETWEEN 0 AND 100000),
    stockage_taux_restauration int CHECK (stockage_taux_restauration BETWEEN 0 AND 100),
    stockage_rendement         numeric(6,2) CHECK (stockage_rendement BETWEEN 0 AND 100),
    --
    created_at  timestamptz DEFAULT now(),
    updated_at  timestamptz DEFAULT now()
);

CREATE INDEX idx_tores_mobile_hash ON tores (mobile_hash);
```

### 7. slm_scores

```sql
CREATE TABLE IF NOT EXISTS slm_scores (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_key  text NOT NULL UNIQUE,
    mobile_hash  text REFERENCES praticiennes(mobile_hash),
    therapist_name text,
    platform     text DEFAULT 'android',
    "timestamp"  bigint,
    -- Therapist scores (SLSA can exceed 100%, up to 50 000%)
    sla_t     int CHECK (sla_t BETWEEN 0 AND 350),
    slsa_t    int CHECK (slsa_t BETWEEN 0 AND 50000),
    slsa_s1_t int CHECK (slsa_s1_t BETWEEN 0 AND 50000),
    slsa_s2_t int CHECK (slsa_s2_t BETWEEN 0 AND 50000),
    slsa_s3_t int CHECK (slsa_s3_t BETWEEN 0 AND 50000),
    slsa_s4_t int CHECK (slsa_s4_t BETWEEN 0 AND 50000),
    slsa_s5_t int CHECK (slsa_s5_t BETWEEN 0 AND 50000),
    slm_t     int CHECK (slm_t BETWEEN 0 AND 100000),
    tot_slm_t int CHECK (tot_slm_t BETWEEN 0 AND 1000),
    -- Patrick scores
    sla_p     int CHECK (sla_p BETWEEN 0 AND 350),
    slsa_p    int CHECK (slsa_p BETWEEN 0 AND 50000),
    slsa_s1_p int CHECK (slsa_s1_p BETWEEN 0 AND 50000),
    slsa_s2_p int CHECK (slsa_s2_p BETWEEN 0 AND 50000),
    slsa_s3_p int CHECK (slsa_s3_p BETWEEN 0 AND 50000),
    slsa_s4_p int CHECK (slsa_s4_p BETWEEN 0 AND 50000),
    slsa_s5_p int CHECK (slsa_s5_p BETWEEN 0 AND 50000),
    slm_p     int CHECK (slm_p BETWEEN 0 AND 100000),
    tot_slm_p int CHECK (tot_slm_p BETWEEN 0 AND 1000),
    --
    created_at  timestamptz DEFAULT now(),
    updated_at  timestamptz DEFAULT now()
);

CREATE INDEX idx_slm_mobile_hash ON slm_scores (mobile_hash);
```

### 8. sla_scores

```sql
CREATE TABLE IF NOT EXISTS sla_scores (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_key  text NOT NULL UNIQUE,
    mobile_hash  text REFERENCES praticiennes(mobile_hash),
    therapist_name text,
    platform     text DEFAULT 'android',
    "timestamp"  bigint,
    sla_t        int CHECK (sla_t BETWEEN 0 AND 350),
    sla_p        int CHECK (sla_p BETWEEN 0 AND 350),
    created_at   timestamptz DEFAULT now(),
    updated_at   timestamptz DEFAULT now()
);

CREATE INDEX idx_sla_mobile_hash ON sla_scores (mobile_hash);
```

## updated_at trigger

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all 8 tables
DO $$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN SELECT unnest(ARRAY[
        'praticiennes', 'consultantes', 'vlbh_sessions', 'leads',
        'billing_praticien', 'tores', 'slm_scores', 'sla_scores'
    ]) LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%s_updated_at BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION update_updated_at();',
            tbl, tbl
        );
    END LOOP;
END;
$$;
```

## Row Level Security (RLS)

```sql
-- Enable RLS on all tables
ALTER TABLE praticiennes ENABLE ROW LEVEL SECURITY;
ALTER TABLE consultantes ENABLE ROW LEVEL SECURITY;
ALTER TABLE vlbh_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_praticien ENABLE ROW LEVEL SECURITY;
ALTER TABLE tores ENABLE ROW LEVEL SECURITY;
ALTER TABLE slm_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE sla_scores ENABLE ROW LEVEL SECURITY;

-- Service role bypasses RLS (used by FastAPI backend).
-- For future anon/auth access, add policies scoped by mobile_hash:
--
-- Example policy for consultantes:
-- CREATE POLICY "Users see own consultantes"
--   ON consultantes FOR SELECT
--   USING (mobile_hash = current_setting('request.jwt.claims', true)::json->>'mobile_hash');
```

## Migration Steps

### Phase 1 — Dual-write (current sprint)
1. Run the DDL above in Supabase SQL editor
2. Create new v2 routers (e.g. `/v2/slm/push`) that use `SupabaseService`
3. Keep existing routers writing to Make.com (no changes)
4. Backfill: export datastore 155674 → import into Supabase tables

### Phase 2 — Read from Supabase
1. Update existing routers to READ from Supabase (fall back to Make.com)
2. Validate data parity with Make.com

### Phase 3 — Full cutover
1. Update existing routers to WRITE to Supabase only
2. Keep Make.com webhooks alive but stop writing to datastore 155674
3. Update iOS app to use v2 endpoints (if different)
4. Decommission Make.com pull/push scenarios for svlbh-v2

### Phase 4 — Cleanup
1. Remove Make.com webhook env vars
2. Remove MakeService class
3. Remove v1 router duplicates (if v2 replaces them)

## Data Backfill Script

```python
"""One-shot script to backfill datastore 155674 → Supabase.

Run manually: python scripts/backfill_make_to_supabase.py
"""
import json, httpx, os
from supabase import create_client

# 1. Export from Make.com datastore via API
MAKE_TOKEN = os.environ["MAKE_API_TOKEN"]
DS_ID = 155674
TEAM_ID = 630342

headers = {"Authorization": f"Token {MAKE_TOKEN}"}
url = f"https://eu2.make.com/api/v2/data-stores/{DS_ID}/data"
resp = httpx.get(url, headers=headers, params={"pg[limit]": 10000})
records = resp.json().get("records", [])

# 2. Insert into Supabase (grouped by module)
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

for r in records:
    module = r.get("module", "").upper()
    if module == "SLM":
        sb.table("slm_scores").upsert({...}).execute()  # map fields
    elif module == "SLA":
        sb.table("sla_scores").upsert({...}).execute()
    elif module == "SESSION":
        sb.table("vlbh_sessions").upsert({...}).execute()
    elif module == "LEAD":
        sb.table("leads").upsert({...}).execute()
    elif module == "TORE":
        sb.table("tores").upsert({...}).execute()
```

## Key Compatibility Notes

- **mobile_hash**: preserved as the primary scoping key for RLS
- **session_key format**: `PP-patientId-sessionNum-praticienCode` — unchanged
- **SLSA range**: 0–50,000% — CHECK constraints match existing Pydantic validators
- **Timestamps**: stored as bigint (ms since epoch) for backward compatibility
- **Upsert on conflict**: all domain tables use UNIQUE on session_key or shamane_code
