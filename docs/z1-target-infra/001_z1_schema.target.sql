-- =========================================================================
-- Z1 / Z1b — TARGET SCHEMA (NE PAS EXÉCUTER AVANT GO TRANSITION)
-- =========================================================================
-- Owner     : PO-07 Infra / Backend
-- Reference : ADR-03 (WhatsApp bridges + JID/LID segmentation)
-- Discovery : rtm-bot@vlbh.energy 2026-04-18 19h10 (migration LID WhatsApp)
-- Hosting   : Supabase eu-central (nLPD compliant)
--
-- Principe cardinal :
--   E.164 = clé métier stable
--   JID   = alias classique (@s.whatsapp.net) — peut disparaître
--   LID   = alias nouveau (@lid) — peut remplacer JID silencieusement
-- =========================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Trigger helper (réutilisable si pas déjà présent)
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =========================================================================
-- CONTACTS Z1 / Z1b
-- =========================================================================
CREATE TABLE IF NOT EXISTS contacts_z1 (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identifiants WhatsApp (au moins un des trois doit être renseigné)
    phone_e164          TEXT,                       -- ex: +41765135784 — CLÉ MÉTIER
    jid_classic         TEXT,                       -- ex: 41765135784@s.whatsapp.net
    lid                 TEXT,                       -- ex: 177111952306424@lid

    -- Identité WhatsApp
    push_name           TEXT,                       -- nom WhatsApp profil
    profile_pic_url     TEXT,

    -- Segmentation
    zone                TEXT NOT NULL
                        CHECK (zone IN ('Z1','Z1b')),
    bridge              TEXT NOT NULL DEFAULT 'wa_z1'
                        CHECK (bridge IN ('wa_z1')),

    -- État onboarding (Z1 → Z1b quand TestFlight activé)
    onboarding_status   TEXT NOT NULL DEFAULT 'visiteuse'
                        CHECK (onboarding_status IN (
                            'visiteuse',            -- Z1 : premier contact
                            'interested',           -- Z1 : a répondu
                            'testflight_invited',   -- Z1b : invitation envoyée
                            'testflight_installed', -- Z1b : app installée
                            'opted_out'             -- hors périmètre
                        )),

    -- Traçabilité LID
    first_seen_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    first_seen_as       TEXT CHECK (first_seen_as IN ('jid','lid','phone')),
    lid_migrated_at     TIMESTAMPTZ,                -- NULL si jamais migré
    jid_lost_at         TIMESTAMPTZ,                -- NULL si JID encore actif

    -- Consentement RGPD / nLPD
    consent_marketing   BOOLEAN NOT NULL DEFAULT false,
    consent_given_at    TIMESTAMPTZ,

    -- Audit
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Au moins un identifiant doit être renseigné
    CONSTRAINT chk_at_least_one_id
        CHECK (phone_e164 IS NOT NULL OR jid_classic IS NOT NULL OR lid IS NOT NULL)
);

CREATE TRIGGER contacts_z1_updated_at
    BEFORE UPDATE ON contacts_z1
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Index UNIQUES partiels : un alias ne peut pointer qu'à UN seul contact
CREATE UNIQUE INDEX IF NOT EXISTS idx_contacts_z1_phone
    ON contacts_z1(phone_e164) WHERE phone_e164 IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_contacts_z1_jid
    ON contacts_z1(jid_classic) WHERE jid_classic IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_contacts_z1_lid
    ON contacts_z1(lid) WHERE lid IS NOT NULL;

-- Index de recherche
CREATE INDEX IF NOT EXISTS idx_contacts_z1_zone
    ON contacts_z1(zone, onboarding_status);

CREATE INDEX IF NOT EXISTS idx_contacts_z1_last_seen
    ON contacts_z1(last_seen_at DESC);

-- =========================================================================
-- MESSAGES Z1 (log brut de tous les messages entrants/sortants)
-- =========================================================================
CREATE TABLE IF NOT EXISTS messages_z1 (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Matching (contact_id peut être NULL si contact pas encore résolu)
    contact_id              UUID REFERENCES contacts_z1(id) ON DELETE SET NULL,
    received_identifier     TEXT NOT NULL,          -- JID ou LID tel que reçu
    identifier_type         TEXT NOT NULL
                            CHECK (identifier_type IN ('jid','lid')),

    -- Message WhatsApp
    wa_message_id           TEXT NOT NULL UNIQUE,   -- ID natif WhatsApp
    direction               TEXT NOT NULL
                            CHECK (direction IN ('in','out')),
    body                    TEXT,
    media_type              TEXT,                   -- image, audio, video, doc, location, null
    media_url               TEXT,

    -- Contexte
    bridge                  TEXT NOT NULL DEFAULT 'wa_z1'
                            CHECK (bridge IN ('wa_z1')),
    is_group                BOOLEAN NOT NULL DEFAULT false,
    quoted_wa_message_id    TEXT,                   -- si c'est une réponse

    -- Timing
    received_at             TIMESTAMPTZ NOT NULL,   -- timestamp WhatsApp natif
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Traitement
    processed_at            TIMESTAMPTZ,            -- quand Make a lu/traité
    processed_by_scenario   INT                     -- ID scénario Make qui a traité
);

CREATE INDEX IF NOT EXISTS idx_messages_z1_contact
    ON messages_z1(contact_id, received_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_z1_identifier
    ON messages_z1(received_identifier, received_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_z1_unprocessed
    ON messages_z1(received_at) WHERE processed_at IS NULL;

-- =========================================================================
-- LID_MIGRATION_LOG (audit trail des migrations JID → LID détectées)
-- =========================================================================
CREATE TABLE IF NOT EXISTS lid_migration_log_z1 (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id          UUID NOT NULL REFERENCES contacts_z1(id) ON DELETE CASCADE,
    old_jid             TEXT,
    new_lid             TEXT NOT NULL,
    detection_method    TEXT NOT NULL
                        CHECK (detection_method IN (
                            'push_name_match',      -- heuristique nom
                            'manual_merge',         -- intervention Patrick
                            'bridge_announce',      -- whatsmeow a annoncé la migration
                            'timing_pattern'        -- corrélation temporelle
                        )),
    confidence          NUMERIC(3,2)                -- 0.00 à 1.00
                        CHECK (confidence >= 0 AND confidence <= 1),
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    applied_at          TIMESTAMPTZ,                -- NULL si pas encore appliqué
    applied_by          TEXT                        -- 'auto', 'patrick', 'rtm-bot'
);

CREATE INDEX IF NOT EXISTS idx_lid_migration_log_contact
    ON lid_migration_log_z1(contact_id);

CREATE INDEX IF NOT EXISTS idx_lid_migration_log_pending
    ON lid_migration_log_z1(detected_at) WHERE applied_at IS NULL;

-- =========================================================================
-- RLS — désactivé pour l'instant (sera activé post-Go avec Supabase Auth)
-- =========================================================================
-- ALTER TABLE contacts_z1 ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE messages_z1 ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE lid_migration_log_z1 ENABLE ROW LEVEL SECURITY;

-- =========================================================================
-- COMMENTS (documentation inline)
-- =========================================================================
COMMENT ON TABLE contacts_z1 IS
    'Contacts WhatsApp zone 1 (visiteuses + onboarded TestFlight). Clé métier = phone_e164. JID et LID sont des alias volatiles.';

COMMENT ON COLUMN contacts_z1.phone_e164 IS
    'Numéro au format E.164 (+417XXXXXXXX). Clé métier stable. NULL si contact jamais révélé son numéro (LID pur).';

COMMENT ON COLUMN contacts_z1.jid_classic IS
    'JID WhatsApp classique (numéro@s.whatsapp.net). Peut devenir NULL si WhatsApp migre le contact vers LID.';

COMMENT ON COLUMN contacts_z1.lid IS
    'Linked ID WhatsApp (XXXX@lid). Identifiant anonymisé de nouvelle génération.';

COMMENT ON TABLE messages_z1 IS
    'Log brut de tous les messages WhatsApp zone 1. contact_id NULL = pas encore résolu (à traiter par job de réconciliation).';

COMMENT ON TABLE lid_migration_log_z1 IS
    'Audit trail des migrations JID → LID détectées. Permet la traçabilité et le rollback si fausse détection.';
