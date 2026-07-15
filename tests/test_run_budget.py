from __future__ import annotations

import pytest

import benchmarks.run as run_module
from benchmarks.run import LocalRunBudget, main as run_main


def test_local_run_budget_does_not_capture_reproduction_by_default() -> None:
    assert LocalRunBudget().reproduction_path is None


def test_run_cli_rejects_nonpositive_time_limit() -> None:
    with pytest.raises(SystemExit) as exc_info:
        run_main(
            [
                "--case",
                "custom_steel_sequence_toy",
                "--strategy",
                "ga",
                "--time-limit-s",
                "0",
                "--no-download",
            ]
        )

    assert exc_info.value.code == 2


def test_run_cli_forwards_reproduction_path(tmp_path, monkeypatch, capsys) -> None:
    captured = {}

    def fake_run_case(_case, **kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(run_module, "run_case", fake_run_case)
    path = tmp_path / "case.optrepro"

    assert run_main(["--case", "custom_steel_sequence_toy", "--reproduction-path", str(path)]) == 0
    capsys.readouterr()

    assert captured["budget"].reproduction_path == str(path.resolve())
