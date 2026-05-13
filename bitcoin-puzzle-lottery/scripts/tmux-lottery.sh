#!/usr/bin/env bash
# Tmux-Starter für Headless-Server
set -euo pipefail
PREFIX="${PREFIX:-/opt/puzzle-lottery}"
SESSION="${SESSION:-puzzle-lottery}"
CONFIG="${1:-${PREFIX}/etc/config.yaml}"

tmux has-session -t "${SESSION}" 2>/dev/null && tmux kill-session -t "${SESSION}"
tmux new-session -d -s "${SESSION}" "exec ${PREFIX}/venv/bin/puzzle-lottery -c ${CONFIG}"
echo "tmux-Session ${SESSION} gestartet. Anhängen: tmux attach -t ${SESSION}"
