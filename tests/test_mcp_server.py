"""Tests for MCP server tool handlers."""

from __future__ import annotations

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from tpb.mcp_server import (
    tpb_create,
    tpb_done,
    tpb_get,
    tpb_increment,
    tpb_list,
    tpb_message,
    tpb_remove,
    tpb_update,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    config_dir = tmp_path / "terminal-progress-bar"
    monkeypatch.setattr("tpb.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("tpb.store.CONFIG_DIR", config_dir)


def test_tpb_create_and_get():
    created = tpb_create("import-data", 0, 100, "Import data")
    assert created["slug"] == "import-data"
    assert created["current"] == 0
    assert created["max"] == 100

    fetched = tpb_get("import-data")
    assert fetched["label"] == "Import data"
    assert fetched["status"] == "active"


def test_tpb_update_and_increment():
    tpb_create("job-a", 0, 100)
    updated = tpb_update("job-a", 25)
    assert updated["current"] == 25

    incremented = tpb_increment("job-a", 5)
    assert incremented["current"] == 30

    decremented = tpb_increment("job-a", -3)
    assert decremented["current"] == 27


def test_tpb_message_done_and_list():
    tpb_create("job-a", 10, 100, "Job A")
    messaged = tpb_message("job-a", "Importing users table")
    assert messaged["status_text"] == "Importing users table"

    done = tpb_done("job-a", "completed")
    assert done["status"] == "done"
    assert done["current"] == 100

    bars = tpb_list()
    assert len(bars) == 1
    assert bars[0]["slug"] == "job-a"


def test_tpb_remove():
    tpb_create("job-a", 0, 100)
    removed = tpb_remove("job-a")
    assert removed == {"removed": "job-a"}
    assert tpb_list() == []


def test_tpb_get_missing_slug_raises_tool_error():
    with pytest.raises(ToolError, match="not found"):
        tpb_get("missing")


def test_tpb_create_duplicate_raises_tool_error():
    tpb_create("job-a", 0, 100)
    with pytest.raises(ToolError, match="already exists"):
        tpb_create("job-a", 0, 100)


def test_tpb_create_invalid_slug_raises_tool_error():
    with pytest.raises(ToolError, match="Invalid slug"):
        tpb_create("Invalid Slug", 0, 100)
