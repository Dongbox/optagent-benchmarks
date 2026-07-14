from __future__ import annotations

import pytest

from benchmarks import cli


def test_top_level_help_lists_the_public_commands(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["--help"]) == 0

    output = capsys.readouterr().out
    assert "python benchmark.py" in output
    assert "list-cases" in output
    assert "compare-ga" in output
    assert "authority" in output
    assert "compare-runs" not in output
    assert "publish-results" not in output
    assert "generate-results-index" not in output


def test_public_command_inventory_is_small_and_current() -> None:
    assert set(cli._commands()) == {
        "list-cases",
        "run",
        "evaluate",
        "suite",
        "authority",
        "compare-ga",
        "publish-telemetry",
        "publish-review",
        "dashboard",
    }


def test_subcommand_arguments_are_delegated(monkeypatch: pytest.MonkeyPatch) -> None:
    received: list[str] = []

    def fake_run(argv: list[str]) -> int:
        received.extend(argv)
        return 7

    monkeypatch.setattr(cli, "_commands", lambda: {"run": ("Run a case.", fake_run)})

    assert cli.main(["run", "--tier", "smoke"]) == 7
    assert received == ["--tier", "smoke"]
