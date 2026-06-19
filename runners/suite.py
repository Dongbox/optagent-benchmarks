from __future__ import annotations

from dataclasses import asdict
import csv
import platform
import sys
from pathlib import Path
from typing import Any

from benchmarks.loaders.catalog import DEFAULT_CATALOG_PATH, catalog_cases, select_cases
from benchmarks.runners.common import DEFAULT_RUN_ROOT, append_jsonl, ensure_run_dir, write_json
from benchmarks.runners.interval_job_shop import JobShopStrategyBudget, run_job_shop_case
from benchmarks.runners.sequence_quadratic_assignment import QapStrategyBudget, run_qap_case
from benchmarks.runners.sequence_blackbox_tsp import TspStrategyBudget, run_tsp_case


IMPLEMENTED_FAMILIES = {"interval_job_shop", "sequence_blackbox_tsp", "sequence_quadratic_assignment"}
DEFAULT_RUNNABLE_FAMILIES = ("interval_job_shop", "sequence_blackbox_tsp", "sequence_quadratic_assignment")


def run_benchmark_suite(
    *,
    catalog_path: str | Path = DEFAULT_CATALOG_PATH,
    output_root: str | Path = DEFAULT_RUN_ROOT,
    families: tuple[str, ...] = DEFAULT_RUNNABLE_FAMILIES,
    tiers: tuple[str, ...] = ("smoke",),
    benchmark_ids: tuple[str, ...] = (),
    strategies: tuple[str, ...] = ("ga", "alns", "tabu"),
    seed: int = 11,
    max_iterations: int = 40,
    time_limit_s: float = 5.0,
    population_size: int = 10,
    trace_limit: int = 8,
    data_cache_dir: str | None = None,
    allow_download: bool = True,
    timestamp: str | None = None,
) -> dict[str, Any]:
    run_dir = ensure_run_dir(output_root, timestamp=timestamp)
    cases = select_cases(
        catalog_cases(catalog_path),
        families=families,
        tiers=tiers,
        benchmark_ids=benchmark_ids,
    )
    budget = TspStrategyBudget(
        seed=seed,
        max_iterations=max_iterations,
        time_limit_s=time_limit_s,
        population_size=population_size,
        trace_limit=trace_limit,
    )
    qap_budget = QapStrategyBudget(
        seed=seed,
        max_iterations=max_iterations,
        time_limit_s=time_limit_s,
        population_size=population_size,
        trace_limit=trace_limit,
    )
    job_shop_budget = JobShopStrategyBudget(
        seed=seed,
        max_iterations=max_iterations,
        time_limit_s=time_limit_s,
        population_size=population_size,
        trace_limit=trace_limit,
    )
    config = {
        "catalog_path": str(catalog_path),
        "families": list(families),
        "tiers": list(tiers),
        "benchmark_ids": list(benchmark_ids),
        "strategies": list(strategies),
        "budget": asdict(budget),
        "family_budgets": {
            "interval_job_shop": asdict(job_shop_budget),
            "sequence_blackbox_tsp": asdict(budget),
            "sequence_quadratic_assignment": asdict(qap_budget),
        },
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
        if family == "sequence_blackbox_tsp":
            case_rows = run_tsp_case(
                case,
                strategies=strategies,
                budget=budget,
                data_cache_dir=data_cache_dir,
                allow_download=allow_download,
            )
            append_jsonl(run_dir / "results.jsonl", case_rows)
            rows.extend(case_rows)
        elif family == "interval_job_shop":
            case_rows = run_job_shop_case(
                case,
                strategies=strategies,
                budget=job_shop_budget,
                data_cache_dir=data_cache_dir,
                allow_download=allow_download,
                include_exact_baseline=True,
            )
            append_jsonl(run_dir / "results.jsonl", case_rows)
            rows.extend(case_rows)
        elif family == "sequence_quadratic_assignment":
            case_rows = run_qap_case(
                case,
                strategies=strategies,
                budget=qap_budget,
                data_cache_dir=data_cache_dir,
                allow_download=allow_download,
            )
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
        "successful_run_count": len(successful_rows),
        "error_run_count": len(rows) - len(successful_rows),
        "families": list(config["families"]),
        "tiers": list(config["tiers"]),
        "strategies": list(config["strategies"]),
        "budget": dict(config["budget"]),
        "skipped_cases": skipped_cases,
        "best_by_case": {
            key: {
                "strategy": row["strategy"],
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
        "solver_name",
        "status",
        "feasible",
        "objective",
        "reference_objective",
        "gap_abs",
        "gap_rel",
        "elapsed_seconds",
        "time_to_best_seconds",
        "time_to_first_feasible_seconds",
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
        f"- Successful runs: {summary['successful_run_count']}",
        f"- Error runs: {summary['error_run_count']}",
        "",
        "## Best By Case",
        "",
        "| Case | Best route | Kind | Objective | Reference | Gap | Gap % | Seconds |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for benchmark_id, row in summary["best_by_case"].items():
        gap_rel = row.get("gap_rel")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{benchmark_id}`",
                    f"`{row['strategy']}`",
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
            "| Case | Route | Kind | Status | Objective | Gap % | Seconds | Metadata highlights |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        metadata = row.get("metadata", {})
        highlights = []
        for key in (
            "iterations",
            "ga_generation_count",
            "alns_iterations",
            "external_rows_requested",
            "external_cache_hits",
            "external_cache_misses",
            "backend_status_name",
            "best_objective_bound",
            "wall_time_seconds",
        ):
            if key in metadata:
                highlights.append(f"{key}={metadata[key]}")
        error = row.get("error")
        if error:
            highlights.append(f"error={error['type']}")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['benchmark_id']}`",
                    f"`{row['strategy']}`",
                    f"`{row.get('kind') or ''}`",
                    str(row.get("status")),
                    _fmt(row.get("objective")),
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
