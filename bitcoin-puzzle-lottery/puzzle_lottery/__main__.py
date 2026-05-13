"""CLI-Einstieg: Orchestrierung, Dashboard, Telegram, Checkpoints."""

from __future__ import annotations

import argparse
import logging
import os
import secrets
import signal
import socket
import sys
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Deque

from rich.console import Console
from rich.live import Live

from . import __version__
from .checkpoint import load_checkpoint, save_checkpoint
from .config_loader import ensure_dirs, load_config
from .dashboard import build_dashboard, format_uptime
from .gpu_info import query_gpu
from .hit_processor import HitProcessor
from .logging_setup import setup_logging
from .stats_parser import RuntimeStats
from .target_manager import TargetManager
from .telegram_client import TelegramClient
from .vanity_runner import VanityRunner, which_or_path

LOG = logging.getLogger(__name__)

_shutdown = threading.Event()
_reload_vanity = threading.Event()


def _handle_sig(_sig, _frm) -> None:
    _shutdown.set()


def _odds_hint(n_targets: int) -> str:
    if n_targets <= 0:
        return "keine Ziele geladen"
    # Jede Puzzle-Adresse: extrem kleine Trefferwahrscheinlichkeit pro zufälligem Key
    return f"≪ 1 / 2^256 effektiv; {n_targets} parallele Ziele (Lotterie-Heuristik)"


def _entropy_ps(cfg: dict) -> str:
    if cfg["orchestrator"].get("scan_mode") != "entropy_mix":
        return ""
    parts = [
        secrets.token_hex(24),
        socket.gethostname(),
        str(time.time_ns()),
        hex(os.getpid()),
    ]
    return "|".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser(description="Bitcoin Puzzle Lottery Scanner (VanitySearch-Orchestrator)")
    ap.add_argument("--config", "-c", default="config.yaml", help="Pfad zur YAML-Konfiguration")
    ap.add_argument("--wizard", action="store_true", help="Interaktive Mindestkonfiguration (Telegram)")
    args = ap.parse_args()

    if args.wizard:
        _run_wizard(Path(args.config))
        return

    cfg = load_config(args.config)
    ensure_dirs(cfg)
    setup_logging(
        Path(cfg["logging"]["dir"]),
        cfg["logging"].get("level", "INFO"),
        int(cfg["logging"].get("max_bytes", 50_000_000)),
        int(cfg["logging"].get("backup_count", 14)),
    )

    cfg["vanity"]["binary"] = which_or_path(cfg["vanity"]["binary"])
    if not Path(cfg["vanity"]["binary"]).is_file():
        LOG.error("VanitySearch-Binary fehlt: %s", cfg["vanity"]["binary"])
        sys.exit(2)

    work = Path(cfg["orchestrator"]["work_dir"])
    ck_path = work / "checkpoint.json"
    hits_vanity = work / cfg["paths"].get("vanity_output_hits", "vanity_hits.txt")
    sec = cfg["security"]
    hits_plain = work / sec.get("plaintext_hits_name", "hits.txt")
    hits_enc = work / sec.get("encrypted_hits_name", "hits.enc.jsonl")

    tg = TelegramClient(cfg)
    stats = RuntimeStats(smooth=int(cfg.get("performance", {}).get("rate_smooth_samples", 6)))

    def on_targets_change(_p: Path, _active: list[str]) -> None:
        _reload_vanity.set()
        LOG.info("Ziel-Set aktualisiert — VanitySearch wird neu gestartet")
        ta = logging.getLogger("telegram_audit")
        if tg.enabled:
            tg.send(f"🔄 <b>Ziel-Reload</b>\nNeue aktive Puzzle-Liste geschrieben.", disable_notification=True)
            ta.info("telegram: target reload")

    tm = TargetManager(cfg, on_change=on_targets_change)
    active_path = tm.initial_write()
    if not active_path.read_text(encoding="utf-8").strip():
        LOG.error("Keine aktiven Ziele — bitte %s befüllen", cfg["orchestrator"]["targets_file"])
        sys.exit(3)

    lines_tail: Deque[str] = deque(maxlen=40)

    def on_stdout_line(line: str) -> None:
        lines_tail.append(line)
        stats.update_from_line(line)

    runner = VanityRunner(cfg, active_path, hits_vanity, on_stdout_line)

    def on_hit(block: str) -> None:
        if tg.enabled:
            tg.hit_alert(block[:3500])
        ta = logging.getLogger("telegram_audit")
        ta.info("HIT notification queued")

    hp = HitProcessor(
        hits_vanity,
        hits_plain,
        hits_enc,
        sec.get("fernet_key_env", "PUZZLE_LOTTERY_FERNET_KEY"),
        on_hit,
    )

    if cfg.get("telegram", {}).get("notify_startup_shutdown", True) and tg.enabled:
        tg.send(
            f"🚀 <b>Puzzle Lottery gestartet</b>\nHost: <code>{socket.gethostname()}</code>\nVersion: {__version__}",
            disable_notification=True,
        )

    signal.signal(signal.SIGINT, _handle_sig)
    signal.signal(signal.SIGTERM, _handle_sig)

    if cfg["orchestrator"].get("benchmark_on_start", True):
        _quick_benchmark(cfg["vanity"]["binary"], cfg["gpu_health"].get("nvidia_smi_path", "nvidia-smi"))

    host = socket.gethostname()
    t_start = time.monotonic()
    last_ck = time.monotonic()
    last_hourly = time.monotonic()
    ck = load_checkpoint(ck_path)
    shared = {"last_engine_start": "—", "running": False}

    def supervisor() -> None:
        while not _shutdown.is_set():
            _reload_vanity.clear()
            shared["last_engine_start"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            ps = _entropy_ps(cfg)
            LOG.info("Starte VanitySearch…")
            runner.start(ps)
            shared["running"] = True
            while runner.poll() is None and not _shutdown.is_set():
                if _reload_vanity.wait(timeout=0.35):
                    _reload_vanity.clear()
                    LOG.info("Neustart VanitySearch wegen Reload-Event")
                    break
                tm.maybe_reload()
            shared["running"] = False
            runner.stop()
            if _shutdown.is_set():
                break
            time.sleep(1.0)

    th_sup = threading.Thread(target=supervisor, name="supervisor", daemon=True)
    th_sup.start()

    console = Console()
    nvidia_path = cfg["gpu_health"].get("nvidia_smi_path", "nvidia-smi")

    with Live(build_dashboard(_dash_dict(cfg, host, 0, stats, {}, active_path, shared["last_engine_start"], shared, lines_tail)), console=console, refresh_per_second=2) as live:
        while not _shutdown.is_set():
            now = time.monotonic()
            uptime = now - t_start
            tm.maybe_reload()
            hp.poll()

            if now - last_ck >= float(cfg["orchestrator"].get("checkpoint_interval_sec", 60)):
                last_ck = now
                est = stats.estimated_keys_from_log2()
                approx = float(est) if est is not None else float(ck.get("approx_total_keys", 0.0))
                save_checkpoint(
                    ck_path,
                    {
                        "approx_total_keys": approx,
                        "uptime_s": uptime,
                        "host": host,
                        "scan_mode": cfg["orchestrator"]["scan_mode"],
                    },
                )
                ck["approx_total_keys"] = approx

            if (
                tg.enabled
                and cfg.get("telegram", {}).get("hourly_report", True)
                and (now - last_hourly) >= 3600.0
            ):
                last_hourly = now
                g = query_gpu(nvidia_path) or {}
                n_active = len([x for x in active_path.read_text(encoding="utf-8").splitlines() if x.strip()])
                tg.hourly_lottery_card(
                    {
                        "keys_total_fmt": f"2^{stats.total_log2:.2f} (Vanity)",
                        "keys_per_sec_fmt": f"{stats.keys_per_sec()/1e9:.3f} Gkeys/s (GPU Ø)",
                        "uptime": format_uptime(uptime),
                        "gpu_temp": f"{g.get('temp_c', '?')} °C",
                        "vram": f"{g.get('mem_used_mb', '?')} / {g.get('mem_total_mb', '?')} MB",
                        "fan": f"{g.get('fan_pct', '?')}%",
                        "mode": cfg["orchestrator"]["scan_mode"],
                        "puzzles": str(n_active),
                        "health": "OK" if shared.get("running") else "STARTING",
                        "odds": _odds_hint(n_active),
                        "host": host,
                        "last_restart": shared["last_engine_start"],
                    }
                )

            g = query_gpu(nvidia_path) or {}
            glog = logging.getLogger("gpu_health")
            try:
                tc = int(float(g["temp_c"])) if g.get("temp_c") not in (None, "") else 0
            except (TypeError, ValueError):
                tc = 0
            if tc >= int(cfg["gpu_health"].get("temp_critical_c", 88)):
                glog.error("GPU critical temp %s", g["temp_c"])
                if tg.enabled:
                    tg.send(f"🔥 GPU-Temperatur kritisch: {g['temp_c']} °C", disable_notification=False)

            st = _dash_dict(cfg, host, uptime, stats, g, active_path, shared["last_engine_start"], shared, lines_tail)
            live.update(build_dashboard(st))
            time.sleep(0.4)

    runner.stop()
    if tg.enabled and cfg.get("telegram", {}).get("notify_startup_shutdown", True):
        tg.send(f"🛑 Puzzle Lottery beendet auf <code>{host}</code>", disable_notification=True)
    LOG.info("Beendet.")


def _dash_dict(cfg, host, uptime, stats, g, active_path, last_engine_start, supervisor_state, lines_tail) -> dict:
    n_active = 0
    if active_path.exists():
        n_active = len([x for x in active_path.read_text(encoding="utf-8").splitlines() if x.strip() and not x.startswith("#")])
    vanity_line = ""
    if lines_tail:
        for x in reversed(lines_tail):
            if "Mkey/s" in x:
                vanity_line = x
                break
    return {
        "host": host,
        "scan_mode": cfg["orchestrator"]["scan_mode"],
        "n_targets": n_active,
        "keys_per_sec_fmt": f"{stats.keys_per_sec()/1e9:.3f} Gkeys/s",
        "mkeys_gpu": f"{stats.mkeys_gpu:.2f}",
        "found": stats.found,
        "uptime_s": uptime,
        "last_engine_start": last_engine_start,
        "gpu": g,
        "vanity_line": vanity_line or stats.raw_line,
        "odds": _odds_hint(n_active),
        "running": supervisor_state.get("running"),
    }


def _quick_benchmark(vanity_bin: str, nvidia_smi: str) -> None:
    import subprocess

    LOG.info("GPU-Check (nvidia-smi)…")
    g = query_gpu(nvidia_smi)
    if g:
        LOG.info("GPU: %s Temp %s°C", g.get("name"), g.get("temp_c"))
    try:
        subprocess.run([vanity_bin, "-l"], check=False, timeout=30, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        LOG.warning("VanitySearch -l: %s", e)


def _run_wizard(out_path: Path) -> None:
    print("=== Puzzle Lottery Setup-Wizard ===\n")
    token = input("Telegram Bot Token (leer = überspringen): ").strip()
    chat = input("Telegram Chat-ID: ").strip()
    vanity = input("Pfad zu VanitySearch [./VanitySearch]: ").strip() or "./VanitySearch"
    targets = input("Pfad zu targets.txt [./targets.txt]: ").strip() or "./targets.txt"
    work = input("Arbeitsverzeichnis [./puzzle-data]: ").strip() or "./puzzle-data"
    sample = Path(__file__).resolve().parent.parent / "config.example.yaml"
    text = sample.read_text(encoding="utf-8") if sample.is_file() else ""
    if "CHANGE_ME" in text and token:
        text = text.replace("CHANGE_ME", token, 1)
    # crude replace chat id line
    lines = text.splitlines()
    out_lines = []
    for line in lines:
        if line.strip().startswith("chat_id:") and chat:
            out_lines.append(f'  chat_id: "{chat}"')
        elif line.strip().startswith("enabled:") and token and chat:
            out_lines.append("  enabled: true")
        elif line.strip().startswith("binary:"):
            out_lines.append(f'  binary: "{vanity}"')
        elif line.strip().startswith("targets_file:"):
            out_lines.append(f'  targets_file: "{targets}"')
        elif line.strip().startswith("work_dir:"):
            out_lines.append(f'  work_dir: "{work}"')
        else:
            out_lines.append(line)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"\nGeschrieben: {out_path}\nBitte manuell prüfen (YAML-Syntax).")


if __name__ == "__main__":
    main()
