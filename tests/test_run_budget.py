from __future__ import annotations

import pytest

from benchmarks.run import main as run_main


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
