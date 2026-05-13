"""Strukturierte Logs mit täglicher Rotation."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(log_dir: Path, level: str = "INFO", max_bytes: int = 50_000_000, backup_count: int = 14) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root.addHandler(sh)

    app = RotatingFileHandler(
        log_dir / "puzzle-lottery.log", maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    app.setFormatter(fmt)
    root.addHandler(app)

    perf = TimedRotatingFileHandler(
        log_dir / "performance.log", when="midnight", interval=1, backupCount=backup_count, encoding="utf-8"
    )
    perf.setFormatter(fmt)
    perf.suffix = "%Y-%m-%d"
    root.addHandler(perf)

    crash = logging.FileHandler(log_dir / "crash.log", encoding="utf-8")
    crash.setLevel(logging.ERROR)
    crash.setFormatter(fmt)
    root.addHandler(crash)

    gpu = logging.FileHandler(log_dir / "gpu_health.log", encoding="utf-8")
    gpu.setFormatter(fmt)
    glog = logging.getLogger("gpu_health")
    glog.addHandler(gpu)
    glog.setLevel(logging.INFO)
    glog.propagate = False
    gh = logging.StreamHandler()
    gh.setFormatter(fmt)
    glog.addHandler(gh)

    tel = logging.FileHandler(log_dir / "telegram.log", encoding="utf-8")
    tel.setFormatter(fmt)
    tlog = logging.getLogger("telegram_audit")
    tlog.addHandler(tel)
    tlog.setLevel(logging.INFO)
    tlog.propagate = False
