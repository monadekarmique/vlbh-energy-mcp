-- iTherapeut 6.0 — J2 Migration: tarif590_invoices, session_scores, rose_des_vents
-- Run this in Supabase SQL Editor AFTER 001_create_tables.sql
-- ADR-001: Supabase PostgreSQL for relational data

-- =========================================================================
-- TARIF 590 INVOICES
-- Stores metadata for generated Tarif 590 PDFs (PDF itself is streamed)
-- =========================================================================
CREATE TABLE IF NOT EXISTS tarif590_invoices (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_number      TEXT NOT NULL UNIQUE,
    patient_id          UUID REFERENCES patients(id) ON DELETE SET NULL,
    therapy_session_id  UUID REFERENCES therapy_sessions(id) ON DELETE SET NULL,
    therapeute_name     TEXT NOT NULL,
    therapeute_rcc      TEXT NOT NULL,
    patient_name        TEXT NOT NULL,
    patient_dob         DATE NOT NULL,
    invoice_date        DATE NOT NULL DEFAULT CURRENT_DATE,
    total_amount        NUMERIC(10, 2) NOT NULL DEFAULT 0,
    prestations_count   INT NOT NULL DEFAULT 0,
    diagnostic          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER tarif590_invoices_updated_at
    BEFORE UPDATE ON tarif590_invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE INDEX IF NOT EXISTS idx_tarif590_patient
    ON tarif590_invoices (patient_id);

CREATE INDEX IF NOT EXISTS idx_tarif590_date
    ON tarif590_invoices (invoice_date DESC);

-- =========================================================================
-- SESSION SCORES (Scores de Lumière per therapy session)
-- patient_scores and therapist_scores stored as JSONB for flexibility
-- (SLA, SLSA, SLPMO, SLM, S1–S5 sub-scores)
-- =========================================================================
CREATE TABLE IF NOT EXISTS session_scores (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    therapy_session_id      UUID NOT NULL REFERENCES therapy_sessions(id) ON DELETE CASCADE,
    patient_id              UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    patient_scores          JSONB NOT NULL DEFAULT '{}',
    therapist_scores        JSONB DEFAULT NULL,
    measurement_notes       TEXT,
    monade_apaisee          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER session_scores_updated_at
    BEFORE UPDATE ON session_scores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE INDEX IF NOT EXISTS idx_session_scores_patient
    ON session_scores (patient_id);

CREATE INDEX IF NOT EXISTS idx_session_scores_session
    ON session_scores (therapy_session_id);

CREATE INDEX IF NOT EXISTS idx_session_scores_date
    ON session_scores (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_session_scores_patient_scores_gin
    ON session_scores USING GIN (patient_scores);

-- =========================================================================
-- ROSE DES VENTS (diagnostic per therapy session)
-- primary and secondary measurements stored as JSONB
-- =========================================================================
CREATE TABLE IF NOT EXISTS rose_des_vents (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    therapy_session_id      UUID NOT NULL REFERENCES therapy_sessions(id) ON DELETE CASCADE,
    patient_id              UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    "primary"               JSONB NOT NULL,
    secondary               JSONB NOT NULL DEFAULT '[]',
    alignment_score         INT CHECK (alignment_score >= 0 AND alignment_score <= 100),
    notes                   TEXT,
    timing                  TEXT NOT NULL DEFAULT 'before'
                            CHECK (timing IN ('before', 'after', 'during')),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER rose_des_vents_updated_at
    BEFORE UPDATE ON rose_des_vents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE INDEX IF NOT EXISTS idx_rdv_patient
    ON rose_des_vents (patient_id);

CREATE INDEX IF NOT EXISTS idx_rdv_session
    ON rose_des_vents (therapy_session_id);

CREATE INDEX IF NOT EXISTS idx_rdv_date
    ON rose_des_vents (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_rdv_primary_gin
    ON rose_des_vents USING GIN ("primary");

-- =========================================================================
-- ROW LEVEL SECURITY (to be configured J4 with Supabase Auth)
-- =========================================================================
-- ALTER TABLE tarif590_invoices ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE session_scores ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE rose_des_vents ENABLE ROW LEVEL SECURITY;
