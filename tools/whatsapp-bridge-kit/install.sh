#!/usr/bin/env bash
# Provision 3 WhatsApp MCP bridges (FelixIsaac/whatsapp-mcp-extended fork)
# for SVLBH security zones:
#   z1 = visiteuses                              — +41798131926
#   z2 = shamanes en formation + certifiees non-pro — +41792168200
#   z3 = shamanes certifiees pro                 — +41799138200
#
# Run on the Mac as user `patricktest`. Prerequisites:
#   - go >= 1.21, python 3.11, uv, sqlite3, cloudflared
#   - cloudflared tunnel already authenticated to svlbhgroup.net
#
# Re-runnable: existing bridge dirs are skipped (no overwrite).

set -euo pipefail

UPSTREAM_REPO="https://github.com/FelixIsaac/whatsapp-mcp-extended.git"
ROOT="${WA_BRIDGES_ROOT:-$HOME/whatsapp-bridges}"
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# id : E.164_phone_without_plus : local_port : public_hostname : zone_label
BRIDGES=(
  "z1:41798131926:8080:z1.svlbhgroup.net:visiteuses"
  "z2:41792168200:8081:z2.svlbhgroup.net:formation-non-pro"
  "z3:41799138200:8082:z3.svlbhgroup.net:certifiees-pro"
)

if [[ "$(id -un)" != "patricktest" ]]; then
  echo "WARNING: running as $(id -un), expected 'patricktest'. Continue? (ctrl+c to abort)"
  read -r _
fi

mkdir -p "$ROOT"

for entry in "${BRIDGES[@]}"; do
  IFS=':' read -r id phone port host zone <<< "$entry"
  dir="$ROOT/$id-$phone"

  if [[ -d "$dir" ]]; then
    echo "[$id] skip — $dir already exists"
    continue
  fi

  echo "[$id] ($zone) cloning fork into $dir"
  git clone --depth=1 "$UPSTREAM_REPO" "$dir"

  # Per-bridge metadata consumed by run.sh / status.sh
  cat > "$dir/.bridge.env" <<EOF
BRIDGE_ID=$id
BRIDGE_PHONE=$phone
BRIDGE_PORT=$port
BRIDGE_HOST=$host
BRIDGE_ZONE=$zone
WEBHOOK_BRIDGE_PARAM=$phone
EOF

  echo "[$id] cloned."
done

cat <<EOF

==========================================================================
Next manual steps:

  1. Build each Go bridge:
       for d in "$ROOT"/*/whatsapp-bridge; do (cd "\$d" && go build); done

  2. Merge cloudflared ingress rules:
       cp -i $KIT_DIR/cloudflared.yml.template ~/.cloudflared/config.yml.new
       # merge into ~/.cloudflared/config.yml, then:
       cloudflared tunnel route dns <TUNNEL_UUID> z1.svlbhgroup.net
       cloudflared tunnel route dns <TUNNEL_UUID> z2.svlbhgroup.net
       cloudflared tunnel route dns <TUNNEL_UUID> z3.svlbhgroup.net
       sudo launchctl kickstart -k system/com.cloudflare.cloudflared

  3. Register MCP servers in Claude Code:
       cp -i $KIT_DIR/mcp.json.template ~/.claude/.mcp.json.new
       # merge into ~/.claude/settings.json (or .mcp.json)

  4. For each bridge, start it and scan QR with the MATCHING phone:

       cd $ROOT/z1-41798131926/whatsapp-bridge && PORT=8080 ./whatsapp-bridge   # visiteuses
       cd $ROOT/z2-41792168200/whatsapp-bridge && PORT=8081 ./whatsapp-bridge   # formation + non-pro
       cd $ROOT/z3-41799138200/whatsapp-bridge && PORT=8082 ./whatsapp-bridge   # pro

     VERIFY the FelixIsaac fork honors the PORT env var. If not, edit
     whatsapp-bridge/main.go listen address before building.

     CRITICAL: scan each QR with the CORRECT phone. A mismatch corrupts the
     bridge<->zone mapping in Make.com datastore 157329 (key: {bridge}-{phone}).

  5. Verify each bridge is connected:
       curl -s http://localhost:8080/api/health   # z1
       curl -s http://localhost:8081/api/health   # z2
       curl -s http://localhost:8082/api/health   # z3
     All 3 must return {"connected": true, ...}.

  6. Verify the JID matches the zone:
       for d in $ROOT/*/whatsapp-bridge/store; do
         echo "=== \$d ==="
         sqlite3 "\$d/whatsapp.db" "SELECT jid FROM whatsmeow_device;"
       done

  7. In Make.com WhatsApp ROUTER (#8944541), ensure 3 webhook URLs exist
     with the right bridge= query parameter:
       https://hook.eu2.make.com/<hook_id>?bridge=41798131926   # z1
       https://hook.eu2.make.com/<hook_id>?bridge=41792168200   # z2
       https://hook.eu2.make.com/<hook_id>?bridge=41799138200   # z3
==========================================================================
EOF
