# Rollback Plan — Z1/Z1b Target Migration

> **STATUT : PROCÉDURE DE SECOURS — à exécuter uniquement si le Go-Live échoue**

## Principe directeur

Tant que la **fenêtre de rollback (T+4h)** n'est pas dépassée, un retour à l'état antérieur est **toujours possible** sans perte de données utilisateur — seuls les messages reçus pendant la fenêtre seront à re-traiter manuellement par Patrick (petit volume attendu : < 50 messages).

L'ancien système Make + datastores reste **intact** pendant toute la bascule. Les scénarios sont **désactivés**, pas supprimés.

## Critères déclenchant un rollback

Un seul critère suffit pour déclencher :

| Critère | Seuil | Qui décide |
|---------|-------|-----------|
| Erreurs Supabase 5xx | > 5% sur 10 min | Patrick (auto-alerte rtm-bot) |
| Contacts non résolus | > 10% sur 1h glissante | Patrick |
| Silence entrant anormal | > 2h heure ouvrée sans message | Patrick |
| Plainte utilisatrice Z1 | 1 plainte confirmée (visiteuse qui n'a pas reçu) | Patrick |
| Bug fonctionnel critique | bug reproductible, non contournable | Patrick |
| Hors fenêtre T+4h | — | Pas de rollback, gérer en fixe forward |

## Niveaux de rollback

### Niveau 1 — Rollback partiel (1 scénario)

**Quand** : 1 scénario `[Z1-TARGET]` dysfonctionne, les autres OK.

**Action** :
```
1. Dans Make : désactiver le scénario [Z1] concerné (toggle OFF)
2. Réactiver le scénario [Z1-ARCHIVE] correspondant (toggle ON)
3. Renommer [Z1-ARCHIVE] ← retirer le préfixe
4. Logger incident dans ADR-03 Asana (commentaire rtm-bot)
```

**Impact** : les autres scénarios migrés restent actifs. Pas de perte fonctionnelle.

**Durée** : 2 min par scénario.

---

### Niveau 2 — Rollback complet Make (bascule inverse)

**Quand** : plusieurs scénarios `[Z1-TARGET]` dysfonctionnent, ou problème transverse non localisé.

**Action** :
```
Pour CHAQUE scénario basculé :
  a) Désactiver le [Z1] (toggle OFF)
  b) Renommer [Z1] → [Z1-FAILED-YYYY-MM-DD]
  c) Renommer [Z1-ARCHIVE] <nom> → <nom> (retirer le préfixe)
  d) Réactiver l'ancien scénario (toggle ON)
```

**Validation** :
- Envoyer 1 message test sur wa_z1 (JID connu) → doit arriver dans l'ancien datastore Make
- Vérifier que le broadcast matinal suivant fonctionne

**Impact** :
- Messages reçus pendant la fenêtre (stockés dans `messages_z1` Supabase) sont **récupérables** :
  ```sql
  SELECT received_identifier, body, received_at
    FROM messages_z1
    WHERE received_at BETWEEN 'T+0' AND 'T+4h'
    ORDER BY received_at;
  ```
  → Patrick les re-traite manuellement après rollback.

- Les messages envoyés pendant la fenêtre (broadcasts) ont bien été délivrés — pas de double envoi au rollback.

**Durée** : 10-15 min.

---

### Niveau 3 — Rollback Supabase (suppression schéma)

**Quand** : problème au niveau schéma Supabase qui compromet la suite (ex: corruption, bug RPC).

**Action** :
```sql
-- Sur Supabase Z1 :

-- 1. Désactiver les RPC (empêche toute nouvelle écriture)
DROP FUNCTION IF EXISTS log_message_z1 CASCADE;
DROP FUNCTION IF EXISTS upsert_contact_z1 CASCADE;
DROP FUNCTION IF EXISTS resolve_contact_z1 CASCADE;
DROP FUNCTION IF EXISTS detect_lid_migration_z1 CASCADE;
DROP FUNCTION IF EXISTS apply_lid_migration_z1 CASCADE;

-- 2. Export de sécurité (avant drop)
COPY contacts_z1 TO '/tmp/z1_contacts_snapshot.csv' WITH CSV HEADER;
COPY messages_z1 TO '/tmp/z1_messages_snapshot.csv' WITH CSV HEADER;
COPY lid_migration_log_z1 TO '/tmp/z1_lid_log_snapshot.csv' WITH CSV HEADER;

-- 3. NE PAS dropper les tables si rollback de niveau 2 en cours
--    (les données serviront pour récupération manuelle)
-- À décider par Patrick selon le contexte.
```

**Impact** : le projet Supabase Z1 reste provisionné (pour retry futur). Les données sont sauvegardées en CSV.

**Durée** : 5 min.

---

### Niveau 4 — Abandon total (nucléaire)

**Quand** : problème systémique, retry Go-Live nécessite refonte.

**Action** :
1. Exécuter Niveau 2 (rollback Make complet) — priorité absolue, rétablir le service
2. Exécuter Niveau 3 (export Supabase) — préserver les données reçues
3. Ne PAS supprimer le projet Supabase Z1 — utile pour la prochaine tentative
4. Ouvrir un post-mortem dans ADR-03 Asana :
   - Qu'est-ce qui a échoué ?
   - Était-ce anticipable ?
   - Que changer pour la prochaine tentative ?
5. Replanifier le Go-Live (pas avant J+7 minimum, pour laisser le temps du fix)

**Durée** : 30-45 min (incluant communication Patrick → éventuellement visiteuses impactées).

---

## Communication pendant un rollback

| Destinataire | Quand | Quoi |
|--------------|-------|------|
| Patrick | Immédiat | Décision rollback prise, niveau choisi |
| rtm-bot | T+0 rollback | Log dans ADR-03 (auto-commentaire via agent) |
| Visiteuses Z1 | Uniquement si Niveau 4 et > 24h downtime | Message WhatsApp manuel Patrick : "désolée pour le délai, je reviens vers vous bientôt" |
| Support Supabase | Si bug Supabase-side | Ticket via console |

## Registre d'exécution (à remplir pendant le rollback réel)

| # | Timestamp | Niveau | Action | Exécuté par | Résultat |
|---|-----------|--------|--------|-------------|----------|
| 1 | | | | | |
| 2 | | | | | |
| ... | | | | | |

## Post-rollback — Mandatory

- [ ] Post-mortem rédigé dans ADR-03 Asana sous 48h
- [ ] Messages reçus pendant la fenêtre extraits de `messages_z1` et traités manuellement
- [ ] Plan retry Go-Live proposé à Patrick sous 72h (avec correctifs)
- [ ] Branche `claude/infra-z1-target-new` garde son état, ajouter un commit `rollback-YYYY-MM-DD` documentant l'incident

## Ce qu'il NE FAUT PAS faire en rollback

- ❌ Supprimer les tables `contacts_z1`, `messages_z1`, `lid_migration_log_z1` (garder pour analyse)
- ❌ Supprimer le projet Supabase Z1 (conserver pour retry)
- ❌ Supprimer les scénarios Make `[Z1-FAILED-*]` (conserver 30 jours minimum pour post-mortem)
- ❌ Dé-provisionner les credentials `SUPABASE_Z1_*` dans Make (les garder)
- ❌ Annoncer publiquement le rollback (communication interne uniquement sauf Niveau 4 prolongé)
