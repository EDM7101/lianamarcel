#!/usr/bin/env bash
# Einfacher Watchdog: prüft systemd-Unit oder Prozess (optional anpassen)
set -euo pipefail
UNIT="${UNIT:-puzzle-lottery.service}"
INTERVAL="${INTERVAL:-120}"

while true; do
  if systemctl is-active --quiet "${UNIT}" 2>/dev/null; then
    :
  else
    echo "$(date -Is) ${UNIT} nicht aktiv — Neustart"
    systemctl restart "${UNIT}" 2>/dev/null || true
  fi
  sleep "${INTERVAL}"
done
