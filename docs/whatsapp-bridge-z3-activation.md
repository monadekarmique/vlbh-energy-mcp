# Activation du bridge z3 (shamanes certifiees pro)

## Etat actuel

- **Numero** : +41799138200
- **Pair WhatsApp** : **oui** (session crypto persistee dans `~/whatsapp-bridges/z3-41799138200/whatsapp-bridge/store/whatsapp.db`)
- **Process bridge** : **arrete** (pas de LaunchAgent charge)
- **Cloudflared ingress** : **absent** pour `z3.svlbhgroup.net`
- **Webhook Make.com** : **absent** dans router #8944541 (pas de route `?bridge=41799138200`)
- **MCP client Claude Code** : entree `whatsapp-z3-certifiees-pro` presente dans `mcp.json.template` — commentable tant que z3 inactif

Les dossiers et la DB sont preserves pour que la session WhatsApp survive et evite un re-pair.

## Activation — checklist

Executer sur le Mac en user `patricktest`. Prerequis : z1 et z2 deja actifs.

### 1. Sanity check — la session z3 est-elle toujours valide ?

```bash
sqlite3 ~/whatsapp-bridges/z3-41799138200/whatsapp-bridge/store/whatsapp.db \
  "SELECT jid, push_name FROM whatsmeow_device;"
```
Doit retourner un JID commencant par `41799138200`. Si vide → re-pair necessaire :

```bash
cd ~/whatsapp-bridges/z3-41799138200/whatsapp-bridge
DISABLE_AUTH_CHECK=true PORT=8082 ./whatsapp-bridge 2>&1 | tee /tmp/z3.log
# scan QR avec +41799138200, ctrl+c une fois "Successfully paired" logge
```

### 2. Charger le LaunchAgent

```bash
cp tools/whatsapp-bridge-kit/launchagents/com.patricktest.whatsapp-bridge-z3.plist \
   ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.patricktest.whatsapp-bridge-z3.plist
# verification
launchctl list | grep whatsapp-bridge-z3
ps aux | grep "z3-41799138200" | grep -v grep
curl -s http://localhost:8082/api/health   # connected: true
```

### 3. Ajouter l'ingress cloudflared

Editer `~/.cloudflared/config.yml` et decommenter la route z3 :

```yaml
  - hostname: z3.svlbhgroup.net
    service: http://localhost:8082
```

Puis :

```bash
cloudflared tunnel route dns <TUNNEL_UUID> z3.svlbhgroup.net
sudo launchctl kickstart -k system/com.cloudflare.cloudflared
curl -I https://z3.svlbhgroup.net/api/health   # doit repondre 200
```

### 4. Ajouter la route Make.com

Dans le scenario #8944541 (WhatsApp ROUTER), ajouter un webhook entrant avec l'URL :

```
https://hook.eu2.make.com/<hook_id>?bridge=41799138200
```

Et la route correspondante dans le router Make qui traite le `bridge` = `41799138200` comme **zone z3 (pro)** — ACL/scenario dedie different des zones z1/z2.

### 5. Activer l'entree MCP dans Claude Code

`mcp.json.template` contient deja l'entree `whatsapp-z3-certifiees-pro`. Si elle etait commentee localement, la decommenter et redemarrer Claude Code.

### 6. Test de bout en bout

1. Envoyer un message WhatsApp depuis un compte externe vers +41799138200
2. Verifier dans le scenario Make #8944541 que l'execution arrive avec `bridge=41799138200`
3. Verifier le routing vers le bon scenario (zone pro)
4. Verifier la reponse auto (si activee) revient au contact

## Desactivation (bascule retour vers etat "paired-but-idle")

```bash
launchctl unload ~/Library/LaunchAgents/com.patricktest.whatsapp-bridge-z3.plist
# NE PAS supprimer le plist ni le dossier du bridge — preserver la session
```

Commenter l'ingress cloudflared z3 et desactiver la route Make. La DB pairing reste intacte pour une future ré-activation.
