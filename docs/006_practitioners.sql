-- iTherapeut 6.0 — Migration 006: Practitioners table
-- Run this in Supabase SQL Editor
-- Multi-practitioner support: each practitioner has their own billing profile

-- =========================================================================
-- PRACTITIONERS
-- =========================================================================
CREATE TABLE IF NOT EXISTS practitioners (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identity
    first_name          TEXT NOT NULL,
    last_name           TEXT NOT NULL,
    email               TEXT,
    phone               TEXT,

    -- Structured address (SIX v2.4 QR-facture requirement)
    street              TEXT NOT NULL,
    house_number        TEXT,
    postal_code         TEXT NOT NULL,
    city                TEXT NOT NULL,
    country             TEXT NOT NULL DEFAULT 'CH',

    -- Billing — QR-facture creditor
    iban                TEXT NOT NULL,

    -- Tarif 590
    rcc_number          TEXT NOT NULL,
    nif_number          TEXT,
    gln_number          TEXT,
    therapy_method      TEXT,           -- Code méthode (1-15, 99)
    therapy_method_text TEXT,           -- Texte libre si AUTRE

    -- Plan & status
    plan                TEXT NOT NULL DEFAULT 'therapeute_59'
                        CHECK (plan IN ('therapeute_59', 'cabinet_pro_179')),
    status              TEXT NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive', 'suspended')),

    -- Cabinet reference (multi-practitioner)
    cabinet_id          UUID,

    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER practitioners_updated_at
    BEFORE UPDATE ON practitioners
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Indexes
CREATE INDEX IF NOT EXISTS idx_practitioners_name
    ON practitioners (last_name, first_name);

CREATE INDEX IF NOT EXISTS idx_practitioners_status
    ON practitioners (status);

CREATE INDEX IF NOT EXISTS idx_practitioners_cabinet
    ON practitioners (cabinet_id)
    WHERE cabinet_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_practitioners_rcc
    ON practitioners (rcc_number);

-- =========================================================================
-- ADD practitioner_id FK to existing tables
-- =========================================================================

-- Add practitioner_id to invoices (optional — auto-fills creditor info)
ALTER TABLE invoices
    ADD COLUMN IF NOT EXISTS practitioner_id UUID REFERENCES practitioners(id);

CREATE INDEX IF NOT EXISTS idx_invoices_practitioner
    ON invoices (practitioner_id)
    WHERE practitioner_id IS NOT NULL;

-- Add practitioner_id to tarif590_invoices (optional — tracks which practitioner)
ALTER TABLE tarif590_invoices
    ADD COLUMN IF NOT EXISTS practitioner_id UUID REFERENCES practitioners(id);

-- Add practitioner_id to therapy_sessions (which practitioner saw the patient)
ALTER TABLE therapy_sessions
    ADD COLUMN IF NOT EXISTS practitioner_id UUID REFERENCES practitioners(id);

CREATE INDEX IF NOT EXISTS idx_therapy_sessions_practitioner
    ON therapy_sessions (practitioner_id)
    WHERE practitioner_id IS NOT NULL;

-- Add practitioner_id to patients (primary practitioner)
ALTER TABLE patients
    ADD COLUMN IF NOT EXISTS practitioner_id UUID REFERENCES practitioners(id);
