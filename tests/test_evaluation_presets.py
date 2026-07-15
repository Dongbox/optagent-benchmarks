from __future__ import annotations

import pytest

from benchmarks.evaluation_presets import (
    FAST_DEVELOPMENT,
    FULL_FINAL,
    FORMAL_CHECKPOINTS_S,
    OBSERVATION_TIMES_S,
    select_preset_cases,
)
from benchmarks.run import all_cases


def test_fast_and_full_presets_share_the_same_single_run_protocol() -> None:
    assert FAST_DEVELOPMENT.time_limit_s == FULL_FINAL.time_limit_s == 20.0
    assert FAST_DEVELOPMENT.max_iterations is FULL_FINAL.max_iterations is None
    assert FAST_DEVELOPMENT.observation_times_s == FULL_FINAL.observation_times_s == OBSERVATION_TIMES_S
    assert FAST_DEVELOPMENT.formal_checkpoints_s == FULL_FINAL.formal_checkpoints_s == FORMAL_CHECKPOINTS_S
    assert len(FAST_DEVELOPMENT.seeds) == 3
    assert len(FULL_FINAL.seeds) == 10


def test_fast_single_family_focus_selects_four_targets_and_observation_sentinels() -> None:
    selected = select_preset_cases(
        all_cases(),
        preset=FAST_DEVELOPMENT,
        target_family="interval_job_shop",
    )
    by_id = {row["benchmark_id"]: row for row in all_cases()}

    assert len(selected) == 6
    assert sum(by_id[case_id]["family"] == "interval_job_shop" for case_id in selected) == 4
    assert {by_id[case_id]["family"] for case_id in selected} == {
        "interval_job_shop",
        "sequence_blackbox_tsp",
        "sequence_quadratic_assignment",
    }


def test_full_preset_uses_fixed_32_case_inventory() -> None:
    selected = select_preset_cases(
        all_cases(),
        preset=FULL_FINAL,
        target_family="interval_job_shop",
    )
    assert len(selected) == 32


def test_full_preset_rejects_unknown_target_family() -> None:
    with pytest.raises(ValueError, match="unknown target family"):
        select_preset_cases(
            all_cases(),
            preset=FULL_FINAL,
            target_family="unknown-family",
        )
