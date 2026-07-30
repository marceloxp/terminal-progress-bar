"""Tests for monitor display."""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from tpb.monitor import MONITOR_FOOTER, _build_display
from tpb.store import create_bar


def test_build_display_includes_footer(isolated_config, monkeypatch):
    monkeypatch.setattr("tpb.config.CONFIG_DIR", isolated_config)
    monkeypatch.setattr("tpb.store.CONFIG_DIR", isolated_config)
    create_bar("job-a", 10, 100, "Job A")

    output = StringIO()
    console = Console(file=output, width=120, force_terminal=True)
    console.print(_build_display())

    rendered = output.getvalue()
    assert MONITOR_FOOTER in rendered
    assert "Job A" in rendered


def test_build_display_footer_when_empty(isolated_config, monkeypatch):
    monkeypatch.setattr("tpb.config.CONFIG_DIR", isolated_config)
    monkeypatch.setattr("tpb.store.CONFIG_DIR", isolated_config)

    output = StringIO()
    console = Console(file=output, width=120, force_terminal=True)
    console.print(_build_display())

    assert MONITOR_FOOTER in output.getvalue()
