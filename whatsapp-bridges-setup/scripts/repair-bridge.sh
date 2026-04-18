#!/usr/bin/env bash
# repair-bridge.sh — Re-pair QR d'un bridge sans impacter les autres
# Usage : bash repair-bridge.sh <z1|z2et3|za>
# Auteur : VLBH / Patrick Bays — 2026-04-18

set -euo pipefail

BRIDGE="${1:-}"
if [[ ! "$BRIDGE" =~ ^(z1|z2et3|za)$ ]]; then
  echo "Usage : $0 <z1|z2et3|za>"
  exit 1
fi

BRIDGES_ROOT="${HOME}/whatsapp-bridges"
DIR="${BRIDGES_ROOT}/bridge-${BRIDGE}"
PLIST_LABEL="energy.vlbh.wa-bridge-${BRIDGE}"
DB_PATH="${DIR}/data/store/whatsapp.db"
BACKUP_DIR="${DIR}/data/backups"

if [[ ! -d "$DIR" ]]; then
  echo "❌ Bridge introuvable : $DIR"
  exit 1
fi

echo "════════════════════════════════════════════"
echo "RE-PAIR bridge-${BRIDGE}"
echo "  Numéro : $(grep BRIDGE_PHONE "${DIR}/.env" | cut -d= -f2)"
echo "════════════════════════════════════════════"
echo ""

# 1. Arrêter le LaunchAgent
echo "▶ Arrêt du LaunchAgent ${PLIST_LABEL}…"
launchctl unload "${HOME}/Library/LaunchAgents/${PLIST_LABEL}.plist" 2>/dev/null || true
pkill -f "bridge-${BRIDGE}/bin/bridge" 2>/dev/null || true
sleep 2

# 2. Backup DB actuelle
if [[ -f "$DB_PATH" ]]; then
  mkdir -p "$BACKUP_DIR"
  TS=$(date +%Y%m%d_%H%M%S)
  BACKUP_FILE="${BACKUP_DIR}/whatsapp_${TS}.db"
  cp "$DB_PATH" "$BACKUP_FILE"
  echo "  ✓ Backup DB → $BACKUP_FILE"
fi

# 3. Supprimer la session actuelle (force re-pair QR)
echo "▶ Suppression de la session actuelle…"
rm -f "${DIR}/data/store/"*.db "${DIR}/data/store/"*.db-journal 2>/dev/null || true

# 4. Lancer le bridge en foreground pour scanner le QR
echo ""
echo "▶ Lancement bridge en foreground pour scan QR…"
echo "  📱 Ouvre WhatsApp mobile → Paramètres → Appareils liés → Lier un appareil"
echo "  Scanne le QR ci-dessous :"
echo ""

cd "$DIR"
./bin/bridge

echo ""
echo "▶ QR scanné. Re-activation LaunchAgent…"
launchctl load "${HOME}/Library/LaunchAgents/${PLIST_LABEL}.plist"
echo "  ✓ ${PLIST_LABEL} actif"

echo ""
echo "════════════════════════════════════════════"
echo "✅ Re-pair terminé pour bridge-${BRIDGE}."
echo ""
echo "⚠ Attendre 5 MINUTES avant de re-pairer un autre bridge (rate-limit WhatsApp)."
echo "⚠ Re-sync historique peut prendre 10-30 min côté whatsapp-mcp."
echo "════════════════════════════════════════════"
