"""Tests for progress bar storage."""

from __future__ import annotations

import json

import pytest

from tpb.config import CONFIG_DIR
from tpb.store import (
    BarExistsError,
    BarNotFoundError,
    create_bar,
    format_status,
    increment,
    list_bars,
    mark_done,
    mark_error,
    read_bar,
    remove_bar,
    set_current,
    set_message,
    format_list,
)


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    config_dir = tmp_path / "terminal-progress-bar"
    monkeypatch.setattr("tpb.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("tpb.store.CONFIG_DIR", config_dir)
    yield config_dir


def test_create_and_read_bar(isolated_config):
    create_bar("backup-db", 0, 100, "Database backup")
    bar = read_bar("backup-db")

    assert bar.slug == "backup-db"
    assert bar.label == "Database backup"
    assert bar.current == 0
    assert bar.max == 100
    assert bar.status == "active"
    assert (isolated_config / "backup-db.json").exists()


def test_create_duplicate_raises(isolated_config):
    create_bar("job-a", 0, 100)
    with pytest.raises(BarExistsError):
        create_bar("job-a", 0, 100)


def test_update_and_increment(isolated_config):
    create_bar("job-a", 0, 100)
    set_current("job-a", 25)
    increment("job-a", 5)
    increment("job-a", -2)

    bar = read_bar("job-a")
    assert bar.current == 28


def test_current_is_clamped(isolated_config):
    create_bar("job-a", 0, 100)
    set_current("job-a", 150)
    assert read_bar("job-a").current == 100

    increment("job-a", 50)
    assert read_bar("job-a").current == 100

    set_current("job-a", -10)
    assert read_bar("job-a").current == 0


def test_mark_done_and_error(isolated_config):
    create_bar("job-a", 40, 100)
    mark_done("job-a", "finished ok")
    bar = read_bar("job-a")
    assert bar.status == "done"
    assert bar.current == 100
    assert bar.status_text == "finished ok"

    create_bar("job-b", 10, 100)
    mark_error("job-b", "connection failed")
    bar = read_bar("job-b")
    assert bar.status == "error"
    assert bar.status_text == "connection failed"


def test_status_text_persists_on_done_without_new_text(isolated_config):
    create_bar("job-a", 10, 100)
    mark_done("job-a", "all good")
    mark_done("job-a")
    assert read_bar("job-a").status_text == "all good"


def test_list_bars_ordered_by_created_at(isolated_config):
    create_bar("second", 0, 100)
    create_bar("first", 0, 100)

    # Force created_at ordering regardless of filesystem sort
    second_path = isolated_config / "second.json"
    first_path = isolated_config / "first.json"
    second_data = json.loads(second_path.read_text())
    first_data = json.loads(first_path.read_text())
    second_data["created_at"] = "2026-01-02T00:00:00Z"
    first_data["created_at"] = "2026-01-01T00:00:00Z"
    second_path.write_text(json.dumps(second_data))
    first_path.write_text(json.dumps(first_data))

    slugs = [bar.slug for bar in list_bars()]
    assert slugs == ["first", "second"]


def test_set_message(isolated_config):
    create_bar("job-a", 10, 100)
    set_message("job-a", "Importing users table")
    assert read_bar("job-a").status_text == "Importing users table"


def test_remove_bar(isolated_config):
    create_bar("job-a", 0, 100)
    remove_bar("job-a")
    with pytest.raises(BarNotFoundError):
        read_bar("job-a")


def test_format_list(isolated_config):
    create_bar("import-data", 25, 100, "Import data")
    create_bar("backup-db", 100, 100, "Database backup")
    mark_done("backup-db")

    output = format_list(list_bars())
    assert "import-data\t25\t100\tactive\tImport data" in output
    assert "backup-db\t100\t100\tdone\tDatabase backup" in output


def test_format_list_empty(isolated_config):
    assert format_list([]) == ""


def test_format_status(isolated_config):
    create_bar("job-a", 5, 100, "My job")
    output = format_status(read_bar("job-a"))
    assert "slug: job-a" in output
    assert "label: My job" in output
    assert "current: 5" in output
    assert "status: active" in output
