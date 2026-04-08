-- ============================================================
-- Migration 003 — iTherapeut 6.0 J3
-- Tables: twint_payments, pipeline_leads
-- Run in: Supabase SQL Editor
-- ============================================================

-- -------------------------------------------------------
-- 1. Twint payment links (Plan 179)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS twint_payments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id  UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    amount      NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    currency    TEXT NOT NULL DEFAULT 'CHF',
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'sent', 'paid', 'expired', 'cancelled')),
    twint_url   TEXT,
    message     TEXT,
    whatsapp_sent BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Auto-update updated_at
CREATE TRIGGER set_twint_payments_updated_at
    BEFORE UPDATE ON twint_payments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Indexes
CREATE INDEX idx_twint_payments_invoice ON twint_payments(invoice_id);
CREATE INDEX idx_twint_payments_patient ON twint_payments(patient_id);
CREATE INDEX idx_twint_payments_status  ON twint_payments(status);

-- -------------------------------------------------------
-- 2. Pipeline leads — CRM funnel (Plan 179)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS pipeline_leads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    email           TEXT,
    phone           TEXT,
    stage           TEXT NOT NULL DEFAULT 'new'
                    CHECK (stage IN ('new', 'contacted', 'scheduled',
                                      'in_treatment', 'completed', 'lost')),
    source          TEXT NOT NULL DEFAULT 'other'
                    CHECK (source IN ('website', 'referral', 'social_media',
                                       'close_crm', 'phone', 'other')),
    notes           TEXT,
    patient_id      UUID REFERENCES patients(id) ON DELETE SET NULL,
    close_lead_id   TEXT,
    priority        INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 3),
    next_action     TEXT,
    next_action_date TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Auto-update updated_at
CREATE TRIGGER set_pipeline_leads_updated_at
    BEFORE UPDATE ON pipeline_leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Indexes
CREATE INDEX idx_pipeline_leads_stage    ON pipeline_leads(stage);
CREATE INDEX idx_pipeline_leads_priority ON pipeline_leads(priority);
CREATE INDEX idx_pipeline_leads_patient  ON pipeline_leads(patient_id);
CREATE INDEX idx_pipeline_leads_close    ON pipeline_leads(close_lead_id)
    WHERE close_lead_id IS NOT NULL;

-- ============================================================
-- NOTE: The update_updated_at() function was created in
-- migration 001. If running this standalone, ensure it exists:
--
-- CREATE OR REPLACE FUNCTION update_updated_at()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     NEW.updated_at = now();
--     RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql;
-- ============================================================
