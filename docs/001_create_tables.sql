-- iTherapeut 6.0 — J1 Migration: patients, therapy_sessions, invoices
-- Run this in Supabase SQL Editor
-- ADR-001: Supabase PostgreSQL for relational data

-- Enable UUID extension (usually already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================================================
-- PATIENTS
-- =========================================================================
CREATE TABLE IF NOT EXISTS patients (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    date_of_birth   DATE,
    email           TEXT,
    phone           TEXT,
    -- Structured address (SIX v2.4 QR-facture requirement)
    street          TEXT,
    house_number    TEXT,
    postal_code     TEXT,
    city            TEXT,
    country         TEXT DEFAULT 'CH',
    notes           TEXT,
    insurance_name  TEXT,
    insurance_number TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Index for search
CREATE INDEX IF NOT EXISTS idx_patients_name
    ON patients (last_name, first_name);

-- =========================================================================
-- THERAPY SESSIONS
-- =========================================================================
CREATE TABLE IF NOT EXISTS therapy_sessions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id          UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    date                TIMESTAMPTZ NOT NULL,
    duration_minutes    INT NOT NULL CHECK (duration_minutes >= 15 AND duration_minutes <= 480),
    session_type        TEXT NOT NULL,
    tarif_code          TEXT,
    tarif_amount        NUMERIC(10, 2),
    notes               TEXT,
    -- VLBH Scores
    sla_score           NUMERIC(5, 2),
    slsa_score          NUMERIC(5, 2),
    slm_score           NUMERIC(5, 2),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER therapy_sessions_updated_at
    BEFORE UPDATE ON therapy_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE INDEX IF NOT EXISTS idx_therapy_sessions_patient
    ON therapy_sessions (patient_id);

CREATE INDEX IF NOT EXISTS idx_therapy_sessions_date
    ON therapy_sessions (date DESC);

-- =========================================================================
-- INVOICES
-- =========================================================================
CREATE TABLE IF NOT EXISTS invoices (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_number          TEXT NOT NULL UNIQUE,
    patient_id              UUID NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
    therapy_session_ids     UUID[] DEFAULT '{}',
    invoice_date            DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date                DATE,
    status                  TEXT NOT NULL DEFAULT 'draft'
                            CHECK (status IN ('draft', 'sent', 'paid', 'cancelled', 'overdue')),
    line_items              JSONB NOT NULL DEFAULT '[]',
    total_amount            NUMERIC(10, 2) NOT NULL DEFAULT 0,
    notes                   TEXT,
    -- Creditor info (immutable per invoice)
    creditor_name           TEXT NOT NULL,
    creditor_street         TEXT NOT NULL,
    creditor_house_number   TEXT,
    creditor_postal_code    TEXT NOT NULL,
    creditor_city           TEXT NOT NULL,
    creditor_country        TEXT NOT NULL DEFAULT 'CH',
    creditor_iban           TEXT NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER invoices_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE INDEX IF NOT EXISTS idx_invoices_patient
    ON invoices (patient_id);

CREATE INDEX IF NOT EXISTS idx_invoices_status
    ON invoices (status);

CREATE INDEX IF NOT EXISTS idx_invoices_date
    ON invoices (invoice_date DESC);

-- =========================================================================
-- ROW LEVEL SECURITY (to be configured with auth later in J4)
-- =========================================================================
-- For now, RLS is disabled — will be enabled when Supabase Auth is set up.
-- ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE therapy_sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
