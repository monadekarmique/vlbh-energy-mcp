# Runbook — Go-Live Z1/Z1b Target (Bascule Blue/Green)

> **STATUT : PRÊT POUR EXÉCUTION — attend signature Go Transition par Patrick**

## Fenêtre recommandée

- **Jour** : mardi ou mercredi (évite week-end, évite lundi routine matin)
- **Heure** : 10:00 - 12:00 CET (après le broadcast matinal 09:00, avant pic messages soir)
- **Durée estimée** : 45 min (exécution) + 4h (monitoring actif) + 20h (monitoring passif)
- **Rollback window** : T+4h maximum

## Prérequis (à valider la veille)

- [ ] Toutes les checklists de `README.md` et `makecom_scenarios_to_duplicate.md` cochées
- [ ] Backup Make datastores Z1 exporté (CSV) et stocké sur Google Drive VLBH
- [ ] Projet Supabase Z1 provisionné, connectivité OK depuis Make (test ping HTTP)
- [ ] Tous les scénarios `[Z1-TARGET]` en OFF dans Make
- [ ] Patrick disponible pendant toute la fenêtre (décisions rollback)
- [ ] rtm-bot@vlbh.energy opérationnel (alertes healthcheck actives)
- [ ] Accès console Supabase Z1 ouvert dans un onglet dédié
- [ ] Accès Make.com ouvert dans un second onglet dédié

## Rôles

- **Exécutant** : Patrick (ou Claude Code pour les étapes SQL)
- **Validateur** : Patrick uniquement (décisions Go/No-Go par phase)
- **Observateur** : rtm-bot@vlbh.energy (alertes automatiques en arrière-plan)

## Communication

- Canal principal : WhatsApp direct Patrick
- Messages opérationnels : thread dédié rtm-bot
- Pas de communication externe pendant la fenêtre (visiteuses, shamanes) — silence radio Z1

---

## Phase 0 — T-15 min : Pre-flight check

```bash
# 1. Vérifier l'état Git
cd ~/vlbh-energy-mcp
git checkout claude/infra-z1-target-new
git pull origin claude/infra-z1-target-new
git status   # doit être clean

# 2. Vérifier l'accès Supabase Z1
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "apikey: $SUPABASE_Z1_ANON_KEY" \
  "$SUPABASE_Z1_URL/rest/v1/"
# Attendu : 200
```

**Go/No-Go** : si l'un des checks échoue → **STOP, investigate**.

---

## Phase 1 — T+0 : Déploiement du schéma Supabase Z1

**Objectif** : créer les tables et RPC sur Supabase Z1 (environnement vide → prêt à recevoir).

```sql
-- Connect to Supabase Z1 SQL Editor
-- Exécuter dans l'ordre :

-- 1. Schema
\i docs/z1-target-infra/001_z1_schema.target.sql

-- 2. RPC functions
\i docs/z1-target-infra/002_z1_rpc.target.sql

-- 3. Smoke test
SELECT resolve_contact_z1('+41765135784@s.whatsapp.net');  -- attendu : NULL
SELECT upsert_contact_z1('41765135784@s.whatsapp.net', 'Eva Test', 'Z1');
-- attendu : UUID
SELECT resolve_contact_z1('41765135784@s.whatsapp.net');
-- attendu : même UUID que ci-dessus
```

**Validation** : 3 tables créées, 5 RPC exposées, smoke test OK.

**Go/No-Go** : si erreur SQL → **ABORT**, exécuter `rollback_plan.md` § Phase 1.

**Durée** : 5 min.

---

## Phase 2 — T+5 : Seed depuis l'ancien datastore Make

**Objectif** : importer les contacts Z1 existants dans la nouvelle table `contacts_z1`.

```bash
# 1. Export datastore Make Z1 (fait la veille, CSV en local)
# File: ~/vlbh-z1-export-YYYY-MM-DD.csv
# Columns: numero, push_name, premier_message, last_seen, ...

# 2. Transform CSV → SQL INSERT (script helper)
python docs/z1-target-infra/seed_from_make_csv.py \
  --input ~/vlbh-z1-export-YYYY-MM-DD.csv \
  --output /tmp/z1_seed.sql

# 3. Apply on Supabase Z1
psql "$SUPABASE_Z1_URL" -f /tmp/z1_seed.sql
```

**Validation** :
```sql
SELECT COUNT(*) FROM contacts_z1;  -- doit matcher le nombre de records CSV
SELECT zone, onboarding_status, COUNT(*)
  FROM contacts_z1 GROUP BY 1, 2;
```

**Go/No-Go** : si écart de comptage > 1% → investigate. Si > 5% → **ABORT**.

**Durée** : 10 min.

> NOTE : le script `seed_from_make_csv.py` n'existe pas encore — à créer selon le format exact de l'export Make. Patrick fournit le CSV la veille.

---

## Phase 3 — T+15 : Bascule des scénarios Make

**Objectif** : activer les scénarios `[Z1-TARGET]` et désactiver les anciens **atomiquement**.

Ordre strict (UN scénario à la fois, validation entre chaque) :

```
Pour chaque scénario listé dans makecom_scenarios_to_duplicate.md :

  a) Désactiver l'ancien scénario (toggle OFF)
  b) Renommer l'ancien : "[Z1-ARCHIVE] <nom original>"
  c) Activer le clone [Z1-TARGET] (toggle ON)
  d) Renommer le clone : "[Z1] <nom original>" (retirer TARGET)
  e) Envoyer 1 message test depuis un numéro de test Patrick
  f) Vérifier réception dans Supabase :
       SELECT * FROM messages_z1 ORDER BY received_at DESC LIMIT 5;
  g) Si OK → scénario suivant
  h) Si KO → rollback immédiat ce scénario (toggle inverse)
```

**Go/No-Go entre chaque scénario** : si échec sur 1 scénario → stopper la bascule, rollback ce scénario, investiguer. Les autres scénarios déjà basculés restent actifs.

**Durée** : 15 min (dépend du nombre de scénarios, ~3 min chacun).

---

## Phase 4 — T+30 : Test end-to-end

**Objectif** : valider le flux complet entrant et sortant avec 3 contacts test (couvrent tous les cas).

| Test | Contact | Action | Résultat attendu |
|------|---------|--------|------------------|
| T1 — JID classique | Patrick (numéro perso) | Envoie "test JID" vers +41798131926 | Message apparaît dans `messages_z1` avec `identifier_type = 'jid'` |
| T2 — LID pur | Eva (41765135784 migrée) | Envoie "test LID" vers +41798131926 | Message apparaît avec `identifier_type = 'lid'` + `detect_lid_migration_z1` log |
| T3 — Sortant broadcast | — | Déclencher manuellement scénario Routine Matin sur 1 contact test | Message reçu côté contact test, entrée `direction='out'` dans DB |

**Go/No-Go** : les 3 tests doivent passer. Un échec → **rollback** (cf. `rollback_plan.md`).

**Durée** : 10 min.

---

## Phase 5 — T+40 : Activation monitoring

```sql
-- Créer une vue monitoring
CREATE OR REPLACE VIEW v_z1_health AS
SELECT
  (SELECT COUNT(*) FROM messages_z1 WHERE received_at > now() - interval '1 hour') as msg_last_hour,
  (SELECT COUNT(*) FROM messages_z1 WHERE received_at > now() - interval '1 hour' AND contact_id IS NULL) as msg_unresolved_last_hour,
  (SELECT COUNT(*) FROM lid_migration_log_z1 WHERE detected_at > now() - interval '1 hour' AND applied_at IS NULL) as pending_lid_migrations;
```

**Alertes rtm-bot à activer** :
- `msg_unresolved_last_hour > 3` → email alerte (contact non résolu = possible bug JID/LID)
- `msg_last_hour == 0 AND heure_ouvrée` → email alerte (silence anormal = bridge down ?)
- `pending_lid_migrations > 10` → email info (batch validation nécessaire)

**Durée** : 5 min.

---

## Phase 6 — T+45 → T+4h : Monitoring actif

- Consulter `SELECT * FROM v_z1_health;` toutes les 30 min
- Si message LID non résolu : investiguer dans les 10 min
- Si aucun message entrant dans une plage normalement active : investiguer

**Seuil déclenchant rollback** :
- Taux d'unresolved > 10% sur 1h glissante
- Aucune réception entrante confirmée dans 2h sur heure normalement active
- Erreur système sur Supabase Z1 (5xx, timeouts > 5%)

---

## Phase 7 — T+4h → T+24h : Monitoring passif

- Alertes rtm-bot seules (pas de surveillance active Patrick requise)
- Compile-rendu T+24h : rapport récap dans ADR-03 Asana (commentaire)

---

## Post-Go (J+1)

- [ ] Renommer `001_z1_schema.target.sql` → `001_z1_schema.live.sql` (retrait suffixe target)
- [ ] Renommer `002_z1_rpc.target.sql` → `002_z1_rpc.live.sql`
- [ ] Commit + push rename sur `claude/infra-z1-target-new`
- [ ] Créer PR vers `main` pour mergeage
- [ ] Archiver les anciens scénarios Make `[Z1-ARCHIVE]` (conservation 30 jours avant suppression)
- [ ] Mettre à jour SPRINT_STATE.md avec le nouveau statut
- [ ] Commentaire de clôture sur ADR-03 Asana : "Go-Live Z1 OK — migration LID gérée"

## Critères de succès

- ✅ 100% des messages entrants sur wa_z1 (JID + LID) apparaissent dans `messages_z1` sur 24h
- ✅ 0 dépendance restante sur le datastore Make Z1 historique
- ✅ Taux de résolution JID/LID > 99% (< 1% de `contact_id IS NULL`)
- ✅ Aucune plainte visiteuse "je n'ai pas reçu de réponse"
- ✅ rtm-bot silencieux pendant 24h (pas d'alerte critique)
