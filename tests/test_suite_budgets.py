from __future__ import annotations

from benchmarks.presentation.common import StrategyBudgetRequest, resolve_family_tier_budget
from benchmarks.presentation.suite import build_summary


def test_tier_defaults_apply_without_an_explicit_ceiling() -> None:
    full = resolve_family_tier_budget(
        family="interval_job_shop",
        tier="full",
        request=StrategyBudgetRequest(),
    )
    pressure = resolve_family_tier_budget(
        family="interval_job_shop",
        tier="pressure",
        request=StrategyBudgetRequest(),
    )

    assert (full.max_iterations, full.time_limit_s, full.population_size) == (50, 10.0, 32)
    assert (pressure.max_iterations, pressure.time_limit_s, pressure.population_size) == (100, 30.0, 64)


def test_explicit_budget_values_remain_tier_ceilings() -> None:
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

    assert (budget.max_iterations, budget.time_limit_s, budget.population_size, budget.trace_limit) == (
        12,
        4.0,
        9,
        3,
    )


def test_exact_full_uses_its_family_time_limit() -> None:
    budget = resolve_family_tier_budget(
        family="exact_linear_mip",
        tier="full",
        request=StrategyBudgetRequest(),
    )

    assert budget.exact_time_limit_s == 30.0


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
