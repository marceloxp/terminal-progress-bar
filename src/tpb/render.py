"""Rich-based rendering for progress bars."""

from __future__ import annotations

from rich.console import Console, Group, RenderableType
from rich.progress import BarColumn, Progress, TaskProgressColumn
from rich.text import Text

from tpb.config import BAR_WIDTH, STATUS_ACTIVE, STATUS_DONE, STATUS_ERROR
from tpb.store import ProgressBar

STATUS_COLORS = {
    STATUS_ACTIVE: "yellow",
    STATUS_DONE: "green",
    STATUS_ERROR: "red",
}


def _status_suffix(bar: ProgressBar) -> str:
    if bar.status == STATUS_DONE:
        return " (completed)"
    if bar.status == STATUS_ERROR:
        return " (error)"
    return ""


def _make_progress(bar: ProgressBar) -> Progress:
    color = STATUS_COLORS.get(bar.status, "white")
    progress = Progress(
        BarColumn(
            bar_width=BAR_WIDTH,
            complete_style=f"bold {color}",
            finished_style=f"bold {color}",
        ),
        TaskProgressColumn(),
        expand=False,
    )
    progress.add_task("", total=bar.max, completed=bar.current, start=True)
    return progress


def render_bar_group(bar: ProgressBar) -> Group:
    """Render a single progress bar with optional status text and trailing blank line."""
    color = STATUS_COLORS.get(bar.status, "white")
    label = Text(f"{bar.label}{_status_suffix(bar)}", style=color)

    parts: list[RenderableType] = [label, _make_progress(bar)]
    if bar.status_text:
        parts.append(Text(bar.status_text, style="dim"))
    parts.append(Text(""))
    return Group(*parts)


def render_bars(bars: list[ProgressBar], console: Console | None = None) -> None:
    """Print all progress bars to the console."""
    console = console or Console()
    if not bars:
        console.print("[dim]No progress bars registered.[/dim]")
        return

    for bar in bars:
        console.print(render_bar_group(bar))
