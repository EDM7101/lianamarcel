# Hetzner GPU — Deployment

## Empfohlene Server

- GPU-Instanzen mit NVIDIA RTX (z. B. GEX44) unter Ubuntu 22.04.
- Öffentliche IPv4, SSH-Key-Login.

## Schritte

1. **NVIDIA-Treiber und CUDA** nach NVIDIA-Dokumentation installieren (Toolkit passend zur Treiberversion). Prüfen: `nvidia-smi`, `nvcc --version`.

2. Repository auf den Server klonen und `install.sh` ausführen:

   ```bash
   cd bitcoin-puzzle-lottery
   chmod +x install.sh update.sh watchdog.sh scripts/*.sh
   sudo ./install.sh
   ```

3. **`/opt/puzzle-lottery/etc/config.yaml`** anpassen:

   - `orchestrator.work_dir` (z. B. `/var/lib/puzzle-lottery`)
   - `orchestrator.targets_file` (z. B. `/opt/puzzle-lottery/targets.txt`)
   - `vanity.binary` falls abweichend
   - `logging.dir` (z. B. `/var/log/puzzle-lottery`)

4. Verzeichnisse anlegen:

   ```bash
   sudo mkdir -p /var/lib/puzzle-lottery /var/log/puzzle-lottery
   ```

5. **systemd** (Beispiel in `systemd/puzzle-lottery.service`):

   ```bash
   sudo cp systemd/puzzle-lottery.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now puzzle-lottery.service
   ```

6. **Persistenz**: optional `nvidia-persistenced` aktivieren, damit die GPU nach Neustart schneller bereitsteht.

7. **Firewall**: nur SSH und ggf. Monitoring — Telegram benötigt ausgehend HTTPS.

## Hinweis

Dieses Projekt führt **keine** sequenzielle Brute-Force-Suche aus, sondern nutzt VanitySearch im **Lotterie-Modus** (`-lottery`): zufällige private Basiskeys pro CUDA-Batch bei voller Nutzung der VanitySearch-GPU-Pipeline.
