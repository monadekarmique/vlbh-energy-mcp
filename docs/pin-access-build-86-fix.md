# PIN access crash — Build 86 (invitees 10001 & 10002)

**Date** : 2026-04-15
**Branche** : `claude/fix-pin-access-build-86-EgW27`
**Ticket Notion** : [P01-4 — Planche tactique, invités 10001/10002 absents](https://www.notion.so/3409cafd5ef081079311c5078b0f65cd) (P0 URGENT, RGPD Fort)
**Risque RGPD lié** : RSK-2 (consentement testeuses, deadline 2026-04-16)

## Symptôme

Deux testeuses (codes invités **10001** et **10002**) font crasher l'app iOS SVLBH Panel sur l'écran PIN après le hotfix Build 86. Build 85 (distribué sur TestFlight le 2026-04-10 au groupe "SVLBH Bash 3 à 5") ne crashait pas mais probablement ne débloquait pas non plus l'onboarding.

## Cause racine — double blocage

### Couche 1 : provisioning data (Make.com)

- **DS 156396** (`billing_praticien`) — 19 records. Avant fix : aucun record pour `code_tier = 10001` ou `10002`. Les alias actifs étaient `0300` (Cornelia), `0301` (Flavia), `0302` (Anne), `0303` (Chloé), `455000` (Patrick).
- **DS 155674** (`svlbh-v2`) — 205 records. ⚠️ Contrairement au rapport initial, ce datastore ne contient **pas** une table de contacts mais des payloads de session (keys `00-{patientID}-{sessionID}-{codeTier}`, contenu incluant `PIN:XXXX` + grilles G1–G15). Rien à "provisionner" ici à froid : les records se créent au premier usage. Seul DS 156396 était bloquant.

### Couche 2 : validation hardcodée (iOS Swift)

Dans le code Swift local (non distribué sur ce repo), `RoutineMatinTab.swift:126` maintient une liste statique `billingKeys` des codes acceptés. Cette liste **n'inclut pas** `10001` ni `10002`.

### Pourquoi Build 85 → Build 86 transforme ça en crash

Build 85 gère probablement un code inconnu en fallback silencieux. Le hotfix Build 86 (non commité, modifs locales sur `.gitignore`, `project.pbxproj`, `ChronoClockView.swift`) a vraisemblablement durci la validation PIN : au lieu du fallback, absence de record côté Make + absence côté `billingKeys` → exception non gérée → crash.

## Fix appliqué (2026-04-15)

### ✅ Côté Make.com — fait dans ce changeset

Deux records alias créés dans DS 156396, pattern aligné avec `0300`–`0303` / `455000` :

| key     | statut         | role    | code_tier | nom_praticien             |
|---------|----------------|---------|-----------|---------------------------|
| `10001` | `invitee_test` | invitee | 10001     | Invitée TestFlight 10001  |
| `10002` | `invitee_test` | invitee | 10002     | Invitée TestFlight 10002  |

Le `statut = "invitee_test"` (distinct de `alias`/`active`/`passive`) permet de filtrer ou purger ces records après le pilote. Le `mobile_hash` est un placeholder (`invitee_10001_placeholder` / `invitee_10002_placeholder`) — à remplacer par le SHA256 tronqué (28 chars) du numéro mobile réel dès que collecté, conformément RSK-2.

Scénario concerné : **9031997** ("VLBH Femmes Groupe Travail - Onboarding TestFlight").

### ⚠️ Côté iOS Swift — à faire hors de ce repo

Fichier cible : `SVLBH Panel/Views/RoutineMatinTab.swift` (repo local `svlbhpanel-v5`, pas accessible depuis cette session).

1. **Ligne 126 — liste `billingKeys`** : remplacer la liste statique par un fetch dynamique depuis DS 156396 (scénario 9031997), ou à minima ajouter `"10001"`, `"10002"`.
2. **Flow PIN — défense en profondeur** : envelopper le lookup Make.com dans un `do/catch`, gérer `nil`/erreur HTTP sans exception non gérée. Afficher `"Code non reconnu, contactez le support"` plutôt que crasher.
3. **Cohérence Build 87** : inclure ces deux changements dans le prochain build TestFlight distribué aux testeuses.

## Vérification

1. **Données Make** : `data-store-records_list` sur DS 156396 filtré sur `10001` / `10002` → 2 records présents. ✅
2. **Scénario onboarding** : exécuter `scenarios_run` sur `9031997` avec `code = 10001` puis `10002` → réponse non vide, pas d'erreur.
3. **Client iOS** : après rebuild avec fix Swift, re-tester saisie PIN avec codes `10001` et `10002` → pas de crash, onboarding complet.
4. **RGPD** : collecter consentement formalisé des deux testeuses avant élargissement (RSK-2 deadline 2026-04-16).

## Références

- Ticket Notion : `3409cafd-5ef0-8107-9311-c5078b0f65cd`
- Bug connexe Notion (Build 85) : `3409cafd-5ef0-8160-8819-f3b4adbe1ae8` — "PIN/Soin initié par le praticien : pas de notification ni date/heure côté patient"
- Make.com scénario : `9031997`
- Make.com datastore : `156396` (billing_praticien), `155674` (svlbh-v2)
- iOS bundle : `M100-LS100-DM85.SVLBH-Panel` — App ID `6760935383`, Team `NKJ86L447D`
