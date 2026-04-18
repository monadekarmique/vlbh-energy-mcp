# WhatsApp MCP Bridges — Setup pérenne `patricktest`

**Date** : 2026-04-18  
**Auteur** : Patrick Bays (VLBH) + Claude  
**Status** : Phase 1 livrée, en attente exécution

## Objectif

3 bridges WhatsApp MCP tournant 24/7 sur la machine macOS `patricktest`, un par niveau d'engagement VLBH :

| Préfixe MCP | Numéro | Zone VLBH | Audience |
|---|---|---|---|
| `wa_z1` | `+41798131926` | Z1/Z1b | Visiteuses, prospects, onboarding TestFlight |
| `wa_z2et3` | `+41792168200` | Z2/Z3 | Shamanes formation + certifiées standard |
| `wa_za` | `+41799138200` | ZA | Shamanes certifiées Pro (billing, MyShamanFamily sessions) |

## Stack

- Base : `whatsapp-mcp` (Go bridge via whatsmeow + Python MCP server). Fork privé sous GitHub `monadekarmique`.
- OS : macOS, démarrage auto via LaunchAgent user-level (pas sudo).
- Isolation : 1 dossier data + 1 DB SQLite + 1 binaire + 1 LaunchAgent par bridge. Zéro state partagé.
- Exposition Cowork : `.mcp.json` avec 3 entrées à préfixes distincts.
- Alerting : healthcheck cron toutes les 15 min → email `monade.karmique` si silence > 2h.
- Gouvernance : ADR-03 tracée dans portfolio Asana `SVLBH-Infra` (à créer).

## Layout filesystem installé

```
/Users/patricktest/whatsapp-bridges/
├── bridge-z1/
│   ├── bin/bridge                  # binaire Go compilé
│   ├── mcp-server/                 # venv Python + main.py
│   ├── data/store/whatsapp.db      # SQLite session + messages
│   └── logs/                       # bridge.log, bridge.err
├── bridge-z2et3/
│   └── (même structure)
├── bridge-za/
│   └── (même structure)
└── shared/
    ├── scripts/                    # install.sh, healthcheck.sh, repair-bridge.sh
    └── .env                        # EMAIL_ALERT, SMTP config

~/Library/LaunchAgents/
├── energy.vlbh.wa-bridge-z1.plist
├── energy.vlbh.wa-bridge-z2et3.plist
└── energy.vlbh.wa-bridge-za.plist

~/Library/Logs/whatsapp-mcp/
└── healthcheck.log
```

## Phases

- **Phase 0** — Discovery & design ✅ (2026-04-18)
- **Phase 1** — Kit livré ✅ (ce dossier)
- **Phase 2** — Install sur patricktest : toi, `bash shared/scripts/install.sh`
- **Phase 3** — Re-pair QR séquentiel : toi, un bridge à la fois (z1 → z2et3 → za)
- **Phase 4** — Wiring `.mcp.json` Cowork : patch à appliquer (voir `mcp-config/`)
- **Phase 5** — Validation end-to-end : on teste les 3 bridges depuis Cowork

## Ordre d'exécution recommandé

1. Lire `docs/repair-runbook.md` en entier avant toute action.
2. Cloner le fork `whatsapp-mcp` (privé `monadekarmique`) sur patricktest.
3. Exécuter `scripts/install.sh` (crée layout, compile bridges, installe venv, copie plists).
4. Activer les 3 LaunchAgents (`launchctl load`).
5. Re-pair QR bridge `z1` d'abord (le plus simple, audience visiteuses).
6. Re-pair QR bridge `z2et3` ensuite (celui qui a été kické aujourd'hui — priorité business).
7. Re-pair QR bridge `za` en dernier.
8. Patcher le `.mcp.json` Cowork avec les 3 entrées préfixées.
9. Relancer Cowork et vérifier que les 3 namespaces MCP répondent.
10. Activer `healthcheck.sh` via `launchctl` ou cron toutes les 15 min.

## Dépendances

- Go ≥ 1.21 (pour compiler les bridges)
- Python ≥ 3.11 (pour les MCP servers)
- macOS Sequoia (patricktest)
- Un compte SMTP pour alertes (gmail app password ou équivalent) → variable `SMTP_APP_PASSWORD` dans `shared/.env`

## Points d'attention

- **Ordre de re-pair** : ne JAMAIS re-pairer deux bridges dans la même minute. Espacer de 5 min minimum pour éviter rate-limit WhatsApp.
- **DB SQLite** : backup automatique avant chaque re-pair (script `repair-bridge.sh` le fait).
- **Multi-device** : vérifier dans WhatsApp mobile → Paramètres → Appareils liés après chaque re-pair, pour confirmer le device actif.
- **Préfixes Cowork** : si tu les changes, il faut aussi modifier les skills VLBH qui appellent `mcp__whatsapp__*` (actuellement non préfixé).
