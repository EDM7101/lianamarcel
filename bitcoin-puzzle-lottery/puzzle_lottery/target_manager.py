"""Schreibt active_targets.txt und beobachtet targets.txt (Hot Reload)."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable, List, Optional

from .modes import read_target_lines, select_active_targets


class TargetManager:
    def __init__(
        self,
        cfg: dict,
        on_change: Optional[Callable[[Path, List[str]], None]] = None,
    ) -> None:
        self._cfg = cfg
        orch = cfg["orchestrator"]
        self.targets_path = Path(orch["targets_file"])
        self.work_dir = Path(orch["work_dir"])
        self.active_name = orch.get("active_targets_name", "active_targets.txt")
        self.interval = float(orch.get("reload_targets_interval_sec", 45))
        self.active_path = self.work_dir / self.active_name
        self._lock = threading.Lock()
        self._mtime: float = 0.0
        self._on_change = on_change
        self._last_lines: List[str] = []
        self._last_refresh = 0.0

    def initial_write(self) -> Path:
        lines = read_target_lines(self.targets_path)
        active, _mode = select_active_targets(lines, self._cfg["orchestrator"]["scan_mode"], self._cfg["orchestrator"])
        self._write_atomic(active)
        self._mtime = self.targets_path.stat().st_mtime if self.targets_path.exists() else 0.0
        self._last_lines = active
        return self.active_path

    def _write_atomic(self, lines: List[str]) -> None:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.active_path.with_suffix(".tmp")
        data = "\n".join(lines) + ("\n" if lines else "")
        tmp.write_text(data, encoding="utf-8")
        tmp.replace(self.active_path)

    def maybe_reload(self) -> bool:
        """True wenn Zielmenge geändert wurde (VanitySearch-Neustart nötig)."""
        if not self.targets_path.exists():
            return False
        now = time.monotonic()
        mtime = self.targets_path.stat().st_mtime
        periodic = (now - self._last_refresh) >= self.interval
        changed_file = mtime > self._mtime
        if not (periodic or changed_file):
            return False
        self._last_refresh = now
        with self._lock:
            lines = read_target_lines(self.targets_path)
            active, _ = select_active_targets(
                lines, self._cfg["orchestrator"]["scan_mode"], self._cfg["orchestrator"]
            )
            prev = self._last_lines
            self._write_atomic(active)
            self._mtime = mtime
            self._last_lines = active
            updated = active != prev or changed_file
            if updated and self._on_change:
                self._on_change(self.active_path, active)
            return updated
