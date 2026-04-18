-- =========================================================================
-- Z1 / Z1b — TARGET RPC FUNCTIONS (NE PAS EXÉCUTER AVANT GO TRANSITION)
-- =========================================================================
-- Ces fonctions exposent une API stable aux scénarios Make.com.
-- Elles abstraient la complexité JID/LID — Make n'a qu'à passer un
-- "identifier" (peu importe JID ou LID) et récupère/crée le bon contact.
-- =========================================================================

-- =========================================================================
-- resolve_contact_z1(identifier) → UUID | NULL
-- Résout un identifiant WhatsApp (JID ou LID) vers un contact_id.
-- Retourne NULL si inconnu (le scénario Make doit alors appeler upsert).
-- =========================================================================
CREATE OR REPLACE FUNCTION resolve_contact_z1(identifier TEXT)
RETURNS UUID AS $$
DECLARE
    contact_uuid UUID;
BEGIN
    IF identifier IS NULL OR identifier = '' THEN
        RETURN NULL;
    END IF;

    -- Match sur JID classique
    IF identifier LIKE '%@s.whatsapp.net' THEN
        SELECT id INTO contact_uuid
            FROM contacts_z1
            WHERE jid_classic = identifier
            LIMIT 1;
        IF FOUND THEN RETURN contact_uuid; END IF;
    END IF;

    -- Match sur LID
    IF identifier LIKE '%@lid' THEN
        SELECT id INTO contact_uuid
            FROM contacts_z1
            WHERE lid = identifier
            LIMIT 1;
        IF FOUND THEN RETURN contact_uuid; END IF;
    END IF;

    -- Match sur E.164 (si identifier est un numéro pur)
    IF identifier LIKE '+%' THEN
        SELECT id INTO contact_uuid
            FROM contacts_z1
            WHERE phone_e164 = identifier
            LIMIT 1;
        IF FOUND THEN RETURN contact_uuid; END IF;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =========================================================================
-- upsert_contact_z1(identifier, push_name, zone, first_seen_as) → UUID
-- Crée ou met à jour un contact Z1. Retourne toujours le contact_id.
-- À appeler par les scénarios Make sur réception d'un message entrant.
-- =========================================================================
CREATE OR REPLACE FUNCTION upsert_contact_z1(
    p_identifier        TEXT,
    p_push_name         TEXT DEFAULT NULL,
    p_zone              TEXT DEFAULT 'Z1',
    p_phone_e164        TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    contact_uuid        UUID;
    v_jid_classic       TEXT;
    v_lid               TEXT;
    v_phone             TEXT;
    v_first_seen_as     TEXT;
BEGIN
    -- Parse l'identifier
    IF p_identifier LIKE '%@s.whatsapp.net' THEN
        v_jid_classic := p_identifier;
        v_first_seen_as := 'jid';
        -- Extraction du numéro (format : 41XXXXXXXXX@s.whatsapp.net → +41XXXXXXXXX)
        v_phone := COALESCE(p_phone_e164, '+' || SPLIT_PART(p_identifier, '@', 1));
    ELSIF p_identifier LIKE '%@lid' THEN
        v_lid := p_identifier;
        v_first_seen_as := 'lid';
        v_phone := p_phone_e164; -- LID ne donne pas le numéro
    ELSIF p_identifier LIKE '+%' THEN
        v_phone := p_identifier;
        v_first_seen_as := 'phone';
    ELSE
        RAISE EXCEPTION 'Unknown identifier format: %', p_identifier;
    END IF;

    -- Tenter la résolution
    contact_uuid := resolve_contact_z1(p_identifier);

    IF contact_uuid IS NOT NULL THEN
        -- Contact existant → update last_seen + enrichir si champ manquant
        UPDATE contacts_z1 SET
            last_seen_at = now(),
            push_name = COALESCE(p_push_name, push_name),
            phone_e164 = COALESCE(phone_e164, v_phone),
            jid_classic = COALESCE(jid_classic, v_jid_classic),
            lid = COALESCE(lid, v_lid)
        WHERE id = contact_uuid;
        RETURN contact_uuid;
    END IF;

    -- Nouveau contact
    INSERT INTO contacts_z1 (
        phone_e164, jid_classic, lid, push_name, zone,
        first_seen_as, first_seen_at, last_seen_at
    ) VALUES (
        v_phone, v_jid_classic, v_lid, p_push_name, p_zone,
        v_first_seen_as, now(), now()
    )
    RETURNING id INTO contact_uuid;

    RETURN contact_uuid;
END;
$$ LANGUAGE plpgsql;

-- =========================================================================
-- log_message_z1 — Insère un message avec résolution auto du contact
-- =========================================================================
CREATE OR REPLACE FUNCTION log_message_z1(
    p_wa_message_id         TEXT,
    p_sender_identifier     TEXT,
    p_direction             TEXT,
    p_body                  TEXT,
    p_received_at           TIMESTAMPTZ,
    p_push_name             TEXT DEFAULT NULL,
    p_media_type            TEXT DEFAULT NULL,
    p_media_url             TEXT DEFAULT NULL,
    p_is_group              BOOLEAN DEFAULT false,
    p_quoted_wa_message_id  TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_contact_id        UUID;
    v_identifier_type   TEXT;
    v_message_id        UUID;
BEGIN
    -- Résolution ou création du contact
    v_contact_id := upsert_contact_z1(p_sender_identifier, p_push_name, 'Z1');

    -- Type d'identifiant
    IF p_sender_identifier LIKE '%@lid' THEN
        v_identifier_type := 'lid';
    ELSE
        v_identifier_type := 'jid';
    END IF;

    -- Insert message (idempotent via wa_message_id UNIQUE)
    INSERT INTO messages_z1 (
        contact_id, received_identifier, identifier_type,
        wa_message_id, direction, body,
        media_type, media_url,
        bridge, is_group, quoted_wa_message_id,
        received_at
    ) VALUES (
        v_contact_id, p_sender_identifier, v_identifier_type,
        p_wa_message_id, p_direction, p_body,
        p_media_type, p_media_url,
        'wa_z1', p_is_group, p_quoted_wa_message_id,
        p_received_at
    )
    ON CONFLICT (wa_message_id) DO UPDATE SET
        contact_id = EXCLUDED.contact_id  -- cas où le contact a été résolu plus tard
    RETURNING id INTO v_message_id;

    RETURN v_message_id;
END;
$$ LANGUAGE plpgsql;

-- =========================================================================
-- detect_lid_migration_z1 — Heuristique de détection JID → LID
-- À appeler quand un message LID arrive d'un push_name déjà connu en JID.
-- =========================================================================
CREATE OR REPLACE FUNCTION detect_lid_migration_z1(
    p_new_lid           TEXT,
    p_push_name         TEXT
) RETURNS UUID AS $$
DECLARE
    v_candidate_id      UUID;
    v_old_jid           TEXT;
    v_migration_log_id  UUID;
BEGIN
    -- Chercher un contact avec même push_name mais JID != LID
    SELECT id, jid_classic INTO v_candidate_id, v_old_jid
        FROM contacts_z1
        WHERE push_name = p_push_name
          AND jid_classic IS NOT NULL
          AND (lid IS NULL OR lid != p_new_lid)
        ORDER BY last_seen_at DESC
        LIMIT 1;

    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    -- Log la détection (pending, à valider par rtm-bot ou Patrick)
    INSERT INTO lid_migration_log_z1 (
        contact_id, old_jid, new_lid,
        detection_method, confidence, detected_at
    ) VALUES (
        v_candidate_id, v_old_jid, p_new_lid,
        'push_name_match', 0.75, now()
    )
    RETURNING id INTO v_migration_log_id;

    RETURN v_migration_log_id;
END;
$$ LANGUAGE plpgsql;

-- =========================================================================
-- apply_lid_migration_z1 — Applique une migration détectée (après validation)
-- =========================================================================
CREATE OR REPLACE FUNCTION apply_lid_migration_z1(
    p_migration_log_id  UUID,
    p_applied_by        TEXT DEFAULT 'auto'
) RETURNS BOOLEAN AS $$
DECLARE
    v_contact_id    UUID;
    v_new_lid       TEXT;
BEGIN
    SELECT contact_id, new_lid INTO v_contact_id, v_new_lid
        FROM lid_migration_log_z1
        WHERE id = p_migration_log_id AND applied_at IS NULL;

    IF NOT FOUND THEN
        RETURN false;
    END IF;

    -- Appliquer au contact
    UPDATE contacts_z1 SET
        lid = v_new_lid,
        lid_migrated_at = now()
        WHERE id = v_contact_id;

    -- Marquer comme appliqué
    UPDATE lid_migration_log_z1 SET
        applied_at = now(),
        applied_by = p_applied_by
        WHERE id = p_migration_log_id;

    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- =========================================================================
-- COMMENTS
-- =========================================================================
COMMENT ON FUNCTION resolve_contact_z1(TEXT) IS
    'Résout un JID, LID ou E.164 vers un contact_id. NULL si inconnu.';

COMMENT ON FUNCTION upsert_contact_z1(TEXT, TEXT, TEXT, TEXT) IS
    'Crée ou enrichit un contact Z1 à partir d''un identifiant WhatsApp.';

COMMENT ON FUNCTION log_message_z1(TEXT, TEXT, TEXT, TEXT, TIMESTAMPTZ, TEXT, TEXT, TEXT, BOOLEAN, TEXT) IS
    'Point d''entrée unique pour les scénarios Make : insère un message + résout auto le contact.';

COMMENT ON FUNCTION detect_lid_migration_z1(TEXT, TEXT) IS
    'Heuristique push_name : détecte un contact JID qui a probablement migré vers LID.';

COMMENT ON FUNCTION apply_lid_migration_z1(UUID, TEXT) IS
    'Applique une migration JID→LID après validation manuelle ou auto.';
