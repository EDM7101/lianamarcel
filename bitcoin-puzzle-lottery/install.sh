#!/usr/bin/env bash
# Bitcoin Puzzle Lottery — Installation (Ubuntu 22.04, NVIDIA)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VS_DIR="${ROOT}/third_party/VanitySearch"
PREFIX="${PREFIX:-/opt/puzzle-lottery}"

echo "== Puzzle Lottery: Abhängigkeiten (APT) =="
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y build-essential libssl-dev python3-pip python3-venv git pkg-config
fi

echo "== CUDA / nvcc =="
CUDA="${CUDA:-/usr/local/cuda}"
if [[ ! -x "${CUDA}/bin/nvcc" ]]; then
  echo "WARNUNG: nvcc nicht unter ${CUDA}/bin/nvcc — bitte CUDA Toolkit (NVIDIA) installieren und CUDA exportieren."
fi

if command -v nvidia-smi >/dev/null 2>&1; then
  CCAP_RAW="$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader,nounits | head -1 | tr -d ' ')"
  CCAP="${CCAP_RAW//./}"
  echo "Erkannte Compute Capability: ${CCAP_RAW} -> CCAP=${CCAP}"
else
  CCAP="${CCAP:-86}"
  echo "nvidia-smi fehlt — verwende CCAP=${CCAP} (überschreibbar)"
fi

echo "== VanitySearch bauen =="
make -C "${VS_DIR}" clean 2>/dev/null || true
make -C "${VS_DIR}" -j"$(nproc)" gpu=1 CCAP="${CCAP}" CUDA="${CUDA}"

echo "== Installation nach ${PREFIX} =="
sudo mkdir -p "${PREFIX}/bin" "${PREFIX}/etc" "${PREFIX}/share"
sudo cp "${VS_DIR}/VanitySearch" "${PREFIX}/bin/VanitySearch"
sudo chmod +x "${PREFIX}/bin/VanitySearch"

if [[ ! -f "${PREFIX}/etc/config.yaml" ]]; then
  sudo cp "${ROOT}/config.example.yaml" "${PREFIX}/etc/config.yaml"
  echo "Beispiel-Konfiguration: ${PREFIX}/etc/config.yaml (bitte anpassen)"
fi

echo "== Python venv =="
sudo python3 -m venv "${PREFIX}/venv"
sudo "${PREFIX}/venv/bin/pip" install --upgrade pip
sudo "${PREFIX}/venv/bin/pip" install -r "${ROOT}/requirements.txt"
sudo "${PREFIX}/venv/bin/pip" install -e "${ROOT}"

echo "== targets.txt =="
if [[ ! -f "${PREFIX}/targets.txt" ]]; then
  sudo cp "${ROOT}/targets.example.txt" "${PREFIX}/targets.txt"
fi

echo "== Benchmark / GPU-Liste =="
"${PREFIX}/bin/VanitySearch" -l || true

echo "Fertig. Start: sudo ${PREFIX}/venv/bin/puzzle-lottery -c ${PREFIX}/etc/config.yaml"
echo "Oder: tmux new -s lottery \"sudo ${PREFIX}/venv/bin/puzzle-lottery -c ${PREFIX}/etc/config.yaml\""
