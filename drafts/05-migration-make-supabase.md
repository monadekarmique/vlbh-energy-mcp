# Draft 05 — Plan de migration Make → Supabase

**Version** : 0.1
**Date** : 2026-04-17
**Statut** : Draft pour revue technique + validation PO-08
**Parent** : `data-model-vlbh.md` v0.2 — question ouverte n°5
**Destinataire prévu** : équipe technique, PO-08 Data Quality

---

## Changelog

| Version | Date | Changements |
|---|---|---|
| 0.1 | 2026-04-17 | Draft initial — inventaire, stratégie dual-write, phasage, plan de rollback |

---

## 1. Objectifs

- Faire basculer le système d'enregistrement canonique des datastores Make.com vers Supabase (shards régionaux EU, CH, CA + Suisse neutre pour le directory).
- Conserver Make.com comme **buffer d'orchestration** (scénarios entrants/sortants) mais supprimer son rôle de source de vérité.
- Introduire le SVLBH_Identifier opaque (UUID) comme pivot en remplacement du hash 256 tronqué 28 actuellement utilisé.
- Mettre en place la géo-fragmentation Z2/Z3 par shard régional conformément à `data-model-vlbh.md` v0.2.
- Zéro perte de données utilisatrices pendant la migration.

---

## 2. État actuel — inventaire des datastores Make

| Datastore | ID Make | Fonction actuelle | Volume estimé | Cible Supabase |
|---|---|---|---|---|
| svlbh-whatsapp-contacts | #157329 | Contacts WhatsApp Z1 + hash 256-28 | À mesurer (préciser) | `visitor_contact` / shard EU |
| svlbh-apple-identity | #156475 | Invitations TestFlight | ~50 (testeuses actives) | `apple_identity` / shard EU |
| billing_praticien | #156396 | Facturation + pointeurs patientes | À mesurer | **À éclater** — voir §4.3 |
| [autres à inventorier] | ? | ? | ? | ? |

**Action préalable** : audit exhaustif des datastores Make (PO-08) pour compléter ce tableau.

---

## 3. État cible — schéma Supabase

Conformément à `data-model-vlbh.md` v0.2 :

- **Pivot global Suisse** (Infomaniak) : `svlbh_identifier_registry`, `svlbh_residency_directory`
- **Shard EU Supabase Francfort** : `visitor_contact`, `apple_identity`, + Z2-EU et Z3-EU
- **Shard CH Infomaniak/Exoscale** : Z2-CH, Z3-CH
- **Shard CA Supabase Toronto/OVH** : Z2-CA, Z3-CA

---

## 4. Mapping détaillé par datastore

### 4.1 svlbh-whatsapp-contacts #157329 → `visitor_contact`

| Champ Make | Champ Supabase | Transformation |
|---|---|---|
| hash_256_28 (legacy) | `pseudonym_hash_legacy` | Copié tel quel pour rétrocompatibilité, deprecated |
| — | `svlbh_id` | **Nouveau** — UUID v4 généré pour chaque record |
| whatsapp_id | `whatsapp_id` | Chiffré AES-256 au repos |
| prenom | `first_name` | Copié |
| lid | `lid` | Copié |
| created_at | `created_at` | Copié |

### 4.2 svlbh-apple-identity #156475 → `apple_identity`

| Champ Make | Champ Supabase | Transformation |
|---|---|---|
| email | `email` | Chiffré AES-256 |
| apple_id OR google_id | `apple_id` / `google_id` | Copié |
| — | `svlbh_id` | Lookup dans `visitor_contact` via WhatsApp si existant, sinon nouveau UUID |
| testflight_invite_sent_at | `testflight_invite_sent_at` | Copié |
| — | `consent_email_timestamp` | **À reconstruire** : date du premier échange ou consentement rétroactif demandé |
| — | `consent_text_version` | `"legacy-pre-v0.2"` par défaut |

**Risque** : les consentements email actuels ne sont pas horodatés de manière formelle. Décision à prendre (§8).

### 4.3 billing_praticien #156396 → éclatement en trois tables

| Nature du record | Destination |
|---|---|
| Identité praticienne + certification | `praticienne_profile` — shard de résidence de la praticienne |
| Redevances réseau / B2B commercial | `billing_praticien` — shard de résidence de la praticienne |
| Dossiers patientes | `patient_record` + `patient_vibrational_signatures` — shard de résidence de **la patiente** |

**Challenge** : le datastore actuel mélange les trois. Nécessite une phase d'annotation manuelle ou semi-automatique pour classifier chaque record avant bascule. Estimation : 2-3 semaines d'effort selon volume.

---

## 5. Calendrier — six phases

### Phase 0 — Préparation (S+0 à S+2)
- Provisionnement Supabase EU Francfort
- Création des schémas SQL (DDL à produire en v0.3 du data model)
- Setup des secrets, keys, RLS policies
- Audit complet des datastores Make (PO-08)

### Phase 1 — Dual-write (S+2 à S+6)
- Modification des scénarios Make pour écrire simultanément dans Make (legacy) et dans Supabase (cible)
- Génération du SVLBH_Identifier à chaque nouvelle entrée
- Monitoring quotidien de la cohérence (reconciliation script)

### Phase 2 — Migration historique (S+6 à S+8)
- Script batch : pour chaque record Make existant, générer un svlbh_id, insérer dans Supabase
- Pour `billing_praticien` : annotation manuelle puis éclatement
- Affectation régionale par défaut : tout en shard EU avec flag `residency_declared = false` (à confirmer avec l'utilisatrice lors de la prochaine interaction)

### Phase 3 — Validation (S+8 à S+10)
- Reconciliation complète Make ↔ Supabase
- Tests d'intégrité référentielle (tous les FK SVLBH_Identifier résolvent)
- Tests applicatifs (scénarios Make lisent désormais depuis Supabase en parallèle)
- Correction des écarts

### Phase 4 — Cutover (S+10, week-end)
- Bascule : Make lit désormais Supabase comme source de vérité
- Make continue d'écrire (orchestration) mais ne garde plus de miroir local
- Monitoring renforcé pendant 7 jours

### Phase 5 — Provisionnement shards CH et CA (S+12 à S+16)
- Création des instances Infomaniak/Exoscale (CH) et Supabase Toronto/OVH (CA)
- Migration des records déjà affectés régionalement
- Activation du routage via `svlbh_residency_directory`

### Phase 6 — Décommissionnement legacy (S+18)
- Suppression des datastores Make redondants (contacts, apple-identity)
- Conservation d'un export chiffré hors ligne pendant 12 mois (traçabilité)
- Suppression du champ `pseudonym_hash_legacy` de Supabase après vérification qu'aucun scénario n'y fait référence

**Total estimé** : 18 semaines en chemin critique. Peut être accéléré à 12 semaines avec ressources dédiées.

---

## 6. Période de double-écriture — enjeux

Pendant la phase 1 (dual-write) :

- **Écriture** : les scénarios Make écrivent dans les deux systèmes ; en cas d'échec Supabase, le record est loggué en file d'attente pour réémission. Pas de blocage du flux utilisatrice.
- **Lecture** : continue de lire depuis Make (autorité maintenue).
- **Réconciliation** : script quotidien qui compare les deux systèmes, alerte sur les divergences, ouvre des tickets Asana P10.
- **Durée** : 4 semaines minimum pour stabilisation.

---

## 7. Plan de rollback

Si la migration échoue ou révèle un problème majeur :

1. **Pendant phase 1 (dual-write)** : rollback trivial — désactiver l'écriture Supabase dans les scénarios Make. Aucune perte.
2. **Pendant phase 4 (cutover)** : procédure de bascule inverse documentée — réactivation de la lecture Make. Fenêtre de 48h pour détecter un problème avant retour impossible.
3. **Après phase 6** : irréversible. Les datastores Make ne peuvent être restaurés qu'à partir des exports chiffrés hors ligne.

---

## 8. Risques identifiés

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Consentement rétroactif insuffisant (emails, données existantes) | Moyenne | Élevé | Conseil juridique avant phase 2. Potentiel re-consent via WhatsApp/email à grande échelle. |
| Volumétrie sous-estimée → timeouts scripts batch | Moyenne | Moyen | Batch par tranches de 10k records, monitoring CPU/IO |
| Affectation régionale incorrecte par défaut | Élevée | Moyen | Tous en EU par défaut avec flag `residency_declared = false`, demande au prochain contact |
| Divergence Make ↔ Supabase pendant dual-write | Moyenne | Moyen | Reconciliation quotidienne + alerting PO-08 |
| Perte de pointeurs dans le billing_praticien éclaté | Moyenne | Élevé | Annotation manuelle avec double validation avant éclatement |
| Bridge WhatsApp vlbh-energy-mcp non mis à jour pour Supabase | Moyenne | Élevé | Planifier le refactor bridge en parallèle phase 1 |

---

## 9. Dépendances externes

- **Conseil juridique** : validation du consentement rétroactif (§8) avant phase 2
- **PO-08 Data Quality** : audit initial + monitoring pendant dual-write
- **PO-11 Onboarding** : coordination car certaines testeuses sont dans svlbh-apple-identity
- **Bridge WhatsApp vlbh-energy-mcp** : refactor pour lire Supabase au lieu de Make

---

## 10. Critères de succès

- 100% des records Make (contacts, apple-identity, billing-praticien) ont un svlbh_id valide dans Supabase
- 0 perte de données détectable (reconciliation OK)
- Scénarios Make fonctionnels en cutover (pas de régression utilisatrice)
- Routage régional actif et conforme à `svlbh_residency_directory`
- DPA signés avec Supabase et sous-traitants techniques
- Décommissionnement legacy validé par audit final
