# Draft 09 — Rétroactivité : migration des données existantes vers SVLBH_Identifier

**Version** : 0.1
**Date** : 2026-04-17
**Statut** : Draft pour revue technique + validation juridique (consentement rétroactif)
**Parent** : `data-model-vlbh.md` v0.2 — question ouverte n°9
**Dépendance** : coordonné avec Draft 05 (migration Make → Supabase)

---

## Changelog

| Version | Date | Changements |
|---|---|---|
| 0.1 | 2026-04-17 | Draft initial — analyse hash legacy, processus de re-pseudonymisation, affectation régionale |

---

## 1. État actuel

### 1.1 Le hash 256 tronqué à 28 caractères

Les contacts actuellement en base (datastore Make `svlbh-whatsapp-contacts #157329`) sont identifiés par un hash SHA-256 tronqué à 28 caractères, généré à partir de WhatsApp ID + prénom + LID.

### 1.2 Limites du hash actuel

- **Réversibilité par force brute** : l'espace des WhatsApp IDs est bornés (format téléphone E.164, ~10^12 possibilités). Un attaquant disposant de la base et d'un range de numéros plausibles peut retrouver le WhatsApp ID source. Le hash ne constitue donc pas une **pseudonymisation forte** au sens de l'art. 4.5 RGPD.
- **Pas d'affectation régionale** : le hash ne porte aucune information de résidence. Tout le stock est actuellement hébergé en UE (Make.com Prague/Francfort).
- **Pas de continuité transzone** : le hash est lié au canal WhatsApp. Si une utilisatrice change de numéro ou entre par un autre canal, la continuité est cassée.
- **Exposition dans les logs** : le hash étant construit à partir d'inputs connus, il apparaît dans les logs Make et peut être corrélé avec d'autres systèmes.

### 1.3 Volumétrie

À mesurer dans le cadre de la Phase 0 du Draft 05. Hypothèse de travail : plusieurs milliers de contacts actifs, plusieurs dizaines de milliers d'historiques.

---

## 2. État cible

Chaque contact existant doit disposer :

1. D'un **SVLBH_Identifier opaque** (UUID v4 ou ULID) non dérivé des données sources
2. D'une **affectation régionale** dans `svlbh_residency_directory` (CH, EU, CA)
3. D'une inscription dans `svlbh_identifier_registry` avec historique de zone
4. De la **suppression du hash legacy** après validation de la migration

---

## 3. Processus de migration — six étapes

### Étape 1 — Génération des nouveaux UUIDs

Pour chaque record existant, génération d'un UUID v4 indépendant de tout input utilisateur.

```sql
-- pseudocode
FOR EACH record IN legacy_make_contacts:
  new_uuid = uuid_v4()
  INSERT INTO migration_mapping (legacy_hash, svlbh_id, legacy_source)
  VALUES (record.hash_256_28, new_uuid, 'make_157329')
```

La table `migration_mapping` est :
- Stockée dans un schéma temporaire protégé
- Accessible uniquement à un compte de service migration (pas en lecture normale)
- Chiffrée au repos
- Destinée à être **détruite** après validation de la migration (étape 6)

### Étape 2 — Migration des records vers Supabase avec svlbh_id

Insertion dans `visitor_contact` avec le nouveau svlbh_id comme PK, et conservation temporaire de `pseudonym_hash_legacy` comme colonne dépréciée.

### Étape 3 — Réécriture des références dans les autres datastores

Tout datastore Make qui référençait un contact par son hash legacy doit être mis à jour pour référencer le svlbh_id.

Exemples de références à identifier :
- `svlbh-apple-identity #156475` : lookup par hash WhatsApp → bascule sur svlbh_id
- Logs Make (orchestration) : les nouveaux logs utilisent svlbh_id, les anciens restent en legacy
- Scénarios Make : refactoring pour requêter sur svlbh_id

### Étape 4 — Affectation régionale

C'est l'étape la plus délicate car **on ne connaît pas la résidence déclarée** de la plupart des contacts historiques.

Stratégie proposée en trois volets :

**Volet A — Heuristique de départ**
- Tous les contacts sont affectés par défaut à `EU` dans `svlbh_residency_directory`
- Le flag `declared_source = 'migration_default'` indique que la résidence n'a pas été déclarée formellement
- Pas d'impact pratique immédiat puisque Z1 est monorégion EU de toute façon

**Volet B — Enrichissement par indicatif téléphonique**
- Pour les contacts avec indicatif WhatsApp +41 (Suisse) ou +33/+49/+... (UE) : inférence probable de résidence
- Pour +1 : ambigu (USA ou Canada — distinguer par NPA). Si NPA canadien : CA probable
- Inscription avec `declared_source = 'inferred_phone_prefix'` — à confirmer à la prochaine interaction

**Volet C — Confirmation à la prochaine interaction**
- Lors du prochain échange WhatsApp avec chaque contact, une question courte est intégrée dans le flux conversationnel :
  « Pour mieux respecter ton cadre juridique, tu résides actuellement en : 🇨🇭 Suisse / 🇪🇺 Union européenne / 🇨🇦 Canada / Autre »
- La réponse met à jour `svlbh_residency_directory.declared_residency` et passe `declared_source = 'user_confirmed'`
- Si aucune réponse après 90 jours, rester en défaut EU

### Étape 5 — Validation de la migration

- Reconciliation : chaque hash legacy a bien un svlbh_id associé, chaque svlbh_id a son record migré
- Intégrité référentielle : toutes les références cross-datastore pointent sur des svlbh_id valides
- Tests applicatifs : les scénarios Make fonctionnent avec la nouvelle clé

### Étape 6 — Destruction de la table de mapping

Une fois la validation confirmée (délai de sécurité recommandé : 30 jours post-migration) :
- Export chiffré de `migration_mapping` conservé hors ligne pendant 12 mois (traçabilité audit)
- Destruction de la table en ligne
- Après 12 mois, destruction de l'export hors ligne

**Après destruction, la migration est irréversible** : il devient impossible de retrouver le hash legacy d'un svlbh_id. C'est précisément l'objectif de pseudonymisation forte.

---

## 4. Enjeu juridique majeur — consentement rétroactif

### 4.1 Le problème

Les contacts actuels en base n'ont pas signé les clauses du nouveau cadre (politique de rétention, affectation régionale, SVLBH_Identifier, etc.). Leur consentement initial (implicite via l'entrée WhatsApp) couvrait Zone 1 telle qu'elle existait.

Une refonte de cette ampleur soulève la question : faut-il obtenir un nouveau consentement ?

### 4.2 Analyse juridique préliminaire

**Arguments « pas de re-consent nécessaire »** :
- Les finalités restent identiques (communication, orientation)
- L'amélioration de la sécurité (SVLBH_Identifier vs hash réversible) est dans l'intérêt de l'utilisatrice
- L'affectation régionale est une mesure de protection, pas un transfert supplémentaire
- Le changement est une **amélioration matérielle de la conformité** sans modification des finalités

**Arguments « re-consent prudentiel »** :
- Le changement de système d'enregistrement (Make → Supabase) constitue un nouveau sous-traitant
- L'art. 13.2.a RGPD impose d'informer la personne concernée des évolutions
- La Loi 25 du Québec est plus stricte sur l'information préalable

### 4.3 Proposition

**Information, pas re-consentement** — approche pragmatique :

1. Un message d'information est envoyé à chaque contact lors de sa prochaine interaction (pas de push massif qui ressemblerait à du spam) :
   > « Pour mieux te protéger, nous avons renforcé notre système d'identification. Tu gardes le contrôle total sur tes données. Consulte notre politique à vlbh.energy/vie-privee. Tu peux retirer ton consentement à tout moment en répondant STOP. »

2. Cette notification est loggée (preuve d'information).

3. Pas de ré-opt-in actif demandé — la continuité de l'échange vaut acceptation (opt-out permanent disponible via STOP).

4. **Validation juridique nécessaire** avant mise en œuvre.

### 4.4 Cas particulier du Québec

La Loi 25 est plus exigeante sur l'information. Pour les contacts dont l'affectation régionale aboutit à `CA` avec NPA québécois, envisager :
- Notification plus complète (document d'information dédié)
- Opt-in actif pour certaines finalités nouvelles
- Consulter un conseil québécois spécialisé avant migration des records CA-QC

---

## 5. Calendrier — alignement avec Draft 05

| Phase Draft 05 | Action Draft 09 correspondante |
|---|---|
| Phase 0 — Préparation | Provisionner `migration_mapping`, valider schéma cible |
| Phase 1 — Dual-write | Chaque nouvel entrant reçoit svlbh_id natif (pas de hash legacy) |
| Phase 2 — Migration historique | Exécution des étapes 1-3 du présent draft |
| Phase 3 — Validation | Reconciliation mapping + tests |
| Phase 4 — Cutover | Scénarios Make basculent sur svlbh_id |
| Phase 5 — Shards régionaux | Application du `svlbh_residency_directory` (volet A + B) |
| Phase 6 — Décommissionnement | Destruction de `migration_mapping`, suppression du hash legacy |

Le volet C (confirmation utilisatrice de résidence) s'exécute **en continu** pendant les 6 à 12 mois suivants, au fil des interactions WhatsApp.

---

## 6. Risques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| Corruption de la table `migration_mapping` pendant la migration | Perte de liaison legacy ↔ svlbh_id = migration à refaire | Backup intermédiaire toutes les heures pendant la phase batch |
| Contact refuse l'affectation régionale inférée | Plainte auprès de l'autorité | Volet C : toujours possible de corriger via interaction simple. Opt-out via STOP |
| Découverte post-migration d'un contact avec résidence différente de l'inférence | Donnée dans le mauvais shard | Processus de migration inter-shard sur déclaration (Draft parallèle à prévoir) |
| Consentement rétroactif jugé insuffisant par une autorité | Ordre de suppression/injonction | Validation juridique formelle avant phase 2 |
| Volumes massifs → migration > fenêtre planifiée | Dépassement calendrier Draft 05 | Batch par tranches de 10k records avec reprise sur erreur |

---

## 7. Critères de succès

- 100% des contacts legacy ont un svlbh_id valide
- 100% ont une affectation dans `svlbh_residency_directory` (même si défaut EU)
- 0 référence legacy_hash restante dans les datastores de production à la fin
- Information préalable envoyée et loggée pour chaque contact
- Destruction effective de `migration_mapping` validée par un audit technique
- Trail d'audit complet conservé pour démontrer la conformité

---

## 8. Décisions à valider

- **Consentement rétroactif** : information passive vs opt-in actif ? Décision juridique requise.
- **Traitement spécifique QC** : conseil québécois à solliciter ou on applique le standard le plus strict uniformément ?
- **Durée de conservation de l'export hors ligne** de `migration_mapping` après destruction en ligne : 12 mois proposés, à confirmer.
- **Inférence par indicatif téléphonique** : acceptable éthiquement et juridiquement, ou trop fragile ?
