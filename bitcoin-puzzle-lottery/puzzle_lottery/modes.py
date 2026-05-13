"""Scan-Modi: Zielauswahl für Lotterie-Orchestrierung (CPU-seitig, VanitySearch bleibt Multi-Target)."""

from __future__ import annotations

import hashlib
import random
import time
from pathlib import Path
from typing import List, Tuple


def read_target_lines(targets_file: Path) -> List[str]:
    if not targets_file.is_file():
        return []
    out: List[str] = []
    for line in targets_file.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out


def mode_pure_random(lines: List[str], _: dict) -> List[str]:
    return list(lines)


def mode_rotating(lines: List[str], cfg: dict) -> List[str]:
    frac = float(cfg.get("active_fraction", 0.35))
    frac = min(1.0, max(0.01, frac))
    k = max(1, int(len(lines) * frac))
    rng = random.SystemRandom()
    return rng.sample(lines, k=min(k, len(lines))) if lines else []


def mode_time_rotation(lines: List[str], cfg: dict) -> List[str]:
    period = int(cfg.get("rotate_period_minutes", 20)) * 60
    bucket = int(time.time() // max(period, 60))
    rng = random.Random(int(hashlib.sha256(str(bucket).encode()).hexdigest()[:16], 16))
    shuffled = lines[:]
    rng.shuffle(shuffled)
    frac = float(cfg.get("active_fraction", 0.5))
    k = max(1, int(len(shuffled) * min(1.0, max(0.02, frac))))
    return shuffled[: min(k, len(shuffled))]


def mode_weighted(lines: List[str], cfg: dict) -> List[str]:
    """Gewichtung über mehrfache Einträge in targets.txt; hier zusätzlich leichte Puzzle-Bias-Heuristik."""
    cap = int(cfg.get("weighted_duplication_cap", 12))
    cap = max(1, cap)
    out: List[str] = []
    rng = random.SystemRandom()
    for addr in lines:
        weight = 1
        if addr.startswith("1") and len(addr) >= 26:
            tail = addr[-4:]
            try:
                h = int(hashlib.md5(addr.encode()).hexdigest(), 16)
                bias = 1 + (h % 5)
            except Exception:
                bias = 1
            weight = min(cap, bias)
        for _ in range(weight):
            out.append(addr)
    rng.shuffle(out)
    frac = float(cfg.get("active_fraction", 1.0))
    k = max(1, int(len(out) * min(1.0, max(0.05, frac))))
    return out[: min(k, len(out))] if out else []


def mode_entropy_mix(lines: List[str], cfg: dict) -> List[str]:
    _ = cfg
    return mode_pure_random(lines, cfg)


MODE_FUNCS = {
    "pure_random": mode_pure_random,
    "rotating": mode_rotating,
    "weighted": mode_weighted,
    "time_rotation": mode_time_rotation,
    "entropy_mix": mode_entropy_mix,
}


def select_active_targets(lines: List[str], scan_mode: str, orch: dict) -> Tuple[List[str], str]:
    fn = MODE_FUNCS.get(scan_mode, mode_pure_random)
    active = fn(lines, orch)
    return active, scan_mode
