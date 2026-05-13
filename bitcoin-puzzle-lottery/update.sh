#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${PREFIX:-/opt/puzzle-lottery}"
cd "${ROOT}"
git pull --ff-only || true
exec "${ROOT}/install.sh"
