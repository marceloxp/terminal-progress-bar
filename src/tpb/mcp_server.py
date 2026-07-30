"""MCP server exposing terminal-progress-bar operations to AI clients."""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from tpb.store import (
    BarExistsError,
    BarNotFoundError,
    ProgressBar,
    StoreError,
    create_bar,
    increment,
    list_bars,
    mark_done,
    mark_error,
    read_bar,
    remove_bar,
    set_current,
    set_message,
)

mcp = MCPServer("terminal-progress-bar")


def _bar_dict(bar: ProgressBar) -> dict[str, Any]:
    return bar.to_dict()


def _run_store(operation):
    try:
        return operation()
    except (BarNotFoundError, BarExistsError, StoreError, ValueError) as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool()
def tpb_create(
    slug: str,
    current: int,
    max_value: int,
    label: str | None = None,
) -> dict[str, Any]:
    """Create a new progress bar."""
    bar = _run_store(lambda: create_bar(slug, current, max_value, label))
    return _bar_dict(bar)


@mcp.tool()
def tpb_update(slug: str, value: int) -> dict[str, Any]:
    """Set the absolute progress value for a bar."""
    bar = _run_store(lambda: set_current(slug, value))
    return _bar_dict(bar)


@mcp.tool()
def tpb_increment(slug: str, delta: int) -> dict[str, Any]:
    """Increment or decrement progress by delta (use negative values to decrement)."""
    bar = _run_store(lambda: increment(slug, delta))
    return _bar_dict(bar)


@mcp.tool()
def tpb_message(slug: str, text: str) -> dict[str, Any]:
    """Set or update the status message shown below a progress bar."""
    bar = _run_store(lambda: set_message(slug, text))
    return _bar_dict(bar)


@mcp.tool()
def tpb_done(slug: str, status_text: str | None = None) -> dict[str, Any]:
    """Mark a progress bar as completed."""
    bar = _run_store(lambda: mark_done(slug, status_text))
    return _bar_dict(bar)


@mcp.tool()
def tpb_error(slug: str, status_text: str | None = None) -> dict[str, Any]:
    """Mark a progress bar as failed."""
    bar = _run_store(lambda: mark_error(slug, status_text))
    return _bar_dict(bar)


@mcp.tool()
def tpb_remove(slug: str) -> dict[str, str]:
    """Remove a progress bar."""
    _run_store(lambda: remove_bar(slug))
    return {"removed": slug}


@mcp.tool()
def tpb_list() -> list[dict[str, Any]]:
    """List all progress bars in creation order."""
    return [_bar_dict(bar) for bar in list_bars()]


@mcp.tool()
def tpb_get(slug: str) -> dict[str, Any]:
    """Get structured status for a single progress bar."""
    bar = _run_store(lambda: read_bar(slug))
    return _bar_dict(bar)


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
