"""CLI entry point for terminal-progress-bar."""

from __future__ import annotations

import re
import sys

import typer
from rich.console import Console

from tpb.monitor import run_monitor
from tpb.render import render_bars
from tpb.store import (
    BarExistsError,
    BarNotFoundError,
    StoreError,
    create_bar,
    format_list,
    format_status,
    increment,
    list_bars,
    mark_done,
    mark_error,
    read_bar,
    remove_bar,
    set_current,
    set_message,
)

app = typer.Typer(
    name="tpb",
    help="Shared terminal progress bars for parallel scripts and processes.",
    no_args_is_help=False,
    invoke_without_command=True,
    add_completion=False,
)
console = Console(stderr=True)

DELTA_PATTERN = re.compile(r"^([+-])(\d+)$")
KNOWN_COMMANDS = frozenset(
    {
        "create",
        "done",
        "error",
        "message",
        "list",
        "rm",
        "status",
        "monitor",
        "--help",
        "-h",
        "--version",
    }
)


def _exit_error(message: str) -> None:
    console.print(f"[red]Error:[/red] {message}")
    sys.exit(1)


def _unknown_args_error(args: list[str]) -> str:
    joined = " ".join(args)
    if len(args) >= 3 and args[1] in KNOWN_COMMANDS:
        command = args[1]
        slug = args[0]
        rest = " ".join(f'"{part}"' if " " in part else part for part in args[2:])
        return (
            f"Unknown command or invalid arguments: {joined}\n"
            f"Did you mean: tpb {command} {slug} {rest}?"
        )
    if len(args) == 2 and args[1] in KNOWN_COMMANDS:
        return (
            f"Unknown command or invalid arguments: {joined}\n"
            f"Did you mean: tpb {args[1]} {args[0]}?"
        )
    return f"Unknown command or invalid arguments: {joined}"


@app.command("create")
def create(
    slug: str = typer.Argument(..., help="Unique identifier for the progress bar."),
    current: int = typer.Argument(..., help="Initial progress value."),
    max_value: int = typer.Argument(..., help="Maximum progress value."),
    label: str | None = typer.Argument(None, help="Human-readable label."),
) -> None:
    """Create a new progress bar."""
    try:
        create_bar(slug, current, max_value, label)
    except BarExistsError as exc:
        _exit_error(str(exc))
    except (StoreError, ValueError) as exc:
        _exit_error(str(exc))


@app.command("done")
def done(
    slug: str = typer.Argument(..., help="Progress bar slug."),
    status_text: str | None = typer.Argument(None, help="Optional status message."),
) -> None:
    """Mark a progress bar as completed."""
    try:
        mark_done(slug, status_text)
    except BarNotFoundError as exc:
        _exit_error(str(exc))


@app.command("error")
def error_cmd(
    slug: str = typer.Argument(..., help="Progress bar slug."),
    status_text: str | None = typer.Argument(None, help="Optional error message."),
) -> None:
    """Mark a progress bar as failed."""
    try:
        mark_error(slug, status_text)
    except BarNotFoundError as exc:
        _exit_error(str(exc))


@app.command("message")
def message_cmd(
    slug: str = typer.Argument(..., help="Progress bar slug."),
    text: str = typer.Argument(..., help="Status message shown below the bar."),
) -> None:
    """Set or update the status message for a progress bar."""
    try:
        set_message(slug, text)
    except BarNotFoundError as exc:
        _exit_error(str(exc))


@app.command("rm")
def rm(slug: str = typer.Argument(..., help="Progress bar slug to remove.")) -> None:
    """Remove a progress bar."""
    try:
        remove_bar(slug)
    except BarNotFoundError as exc:
        _exit_error(str(exc))


@app.command("list")
def list_cmd() -> None:
    """List all progress bars as plain text (slug, current, max, status, label)."""
    sys.stdout.write(format_list(list_bars()))


@app.command("status")
def status(slug: str = typer.Argument(..., help="Progress bar slug.")) -> None:
    """Print machine-readable status for a progress bar."""
    try:
        bar = read_bar(slug)
        sys.stdout.write(format_status(bar) + "\n")
    except BarNotFoundError as exc:
        _exit_error(str(exc))


@app.command("monitor")
def monitor() -> None:
    """Watch progress bars in real time."""
    run_monitor()


def _handle_slug_update(slug: str, value: str) -> None:
    delta_match = DELTA_PATTERN.match(value)
    try:
        if delta_match:
            sign, amount = delta_match.groups()
            delta = int(amount) if sign == "+" else -int(amount)
            increment(slug, delta)
        else:
            set_current(slug, int(value))
    except BarNotFoundError as exc:
        _exit_error(str(exc))
    except ValueError:
        _exit_error(f"Invalid value '{value}': expected integer or +/-N")


def main() -> None:
    """Dispatch CLI commands and slug-based updates."""
    args = sys.argv[1:]

    if not args:
        render_bars(list_bars(), Console())
        return

    if args[0] in KNOWN_COMMANDS or args[0].startswith("-"):
        app()
        return

    if len(args) == 2:
        _handle_slug_update(args[0], args[1])
        return

    _exit_error(_unknown_args_error(args))


if __name__ == "__main__":
    main()
