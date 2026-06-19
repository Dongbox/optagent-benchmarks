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


IMPLEMENTED_FAMILIES = {
    "cumulative_resource_scheduling",
    "exact_linear_mip",
    "interval_job_shop",
    "sequence_blackbox_tsp",
    "sequence_quadratic_assignment",
}
DEFAULT_RUNNABLE_FAMILIES = ("interval_job_shop", "sequence_blackbox_tsp", "sequence_quadratic_assignment")
DEFAULT_STRATEGIES = ("ga", "alns", "tabu")
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
    timestamp: str | None = None,
) -> dict[str, Any]:
    run_dir = ensure_run_dir(output_root, timestamp=timestamp)
    cases = select_cases(
        catalog_cases(catalog_path),
        families=families,
        tiers=tiers,
        benchmark_ids=benchmark_ids,
    )
    budget_request = StrategyBudgetRequest(
        seed=seed,
        max_iterations=max_iterations,
        time_limit_s=time_limit_s,
        population_size=population_size,
        trace_limit=trace_limit,
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
        effective_budget = resolve_family_tier_budget(
            family=family,
            tier=str(case.get("tier") or "smoke"),
            request=budget_request,
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
            case_rows = [_normalize_case_row(row, effective_budget) for row in case_rows]
            append_jsonl(run_dir / "results.jsonl", case_rows)
            rows.extend(case_rows)
        elif family == "exact_linear_mip":
            case_rows = run_mip_case(
                case,
                strategies=strategy_plan[family],
                budget=_mip_budget(effective_budget),
                data_cache_dir=data_cache_dir,
                allow_download=allow_download,
            )
            case_rows = [_normalize_case_row(row, effective_budget) for row in case_rows]
            append_jsonl(run_dir / "results.jsonl", case_rows)
            rows.extend(case_rows)
        elif family == "cumulative_resource_scheduling":
            case_rows = run_rcpsp_case(
                case,
                strategies=strategy_plan[family],
                budget=_rcpsp_budget(effective_budget),
                data_cache_dir=data_cache_dir,
                allow_download=allow_download,
                include_exact_baseline=True,
            )
            case_rows = [_normalize_case_row(row, effective_budget) for row in case_rows]
            append_jsonl(run_dir / "results.jsonl", case_rows)
            rows.extend(case_rows)
        elif family == "interval_job_shop":
            case_rows = run_job_shop_case(
                case,
                strategies=strategy_plan[family],
                budget=_job_shop_budget(effective_budget),
                data_cache_dir=data_cache_dir,
                allow_download=allow_download,
                include_exact_baseline=True,
            )
            case_rows = [_normalize_case_row(row, effective_budget) for row in case_rows]
            append_jsonl(run_dir / "results.jsonl", case_rows)
            rows.extend(case_rows)
        elif family == "sequence_quadratic_assignment":
            case_rows = run_qap_case(
                case,
                strategies=strategy_plan[family],
                budget=_qap_budget(effective_budget),
                data_cache_dir=data_cache_dir,
                allow_download=allow_download,
            )
            case_rows = [_normalize_case_row(row, effective_budget) for row in case_rows]
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
    )


def _qap_budget(budget: EffectiveStrategyBudget) -> QapStrategyBudget:
    return QapStrategyBudget(
        seed=budget.seed,
        max_iterations=budget.max_iterations,
        time_limit_s=budget.time_limit_s,
        population_size=budget.population_size,
        trace_limit=budget.trace_limit,
    )


def _job_shop_budget(budget: EffectiveStrategyBudget) -> JobShopStrategyBudget:
    return JobShopStrategyBudget(
        seed=budget.seed,
        max_iterations=budget.max_iterations,
        time_limit_s=budget.time_limit_s,
        population_size=budget.population_size,
        trace_limit=budget.trace_limit,
        cpsat_time_limit_s=budget.exact_time_limit_s,
    )


def _rcpsp_budget(budget: EffectiveStrategyBudget) -> RcpspStrategyBudget:
    return RcpspStrategyBudget(
        seed=budget.seed,
        max_iterations=budget.max_iterations,
        time_limit_s=budget.time_limit_s,
        population_size=budget.population_size,
        trace_limit=budget.trace_limit,
        cpsat_time_limit_s=budget.exact_time_limit_s,
    )


def _mip_budget(budget: EffectiveStrategyBudget) -> MipExactBudget:
    return MipExactBudget(
        seed=budget.seed,
        max_iterations=0,
        time_limit_s=budget.exact_time_limit_s or budget.time_limit_s,
        population_size=0,
        trace_limit=0,
        backend="optx",
    )


def _normalize_case_row(row: dict[str, Any], budget: EffectiveStrategyBudget) -> dict[str, Any]:
    row["budget_profile"] = budget.profile
    row["effective_max_iterations"] = budget.max_iterations
    row["effective_time_limit_s"] = budget.time_limit_s
    row["effective_population_size"] = budget.population_size
    row["effective_trace_limit"] = budget.trace_limit
    if budget.exact_time_limit_s is not None:
        row["effective_exact_time_limit_s"] = budget.exact_time_limit_s
    row["effective_budget"] = budget.to_dict()
    metadata = row.get("metadata")
    if isinstance(metadata, dict):
        metadata.setdefault("budget_profile", budget.profile)
        metadata.setdefault("effective_budget", budget.to_dict())
    return normalize_result_row(row)


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
        "budget": dict(config["budget"]),
        "budget_policy": config.get("budget_policy"),
        "family_budgets": config.get("family_budgets", {}),
        "profile_counts": _profile_counts(rows),
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
            "summary": str(run_dir / "summary.json"),
            "report": str(run_dir / "report.md"),
        },
    }


def write_results_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "kind",
        "benchmark_id",
        "family",
        "tier",
        "strategy",
        "strategy_profile",
        "budget_profile",
        "model_style",
        "solver_name",
        "status",
        "feasible",
        "objective",
        "raw_objective",
        "reference_objective",
        "gap_abs",
        "gap_rel",
        "elapsed_seconds",
        "time_to_best_seconds",
        "time_to_first_feasible_seconds",
        "effective_max_iterations",
        "effective_time_limit_s",
        "effective_population_size",
        "effective_exact_time_limit_s",
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
