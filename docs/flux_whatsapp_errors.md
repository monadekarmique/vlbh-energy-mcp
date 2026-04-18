# Erreurs connues — Flux WhatsApp ROUTER #8944541

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
