#!/usr/bin/env bash
# healthcheck.sh — Ping les 3 bridges, alerte email si silence > 2h
# Usage : bash healthcheck.sh (prévu pour cron / launchd toutes les 15 min)
# Auteur : VLBH / Patrick Bays — 2026-04-18

set -euo pipefail

BRIDGES_ROOT="${HOME}/whatsapp-bridges"
LOG_FILE="${HOME}/Library/Logs/whatsapp-mcp/healthcheck.log"
ENV_FILE="${BRIDGES_ROOT}/shared/.env"

# shellcheck disable=SC1090
source "$ENV_FILE"

mkdir -p "$(dirname "$LOG_FILE")"

BRIDGES=("z1" "z2et3" "za")
NOW=$(date +%s)
SILENCE_LIMIT=$((ALERT_SILENCE_HOURS * 3600))

send_alert() {
  local subject="$1"
  local body="$2"
  python3 <<PYEOF
import smtplib, ssl
from email.mime.text import MIMEText
msg = MIMEText("""$body""")
msg["Subject"] = """$subject"""
msg["From"] = "$SMTP_USER"
msg["To"] = "$EMAIL_ALERT"
ctx = ssl.create_default_context()
with smtplib.SMTP_SSL("$SMTP_HOST", $SMTP_PORT, context=ctx) as s:
    s.login("$SMTP_USER", "$SMTP_APP_PASSWORD")
    s.sendmail(msg["From"], [msg["To"]], msg.as_string())
PYEOF
}

for bridge in "${BRIDGES[@]}"; do
  DB="${BRIDGES_ROOT}/bridge-${bridge}/data/store/whatsapp.db"
  PLIST_LABEL="energy.vlbh.wa-bridge-${bridge}"

  # 1. LaunchAgent actif ?
  if ! launchctl list | grep -q "$PLIST_LABEL"; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ALERT bridge-${bridge} : LaunchAgent non chargé" | tee -a "$LOG_FILE"
    send_alert "[VLBH WA] bridge-${bridge} DOWN" "LaunchAgent ${PLIST_LABEL} non chargé sur patricktest."
    continue
  fi

  # 2. DB existe ?
  if [[ ! -f "$DB" ]]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ALERT bridge-${bridge} : DB manquante" | tee -a "$LOG_FILE"
    send_alert "[VLBH WA] bridge-${bridge} DB missing" "DB $DB introuvable — bridge pas pairé ?"
    continue
  fi

  # 3. Dernier message reçu ?
  LAST_TS=$(sqlite3 "$DB" "SELECT MAX(timestamp) FROM messages;" 2>/dev/null || echo "0")
  if [[ -z "$LAST_TS" || "$LAST_TS" == "0" ]]; then
    LAST_TS=0
  fi

  DELTA=$((NOW - LAST_TS))
  if (( DELTA > SILENCE_LIMIT )); then
    HUMAN_DELTA=$((DELTA / 3600))
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ALERT bridge-${bridge} : silence ${HUMAN_DELTA}h" | tee -a "$LOG_FILE"
    send_alert "[VLBH WA] bridge-${bridge} silent ${HUMAN_DELTA}h" \
      "Aucun message reçu depuis ${HUMAN_DELTA}h sur bridge-${bridge}. Vérifier WhatsApp mobile → Appareils liés."
  else
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] OK bridge-${bridge} : dernier message $((DELTA / 60)) min" >> "$LOG_FILE"
  fi
done
