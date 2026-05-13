"""nvidia-smi CSV für Dashboard und Alerts."""

from __future__ import annotations

import subprocess
from typing import Dict, Optional

LOG = logging.getLogger(__name__)


def query_gpu(nvidia_smi: str = "nvidia-smi") -> Optional[Dict[str, str]]:
    try:
        out = subprocess.check_output(
            [
                nvidia_smi,
                "--query-gpu=utilization.gpu,utilization.memory,temperature.gpu,memory.used,memory.total,fan.speed,name",
                "--format=csv,noheader,nounits",
            ],
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).decode("utf-8", errors="replace")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        LOG.debug("nvidia-smi: %s", e)
        return None
    line = out.strip().splitlines()[0] if out.strip() else ""
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 7:
        return None
    return {
        "util_gpu": parts[0],
        "util_mem": parts[1],
        "temp_c": parts[2],
        "mem_used_mb": parts[3],
        "mem_total_mb": parts[4],
        "fan_pct": parts[5],
        "name": parts[6],
    }
