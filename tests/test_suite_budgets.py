from __future__ import annotations

import pytest

from benchmarks.presentation.common import StrategyBudgetRequest, resolve_family_tier_budget
from benchmarks.presentation.suite import build_review_metadata, build_summary


def test_tier_defaults_use_time_limits_without_iteration_caps() -> None:
    expected = {
        "smoke": (2.0, 8),
        "calibration": (5.0, 16),
        "full": (10.0, 32),
        "pressure": (30.0, 64),
    }

    for tier, (time_limit_s, population_size) in expected.items():
        budget = resolve_family_tier_budget(
            family="interval_job_shop",
            tier=tier,
            request=StrategyBudgetRequest(),
        )

        assert budget.max_iterations is None
        assert (budget.time_limit_s, budget.population_size) == (time_limit_s, population_size)
        assert budget.profile == f"interval_job_shop_{tier}_budget_v2"


def test_time_limit_disables_explicit_iteration_ceiling() -> None:
    budget = resolve_family_tier_budget(
        family="interval_job_shop",
        tier="pressure",
        request=StrategyBudgetRequest(
            max_iterations=12,
            time_limit_s=4.0,
            population_size=9,
            trace_limit=3,
        ),
    )

    assert budget.max_iterations is None
    assert (budget.time_limit_s, budget.population_size, budget.trace_limit) == (4.0, 9, 3)


def test_budget_rejects_nonpositive_time_even_with_iteration_limit() -> None:
    with pytest.raises(ValueError, match="time_limit_s must be > 0"):
        resolve_family_tier_budget(
            family="interval_job_shop",
            tier="pressure",
            request=StrategyBudgetRequest(max_iterations=12, time_limit_s=0.0),
        )


def test_exact_full_uses_its_family_time_limit() -> None:
    budget = resolve_family_tier_budget(
        family="exact_linear_mip",
        tier="full",
        request=StrategyBudgetRequest(),
    )

    assert budget.exact_time_limit_s == 30.0
    assert budget.max_iterations is None


def test_summary_distinguishes_requested_and_executed_families(tmp_path) -> None:
    summary = build_summary(
        run_dir=tmp_path,
        config={
            "families": ["interval_job_shop", "exact_linear_mip"],
            "tiers": ["pressure"],
            "strategies": ["ga"],
            "budget": {},
        },
        selected_case_count=1,
        skipped_cases=[],
        rows=[
            {
                "benchmark_id": "jsplib_test",
                "family": "interval_job_shop",
                "status": "feasible",
                "feasible": True,
                "objective": 10.0,
                "elapsed_seconds": 0.1,
                "strategy": "ga",
            }
        ],
    )

    assert summary["requested_families"] == ["interval_job_shop", "exact_linear_mip"]
    assert summary["executed_families"] == ["interval_job_shop"]
    assert summary["requested_families_without_rows"] == ["exact_linear_mip"]


def test_review_metadata_is_a_complete_single_family_contract() -> None:
    metadata = build_review_metadata(families=("sequence_blackbox_tsp",), expected_seed_count=1)

    assert metadata == {
        "preset_id": "standard_benchmark_suite",
        "preset_version": "1",
        "review_mode": "single_family_focus",
        "target_families": ["sequence_blackbox_tsp"],
        "formal_checkpoints_s": [5.0, 10.0, 20.0],
        "observation_times_s": [float(value) for value in range(1, 21)],
        "expected_seed_count": 1,
    }


def test_review_metadata_is_shared_by_multi_family_calibration() -> None:
    metadata = build_review_metadata(
        families=("sequence_blackbox_tsp", "interval_job_shop"),
        expected_seed_count=3,
    )

    assert metadata["review_mode"] == "multi_family_suite"
    assert metadata["target_families"] == ["interval_job_shop", "sequence_blackbox_tsp"]
    assert metadata["expected_seed_count"] == 3
