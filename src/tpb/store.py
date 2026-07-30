"""JSON file storage with per-slug files and file locking."""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from tpb.config import (
    CONFIG_DIR,
    STATUS_ACTIVE,
    STATUS_DONE,
    STATUS_ERROR,
    bar_path,
    validate_slug,
)


class StoreError(Exception):
    """Base error for storage operations."""


class BarNotFoundError(StoreError):
    """Raised when a progress bar slug does not exist."""


class BarExistsError(StoreError):
    """Raised when creating a bar that already exists."""


@dataclass
class ProgressBar:
    slug: str
    label: str
    current: int
    max: int
    status: str = STATUS_ACTIVE
    status_text: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        validate_slug(self.slug)
        if self.max <= 0:
            raise ValueError("max must be greater than 0")
        self.current = _clamp(self.current, 0, self.max)
        if not self.created_at:
            now = _utc_now()
            self.created_at = now
            self.updated_at = now
        if not self.updated_at:
            self.updated_at = self.created_at

    @classmethod
    def from_dict(cls, data: dict) -> ProgressBar:
        return cls(
            slug=data["slug"],
            label=data.get("label", data["slug"]),
            current=data["current"],
            max=data["max"],
            status=data.get("status", STATUS_ACTIVE),
            status_text=data.get("status_text", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def to_dict(self) -> dict:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def ensure_config_dir() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


@contextmanager
def _file_lock(path: Path) -> Iterator[None]:
    ensure_config_dir()
    lock_path = path.with_suffix(path.suffix + ".lock")
    with open(lock_path, "w") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _atomic_write(path: Path, data: dict) -> None:
    ensure_config_dir()
    fd, tmp_path = tempfile.mkstemp(
        dir=CONFIG_DIR, prefix=f".{path.stem}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w") as tmp_file:
            json.dump(data, tmp_file, indent=2)
            tmp_file.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        os.unlink(tmp_path)
        raise


def _read_bar_unlocked(path: Path) -> ProgressBar:
    with open(path) as f:
        return ProgressBar.from_dict(json.load(f))


def read_bar(slug: str) -> ProgressBar:
    path = bar_path(slug)
    if not path.exists():
        raise BarNotFoundError(f"Progress bar '{slug}' not found")
    with _file_lock(path):
        return _read_bar_unlocked(path)


def list_bars() -> list[ProgressBar]:
    ensure_config_dir()
    bars: list[ProgressBar] = []
    for path in sorted(CONFIG_DIR.glob("*.json")):
        if path.name.endswith(".lock"):
            continue
        try:
            bars.append(_read_bar_unlocked(path))
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
    bars.sort(key=lambda b: b.created_at)
    return bars


def create_bar(
    slug: str,
    current: int,
    max_value: int,
    label: str | None = None,
) -> ProgressBar:
    path = bar_path(slug)
    if path.exists():
        raise BarExistsError(f"Progress bar '{slug}' already exists")

    bar = ProgressBar(
        slug=slug,
        label=label or slug.replace("-", " ").replace("_", " ").title(),
        current=current,
        max=max_value,
    )
    with _file_lock(path):
        _atomic_write(path, bar.to_dict())
    return bar


def _update_bar(slug: str, updater) -> ProgressBar:
    path = bar_path(slug)
    if not path.exists():
        raise BarNotFoundError(f"Progress bar '{slug}' not found")

    with _file_lock(path):
        bar = _read_bar_unlocked(path)
        updater(bar)
        bar.updated_at = _utc_now()
        _atomic_write(path, bar.to_dict())
        return bar


def set_current(slug: str, value: int) -> ProgressBar:
    def updater(bar: ProgressBar) -> None:
        bar.current = _clamp(value, 0, bar.max)

    return _update_bar(slug, updater)


def increment(slug: str, delta: int) -> ProgressBar:
    def updater(bar: ProgressBar) -> None:
        bar.current = _clamp(bar.current + delta, 0, bar.max)

    return _update_bar(slug, updater)


def mark_done(slug: str, status_text: str | None = None) -> ProgressBar:
    def updater(bar: ProgressBar) -> None:
        bar.current = bar.max
        bar.status = STATUS_DONE
        if status_text is not None:
            bar.status_text = status_text

    return _update_bar(slug, updater)


def mark_error(slug: str, status_text: str | None = None) -> ProgressBar:
    def updater(bar: ProgressBar) -> None:
        bar.status = STATUS_ERROR
        if status_text is not None:
            bar.status_text = status_text

    return _update_bar(slug, updater)


def set_message(slug: str, message: str) -> ProgressBar:
    def updater(bar: ProgressBar) -> None:
        bar.status_text = message

    return _update_bar(slug, updater)


def remove_bar(slug: str) -> None:
    path = bar_path(slug)
    lock_path = path.with_suffix(path.suffix + ".lock")
    if not path.exists():
        raise BarNotFoundError(f"Progress bar '{slug}' not found")

    with _file_lock(path):
        path.unlink()
    if lock_path.exists():
        lock_path.unlink(missing_ok=True)


def format_status(bar: ProgressBar) -> str:
    lines = [
        f"slug: {bar.slug}",
        f"label: {bar.label}",
        f"current: {bar.current}",
        f"max: {bar.max}",
        f"status: {bar.status}",
        f"status_text: {bar.status_text}",
        f"created_at: {bar.created_at}",
        f"updated_at: {bar.updated_at}",
    ]
    return "\n".join(lines)


def format_list(bars: list[ProgressBar]) -> str:
    """Format all bars as plain text lines for scripting and quick inspection."""
    if not bars:
        return ""

    lines = []
    for bar in bars:
        line = (
            f"{bar.slug}\t{bar.current}\t{bar.max}\t{bar.status}\t{bar.label}"
        )
        if bar.status_text:
            line += f"\t{bar.status_text}"
        lines.append(line)
    return "\n".join(lines) + "\n"
