"""Real-time monitor using watchdog and Rich Live display."""

from __future__ import annotations

import select
import sys
import termios
import tty
from contextlib import contextmanager
from typing import Iterator

from rich.console import Group
from rich.live import Live
from rich.text import Text
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from tpb.config import CONFIG_DIR
from tpb.render import render_bar_group
from tpb.store import ensure_config_dir, list_bars

MONITOR_FOOTER = "q to exit"
_POLL_INTERVAL = 0.25


class _ConfigDirHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        self.changed = False

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        if event.src_path.endswith(".json") or event.src_path.endswith(".lock"):
            self.changed = True


def _build_display() -> Group:
    bars = list_bars()
    parts: list[Group | Text] = []
    if not bars:
        parts.append(Text("[dim]No progress bars registered.[/dim]"))
    else:
        parts.extend(render_bar_group(bar) for bar in bars)
    parts.append(Text(""))
    parts.append(Text(MONITOR_FOOTER, style="dim"))
    return Group(*parts)


@contextmanager
def _cbreak_stdin() -> Iterator[None]:
    if not sys.stdin.isatty():
        yield
        return

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _read_key(timeout: float = _POLL_INTERVAL) -> str | None:
    if not sys.stdin.isatty():
        return None

    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if not ready:
        return None
    return sys.stdin.read(1)


def run_monitor() -> None:
    """Watch the config directory and redraw progress bars on changes."""
    ensure_config_dir()
    handler = _ConfigDirHandler()
    observer = Observer()
    observer.schedule(handler, str(CONFIG_DIR), recursive=False)
    observer.start()

    try:
        with _cbreak_stdin():
            with Live(_build_display(), refresh_per_second=4, screen=True) as live:
                while True:
                    key = _read_key()
                    if key in {"q", "Q"}:
                        break
                    if handler.changed:
                        handler.changed = False
                        live.update(_build_display())
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
