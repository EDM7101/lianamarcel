# NVIDIA / RTX — Performance und Stabilität

## Compute Capability

`install.sh` liest `nvidia-smi --query-gpu=compute_cap` und setzt `CCAP` für den VanitySearch-Build (Makefile: ohne Punkt, z. B. `8.6` → `86`).

Manuell: `make -C third_party/VanitySearch gpu=1 CCAP=89 CUDA=/usr/local/cuda`

## RTX / Ada

- CCAP typisch **86** (Ampere), **89** (Ada), **80** (A100) — immer zur installierten GPU passend wählen.
- Neubau nach Treiber- oder CUDA-Wechsel nicht vergessen.

## Stabilität 24/7

- **Power Limit** (optional): `nvidia-smi -pl ...` für thermische Reserve.
- **Lüfterkurve**: Hetzner-GPU-Server meist feste Gehäuselüfter; GPU-Temperatur über Dashboard und `gpu_health.log` beobachten.
- **Watchdog**: `watchdog.sh` oder `Restart=always` in systemd (bereits im Beispiel-Service).

## PCIe / VRAM

- VanitySearch skaliert mit `-g`; Standard ist automatisch. Bei sehr vielen Zielen `-m` erhöhen (siehe VanitySearch-Hinweise in der Konsole).
- Ein GPU: `CUDA_VISIBLE_DEVICES=0` (Orchestrator setzt dies standardmäßig auf die erste konfigurierte GPU).

## Asynchrone CUDA-Transfers

Die Kernlogik liegt in **VanitySearch** (`GPUEngine.cu`, `cudaMemcpyAsync`); der Lotterie-Modus ändert nur die **Schlüsselbasis** pro Batch, nicht die Kernel.

## Optional: Keyhunt

Kangaroo-/Pollard-Verfahren (Keyhunt) zielen auf ** strukturierte** Suchräume, nicht auf rein zufällige Lotterie-Keys. Eine sinnvolle Kopplung ist nur für spezialisierte Szenarien relevant — hier nicht integriert; VanitySearch bleibt der GPU-Pfad.
