# Référence : Erreurs scénario Make 8944541 (SVLBH WhatsApp ROUTER)

> **BUT** : servir de référence d'entrée pour la conception de l'infra Z1/Z1b target. Pas de fix sur le scénario existant (Option B décidée par Patrick le 2026-04-20).

## Métadonnées scénario

| Champ | Valeur |
|-------|--------|
| Scenario ID | `8944541` |
| Name | SVLBH WhatsApp ROUTER |
| Team | `630342` |
| Organization | `1799074` |
| Hook ID | `4000349` |
| Created | `2026-03-26T20:20:02.867Z` |
| Last edit | `2026-04-18T07:57:51.984Z` |
| isActive | `true` |
| isPaused | `false` |
| **errors (cumulative)** | **`108`** |
| maxErrors config | `3` (ignoré — scénario ne pause pas) |
| Scheduling | `immediately` (webhook instant) |

## Datastores impliqués

| ID | Rôle | Clé utilisée | Champs |
|----|------|--------------|--------|
| `157329` | Registry contacts WhatsApp | `{{bridge}}-{{stripped_id}}` | jid, lid, phone, name, bridge |
| `155674` | Metadata contacts (segment, auto-reply, CRM) | `CT-{{from}}` | payload, segment, auto_reply, prenom, nom, email, telephone |

## Analyse des 50 dernières exécutions (2026-04-16 → 2026-04-20)

### Pattern observé

**Toutes les exécutions récentes réussissent (`status: 1`) avec EXACTEMENT 5 opérations.** Aucune exécution récente en status 3 (erreur).

→ Les **108 erreurs** sont un **compteur historique cumulé** (erreurs passées avant la dernière édition 2026-04-18). Les bugs actuels ne produisent **pas d'erreurs** — ils produisent des **données corrompues silencieuses**.

### Distribution des 50 dernières exécutions

| Métrique | Valeur |
|----------|--------|
| Status 1 (success) | 50 / 50 (100%) |
| Operations = 5 | 49 / 50 (98%) |
| Operations = 4 | 1 / 50 (2%) — execution `d8cb23ab` |
| Durée moyenne | 418 ms |
| Durée max | 1918 ms (exec `340a5197`) |
| Centicredits moyens | 500 (= 5 ops × 100) |

### Interprétation du "5 opérations constantes"

Le blueprint a les chemins d'exécution suivants :
- **Path A (Nouveau contact)** : `1 → 8 → 10` = 3 ops
- **Path B (existing + auto_reply)** : `1 → 8 → 2 → 3 → 4 → 5` = 6 ops
- **Path C (existing + no auto_reply)** : `1 → 8 → 2 → 3 → 7` = 5 ops

**→ 98% des exécutions suivent Path C : contact trouvé dans 157329 + contact trouvé dans 155674 + route "no auto_reply" (auto_reply=false ou filtres anti-triviaux matchent).**

Cela implique :
1. Les messages arrivent majoritairement de contacts déjà en base **avec `auto_reply=false`** dans datastore 155674
2. Le chemin de création de nouveau contact (Path A) est **rarement emprunté** dans les exécutions récentes
3. **Aucun contact LID pur** n'a traversé le scénario dans cette fenêtre — OU les contacts LID sont tous traités comme "nouveaux" et logués dans 157329 avec un faux téléphone

### Hypothèses de causes des 108 erreurs historiques

Comme le status actuel est 1 partout, les 108 erreurs passées venaient probablement de :

| Hypothèse | Probabilité | Signal |
|-----------|-------------|--------|
| **H1 — Lookup 155674 échoue sur LID** : key `CT-177111952306424@lid` inexistante → module 2 erreur non gérée | HAUTE | Cohérent avec découverte Eva (rtm-bot 2026-04-18 19h10) |
| **H2 — Claude Haiku rate-limit** : auto-reply route, module 4 échoue si quota Anthropic épuisé | MOYENNE | Modèle `claude-haiku-4-5-20251001` utilisé, volume inconnu |
| **H3 — Timeout webhook** : module 1 webhook dépasse 40s | FAIBLE | Durées observées < 2s |
| **H4 — Datastore 157329 ou 155674 plein** : limite Make free tier | FAIBLE | Pas d'indicateur actif |
| **H5 — Bug fix déployé 2026-04-18** : dernière édition du scénario ce jour → une partie des 108 erreurs a été corrigée mais le compteur cumulé reste | HAUTE | `lastEdit: 2026-04-18T07:57:51.984Z` |

**Hypothèse dominante : H1 + H5.** Les erreurs LID ont probablement été en partie corrigées le 2026-04-18 (peut-être ajout du stripping `@lid` dans la clé), mais le bug de données corrompues persiste (phantom contacts LID avec faux téléphone).

## Extrait de 5 exécutions récentes (échantillon)

| Timestamp | Exec ID | Duration | Ops | Status |
|-----------|---------|----------|-----|--------|
| 2026-04-20T08:24:16 | `7bc8d8df...` | 367ms | 5 | SUCCESS |
| 2026-04-20T07:52:20 | `b6b4fc62...` | 328ms | 5 | SUCCESS |
| 2026-04-20T07:04:17 | `f055a25b...` | 476ms | 5 | SUCCESS |
| 2026-04-19T17:00:23 | `340a5197...` | **1918ms** | 5 | SUCCESS (durée anormale) |
| 2026-04-18T08:00:36 | `d8cb23ab...` | 342ms | **4** | SUCCESS (ops différent) |

## Implications pour le design Z1/Z1b target

Cette analyse **renforce 3 choix architecturaux** du schéma `001_z1_schema.target.sql` et ajoute **2 nouvelles exigences** :

### Choix validés (déjà dans le design)

1. ✅ **Schéma LID séparé** (`jid_classic`, `lid` colonnes distinctes) — répond à H1
2. ✅ **Log systématique dans `messages_z1`** — permet la détection de bugs silencieux (qu'on ne voit pas comme "erreurs" Make)
3. ✅ **RPC `resolve_contact_z1`** qui matche sur JID **ET** LID — élimine la cause H1

### Nouvelles exigences à ajouter au runbook Go-Live

4. 🆕 **Observability "silent bad data"** : il ne suffit pas de surveiller les erreurs Supabase. Il faut aussi surveiller :
   - Contacts créés sans `phone_e164` mais avec un `lid` (= phantom contact potentiel)
   - Requête de monitoring à ajouter à `v_z1_health` :
     ```sql
     (SELECT COUNT(*) FROM contacts_z1
      WHERE phone_e164 IS NULL
        AND lid IS NOT NULL
        AND created_at > now() - interval '1 hour') as phantom_contacts_last_hour
     ```

5. 🆕 **Préserver la distribution auto_reply** : 98% des messages = `auto_reply=false`. Le migration Supabase doit préserver cette flag côté `contacts_z1.auto_reply_enabled` (à ajouter au schéma).

### Suggestion de refactoring schema

Ajouter à `001_z1_schema.target.sql` (à valider avec Patrick) :

```sql
ALTER TABLE contacts_z1 ADD COLUMN auto_reply_enabled BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE contacts_z1 ADD COLUMN segment TEXT;  -- depuis datastore 155674
ALTER TABLE contacts_z1 ADD COLUMN crm_prenom TEXT;
ALTER TABLE contacts_z1 ADD COLUMN crm_nom TEXT;
ALTER TABLE contacts_z1 ADD COLUMN crm_email TEXT;
```

## Contacts test identifiés pour le smoke test Jour D

Basé sur les découvertes :

| Test | Contact | Type | Statut attendu dans datastore Make actuel |
|------|---------|------|-------------------------------------------|
| T1 | Patrick (numéro perso) | JID classique | Présent dans 157329 + 155674 |
| T2 | Eva (41765135784 → 177111952306424@lid) | **LID migré** | Dans 157329 sous faux téléphone, absent ou mal indexé dans 155674 |
| T3 | Contact test neuf (numéro jamais vu) | Nouveau JID | Absent des deux datastores |

## Références

- ADR-03 : [WhatsApp bridges pérennes sur patricktest](https://app.asana.com/1/1214046872168643/project/1214127314362625/task/1214141207943673)
- Task scenario 8944541 : [Infra messagerie critique](https://app.asana.com/1/1214046872168643/project/1214033478319998/task/1214135119657875)
- Task Z1 TARGET : [Préparation Go Transition](https://app.asana.com/1/1214046872168643/project/1214033517139508/task/1214126088656424)
- Message rtm-bot déclencheur : 2026-04-18 19h10 (découverte LID Eva)
- Décision Option B : commentaire Asana rtm-bot du 2026-04-20 10h01

## Extraction brute (pour archive)

```
Source   : MCP Make (mcp__a9f71a2b__executions_list + scenarios_get)
Date extraction : 2026-04-20
Fenêtre  : 2026-04-16 08:15 → 2026-04-20 08:24 (50 exécutions + 1 event modify)
Blueprint : voir docs/z1-target-infra/reference/scenario_8944541_blueprint.json (à générer au Jour D-1 avant Go)
```
