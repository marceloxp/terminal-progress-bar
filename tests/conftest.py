"""Shared pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def isolated_config(tmp_path):
    return tmp_path / "terminal-progress-bar"
