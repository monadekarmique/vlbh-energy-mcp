# Z1 / Z1b — TARGET Infrastructure

> **STATUT : TARGET — NE PAS DÉPLOYER AVANT LE GO OFFICIEL**
> 
> Tous les artefacts de ce dossier sont préparatoires. Aucune migration SQL ne doit être exécutée en production tant que Patrick n'a pas signé le **Go Transition**. Aucun scénario Make existant ne doit être modifié.

## Contexte

- **Propriétaire** : PO-07 Infra / Backend
- **Déclencheur** : ADR-03 (gestion JID/LID WhatsApp) + découverte rtm-bot du 2026-04-18 19h10
- **Stratégie** : Blue/Green — nouvelle infra montée en parallèle, bascule atomique Jour D
- **Risque principal** : messages entrants sur `@lid` invisibles pour les scénarios Make qui filtrent par JID classique `@s.whatsapp.net`

## Principe cardinal

**Ne jamais utiliser JID ou LID comme clé de matching fonctionnelle.** Le téléphone E.164 reste la clé métier stable ; JID et LID sont des alias volatiles.

## Périmètre Zone 1

| Zone | Bridge WhatsApp | Numéro | Audience |
|------|----------------|--------|----------|
| **Z1** | `wa_z1` | +41798131926 | Visiteuses (pré-onboarding, première interaction) |
| **Z1b** | `wa_z1` (même bridge) | +41798131926 | Visiteuses post-onboarding TestFlight (E.164 connu) |

Z1 et Z1b partagent le bridge mais se distinguent au niveau base de données (colonne `zone` sur `contacts_z1`).

## Artefacts (ce dossier)

| Fichier | Rôle | À exécuter quand |
|---------|------|------------------|
| `README.md` | Ce document | — |
| `001_z1_schema.target.sql` | Schéma Supabase cible (tables) | Jour D, phase 1 |
| `002_z1_rpc.target.sql` | RPC de résolution JID/LID | Jour D, phase 2 |
| `003_z1_seed.target.sql` | Seed initial (migration depuis datastore actuel) | Jour D, phase 3 |
| `makecom_scenarios_to_duplicate.md` | Liste des scénarios Make à cloner + contrats I/O | Préparatoire |
| `go_live_runbook.md` | Runbook bascule Jour D | Jour D |
| `rollback_plan.md` | Plan retour arrière si échec | Jour D (secours) |

## Convention de nommage

- Suffixe `.target.sql` → SQL **prêt mais pas appliqué**
- Suffixe `.live.sql` (après Go) → SQL **actif en production**
- Scénarios Make dupliqués : préfixe `[Z1-TARGET]` tant qu'en staging, renommés `[Z1]` au Jour D

## État actuel (avant Go)

- [x] Design schema validé (ce dossier)
- [x] RPC de résolution définies
- [ ] Projet Supabase Z1 provisionné (Swiss hosting — nLPD)
- [ ] Seed SQL généré depuis datastore Make actuel
- [ ] Scénarios Make dupliqués en staging avec préfixe `[Z1-TARGET]`
- [ ] Smoke test sur staging (minimum 3 contacts test : 1 JID classique, 1 LID pur, 1 migré)
- [ ] Runbook Jour D revu par Patrick
- [ ] **Go Transition signé par Patrick**

## Post-Go (à faire Jour D)

- [ ] Phase 1 : exécuter migrations SQL sur Supabase production
- [ ] Phase 2 : basculer les scénarios Make dupliqués en actifs
- [ ] Phase 3 : désactiver les anciens scénarios Make
- [ ] Phase 4 : monitoring 24h (alertes si LID non résolu)
- [ ] Retirer le suffixe `.target.sql` (renommer en `.live.sql`)

## Contact

- **Décideur** : Patrick Bays
- **Exécutant** : Claude Code (branche `claude/prepare-conversation-context-BIJbE`)
- **Observateur** : rtm-bot@vlbh.energy (alertes healthcheck)
