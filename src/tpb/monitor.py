"""Real-time monitor using watchdog and Rich Live display."""

from __future__ import annotations

import time

from rich.console import Group
from rich.live import Live
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from tpb.config import CONFIG_DIR
from tpb.render import render_bar_group
from tpb.store import ensure_config_dir, list_bars


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
    if not bars:
        from rich.text import Text

        return Group(Text("[dim]No progress bars registered.[/dim]"))

    return Group(*[render_bar_group(bar) for bar in bars])


def run_monitor() -> None:
    """Watch the config directory and redraw progress bars on changes."""
    ensure_config_dir()
    handler = _ConfigDirHandler()
    observer = Observer()
    observer.schedule(handler, str(CONFIG_DIR), recursive=False)
    observer.start()

    try:
        with Live(_build_display(), refresh_per_second=4, screen=True) as live:
            while True:
                if handler.changed:
                    handler.changed = False
                    live.update(_build_display())
                time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
