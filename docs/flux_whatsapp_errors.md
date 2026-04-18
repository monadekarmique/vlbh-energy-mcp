# Erreurs connues — Flux WhatsApp ROUTER #8944541

## 0. Bridge mapping (numero WhatsApp <-> bridge MCP)

Le routeur Make.com utilise la cle composite `{bridge}-{phone}` dans le datastore 157329 (contacts WhatsApp). `bridge` = numero E.164 sans le `+` du compte WhatsApp appaire sur ce bridge.

Architecture: 1 DB whatsmeow = 1 device_jid = 1 numero WhatsApp. Donc 1 bridge par numero.

| id  | numero       | port local | hostname public         | webhook param        |
|-----|--------------|------------|-------------------------|----------------------|
| b1  | 41792168200  | 8080       | wa1.svlbhgroup.net      | `?bridge=41792168200`|
| b2  | 41798131926  | 8081       | wa2.svlbhgroup.net      | `?bridge=41798131926`|

Les 2 bridges tournent sur le Mac de Patrick (user macOS `patrickbays`) sous `~/whatsapp-bridges/`. Les comptes WhatsApp eux-memes sont nommes "patricktest" cote WhatsApp Business — c'est juste un label, pas un user macOS.

Provisionnement: voir `tools/whatsapp-bridge-kit/` (install.sh + templates mcp.json/cloudflared.yml).

### Re-pair checklist (a refaire si `whatsmeow_device` est vide ou `/api/health` renvoie `connected: false`)

1. `curl -s http://localhost:<PORT>/api/health` — confirmer l'etat
2. Stop le process Go: `pkill -f "whatsapp-bridge.*<PORT>"`
3. Relancer: `cd ~/whatsapp-bridges/<id>-<phone>/whatsapp-bridge && PORT=<PORT> ./whatsapp-bridge`
4. Scanner le QR avec **le bon numero** (b1 -> 41792168200, b2 -> 41798131926). Un mauvais appairage corrompt le mapping `bridge=` cote Make.
5. Verifier: `sqlite3 ~/whatsapp-bridges/<id>-<phone>/whatsapp-bridge/store/whatsapp.db "SELECT jid FROM whatsmeow_device;"` doit retourner le JID attendu.
6. Tester un message entrant -> verifier qu'il arrive dans le scenario Make avec le bon `bridge=` en query string.

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
