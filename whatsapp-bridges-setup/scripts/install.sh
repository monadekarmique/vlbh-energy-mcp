#!/usr/bin/env bash
# install.sh — Bootstrap 3 bridges WhatsApp MCP sur patricktest
# Usage : bash install.sh [--from-scratch|--upgrade]
# Auteur : VLBH / Patrick Bays — 2026-04-18

set -euo pipefail

# ---- Config ----
BRIDGES_ROOT="${HOME}/whatsapp-bridges"
LAUNCHAGENTS="${HOME}/Library/LaunchAgents"
LOGS_ROOT="${HOME}/Library/Logs/whatsapp-mcp"
UPSTREAM_REPO="${UPSTREAM_REPO:-git@github.com:monadekarmique/whatsapp-mcp.git}"  # fork privé
FALLBACK_UPSTREAM="https://github.com/lharries/whatsapp-mcp.git"

BRIDGES=("z1" "z2et3" "za")
declare -A PHONES=(
  ["z1"]="+41798131926"
  ["z2et3"]="+41792168200"
  ["za"]="+41799138200"
)

# ---- Pré-requis ----
check_tool() {
  if ! command -v "$1" &>/dev/null; then
    echo "❌ Outil manquant : $1"; exit 1
  fi
}
echo "▶ Vérification des prérequis…"
check_tool go
check_tool python3
check_tool git
check_tool launchctl

GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
echo "  Go $GO_VERSION ✓"
PY_VERSION=$(python3 --version | awk '{print $2}')
echo "  Python $PY_VERSION ✓"

# ---- Clone fork ----
SRC_DIR="${BRIDGES_ROOT}/_source"
if [[ ! -d "$SRC_DIR" ]]; then
  echo "▶ Clonage du fork whatsapp-mcp…"
  mkdir -p "$BRIDGES_ROOT"
  if ! git clone "$UPSTREAM_REPO" "$SRC_DIR" 2>/dev/null; then
    echo "  Fork privé inaccessible, fallback upstream public."
    git clone "$FALLBACK_UPSTREAM" "$SRC_DIR"
  fi
else
  echo "▶ Source déjà présente, git pull…"
  (cd "$SRC_DIR" && git pull --ff-only)
fi

# ---- Build + install par bridge ----
for bridge in "${BRIDGES[@]}"; do
  phone="${PHONES[$bridge]}"
  dir="${BRIDGES_ROOT}/bridge-${bridge}"
  echo ""
  echo "▶ Setup bridge-${bridge} (${phone})…"

  mkdir -p "${dir}"/{bin,mcp-server,data/store,logs}

  # Compile Go bridge
  echo "  • Compilation Go…"
  (cd "${SRC_DIR}/whatsapp-bridge" && go build -o "${dir}/bin/bridge" .)

  # Install Python MCP server
  echo "  • Setup venv Python MCP…"
  python3 -m venv "${dir}/mcp-server/venv"
  # shellcheck disable=SC1091
  source "${dir}/mcp-server/venv/bin/activate"
  pip install --quiet --upgrade pip
  pip install --quiet -r "${SRC_DIR}/whatsapp-mcp-server/requirements.txt"
  cp "${SRC_DIR}/whatsapp-mcp-server/main.py" "${dir}/mcp-server/main.py"
  cp "${SRC_DIR}/whatsapp-mcp-server/whatsapp.py" "${dir}/mcp-server/whatsapp.py" 2>/dev/null || true
  deactivate

  # Patch main.py pour pointer vers la DB isolée
  # (whatsapp-mcp upstream lit la DB relative — on force le chemin absolu)
  DB_PATH="${dir}/data/store/whatsapp.db"
  echo "  • DB path : ${DB_PATH}"

  # Config .env par bridge
  cat > "${dir}/.env" <<EOF
BRIDGE_ID=${bridge}
BRIDGE_PHONE=${phone}
DB_PATH=${DB_PATH}
LOG_DIR=${dir}/logs
EOF

  echo "  ✓ bridge-${bridge} prêt (binaire + venv + data dir)"
done

# ---- LaunchAgents ----
echo ""
echo "▶ Installation LaunchAgents…"
mkdir -p "${LAUNCHAGENTS}" "${LOGS_ROOT}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_SRC="${SCRIPT_DIR}/../launchd"

for bridge in "${BRIDGES[@]}"; do
  src="${PLIST_SRC}/energy.vlbh.wa-bridge-${bridge}.plist"
  dst="${LAUNCHAGENTS}/energy.vlbh.wa-bridge-${bridge}.plist"
  if [[ -f "$src" ]]; then
    cp "$src" "$dst"
    echo "  ✓ ${dst}"
  else
    echo "  ⚠ Plist manquant : $src"
  fi
done

# ---- Shared scripts + env ----
mkdir -p "${BRIDGES_ROOT}/shared/scripts"
cp "${SCRIPT_DIR}/healthcheck.sh" "${BRIDGES_ROOT}/shared/scripts/" 2>/dev/null || true
cp "${SCRIPT_DIR}/repair-bridge.sh" "${BRIDGES_ROOT}/shared/scripts/" 2>/dev/null || true
chmod +x "${BRIDGES_ROOT}"/shared/scripts/*.sh || true

# .env global (healthcheck)
if [[ ! -f "${BRIDGES_ROOT}/shared/.env" ]]; then
  cat > "${BRIDGES_ROOT}/shared/.env" <<'EOF'
# Alerte email healthcheck
EMAIL_ALERT="monade.karmique@gmail.com"
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=465
SMTP_USER="monade.karmique@gmail.com"
SMTP_APP_PASSWORD="CHANGE_ME_gmail_app_password"
ALERT_SILENCE_HOURS=2
EOF
  echo "  ⚠ Éditer ${BRIDGES_ROOT}/shared/.env (SMTP_APP_PASSWORD à remplir)"
fi

# ---- Résumé ----
cat <<EOF

════════════════════════════════════════════
✅ Install terminée.

Étapes suivantes (MANUELLES) :

1. Remplir ${BRIDGES_ROOT}/shared/.env (SMTP_APP_PASSWORD).
2. Activer les LaunchAgents :
     launchctl load ~/Library/LaunchAgents/energy.vlbh.wa-bridge-z1.plist
     launchctl load ~/Library/LaunchAgents/energy.vlbh.wa-bridge-z2et3.plist
     launchctl load ~/Library/LaunchAgents/energy.vlbh.wa-bridge-za.plist
3. Re-pair QR séquentiel (5 min entre chaque) :
     bash ${BRIDGES_ROOT}/shared/scripts/repair-bridge.sh z1
     bash ${BRIDGES_ROOT}/shared/scripts/repair-bridge.sh z2et3
     bash ${BRIDGES_ROOT}/shared/scripts/repair-bridge.sh za
4. Patcher le .mcp.json Cowork (voir mcp-config/mcp-servers-patch.json).
5. Relancer Cowork et tester chaque namespace (wa_z1 / wa_z2et3 / wa_za).
6. Activer healthcheck :
     launchctl load ~/Library/LaunchAgents/energy.vlbh.wa-healthcheck.plist
════════════════════════════════════════════
EOF
