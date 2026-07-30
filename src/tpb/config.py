"""Configuration constants and slug validation."""

from __future__ import annotations

import re
from pathlib import Path

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
CONFIG_DIR = Path.home() / ".config" / "terminal-progress-bar"
BAR_WIDTH = 50
LOCK_TIMEOUT = 5.0

STATUS_ACTIVE = "active"
STATUS_DONE = "done"
STATUS_ERROR = "error"

VALID_STATUSES = {STATUS_ACTIVE, STATUS_DONE, STATUS_ERROR}


def validate_slug(slug: str) -> str:
    if not SLUG_PATTERN.match(slug):
        raise ValueError(
            f"Invalid slug '{slug}': must match [a-z0-9][a-z0-9_-]*"
        )
    return slug


def bar_path(slug: str) -> Path:
    validate_slug(slug)
    return CONFIG_DIR / f"{slug}.json"
