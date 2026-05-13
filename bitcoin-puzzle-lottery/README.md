# Bitcoin Puzzle Lottery Scanner

GPU-orientierter **Lotterie-Scanner** für Bitcoin-Puzzle-Adressen: Orchestrierung in Python, Kernberechnung durch erweiterten [**VanitySearch**](https://github.com/JeanLucPons/VanitySearch) (GPL v3) mit Modus **`-lottery`** (neue zufällige GPU-Basiskeys pro CUDA-Batch).

## Schnellstart

```bash
cd bitcoin-puzzle-lottery
chmod +x install.sh update.sh watchdog.sh scripts/*.sh
sudo ./install.sh
sudo cp config.example.yaml /opt/puzzle-lottery/etc/config.yaml
# config.yaml: Pfade, Telegram, scan_mode
sudo /opt/puzzle-lottery/venv/bin/puzzle-lottery -c /opt/puzzle-lottery/etc/config.yaml
```

## Dokumentation

- [Telegram](docs/TELEGRAM.md)
- [Hetzner / Server](docs/HETZNER.md)
- [NVIDIA / RTX](docs/NVIDIA.md)
- [Keyhunt (optional, nicht angebunden)](docs/KEYHUNT.md)

## Ziele

Standard: `targets.txt` (eine Adresse pro Zeile). CSV mit Spalte `address`:

```bash
python3 scripts/csv_to_targets.py puzzle-liste.csv targets.txt
```

## Lizenz

- Eigenes Orchestrierungs- und Skriptmaterial: wie das umgebende Repository.
- `third_party/VanitySearch`: **GNU GPL v3** (Upstream JeanLucPons/VanitySearch).

## Upstream-Anpassungen (Ubuntu 22.04 / GCC 13)

- `-lottery` und kleinere Build-Fixes (`Timer.h`, `sha256.h/.cpp`, `sha512.h/.cpp`, `Makefile` mit `-std=c++11`, `CXXCUDA ?= g++`, `hmac_sha512`-Variablenname).
