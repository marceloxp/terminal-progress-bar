"""Tests for CLI dispatch."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

import tpb.cli as cli_module
from tpb.store import create_bar, read_bar


runner = CliRunner()


def test_main_help_mentions_command_help():
    result = runner.invoke(cli_module.app, ["--help"])
    assert result.exit_code == 0
    assert "tpb create --help" in result.stdout


def test_create_command(isolated_config, monkeypatch):
    monkeypatch.setattr("tpb.config.CONFIG_DIR", isolated_config)
    monkeypatch.setattr("tpb.store.CONFIG_DIR", isolated_config)

    result = runner.invoke(cli_module.app, ["create", "backup-db", "0", "100", "Backup"])
    assert result.exit_code == 0
    assert read_bar("backup-db").label == "Backup"


def test_status_command(isolated_config, monkeypatch):
    monkeypatch.setattr("tpb.config.CONFIG_DIR", isolated_config)
    monkeypatch.setattr("tpb.store.CONFIG_DIR", isolated_config)
    create_bar("job-a", 10, 100, "Job A")

    result = runner.invoke(cli_module.app, ["status", "job-a"])
    assert result.exit_code == 0
    assert "slug: job-a" in result.stdout
    assert "current: 10" in result.stdout


def test_message_command(isolated_config, monkeypatch):
    monkeypatch.setattr("tpb.config.CONFIG_DIR", isolated_config)
    monkeypatch.setattr("tpb.store.CONFIG_DIR", isolated_config)
    create_bar("import-data", 0, 100, "Import data")

    result = runner.invoke(
        cli_module.app,
        ["message", "import-data", "Importando a Tabela de usuários"],
    )
    assert result.exit_code == 0
    assert read_bar("import-data").status_text == "Importando a Tabela de usuários"


def test_list_command(isolated_config, monkeypatch):
    monkeypatch.setattr("tpb.config.CONFIG_DIR", isolated_config)
    monkeypatch.setattr("tpb.store.CONFIG_DIR", isolated_config)
    create_bar("import-data", 25, 100, "Import data")
    create_bar("backup-db", 0, 50, "Database backup")

    result = runner.invoke(cli_module.app, ["list"])
    assert result.exit_code == 0
    assert "import-data\t25\t100\tactive\tImport data" in result.stdout
    assert "backup-db\t0\t50\tactive\tDatabase backup" in result.stdout


def test_list_command_empty(isolated_config, monkeypatch):
    monkeypatch.setattr("tpb.config.CONFIG_DIR", isolated_config)
    monkeypatch.setattr("tpb.store.CONFIG_DIR", isolated_config)

    result = runner.invoke(cli_module.app, ["list"])
    assert result.exit_code == 0
    assert result.stdout == ""


def test_status_requires_slug(isolated_config, monkeypatch):
    monkeypatch.setattr("tpb.config.CONFIG_DIR", isolated_config)
    monkeypatch.setattr("tpb.store.CONFIG_DIR", isolated_config)

    result = runner.invoke(cli_module.app, ["status"])
    assert result.exit_code != 0


def test_unknown_args_shows_hint(isolated_config, monkeypatch):
    monkeypatch.setattr("tpb.config.CONFIG_DIR", isolated_config)
    monkeypatch.setattr("tpb.store.CONFIG_DIR", isolated_config)
    create_bar("import", 0, 100)

    monkeypatch.setattr(
        "sys.argv",
        ["tpb", "import", "message", "Importando tabela"],
    )
    with pytest.raises(SystemExit) as exc:
        cli_module.main()
    assert exc.value.code == 1


def test_unknown_args_hint_message(isolated_config, monkeypatch):
    monkeypatch.setattr("tpb.config.CONFIG_DIR", isolated_config)
    monkeypatch.setattr("tpb.store.CONFIG_DIR", isolated_config)

    assert "tpb message import" in cli_module._unknown_args_error(
        ["import", "message", "Importando tabela"]
    )


def test_slug_update_via_main(isolated_config, monkeypatch):
    monkeypatch.setattr("tpb.config.CONFIG_DIR", isolated_config)
    monkeypatch.setattr("tpb.store.CONFIG_DIR", isolated_config)
    create_bar("job-a", 0, 100)

    monkeypatch.setattr("sys.argv", ["tpb", "job-a", "42"])
    cli_module.main()
    assert read_bar("job-a").current == 42

    monkeypatch.setattr("sys.argv", ["tpb", "job-a", "+5"])
    cli_module.main()
    assert read_bar("job-a").current == 47
