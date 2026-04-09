-- ============================================================
-- Migration 004 — iTherapeut 6.0 J4
-- Tables: chromo_sessions, tore_sessions
-- Run in: Supabase SQL Editor
-- ============================================================

-- -------------------------------------------------------
-- 1. Chromotherapy sessions (Plan 59/179)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS chromo_sessions (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    therapy_session_id    UUID NOT NULL REFERENCES therapy_sessions(id) ON DELETE CASCADE,
    patient_id            UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    prescriptions         JSONB NOT NULL DEFAULT '[]'::jsonb,
    rose_des_vents_id     UUID REFERENCES rose_des_vents(id) ON DELETE SET NULL,
    scores_id             UUID REFERENCES score_snapshots(id) ON DELETE SET NULL,
    observation           TEXT,
    protocol_source       TEXT NOT NULL DEFAULT '5_elements'
                          CHECK (protocol_source IN ('5_elements', 'hdom', 'spectro_chrome', 'custom')),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Auto-update updated_at
CREATE TRIGGER set_chromo_sessions_updated_at
    BEFORE UPDATE ON chromo_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Indexes
CREATE INDEX idx_chromo_sessions_therapy   ON chromo_sessions(therapy_session_id);
CREATE INDEX idx_chromo_sessions_patient   ON chromo_sessions(patient_id);
CREATE INDEX idx_chromo_sessions_protocol  ON chromo_sessions(protocol_source);
CREATE INDEX idx_chromo_sessions_rdv       ON chromo_sessions(rose_des_vents_id)
    WHERE rose_des_vents_id IS NOT NULL;

-- Validate prescriptions is a non-empty array
ALTER TABLE chromo_sessions
    ADD CONSTRAINT chromo_prescriptions_not_empty
    CHECK (jsonb_array_length(prescriptions) > 0);

-- -------------------------------------------------------
-- 2. Tore measurement sessions (Plan 179)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS tore_sessions (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    therapy_session_id    UUID NOT NULL REFERENCES therapy_sessions(id) ON DELETE CASCADE,
    patient_id            UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    before                JSONB NOT NULL DEFAULT '{}'::jsonb,
    after                 JSONB,
    measurement_notes     TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Auto-update updated_at
CREATE TRIGGER set_tore_sessions_updated_at
    BEFORE UPDATE ON tore_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Indexes
CREATE INDEX idx_tore_sessions_therapy  ON tore_sessions(therapy_session_id);
CREATE INDEX idx_tore_sessions_patient  ON tore_sessions(patient_id);

-- ============================================================
-- NOTE: Auth tables are managed by Supabase Auth (GoTrue).
-- No custom migration needed — user metadata (role, full_name)
-- is stored in auth.users.raw_user_meta_data JSONB column.
-- ============================================================

-- ============================================================
-- REFERENCE: update_updated_at() function created in migration 001.
-- ============================================================