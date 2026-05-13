"""Rich-Terminal-Dashboard."""

from __future__ import annotations

from typing import Any, Dict

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table


def format_uptime(seconds: float) -> str:
    d = int(seconds // 86400)
    h = int((seconds % 86400) // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if d > 0:
        return f"{d}d {h:02d}:{m:02d}:{s:02d}"
    return f"{h:02d}:{m:02d}:{s:02d}"


def build_dashboard(state: Dict[str, Any]) -> Layout:
    root = Layout()
    root.split_column(Layout(name="header", size=3), Layout(name="body"))

    title = (
        f"[bold cyan]Bitcoin Puzzle Lottery[/]  │  {state.get('host','')}  │  "
        f"Modus [yellow]{state.get('scan_mode','')}[/]  │  Ziele [green]{state.get('n_targets',0)}[/]"
    )
    root["header"].update(Panel(title, style="bold white on dark_blue"))

    tbl = Table(show_header=True, header_style="bold magenta", expand=True)
    tbl.add_column("Metrik", style="dim", width=28)
    tbl.add_column("Wert", style="white")

    g = state.get("gpu") or {}
    tbl.add_row("Keys/s (GPU, Ø)", f"{state.get('keys_per_sec_fmt','—')}")
    tbl.add_row("Mkey/s roh (Vanity)", f"{state.get('mkeys_gpu','—')}")
    tbl.add_row("Treffer (Vanity)", str(state.get("found", 0)))
    tbl.add_row("Uptime Orchestrator", format_uptime(float(state.get("uptime_s", 0))))
    tbl.add_row("Letzter Engine-Start", str(state.get("last_engine_start", "—")))
    tbl.add_row("GPU", str(g.get("name", "—")))
    tbl.add_row("GPU Util %", str(g.get("util_gpu", "—")))
    tbl.add_row("GPU Temp °C", str(g.get("temp_c", "—")))
    tbl.add_row("VRAM MB", f"{g.get('mem_used_mb','—')} / {g.get('mem_total_mb','—')}")
    tbl.add_row("Lüfter %", str(g.get("fan_pct", "—")))
    tbl.add_row("Vanity Zeile", str(state.get("vanity_line", "—"))[:120])
    tbl.add_row("Schätzung Odds", str(state.get("odds", "—")))

    root["body"].update(Panel(tbl, title="Live", border_style="cyan"))
    return root


def render_dashboard(console: Console, state: Dict[str, Any]) -> None:
    console.print(build_dashboard(state))
