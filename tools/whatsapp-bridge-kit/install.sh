#!/usr/bin/env bash
# Provision 2 WhatsApp MCP bridges (FelixIsaac/whatsapp-mcp-extended fork)
# for SVLBH numbers 41792168200 (b1) and 41798131926 (b2).
#
# Run on the Mac host (user patrickbays). Prerequisites:
#   - go >= 1.21, python 3.11, uv, sqlite3, cloudflared
#   - cloudflared tunnel already authenticated to svlbhgroup.net
#
# Re-runnable: existing bridge dirs are skipped (no overwrite).

set -euo pipefail

UPSTREAM_REPO="https://github.com/FelixIsaac/whatsapp-mcp-extended.git"
ROOT="${WA_BRIDGES_ROOT:-$HOME/whatsapp-bridges}"
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# id : E.164_phone_without_plus : local_port : public_hostname
BRIDGES=(
  "b1:41792168200:8080:wa1.svlbhgroup.net"
  "b2:41798131926:8081:wa2.svlbhgroup.net"
)

mkdir -p "$ROOT"

for entry in "${BRIDGES[@]}"; do
  IFS=':' read -r id phone port host <<< "$entry"
  dir="$ROOT/$id-$phone"

  if [[ -d "$dir" ]]; then
    echo "[$id] skip — $dir already exists"
    continue
  fi

  echo "[$id] cloning fork into $dir"
  git clone --depth=1 "$UPSTREAM_REPO" "$dir"

  # Per-bridge metadata consumed by run.sh / status.sh
  cat > "$dir/.bridge.env" <<EOF
BRIDGE_ID=$id
BRIDGE_PHONE=$phone
BRIDGE_PORT=$port
BRIDGE_HOST=$host
WEBHOOK_BRIDGE_PARAM=$phone
EOF

  echo "[$id] cloned. Build the Go bridge manually:"
  echo "       cd '$dir/whatsapp-bridge' && go build -o whatsapp-bridge ."
done

cat <<EOF

==========================================================================
Next manual steps (the kit does not auto-run anything that touches WhatsApp):

  1. Build each Go bridge:
       for d in "$ROOT"/*/whatsapp-bridge; do (cd "\$d" && go build); done

  2. Merge cloudflared ingress rules:
       cp -i $KIT_DIR/cloudflared.yml.template ~/.cloudflared/config.yml.new
       # then merge into ~/.cloudflared/config.yml and reload:
       sudo launchctl kickstart -k system/com.cloudflare.cloudflared

  3. Register MCP servers in Claude Code:
       cp -i $KIT_DIR/mcp.json.template ~/.claude/.mcp.json.new
       # merge into ~/.claude/settings.json (or .mcp.json)

  4. For each bridge, start it in its own terminal and scan QR
     with the MATCHING phone number:

       cd $ROOT/b1-41792168200/whatsapp-bridge && PORT=8080 ./whatsapp-bridge
       cd $ROOT/b2-41798131926/whatsapp-bridge && PORT=8081 ./whatsapp-bridge

     NOTE: verify the FelixIsaac fork honors the PORT env var. If not,
     edit whatsapp-bridge/main.go (the listen address) before building.

  5. Verify each bridge is connected:
       curl -s http://localhost:8080/api/health   # b1 -> 41792168200
       curl -s http://localhost:8081/api/health   # b2 -> 41798131926
     Both must return {"connected": true, ...}.

  6. Update the Make.com WhatsApp ROUTER (#8944541) webhook URL for b2
     by appending ?bridge=41798131926 (b1 already uses ?bridge=41792168200).
==========================================================================
EOF
