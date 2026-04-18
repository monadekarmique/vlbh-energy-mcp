# Make.com — Scénarios à dupliquer pour la cible Z1/Z1b

> **STATUT : INVENTAIRE & CONTRATS — PAS DE MODIFICATION DES SCÉNARIOS EXISTANTS**
>
> Les scénarios listés ci-dessous sont ceux qui interagissent aujourd'hui avec la Zone 1 via Make.com (datastores + webhooks WhatsApp). Ils restent actifs jusqu'au Go.
> Chaque scénario existant doit être **cloné** dans Make (menu `⋯ → Clone`), puis préfixé `[Z1-TARGET]`, puis modifié pour pointer vers Supabase Z1 via les RPC définies dans `002_z1_rpc.target.sql`.

## Environnement Make.com

| Paramètre | Valeur |
|-----------|--------|
| Organization | `monadekarmique` |
| Team ID | `630342` |
| Region | `eu2` |
| Connecteur HTTP Supabase | à créer au Jour D (`sb_z1_service`) |
| Ancien connecteur datastore | `a9f71a2b` (à conserver actif pendant la bascule) |

## Inventaire des scénarios Z1 à dupliquer

> **À compléter par Patrick** avant le Go — inspection manuelle dans Make ou via MCP Make si l'accès est réparé.
>
> Pour chaque scénario Z1 identifié, remplir les colonnes ci-dessous.

| # | Nom actuel | Scénario ID | Rôle métier | Trigger | Datastore lu | Datastore écrit | Webhook sortant | Filtres JID/LID actuels |
|---|-----------|-------------|-------------|---------|--------------|-----------------|-----------------|-------------------------|
| 1 | Routine Matin Broadcast WhatsApp | `8995179` | Broadcast quotidien visiteuses | Scheduler 09:00 | `datastore:GetRecord` (module 1) | — | WhatsApp wa_z1 | N/A (sortant, pas de filtre entrant) |
| 2 | [à identifier] Entrant Z1 | ? | Réception messages visiteuses | Webhook whatsmeow wa_z1 | — | `datastore:z1_contacts` | — | **CRITIQUE : filtre à auditer** |
| 3 | [à identifier] Onboarding TestFlight | ? | Déclenche invite TestFlight | Webhook or scheduler | `datastore:z1_contacts` | `datastore:z1_contacts` | API TestFlight | N/A |
| 4 | [à identifier] Nurture Z1 | ? | Message follow-up J+1, J+3, J+7 | Scheduler | `datastore:z1_contacts` | `datastore:z1_contacts` | WhatsApp wa_z1 | Peut-être sur JID |
| ... | | | | | | | | |

## Contrat I/O — Nouveaux modules Supabase (à utiliser dans les scénarios dupliqués)

Les scénarios `[Z1-TARGET]` doivent remplacer **tous** les appels datastore Make par des appels HTTP vers les RPC Supabase Z1.

### 1. Réception d'un message entrant (remplace datastore:AddRecord)

**Ancien** (Make datastore `z1_contacts`) :
```
Module: datastore.add
Key: {{numero}}@s.whatsapp.net
Payload: { nom, push_name, premier_message, ... }
```

**Nouveau** (Supabase RPC) :
```
Module: http.makeRequest
URL: {{SUPABASE_Z1_URL}}/rest/v1/rpc/log_message_z1
Method: POST
Headers:
  apikey: {{SUPABASE_Z1_SERVICE_KEY}}
  Authorization: Bearer {{SUPABASE_Z1_SERVICE_KEY}}
  Content-Type: application/json
Body:
{
  "p_wa_message_id": "{{1.message.id}}",
  "p_sender_identifier": "{{1.message.sender}}",   // JID ou LID — peu importe
  "p_direction": "in",
  "p_body": "{{1.message.body}}",
  "p_received_at": "{{1.message.timestamp}}",
  "p_push_name": "{{1.message.pushName}}",
  "p_media_type": "{{1.message.mediaType}}",
  "p_media_url": "{{1.message.mediaUrl}}",
  "p_is_group": false
}
```

Retour : `message_id` (UUID) — utilisable pour tracer le traitement.

### 2. Résolution d'un contact existant (remplace datastore:GetRecord)

**Ancien** :
```
Module: datastore.get
Key: {{numero}}@s.whatsapp.net
→ si absent: 404 silencieux → scenario ignore le message entrant LID
```

**Nouveau** :
```
Module: http.makeRequest
URL: {{SUPABASE_Z1_URL}}/rest/v1/rpc/resolve_contact_z1
Method: POST
Body:
{
  "identifier": "{{1.message.sender}}"   // fonctionne JID ET LID
}
→ retourne contact_id UUID ou null
→ si null: appeler upsert_contact_z1 pour créer
```

### 3. Broadcast sortant (ne change pas côté trigger)

Les broadcasts sortants continuent d'utiliser le bridge `wa_z1`. Seul change la source de la liste des destinataires :

**Ancien** : liste lue depuis datastore Make
**Nouveau** : requête Supabase `GET /rest/v1/contacts_z1?zone=eq.Z1&onboarding_status=eq.visiteuse&consent_marketing=eq.true`

Le bridge whatsmeow enverra sur le JID **ou** LID disponible dans le contact. Il n'y a pas besoin de distinguer côté Make.

### 4. Détection migration JID → LID (NOUVEAU — à ajouter)

Module optionnel à insérer après `log_message_z1` quand le message arrive sur un `@lid` inconnu :

```
Module: http.makeRequest
URL: {{SUPABASE_Z1_URL}}/rest/v1/rpc/detect_lid_migration_z1
Body:
{
  "p_new_lid": "{{1.message.sender}}",
  "p_push_name": "{{1.message.pushName}}"
}
→ si retour non-null: log dans lid_migration_log_z1 (pending)
→ notification rtm-bot via email pour validation
```

## Variables d'environnement à ajouter dans Make

| Variable | Valeur (à remplir par Patrick) |
|----------|-------------------------------|
| `SUPABASE_Z1_URL` | `https://<project-ref>.supabase.co` |
| `SUPABASE_Z1_SERVICE_KEY` | (généré à la création du projet Supabase Z1) |
| `SUPABASE_Z1_ANON_KEY` | (généré à la création du projet Supabase Z1) |

## Checklist préparation (avant Go)

- [ ] Lister exhaustivement les scénarios Z1 existants (compléter tableau ci-dessus)
- [ ] Identifier tous les filtres/matchs par `@s.whatsapp.net` dans les scénarios
- [ ] Cloner chaque scénario avec préfixe `[Z1-TARGET]`
- [ ] Désactiver chaque clone (`[Z1-TARGET]` en OFF jusqu'au Jour D)
- [ ] Remplacer les modules datastore par des modules HTTP Supabase (voir contrats ci-dessus)
- [ ] Provisionner le projet Supabase Z1 en Swiss region
- [ ] Créer les variables `SUPABASE_Z1_*` dans Make team 630342
- [ ] Smoke test chaque scénario `[Z1-TARGET]` sur contact test (manuel)
- [ ] Valider matching JID, LID et E.164 sur 3 contacts test distincts

## Scénarios à NE PAS dupliquer

- Tous les scénarios Z2, Z3, ZA — hors périmètre de cette transition
- Scénarios comptables/billing — n'interagissent pas avec Z1

## Convention de renommage Jour D

| Jour J (avant Go) | Jour D (au Go) | Jour D+1 (après validation) |
|-------------------|---------------|------------------------------|
| `Routine Matin Broadcast WhatsApp` (actif) | OFF | → archive `[Z1-ARCHIVE] Routine Matin Broadcast WhatsApp` |
| `[Z1-TARGET] Routine Matin Broadcast WhatsApp` (OFF) | ON, rename `[Z1] Routine Matin Broadcast WhatsApp` | actif |
