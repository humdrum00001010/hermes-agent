"""Regression: `hermes auth add <provider>` with exhausted stdin (closed
pipe, heredoc with too few lines, Ctrl-D at the prompt) must hit the
designed "No API key provided." abort, not an EOFError traceback.

The refactor that added the `_ask` helper (8d4e21c1f0, "replaces 7
EOF/Ctrl-C ladders") missed `_add_api_key_credential`'s two prompt sites,
so `masked_secret_prompt` re-raised `EOFError` (by design) into code that
never caught it."""

import argparse
import io
import sys

import pytest


def _parse_auth_args(argv: list[str]) -> argparse.Namespace:
    """Parse `hermes auth <argv>` through the real subcommand parser."""
    from hermes_cli.subcommands.auth import build_auth_parser

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    build_auth_parser(subparsers, cmd_auth=lambda args: None)
    return parser.parse_args(["auth", *argv])


def test_auth_add_closed_stdin_aborts_cleanly(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    from hermes_cli.auth_commands import auth_command

    monkeypatch.setattr(sys, "stdin", io.StringIO(""))

    # The designed path: no answer -> "No API key provided." via SystemExit.
    with pytest.raises(SystemExit) as exc:
        auth_command(_parse_auth_args(["add", "openrouter"]))

    assert "No API key provided" in str(exc.value)
    assert "Traceback" not in capsys.readouterr().out


def test_auth_add_with_key_needs_no_prompt(tmp_path, monkeypatch, capsys):
    """--api-key short-circuits the prompts; must succeed with closed stdin."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    from hermes_cli.auth_commands import auth_command

    monkeypatch.setattr(sys, "stdin", io.StringIO(""))

    # Should store the credential without any prompt reads (label falls to
    # the default because stdin is not a tty) — and must not raise.
    auth_command(_parse_auth_args(["add", "openrouter", "--api-key", "sk-test",
                                   "--label", "probe"]))
    out = capsys.readouterr().out
    assert "Added openrouter" in out
    assert "Traceback" not in out
