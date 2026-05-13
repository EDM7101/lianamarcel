"""VanitySearch-Statuszeile parsen."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import List, Optional


_LINE_RE = re.compile(
    r"\[\s*([0-9.]+)\s+Mkey/s\]\[GPU\s+([0-9.]+)\s+Mkey/s\]\[Total\s+2\^([0-9.]+)\]"
)


@dataclass
class RuntimeStats:
    mkeys_total: float = 0.0
    mkeys_gpu: float = 0.0
    total_log2: float = 0.0
    found: int = 0
    raw_line: str = ""
    _gpu_hist: List[float] = field(default_factory=list)
    _tot_hist: List[float] = field(default_factory=list)
    smooth: int = 6

    def update_from_line(self, line: str) -> bool:
        m = _LINE_RE.search(line)
        if not m:
            if "Found" in line:
                mf = re.search(r"Found\s+(\d+)", line)
                if mf:
                    self.found = int(mf.group(1))
            return False
        self.raw_line = line.strip()
        g = float(m.group(1))
        gg = float(m.group(2))
        t2 = float(m.group(3))
        self.mkeys_total = g
        self.mkeys_gpu = gg
        self.total_log2 = t2
        self._tot_hist.append(g)
        self._gpu_hist.append(gg)
        if len(self._tot_hist) > self.smooth:
            self._tot_hist.pop(0)
        if len(self._gpu_hist) > self.smooth:
            self._gpu_hist.pop(0)
        mf = re.search(r"Found\s+(\d+)", line)
        if mf:
            self.found = int(mf.group(1))
        return True

    def avg_gpu_mkeys(self) -> float:
        return sum(self._gpu_hist) / max(len(self._gpu_hist), 1)

    def keys_per_sec(self) -> float:
        return self.avg_gpu_mkeys() * 1e6

    def estimated_keys_from_log2(self) -> Optional[float]:
        if self.total_log2 <= 0:
            return None
        try:
            return math.pow(2.0, self.total_log2)
        except OverflowError:
            return None
