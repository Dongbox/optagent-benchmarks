from __future__ import annotations

from dataclasses import asdict
import csv
import platform
import sys
from pathlib import Path
from typing import Any

from benchmarks.loaders.catalog import DEFAULT_CATALOG_PATH, catalog_cases, select_cases
from benchmarks.runners.common import (
    DEFAULT_RUN_ROOT,
    EffectiveStrategyBudget,
    StrategyBudgetRequest,
    append_jsonl,
    ensure_run_dir,
    metadata_highlights,
    normalize_result_row,
    resolve_family_tier_budget,
    write_json,
)
from benchmarks.runners.cumulative_resource_scheduling import RcpspStrategyBudget, run_rcpsp_case
from benchmarks.runners.exact_linear_mip import MipExactBudget, run_mip_case
from benchmarks.runners.interval_job_shop import JobShopStrategyBudget, run_job_shop_case
from benchmarks.runners.sequence_quadratic_assignment import QapStrategyBudget, run_qap_case
from benchmarks.runners.sequence_blackbox_tsp import TspStrategyBudget, run_tsp_case
from benchmarks.runners.telemetry import normalize_telemetry, write_anytime_jsonl, write_throughput_jsonl


IMPLEMENTED_FAMILIES = {
    "cumulative_resource_scheduling",
    "exact_linear_mip",
    "interval_job_shop",
    "sequence_blackbox_tsp",
    "sequence_quadratic_assignment",
}
DEFAULT_RUNNABLE_FAMILIES = ("interval_job_shop", "sequence_blackbox_tsp", "sequence_quadratic_assignment")
DEFAULT_STRATEGIES = ("ga", "alns", "tabu")
DEFAULT_CANDIDATE_STRATEGIES = ("local_search", "alns", "ga", "tabu")
DEFAULT_PARALLEL_THREAD_COUNTS = (1, 2, 4, 8, 16)
SCHEDULING_FAMILIES = {"interval_job_shop", "cumulative_resource_scheduling"}
SCHEDULING_DEFAULT_STRATEGIES = ("ga", "alns")
SCHEDULING_STRATEGY_REPLACEMENTS = {"tabu": "alns", "lns": "alns"}
SEQUENCE_DEFAULT_STRATEGIES = ("ga", "alns", "tabu")


def run_benchmark_suite(
    *,
    catalog_path: str | Path = DEFAULT_CATALOG_PATH,
    output_root: str | Path = DEFAULT_RUN_ROOT,
    families: tuple[str, ...] = DEFAULT_RUNNABLE_FAMILIES,
    tiers: tuple[str, ...] = ("smoke",),
    benchmark_ids: tuple[str, ...] = (),
    strategies: tuple[str, ...] = DEFAULT_STRATEGIES,
    seed: int = 11,
    max_iterations: int = 40,
    time_limit_s: float = 5.0,
    population_size: int = 10,
    trace_limit: int = 8,
    data_cache_dir: str | None = None,
    allow_download: bool = True,
    model_styles: tuple[str, ...] = (),
    default_candidate_matrix: bool = False,
    parallel_thread_counts: tuple[int, ...] = (),
    timestamp: str | None = None,
) -> dict[str, Any]:
    run_dir = ensure_run_dir(output_root, timestamp=timestamp)
    cases = select_cases(
        catalog_cases(catalog_path),
        families=families,
        tiers=tiers,
        benchmark_ids=benchmark_ids,
    )
    thread_counts = _normalize_thread_counts(parallel_thread_counts)
    budget_request = StrategyBudgetRequest(
        seed=seed,
        max_iterations=max_iterations,
        time_limit_s=time_limit_s,
        population_size=population_size,
        trace_limit=trace_limit,
        thread_count=1,
    )
    budget_matrix = _budget_matrix(families=families, tiers=tiers, request=budget_request)
    strategy_plan = {
        family: _effective_strategies_for_family(family, strategies)
        for family in families
    }
    strategy_substitutions = [
        {
            "family": family,
            "requested": list(strategies),
            "effective": list(effective),
            "reason": (
                "standalone tabu/lns do not currently produce feasible scheduling benchmark rows; "
                "alns is the repairable scheduling search route"
            ),
        }
        for family, effective in strategy_plan.items()
        if tuple(strategies) != tuple(effective)
    ]
    config = {
        "catalog_path": str(catalog_path),
        "families": list(families),
        "tiers": list(tiers),
        "benchmark_ids": list(benchmark_ids),
        "strategies": list(strategies),
        "family_strategy_plan": {family: list(values) for family, values in strategy_plan.items()},
        "strategy_substitutions": strategy_substitutions,
        "default_candidate_matrix": bool(default_candidate_matrix),
        "parallel_matrix_enabled": bool(thread_counts),
        "parallel_thread_counts": list(thread_counts or (1,)),
        "model_styles": list(model_styles),
        "budget": asdict(budget_request),
        "budget_policy": "family_tier_ceiling_v1",
        "family_budgets": budget_matrix,
        "allow_download": allow_download,
        "data_cache_dir": data_cache_dir,
        "implemented_families": sorted(IMPLEMENTED_FAMILIES),
        "python": sys.version,
        "platform": platform.platform(),
    }
    write_json(run_dir / "config.json", config)

    rows: list[dict[str, Any]] = []
    skipped_cases: list[dict[str, Any]] = []
    for case in cases:
        family = case["family"]
        if family not in IMPLEMENTED_FAMILIES:
            skipped_cases.append(
                {
                    "benchmark_id": case["benchmark_id"],
                    "family": family,
                    "reason": "family runner is not implemented yet",
                }
            )
            continue
        for thread_count in thread_counts or (1,):
            effective_budget = resolve_family_tier_budget(
                family=family,
                tier=str(case.get("tier") or "smoke"),
                request=StrategyBudgetRequest(
                    seed=seed,
                    max_iterations=max_iterations,
                    time_limit_s=time_limit_s,
                    population_size=population_size,
                    trace_limit=trace_limit,
                    thread_count=thread_count,
                ),
            )
            if family == "sequence_blackbox_tsp":
                case_rows = run_tsp_case(
                    case,
                    strategies=strategy_plan[family],
                    budget=_tsp_budget(effective_budget),
                    data_cache_dir=data_cache_dir,
                    allow_download=allow_download,
                    model_styles=model_styles,
                )
            elif family == "exact_linear_mip":
                case_rows = run_mip_case(
                    case,
                    strategies=strategy_plan[family],
                    budget=_mip_budget(effective_budget),
                    data_cache_dir=data_cache_dir,
                    allow_download=allow_download,
                )
            elif family == "cumulative_resource_scheduling":
                case_rows = run_rcpsp_case(
                    case,
                    strategies=strategy_plan[family],
                    budget=_rcpsp_budget(effective_budget),
                    data_cache_dir=data_cache_dir,
                    allow_download=allow_download,
                    include_exact_baseline=True,
                )
            elif family == "interval_job_shop":
                case_rows = run_job_shop_case(
                    case,
                    strategies=strategy_plan[family],
                    budget=_job_shop_budget(effective_budget),
                    data_cache_dir=data_cache_dir,
                    allow_download=allow_download,
                    include_exact_baseline=True,
                )
            elif family == "sequence_quadratic_assignment":
                case_rows = run_qap_case(
                    case,
                    strategies=strategy_plan[family],
                    budget=_qap_budget(effective_budget),
                    data_cache_dir=data_cache_dir,
                    allow_download=allow_download,
                )
            else:
                case_rows = []
            case_rows = [
                _normalize_case_row(
                    row,
                    effective_budget,
                    parallel_matrix_enabled=bool(thread_counts),
                )
                for row in case_rows
            ]
            append_jsonl(run_dir / "results.jsonl", case_rows)
            rows.extend(case_rows)

    summary = build_summary(
        run_dir=run_dir,
        config=config,
        selected_case_count=len(cases),
        skipped_cases=skipped_cases,
        rows=rows,
    )
    write_json(run_dir / "summary.json", summary)
    write_results_csv(run_dir / "results.csv", rows)
    write_anytime_jsonl(run_dir / "anytime.jsonl", rows)
    write_throughput_jsonl(run_dir / "throughput.jsonl", rows)
    (run_dir / "report.md").write_text(render_report(summary, rows), encoding="utf-8")
    return summary


def _budget_matrix(
    *,
    families: tuple[str, ...],
    tiers: tuple[str, ...],
    request: StrategyBudgetRequest,
) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        family: {
            tier: resolve_family_tier_budget(
                family=family,
                tier=tier,
                request=request,
            ).to_dict()
            for tier in tiers
        }
        for family in families
    }


def _normalize_thread_counts(thread_counts: tuple[int, ...]) -> tuple[int, ...]:
    if not thread_counts:
        return ()
    normalized = sorted({int(value) for value in thread_counts})
    if any(value < 1 for value in normalized):
        raise ValueError("parallel thread counts must be >= 1")
    return tuple(normalized)


def _effective_strategies_for_family(family: str, requested: tuple[str, ...]) -> tuple[str, ...]:
    if family == "exact_linear_mip":
        return requested
    defaults = SCHEDULING_DEFAULT_STRATEGIES if family in SCHEDULING_FAMILIES else SEQUENCE_DEFAULT_STRATEGIES
    source = requested or defaults
    effective: list[str] = []
    for strategy in source:
        replacement = (
            SCHEDULING_STRATEGY_REPLACEMENTS.get(strategy, strategy)
            if family in SCHEDULING_FAMILIES
            else strategy
        )
        if replacement not in effective:
            effective.append(replacement)
    return tuple(effective)


def _tsp_budget(budget: EffectiveStrategyBudget) -> TspStrategyBudget:
    return TspStrategyBudget(
        seed=budget.seed,
        max_iterations=budget.max_iterations,
        time_limit_s=budget.time_limit_s,
        population_size=budget.population_size,
        trace_limit=budget.trace_limit,
        thread_count=budget.thread_count,
    )


def _qap_budget(budget: EffectiveStrategyBudget) -> QapStrategyBudget:
    return QapStrategyBudget(
        seed=budget.seed,
        max_iterations=budget.max_iterations,
        time_limit_s=budget.time_limit_s,
        population_size=budget.population_size,
        trace_limit=budget.trace_limit,
        thread_count=budget.thread_count,
    )


def _job_shop_budget(budget: EffectiveStrategyBudget) -> JobShopStrategyBudget:
    return JobShopStrategyBudget(
        seed=budget.seed,
        max_iterations=budget.max_iterations,
        time_limit_s=budget.time_limit_s,
        population_size=budget.population_size,
        trace_limit=budget.trace_limit,
        thread_count=budget.thread_count,
        cpsat_time_limit_s=budget.exact_time_limit_s,
    )


def _rcpsp_budget(budget: EffectiveStrategyBudget) -> RcpspStrategyBudget:
    return RcpspStrategyBudget(
        seed=budget.seed,
        max_iterations=budget.max_iterations,
        time_limit_s=budget.time_limit_s,
        population_size=budget.population_size,
        trace_limit=budget.trace_limit,
        thread_count=budget.thread_count,
        cpsat_time_limit_s=budget.exact_time_limit_s,
    )


def _mip_budget(budget: EffectiveStrategyBudget) -> MipExactBudget:
    return MipExactBudget(
        seed=budget.seed,
        max_iterations=0,
        time_limit_s=budget.exact_time_limit_s or budget.time_limit_s,
        population_size=0,
        trace_limit=0,
        thread_count=budget.thread_count,
        backend="optx",
    )


def _normalize_case_row(
    row: dict[str, Any],
    budget: EffectiveStrategyBudget,
    *,
    parallel_matrix_enabled: bool = False,
) -> dict[str, Any]:
    row["budget_profile"] = budget.profile
    row["effective_max_iterations"] = budget.max_iterations
    row["effective_time_limit_s"] = budget.time_limit_s
    row["effective_population_size"] = budget.population_size
    row["effective_trace_limit"] = budget.trace_limit
    row["thread_count"] = budget.thread_count
    row["parallel_matrix_enabled"] = bool(parallel_matrix_enabled)
    if budget.exact_time_limit_s is not None:
        row["effective_exact_time_limit_s"] = budget.exact_time_limit_s
    row["effective_budget"] = budget.to_dict()
    metadata = row.get("metadata")
    if isinstance(metadata, dict):
        metadata.setdefault("budget_profile", budget.profile)
        metadata.setdefault("effective_budget", budget.to_dict())
        metadata.setdefault("thread_count", budget.thread_count)
        metadata.setdefault("parallel_matrix_enabled", bool(parallel_matrix_enabled))
    return normalize_telemetry(normalize_result_row(row))


def _profile_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        profile = str(row.get("strategy_profile") or "")
        if not profile:
            continue
        counts[profile] = counts.get(profile, 0) + 1
    return counts


def build_summary(
    *,
    run_dir: Path,
    config: dict[str, Any],
    selected_case_count: int,
    skipped_cases: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    successful_rows = [
        row
        for row in rows
        if row.get("status") != "error" and row.get("objective") is not None and row.get("feasible") is True
    ]
    error_rows = [row for row in rows if row.get("status") == "error"]
    non_feasible_rows = [row for row in rows if row.get("status") != "error" and row.get("feasible") is not True]
    best_by_case: dict[str, dict[str, Any]] = {}
    for row in successful_rows:
        key = str(row["benchmark_id"])
        current = best_by_case.get(key)
        if current is None or (float(row["objective"]), float(row["elapsed_seconds"])) < (
            float(current["objective"]),
            float(current["elapsed_seconds"]),
        ):
            best_by_case[key] = row

    return {
        "run_dir": str(run_dir),
        "selected_case_count": selected_case_count,
        "executed_case_count": len({row["benchmark_id"] for row in rows}),
        "skipped_case_count": len(skipped_cases),
        "strategy_run_count": len(rows),
        "strategy_row_count": sum(1 for row in rows if row.get("kind") == "strategy_run"),
        "exact_baseline_row_count": sum(1 for row in rows if row.get("kind") == "exact_baseline"),
        "successful_run_count": len(successful_rows),
        "error_run_count": len(error_rows),
        "non_feasible_run_count": len(non_feasible_rows),
        "families": list(config["families"]),
        "tiers": list(config["tiers"]),
        "strategies": list(config["strategies"]),
        "family_strategy_plan": config.get("family_strategy_plan", {}),
        "strategy_substitutions": config.get("strategy_substitutions", []),
        "parallel_matrix_enabled": bool(config.get("parallel_matrix_enabled", False)),
        "parallel_thread_counts": list(config.get("parallel_thread_counts", [1])),
        "parallel_matrix": (
            build_parallel_matrix(rows)
            if config.get("parallel_matrix_enabled", False)
            else {"enabled": False, "reason": "not requested", "groups": []}
        ),
        "default_candidate_matrix_enabled": bool(config.get("default_candidate_matrix", False)),
        "default_candidate_matrix": (
            build_default_candidate_matrix(rows)
            if config.get("default_candidate_matrix", False)
            else {"enabled": False, "reason": "not requested", "ranked_strategies": []}
        ),
        "budget": dict(config["budget"]),
        "budget_policy": config.get("budget_policy"),
        "family_budgets": config.get("family_budgets", {}),
        "profile_counts": _profile_counts(rows),
        "family_improvement_summary": _family_improvement_summary(rows),
        "skipped_cases": skipped_cases,
        "best_by_case": {
            key: {
                "strategy": row["strategy"],
                "strategy_profile": row.get("strategy_profile"),
                "model_style": row.get("model_style"),
                "kind": row.get("kind"),
                "objective": row["objective"],
                "reference_objective": row.get("reference_objective"),
                "gap_abs": row.get("gap_abs"),
                "gap_rel": row.get("gap_rel"),
                "elapsed_seconds": row.get("elapsed_seconds"),
            }
            for key, row in sorted(best_by_case.items())
        },
        "artifacts": {
            "config": str(run_dir / "config.json"),
            "results_jsonl": str(run_dir / "results.jsonl"),
            "results_csv": str(run_dir / "results.csv"),
            "anytime_jsonl": str(run_dir / "anytime.jsonl"),
            "throughput_jsonl": str(run_dir / "throughput.jsonl"),
            "summary": str(run_dir / "summary.json"),
            "report": str(run_dir / "report.md"),
        },
    }


def build_default_candidate_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Rank strategy candidates by coverage, feasibility, quality, and runtime."""

    strategy_rows = [
        row
        for row in rows
        if row.get("kind") == "strategy_run" and int(row.get("thread_count") or 1) == 1
    ]
    by_strategy: dict[str, list[dict[str, Any]]] = {}
    for row in strategy_rows:
        strategy = str(row.get("strategy") or "")
        if strategy:
            by_strategy.setdefault(strategy, []).append(row)

    ranked = [
        _default_candidate_score(strategy, strategy_rows)
        for strategy, strategy_rows in sorted(by_strategy.items())
    ]
    ranked.sort(key=_default_candidate_sort_key)
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
        row["recommended"] = index == 1
    return {
        "enabled": True,
        "selection_policy": "feasible_coverage_then_error_then_gap_then_time_then_improvement_v1",
        "ranked_strategies": ranked,
        "recommended_strategy": ranked[0]["strategy"] if ranked else None,
        "strategy_count": len(ranked),
        "row_count": len(strategy_rows),
    }


def build_parallel_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    matrix_rows = [row for row in rows if row.get("parallel_matrix_enabled")]
    by_group: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in matrix_rows:
        key = (
            str(row.get("benchmark_id") or ""),
            str(row.get("strategy") or ""),
            str(row.get("strategy_profile") or ""),
            str(row.get("model_style") or ""),
            str(row.get("kind") or ""),
        )
        by_group.setdefault(key, []).append(row)

    groups = []
    for key, group_rows in sorted(by_group.items()):
        baseline = _thread_row(group_rows, 1)
        rows_by_thread = []
        for row in sorted(group_rows, key=lambda item: int(item.get("thread_count") or 1)):
            rows_by_thread.append(_parallel_matrix_row(row, baseline))
        groups.append(
            {
                "benchmark_id": key[0],
                "strategy": key[1],
                "strategy_profile": key[2],
                "model_style": key[3],
                "kind": key[4],
                "baseline_thread_count": 1,
                "has_baseline": baseline is not None,
                "rows": rows_by_thread,
            }
        )
    return {
        "enabled": True,
        "thread_counts": sorted({int(row.get("thread_count") or 1) for row in matrix_rows}),
        "group_count": len(groups),
        "groups": groups,
    }


def _thread_row(rows: list[dict[str, Any]], thread_count: int) -> dict[str, Any] | None:
    for row in rows:
        if int(row.get("thread_count") or 1) == thread_count:
            return row
    return None


def _parallel_matrix_row(row: dict[str, Any], baseline: dict[str, Any] | None) -> dict[str, Any]:
    baseline_elapsed = _float_or_none(baseline.get("elapsed_seconds")) if baseline else None
    elapsed = _float_or_none(row.get("elapsed_seconds"))
    thread_count = int(row.get("thread_count") or 1)
    speedup = baseline_elapsed / elapsed if baseline_elapsed is not None and elapsed and elapsed > 0 else None
    efficiency = speedup / thread_count if speedup is not None and thread_count > 0 else None
    throughput_speedup = _throughput_speedup(row, baseline)
    return {
        "thread_count": thread_count,
        "status": row.get("status"),
        "feasible": row.get("feasible"),
        "objective": row.get("objective"),
        "gap_rel": row.get("gap_rel"),
        "elapsed_seconds": row.get("elapsed_seconds"),
        "speedup": speedup,
        "efficiency": efficiency,
        "quality_delta_vs_1_thread": _delta_float(row, baseline, "objective"),
        "gap_delta_vs_1_thread": _delta_float(row, baseline, "gap_rel"),
        "throughput_speedup": throughput_speedup,
    }


def _throughput_speedup(row: dict[str, Any], baseline: dict[str, Any] | None) -> float | None:
    if baseline is None:
        return None
    for field in (
        "evaluations_per_s",
        "moves_attempted_per_s",
        "delta_evaluations_per_s",
        "repairs_attempted_per_s",
    ):
        current = _float_or_none(row.get(field))
        base = _float_or_none(baseline.get(field))
        if current is not None and base is not None and base > 0:
            return current / base
    return None


def _delta_float(
    row: dict[str, Any],
    baseline: dict[str, Any] | None,
    field: str,
) -> float | None:
    if baseline is None:
        return None
    current = _float_or_none(row.get(field))
    base = _float_or_none(baseline.get(field))
    if current is None or base is None:
        return None
    return current - base


def _default_candidate_score(strategy: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [
        row
        for row in rows
        if row.get("status") != "error" and row.get("feasible") is True and row.get("objective") is not None
    ]
    error_rows = [row for row in rows if row.get("status") == "error"]
    non_feasible = [row for row in rows if row.get("status") != "error" and row.get("feasible") is not True]
    gap_values = [
        float(row["gap_rel"])
        for row in successful
        if row.get("gap_rel") is not None
    ]
    elapsed_values = [
        float(row["elapsed_seconds"])
        for row in rows
        if row.get("elapsed_seconds") is not None
    ]
    improvement_values = [
        float(row["improvement_per_second"])
        for row in successful
        if row.get("improvement_per_second") is not None
    ]
    row_count = len(rows)
    successful_count = len(successful)
    feasible_rate = successful_count / row_count if row_count else 0.0
    error_rate = len(error_rows) / row_count if row_count else 0.0
    non_feasible_rate = len(non_feasible) / row_count if row_count else 0.0
    return {
        "strategy": strategy,
        "row_count": row_count,
        "successful_count": successful_count,
        "error_count": len(error_rows),
        "non_feasible_count": len(non_feasible),
        "feasible_rate": feasible_rate,
        "error_rate": error_rate,
        "non_feasible_rate": non_feasible_rate,
        "families_covered": sorted({str(row.get("family")) for row in rows if row.get("family")}),
        "family_count": len({str(row.get("family")) for row in rows if row.get("family")}),
        "cases_covered": sorted({str(row.get("benchmark_id")) for row in rows if row.get("benchmark_id")}),
        "case_count": len({str(row.get("benchmark_id")) for row in rows if row.get("benchmark_id")}),
        "tiers_covered": sorted({str(row.get("tier")) for row in rows if row.get("tier")}),
        "avg_gap_rel": sum(gap_values) / len(gap_values) if gap_values else None,
        "max_gap_rel": max(gap_values) if gap_values else None,
        "avg_elapsed_seconds": sum(elapsed_values) / len(elapsed_values) if elapsed_values else None,
        "total_elapsed_seconds": sum(elapsed_values) if elapsed_values else None,
        "avg_improvement_per_second": (
            sum(improvement_values) / len(improvement_values)
            if improvement_values
            else None
        ),
    }


def _default_candidate_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    avg_gap = float("inf") if row.get("avg_gap_rel") is None else float(row["avg_gap_rel"])
    max_gap = float("inf") if row.get("max_gap_rel") is None else float(row["max_gap_rel"])
    avg_elapsed = (
        float("inf")
        if row.get("avg_elapsed_seconds") is None
        else float(row["avg_elapsed_seconds"])
    )
    return (
        -int(row.get("family_count", 0)),
        -int(row.get("case_count", 0)),
        -float(row.get("feasible_rate", 0.0)),
        float(row.get("error_rate", 0.0)),
        float(row.get("non_feasible_rate", 0.0)),
        avg_gap,
        max_gap,
        avg_elapsed,
        -float(row.get("avg_improvement_per_second") or 0.0),
        str(row.get("strategy") or ""),
    )


def _family_improvement_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("kind") != "strategy_run":
            continue
        family = str(row.get("family") or "unknown")
        bucket = summary.setdefault(
            family,
            {
                "rows_with_improvement": 0,
                "improvement_abs_sum": 0.0,
                "improvement_per_second_sum": 0.0,
                "avg_improvement_abs": None,
                "avg_improvement_per_second": None,
            },
        )
        improvement_abs = _float_or_none(row.get("improvement_abs"))
        improvement_per_second = _float_or_none(row.get("improvement_per_second"))
        if improvement_abs is None or improvement_per_second is None:
            continue
        bucket["rows_with_improvement"] += 1
        bucket["improvement_abs_sum"] += improvement_abs
        bucket["improvement_per_second_sum"] += improvement_per_second
    for bucket in summary.values():
        count = int(bucket["rows_with_improvement"])
        if count:
            bucket["avg_improvement_abs"] = bucket["improvement_abs_sum"] / count
            bucket["avg_improvement_per_second"] = bucket["improvement_per_second_sum"] / count
        del bucket["improvement_abs_sum"]
        del bucket["improvement_per_second_sum"]
    return summary


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def write_results_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "kind",
        "benchmark_id",
        "family",
        "tier",
        "strategy",
        "strategy_profile",
        "budget_profile",
        "benchmark_schema_version",
        "thread_count",
        "parallel_matrix_enabled",
        "model_style",
        "solver_name",
        "status",
        "feasible",
        "objective",
        "best_cost",
        "reference_cost",
        "initial_cost",
        "improvement_abs",
        "improvement_rel",
        "improvement_per_second",
        "improvement_per_evaluation",
        "improvement_per_move",
        "raw_objective",
        "reference_objective",
        "gap_abs",
        "gap_rel",
        "runtime_s",
        "elapsed_seconds",
        "time_to_best_seconds",
        "time_to_first_feasible_seconds",
        "termination_reason",
        "effective_max_iterations",
        "effective_time_limit_s",
        "effective_population_size",
        "effective_exact_time_limit_s",
        "moves_attempted",
        "moves_accepted",
        "moves_improved",
        "evaluations",
        "delta_evaluations",
        "full_evaluations",
        "repairs_attempted",
        "repairs_succeeded",
        "moves_attempted_per_s",
        "moves_accepted_per_s",
        "evaluations_per_s",
        "delta_evaluations_per_s",
        "full_evaluations_per_s",
        "repairs_attempted_per_s",
        "repairs_succeeded_per_s",
        "construct_candidates_evaluated",
        "construct_best_improvements",
        "ga_scheduling_repair_count",
        "ga_scheduling_repair_success_count",
        "ga_infeasible_offspring_count",
        "ga_first_feasible_generation",
        "lns_applications",
        "sequence_graph_delta_count",
        "full_root_eval_delta_count",
        "tsp_two_opt_moves_evaluated",
        "tsp_two_opt_improvements",
        "tsp_repair_insertions",
        "tsp_preserved_edge_ratio",
        "qap_swap_delta_count",
        "qap_swap_improvement_count",
        "qap_repair_assignment_count",
        "qap_common_assignment_preservation_ratio",
        "dimension",
        "edge_weight_type",
    ]
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render_report(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Modeling-Native Benchmark Run",
        "",
        f"- Run dir: `{summary['run_dir']}`",
        f"- Families: `{', '.join(summary['families'])}`",
        f"- Tiers: `{', '.join(summary['tiers'])}`",
        f"- Strategies: `{', '.join(summary['strategies'])}`",
        f"- Parallel matrix: `{summary.get('parallel_matrix_enabled', False)}`",
        f"- Thread counts: `{', '.join(str(value) for value in summary.get('parallel_thread_counts', [1]))}`",
        f"- Selected cases: {summary['selected_case_count']}",
        f"- Executed cases: {summary['executed_case_count']}",
        f"- Runs: {summary['strategy_run_count']}",
        f"- Strategy rows: {summary.get('strategy_row_count', 0)}",
        f"- Exact baseline rows: {summary.get('exact_baseline_row_count', 0)}",
        f"- Successful runs: {summary['successful_run_count']}",
        f"- Non-feasible runs: {summary['non_feasible_run_count']}",
        f"- Error runs: {summary['error_run_count']}",
        "",
        "## Effective Strategies",
        "",
        "| Family | Strategies |",
        "| --- | --- |",
    ]
    for family, strategies in sorted(summary.get("family_strategy_plan", {}).items()):
        strategy_text = ", ".join(f"`{strategy}`" for strategy in strategies)
        lines.append(f"| `{family}` | {strategy_text} |")
    if summary.get("strategy_substitutions"):
        lines.extend(["", "Strategy substitutions:", ""])
        for item in summary["strategy_substitutions"]:
            requested = ", ".join(item.get("requested", []))
            effective = ", ".join(item.get("effective", []))
            lines.append(
                f"- `{item.get('family')}`: `{requested}` -> `{effective}` ({item.get('reason')})"
            )
    lines.extend(
        [
            "",
            "## Family Budgets",
            "",
            "| Family | Tier | Budget profile | Iterations | Seconds | Population | Trace | Exact seconds |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for family, tier_budgets in sorted(summary.get("family_budgets", {}).items()):
        for tier, budget in sorted(tier_budgets.items()):
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{family}`",
                        f"`{tier}`",
                        f"`{budget.get('profile', '')}`",
                        _fmt(budget.get("max_iterations")),
                        _fmt(budget.get("time_limit_s")),
                        _fmt(budget.get("population_size")),
                        _fmt(budget.get("trace_limit")),
                        _fmt(budget.get("exact_time_limit_s")),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Strategy Profiles",
            "",
            "| Profile | Rows |",
            "| --- | ---: |",
        ]
    )
    for profile, count in sorted(summary.get("profile_counts", {}).items()):
        lines.append(f"| `{profile}` | {count} |")
    lines.extend(
        [
            "",
            "## Search Efficiency",
            "",
            "| Family | Rows with improvement | Avg improvement | Avg improvement/s |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for family, item in sorted(summary.get("family_improvement_summary", {}).items()):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{family}`",
                    _fmt(item.get("rows_with_improvement")),
                    _fmt(item.get("avg_improvement_abs")),
                    _fmt(item.get("avg_improvement_per_second")),
                ]
            )
                + " |"
        )
    if summary.get("parallel_matrix_enabled"):
        matrix = summary.get("parallel_matrix", {})
        lines.extend(
            [
                "",
                "## Parallel Matrix",
                "",
                f"- Thread counts: `{', '.join(str(value) for value in matrix.get('thread_counts', []))}`",
                "",
                "| Case | Strategy | Profile | Style | Kind | Threads | Objective | Gap % | Seconds | Speedup | Efficiency | Quality delta | Throughput speedup |",
                "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for group in matrix.get("groups", []):
            for row in group.get("rows", []):
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            f"`{group.get('benchmark_id')}`",
                            f"`{group.get('strategy')}`",
                            f"`{group.get('strategy_profile')}`",
                            f"`{group.get('model_style')}`",
                            f"`{group.get('kind')}`",
                            _fmt(row.get("thread_count")),
                            _fmt(row.get("objective")),
                            _fmt_pct(row.get("gap_rel")),
                            _fmt(row.get("elapsed_seconds")),
                            _fmt(row.get("speedup")),
                            _fmt(row.get("efficiency")),
                            _fmt(row.get("quality_delta_vs_1_thread")),
                            _fmt(row.get("throughput_speedup")),
                        ]
                    )
                    + " |"
                )
    if summary.get("default_candidate_matrix_enabled"):
        matrix = summary.get("default_candidate_matrix", {})
        lines.extend(
            [
                "",
                "## Default Strategy Candidate Matrix",
                "",
                f"- Selection policy: `{matrix.get('selection_policy', '')}`",
                f"- Recommended strategy: `{matrix.get('recommended_strategy') or ''}`",
                "",
                "| Rank | Strategy | Recommended | Rows | Families | Cases | Feasible % | Errors | Non-feasible | Avg gap % | Max gap % | Avg seconds | Avg improvement/s |",
                "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in matrix.get("ranked_strategies", []):
            lines.append(
                "| "
                + " | ".join(
                    [
                        _fmt(row.get("rank")),
                        f"`{row.get('strategy')}`",
                        "yes" if row.get("recommended") else "",
                        _fmt(row.get("row_count")),
                        _fmt(row.get("family_count")),
                        _fmt(row.get("case_count")),
                        _fmt_pct(row.get("feasible_rate")),
                        _fmt(row.get("error_count")),
                        _fmt(row.get("non_feasible_count")),
                        _fmt_pct(row.get("avg_gap_rel")),
                        _fmt_pct(row.get("max_gap_rel")),
                        _fmt(row.get("avg_elapsed_seconds")),
                        _fmt(row.get("avg_improvement_per_second")),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Best By Case",
            "",
            "| Case | Best route | Profile | Style | Kind | Objective | Reference | Gap | Gap % | Seconds |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for benchmark_id, row in summary["best_by_case"].items():
        gap_rel = row.get("gap_rel")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{benchmark_id}`",
                    f"`{row['strategy']}`",
                    f"`{row.get('strategy_profile') or ''}`",
                    f"`{row.get('model_style') or ''}`",
                    f"`{row.get('kind') or ''}`",
                    _fmt(row.get("objective")),
                    _fmt(row.get("reference_objective")),
                    _fmt(row.get("gap_abs")),
                    _fmt_pct(gap_rel),
                    _fmt(row.get("elapsed_seconds")),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Runs",
            "",
            "| Case | Route | Profile | Budget profile | Style | Kind | Status | Objective | Raw objective | Gap % | Seconds | Metadata highlights |",
            "| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        metadata = row.get("metadata", {})
        highlights = metadata_highlights(metadata) if isinstance(metadata, dict) else []
        error = row.get("error")
        if error:
            highlights.append(f"error={error['type']}")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['benchmark_id']}`",
                    f"`{row['strategy']}`",
                    f"`{row.get('strategy_profile') or ''}`",
                    f"`{row.get('budget_profile') or ''}`",
                    f"`{row.get('model_style') or ''}`",
                    f"`{row.get('kind') or ''}`",
                    str(row.get("status")),
                    _fmt(row.get("objective")),
                    _fmt(row.get("raw_objective")),
                    _fmt_pct(row.get("gap_rel")),
                    _fmt(row.get("elapsed_seconds")),
                    ", ".join(highlights) if highlights else "",
                ]
            )
            + " |"
        )

    if summary["skipped_cases"]:
        lines.extend(["", "## Skipped Cases", "", "| Case | Family | Reason |", "| --- | --- | --- |"])
        for row in summary["skipped_cases"]:
            lines.append(f"| `{row['benchmark_id']}` | `{row['family']}` | {row['reason']} |")
    return "\n".join(lines) + "\n"


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _fmt_pct(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value) * 100:.3f}%"
