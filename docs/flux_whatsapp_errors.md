# Erreurs connues — Flux WhatsApp ROUTER #8944541

## 0. Bridge mapping (zones de securite <-> numero WhatsApp)

Le routeur Make.com utilise la cle composite `{bridge}-{phone}` dans le datastore 157329 (contacts WhatsApp). `bridge` = numero E.164 sans le `+` du compte WhatsApp appaire sur ce bridge.

Architecture: 1 DB whatsmeow = 1 device_jid = 1 numero WhatsApp → **1 bridge par zone de securite**.

| id  | zone                        | population cible                                 | numero        | port | hostname public     |
|-----|-----------------------------|--------------------------------------------------|---------------|------|---------------------|
| z1  | visiteuses                  | visiteuses                                       | +41798131926  | 8080 | z1.svlbhgroup.net   |
| z2  | formation + certifiees non-pro | shamanes en formation + certifiees non-pro    | +41792168200  | 8081 | z2.svlbhgroup.net   |
| z3  | certifiees pro              | shamanes certifiees pro                          | +41799138200  | 8082 | z3.svlbhgroup.net   |

Hote: Mac de Patrick, user macOS `patricktest`. Dossier racine `~/whatsapp-bridges/{z1,z2,z3}-<phone>/`.

"patricktest" designe ici **l'user macOS** ET le label du compte WhatsApp Business sur lequel les 3 numeros ont ete migres depuis l'user `patrickbays` (migration avril 2026).

Provisionnement: voir `tools/whatsapp-bridge-kit/` (install.sh + templates mcp.json/cloudflared.yml).

### Re-pair checklist (si `whatsmeow_device` est vide ou `/api/health` renvoie `connected: false`)

1. `curl -s http://localhost:<PORT>/api/health` — confirmer l'etat de chaque bridge
2. Stop le process Go concerne: `pkill -f "whatsapp-bridge.*<PORT>"`
3. Relancer: `cd ~/whatsapp-bridges/<id>-<phone>/whatsapp-bridge && PORT=<PORT> ./whatsapp-bridge`
4. Scanner le QR avec **le bon numero de la zone** (z1 → +41798131926, z2 → +41792168200, z3 → +41799138200). Un mauvais appairage corrompt le mapping `bridge=` cote Make et melange les zones de securite.
5. Verifier: `sqlite3 ~/whatsapp-bridges/<id>-<phone>/whatsapp-bridge/store/whatsapp.db "SELECT jid FROM whatsmeow_device;"` doit retourner le JID attendu.
6. Tester un message entrant → verifier qu'il arrive dans le scenario Make #8944541 avec le bon `bridge=` en query string.

## 1. DataError: Duplicate key error

- **Module**: `datastore:AddRecord` (datastore 157329 — contacts WhatsApp)
- **Cause**: Un contact envoie plusieurs messages rapidement. La route "Nouveau contact" (module 10) tente un `AddRecord` alors que la cle `{bridge}-{phone}` existe deja.
- **Frequence**: ~20 executions en erreur entre le 3-4 avril 2026
- **Fix applique** (4 avril 10h53): `"overwrite": true` dans le mapper du module 10
- **Fix alternatif**: Remplacer `datastore:AddRecord` par `datastore:UpdateRecord`

## 2. Race condition contacts simultanes

- **Cause**: Le `GetRecord` (module 8) retourne vide pour 2 messages simultanes du meme nouveau contact. Les deux passent le filtre "Nouveau contact" → le 2e echoue en duplicate key.
- **Fix**: `overwrite: true` sur le AddRecord, ou ajouter un error handler `Resume` apres le module AddRecord.

## 3. Non-JSON response ("Accepted")

- **Cause**: Un webhook Make.com retourne "Accepted" sans corps JSON quand le scenario appele n'a pas de module Webhook Response.
- **Fix**: Ajouter un module `Webhook Response` dans le scenario appele. Cote MCP server, cette erreur est geree gracieusement (`found: false`).

## 4. Timeout API Anthropic (module 4, auto-reply)

- **Cause**: Claude met plus de 30s a repondre dans le module HTTP auto-reply.
- **Fix**: Augmenter le timeout ou basculer sur un modele plus rapide (Haiku).

## Architecture du flux

```
WhatsApp message → Webhook (hook 4000349)
  → GetRecord contacts (datastore 157329, cle: {bridge}-{phone})
  → Router:
      Route 1: "Nouveau contact" (jid vide) → AddRecord (overwrite: true)
      Route 2: "Contact existant" → GetRecord svlbh-v2 (155674, cle: CT-{from})
        → Sub-router:
            Route A: auto_reply=true → Claude API → WebhookRespond
            Route B: no auto_reply → WebhookRespond
```

## Superagent SA v1

Le Superagent (#8997261) tourne toutes les 15 min et connait ces erreurs.
Si pattern d'erreurs repetees detecte, il envoie `ALERTE: [FLUX_WA]` via WhatsApp et iMessage a Patrick.
