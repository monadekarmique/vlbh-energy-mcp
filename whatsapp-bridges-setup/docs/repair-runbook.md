# Runbook — Re-pair d'un bridge WhatsApp VLBH

**Quand utiliser** : un bridge apparaît kické (alerte email healthcheck, ou `list_chats` vide dans Cowork), ou après migration machine.

## Principes de sécurité

1. **Un bridge à la fois.** Jamais deux re-pair simultanés — WhatsApp rate-limite la création de devices par compte.
2. **Espacer de 5 minutes** entre deux re-pair consécutifs sur le même compte.
3. **Vérifier côté mobile** après chaque re-pair : WhatsApp → Paramètres → Appareils liés → le nouveau device doit apparaître.
4. **Backup DB automatique** avant re-pair (fait par `repair-bridge.sh`).
5. **Re-sync historique prend 10-30 min** après re-pair — ne pas paniquer si `list_chats` est vide les premières minutes.

## Ordre recommandé si les 3 bridges sont à re-pairer

1. `z1` (+41798131926) — le plus simple, visiteuses.
2. Attendre 5 min.
3. `z2et3` (+41792168200) — compte business, priorité si kické.
4. Attendre 5 min.
5. `za` (+41799138200) — Pro, dernier car volume messages plus faible.

## Procédure manuelle (si `repair-bridge.sh` indisponible)

```bash
# 1. Arrêter le LaunchAgent du bridge concerné (exemple z2et3)
launchctl unload ~/Library/LaunchAgents/energy.vlbh.wa-bridge-z2et3.plist

# 2. Tuer le process Go résiduel si besoin
pkill -f bridge-z2et3/bin/bridge

# 3. Backup DB
cp ~/whatsapp-bridges/bridge-z2et3/data/store/whatsapp.db \
   ~/whatsapp-bridges/bridge-z2et3/data/backups/whatsapp_$(date +%Y%m%d_%H%M%S).db

# 4. Supprimer la session morte (force le QR au redémarrage)
rm ~/whatsapp-bridges/bridge-z2et3/data/store/whatsapp.db*

# 5. Lancer en foreground pour scanner le QR
cd ~/whatsapp-bridges/bridge-z2et3 && ./bin/bridge
# → QR apparaît dans le terminal
# → WhatsApp mobile → Paramètres → Appareils liés → Lier un appareil → scan
# → Attendre "Login successful" puis Ctrl+C

# 6. Re-lancer le LaunchAgent
launchctl load ~/Library/LaunchAgents/energy.vlbh.wa-bridge-z2et3.plist
```

## Vérification post re-pair

```bash
# Bridge tourne ?
launchctl list | grep energy.vlbh.wa-bridge-z2et3

# DB a des messages récents ?
sqlite3 ~/whatsapp-bridges/bridge-z2et3/data/store/whatsapp.db \
  "SELECT COUNT(*), MAX(datetime(timestamp, 'unixepoch')) FROM messages;"

# Test depuis Cowork :
# Utiliser mcp__wa_z2et3__search_contacts pour valider namespace
```

## Cas d'échec connus

### Le QR ne s'affiche pas dans le terminal
Cause probable : la session précédente n'a pas été proprement supprimée. Re-run étape 4.

### "Device pairing rejected"
Cause probable : tu as dépassé 4 devices sur ce compte WhatsApp. Va sur WhatsApp mobile et déconnecte un device ancien.

### Re-sync bloqué à N messages
Normal pour les gros comptes. Laisser tourner plusieurs heures. Si > 24h sans progression, relancer le LaunchAgent.

### Le LaunchAgent crash-loop
Vérifier `~/whatsapp-bridges/bridge-{zone}/logs/bridge.err`. Symptômes fréquents :
- Permissions data dir → `chmod -R u+rw ~/whatsapp-bridges/bridge-{zone}/data`
- Port déjà occupé (si bridge utilise un port HTTP interne)
- Go binaire non exécutable → `chmod +x ~/whatsapp-bridges/bridge-{zone}/bin/bridge`

## Escalade

Si un bridge reste indisponible > 4h après re-pair réussi, ouvrir une tâche Asana dans `SVLBH-Infra` → section `Incidents`, taguer `whatsapp-bridges`.
