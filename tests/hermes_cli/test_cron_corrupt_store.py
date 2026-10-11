"""Regression: `hermes cron <verb>` must fail with a clean error, not a
traceback, when jobs.json can't be parsed at all (restored backup,
interrupted hand-edit). load_jobs() raises the designed RuntimeError
"Cron database corrupted and unrepairable" (#6797 chose refusing to load
over silently treating the store as empty); nothing in the CLI caught it,
so every cron verb dumped a traceback wall instead."""

import types

import pytest

import hermes_cli.cron as cron_mod


@pytest.mark.parametrize("verb", ["list", "status", "doctor"])
def test_cron_commands_report_corrupt_store_cleanly(tmp_path, monkeypatch, capsys, verb):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    (tmp_path / "cron").mkdir(parents=True, exist_ok=True)
    (tmp_path / "cron" / "jobs.json").write_bytes(b'{"jobs": ')  # truncated write / typo

    rc = cron_mod.cron_command(types.SimpleNamespace(cron_command=verb))

    out = capsys.readouterr().out
    assert "Traceback" not in out
    assert rc == 1
    assert "corrupted and unrepairable" in out


def test_bare_list_store_still_autorepaired_not_crash(tmp_path, monkeypatch, capsys):
    """A top-level array is a repairable shape (wrapped): no crash, and
    the non-object record is skipped."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    (tmp_path / "cron").mkdir(parents=True, exist_ok=True)
    (tmp_path / "cron" / "jobs.json").write_bytes(b'[{"id": 1}]')

    rc = cron_mod.cron_command(types.SimpleNamespace(cron_command="list"))

    out = capsys.readouterr().out
    assert "Traceback" not in out
    assert rc == 0
