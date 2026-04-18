# ADR-03 — Bridges WhatsApp MCP pérennes sur patricktest (segmentation Zone)

**Status** : Proposed — en attente validation Patrick  
**Date** : 2026-04-18  
**Portfolio Asana** : SVLBH-Infra (à créer)  
**Décideur** : Patrick Bays (Business Owner VLBH)  
**Auteur** : Claude + Patrick

## Contexte

L'écosystème VLBH envoie et reçoit des messages WhatsApp automatisés pour 3 audiences distinctes (visiteuses, shamanes en formation/certifiées standard, shamanes Pro). Historiquement, un seul bridge WhatsApp MCP existait (`patrickbays`), pointant vers le numéro business unique. Ce schéma est insuffisant :

1. Mélanger les audiences sur un même canal crée des risques réputationnels (visiteuses recevant des messages opérationnels Pro, et vice versa).
2. La contrainte WhatsApp « 4 devices max par compte » rend le bridge fragile à toute migration/re-pair.
3. Le device du compte business (`+41792168200`) a été kické le 2026-04-18, entraînant une panne silencieuse des envois automatisés.

## Décision

Architecture **3-bridge isolés** sur la machine macOS `patricktest`, un par segment fonctionnel VLBH :

| Préfixe MCP | Numéro | Zone | Audience |
|---|---|---|---|
| `wa_z1` | `+41798131926` | Z1/Z1b | Visiteuses, onboarding TestFlight |
| `wa_z2et3` | `+41792168200` | Z2/Z3 | Shamanes formation + certifiées standard |
| `wa_za` | `+41799138200` | ZA | Shamanes certifiées Pro |

Chaque bridge = 1 binaire Go `whatsmeow` + 1 DB SQLite + 1 MCP Python FastMCP + 1 LaunchAgent user-level. Zéro state partagé. Préfixes MCP distincts exposés à Cowork via `.mcp.json`.

Healthcheck cron toutes les 15 min, alerte email `monade.karmique@gmail.com` si silence > 2h.

## Conséquences positives

- **Isolation** : un bridge kické n'impacte pas les autres.
- **Segmentation business** : aucun mélange inter-audiences au runtime.
- **Scalabilité** : ajouter un 4ème bridge (ex. zone internationale) = copier-coller un dossier + 1 plist.
- **Observabilité** : healthcheck alerte Patrick avant qu'une panne devienne un problème client.
- **Reversibilité** : DB backup avant chaque re-pair, scripts d'installation idempotents.

## Conséquences négatives / risques

- **Coût CPU/mémoire** : 3 daemons Go + 3 venv Python sur la même machine. Acceptable pour macOS moderne mais à surveiller.
- **Complexité opérationnelle** : 3 re-pair QR au lieu de 1 si tout est kické simultanément.
- **Dépendance machine unique** : si `patricktest` tombe, les 3 bridges tombent ensemble. Mitigation future : hot-standby sur une 2ème machine (hors scope v1).
- **Rate-limit WhatsApp** : re-pair serré peut déclencher un blocage temporaire du compte. Mitigation : espacer 5 min entre re-pair.

## Alternatives rejetées

### A. Un seul bridge, multi-audiences sur le même numéro
Rejetée : mélange les messages de natures différentes, pas de segmentation possible au runtime, et risque business de pollution d'audience.

### B. Bridges hébergés sur cloud (Fly.io / Render)
Rejetée v1 : complexité de gestion des sessions WhatsApp persistantes en environnement conteneurisé, coûts récurrents, et déplacement du device = kick forcé à chaque redéploiement. À réévaluer v2 si fiabilité insuffisante.

### C. Solutions SaaS (Twilio WhatsApp Business API, 360Dialog)
Rejetée v1 : coût significatif pour le volume actuel, latence d'approbation Meta pour templates, perte du contrôle fin sur les interactions conversationnelles.

## Plan d'exécution

1. ✅ Phase 0 — Discovery & design (2026-04-18)
2. ✅ Phase 1 — Kit d'installation livré (`whatsapp-bridges-setup/`)
3. ⏳ Phase 2 — Install sur patricktest (`bash install.sh`)
4. ⏳ Phase 3 — Re-pair QR séquentiel (z1 → z2et3 → za, 5 min d'espacement)
5. ⏳ Phase 4 — Patch `.mcp.json` Cowork
6. ⏳ Phase 5 — Validation end-to-end + activation healthcheck

## Métriques de succès

- 100% uptime bridge sur 30 jours glissants (objectif).
- Détection de panne < 2h via healthcheck (SLA interne).
- Zéro mélange audience observé sur 30 jours.
- Re-pair manuel < 15 min / bridge (runbook).

## Références

- Fork privé : `github.com/monadekarmique/whatsapp-mcp` (base upstream : `github.com/lharries/whatsapp-mcp`)
- Nomenclature Zone VLBH : cf. mémoire `reference_whatsapp_bridges.md`
- Kit installation : `vlbh-energy-mcp/whatsapp-bridges-setup/`
- Runbook re-pair : `docs/repair-runbook.md`
