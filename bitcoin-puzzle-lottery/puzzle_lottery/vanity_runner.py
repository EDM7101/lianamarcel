"""VanitySearch als Subprozess mit Argumentbau."""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Callable, List, Optional


class VanityRunner:
    def __init__(self, cfg: dict, active_targets: Path, hits_out: Path, on_stdout_line: Callable[[str], None]) -> None:
        self.cfg = cfg
        self.active_targets = active_targets
        self.hits_out = hits_out
        self.on_stdout_line = on_stdout_line
        self.proc: Optional[subprocess.Popen[str]] = None
        self._threads: List[threading.Thread] = []

    def build_argv(self, entropy_seed_extra: str = "") -> List[str]:
        v = self.cfg["vanity"]
        exe = v["binary"]
        args: List[str] = [exe]
        if v.get("gpu", True):
            args.append("-gpu")
        sm = (v.get("search_mode") or "both").lower()
        if sm == "uncompressed":
            args.append("-u")
        elif sm == "both":
            args.append("-b")
        # compressed: VanitySearch-Standard (ohne Flag)
        if v.get("lottery_kernel_reseed", True):
            args.append("-lottery")
        elif int(v.get("rekey_mkeys", 0) or 0) > 0:
            args.extend(["-r", str(int(v["rekey_mkeys"]))])
        gids = v.get("gpu_ids") or [0]
        args.append("-gpuId")
        args.append(",".join(str(int(x)) for x in gids))
        grid = v.get("grid")
        if grid and isinstance(grid, (list, tuple)) and len(grid) >= 2:
            args.append("-g")
            args.append(",".join(str(int(x)) for x in grid))
        threads = v.get("cpu_threads")
        if threads is not None:
            args.extend(["-t", str(int(threads))])
        args.extend(["-m", str(int(v.get("max_found", 65536)))])
        args.extend(["-i", str(self.active_targets)])
        args.extend(["-o", str(self.hits_out)])
        if entropy_seed_extra:
            args.extend(["-ps", entropy_seed_extra[:2000]])
        for ex in v.get("extra_args") or []:
            if isinstance(ex, str) and ex.strip():
                args.append(ex.strip())
        return args

    def start(self, entropy_seed_extra: str = "") -> None:
        self.stop()
        argv = self.build_argv(entropy_seed_extra)
        env = os.environ.copy()
        # CUDA stabiler: erste GPU
        if self.cfg["vanity"].get("gpu", True):
            gids = self.cfg["vanity"].get("gpu_ids") or [0]
            env.setdefault("CUDA_VISIBLE_DEVICES", str(int(gids[0])))
        self.hits_out.parent.mkdir(parents=True, exist_ok=True)
        if not self.hits_out.exists():
            self.hits_out.write_text("", encoding="utf-8")
        self.proc = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )

        def reader() -> None:
            assert self.proc and self.proc.stdout
            for line in self.proc.stdout:
                self.on_stdout_line(line.rstrip("\n"))

        t = threading.Thread(target=reader, name="vanity-stdout", daemon=True)
        t.start()
        self._threads = [t]

    def stop(self, timeout: float = 8.0) -> None:
        if self.proc is None:
            return
        try:
            self.proc.terminate()
            self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.proc = None

    def poll(self) -> Optional[int]:
        if self.proc is None:
            return None
        return self.proc.poll()


def which_or_path(binary: str) -> str:
    if Path(binary).is_file():
        return str(Path(binary).resolve())
    w = shutil.which(binary)
    return w or binary
