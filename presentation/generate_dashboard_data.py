"""Legacy dashboard aggregate generator for Git-managed run summaries.

The supported telemetry metrics dashboard path is
``benchmarks.telemetry_artifacts`` plus ``benchmarks.presentation.dashboard``.
This module remains only for historical `presentation/results/` aggregates.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean
from typing import Any

from benchmarks.presentation.common import write_json


PRESENTATION_ROOT = Path(__file__).resolve().parents[0]
DEFAULT_RESULTS_ROOT = PRESENTATION_ROOT / "results"
DEFAULT_AGGREGATES_ROOT = PRESENTATION_ROOT / "aggregates"
GENERATED_SCHEMA_VERSION = 1


def generate_dashboard_data(
    *,
    results_root: str | Path = DEFAULT_RESULTS_ROOT,
    aggregates_root: str | Path = DEFAULT_AGGREGATES_ROOT,
    generated_at: str | None = None,
    check: bool = False,
) -> dict[str, Any]:
    results_path = Path(results_root)
    aggregates_path = Path(aggregates_root)
    runs = load_run_summaries(results_path)
    effective_generated_at = generated_at or _latest_created_at(runs)
    index = build_results_index(runs, results_root=results_path, generated_at=effective_generated_at)
    aggregates = {
        "leaderboard.json": build_leaderboard(runs, results_root=results_path, generated_at=effective_generated_at),
        "commit-history.json": build_commit_history(runs, results_root=results_path, generated_at=effective_generated_at),
        "strategy-comparison.json": build_strategy_comparison(
            runs,
            results_root=results_path,
            generated_at=effective_generated_at,
        ),
        "runtime-quality.json": build_runtime_quality(runs, results_root=results_path, generated_at=effective_generated_at),
    }

    outputs = {
        results_path / "index.json": index,
        **{aggregates_path / name: payload for name, payload in aggregates.items()},
    }
    if check:
        mismatches = _check_outputs(outputs)
        if mismatches:
            raise SystemExit("generated dashboard data is stale:\n" + "\n".join(f"- {path}" for path in mismatches))
    else:
        for path, payload in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            write_json(path, payload)
    return {
        "schema_version": GENERATED_SCHEMA_VERSION,
        "generated_at": effective_generated_at,
        "run_count": len(runs),
        "outputs": {str(path): payload for path, payload in outputs.items()},
    }


def load_run_summaries(results_root: str | Path = DEFAULT_RESULTS_ROOT) -> list[dict[str, Any]]:
    root = Path(results_root)
    runs: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.json")):
        if _is_generated_or_schema(path, root):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON file: {path}") from exc
        if not _is_run_summary(payload):
            continue
        run = deepcopy(payload)
        run["_summary_path"] = _dashboard_path(path, root)
        run["_relative_summary_path"] = path.relative_to(root).as_posix()
        runs.append(run)
    runs.sort(key=_run_sort_key)
    _validate_unique_run_ids(runs)
    return runs


def build_results_index(
    runs: list[dict[str, Any]],
    *,
    results_root: str | Path = DEFAULT_RESULTS_ROOT,
    generated_at: str | None = None,
) -> dict[str, Any]:
    groups: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    index_runs: list[dict[str, Any]] = []
    for run in runs:
        group = str(run["benchmark_group"])
        strategy = str(run["strategy"])
        summary_path = str(run["_summary_path"])
        groups[group][strategy].append(summary_path)
        index_runs.append(_index_run_entry(run))
    return {
        "schema_version": GENERATED_SCHEMA_VERSION,
        "generated_at": generated_at or _latest_created_at(runs),
        "runs": index_runs,
        "groups": {
            group: {strategy: sorted(paths) for strategy, paths in sorted(strategy_map.items())}
            for group, strategy_map in sorted(groups.items())
        },
    }


def build_leaderboard(
    runs: list[dict[str, Any]],
    *,
    results_root: str | Path = DEFAULT_RESULTS_ROOT,
    generated_at: str | None = None,
) -> dict[str, Any]:
    by_group_strategy: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    benchmark_ids_by_group: dict[str, set[str]] = defaultdict(set)
    for run in runs:
        by_group_strategy[(str(run["benchmark_group"]), str(run["strategy"]))].append(run)
        benchmark_ids_by_group[str(run["benchmark_group"])].add(str(run["benchmark_id"]))

    groups: dict[str, dict[str, Any]] = {}
    for group in sorted(benchmark_ids_by_group):
        entries: list[dict[str, Any]] = []
        for (entry_group, strategy), strategy_runs in sorted(by_group_strategy.items()):
            if entry_group != group:
                continue
            best_run = _best_run(strategy_runs)
            entries.append(
                {
                    "rank": 0,
                    "benchmark_group": group,
                    "strategy": strategy,
                    "run_count": len(strategy_runs),
                    "success_rate": _rate(strategy_runs, lambda run: _metrics(run).get("status") == "success"),
                    "feasible_rate": _rate(strategy_runs, lambda run: _metrics(run).get("feasible") is True),
                    "best_run_id": best_run.get("run_id"),
                    "best_summary_path": best_run.get("_summary_path"),
                    "best_objective": _number(_metrics(best_run).get("objective")),
                    "best_cost": _number(_metrics(best_run).get("best_cost")),
                    "best_gap_rel": _number(_metrics(best_run).get("gap_rel")),
                    "best_runtime_ms": _number(_metrics(best_run).get("runtime_ms")),
                    "latest_created_at": _latest_created_at(strategy_runs),
                    "optagent_commit": _optagent(best_run).get("commit"),
                    "optagent_commit_url": _optagent(best_run).get("commit_url"),
                }
            )
        entries.sort(key=_leaderboard_sort_key)
        for index, entry in enumerate(entries, start=1):
            entry["rank"] = index
        groups[group] = {
            "benchmark_count": len(benchmark_ids_by_group[group]),
            "strategy_count": len(entries),
            "run_count": sum(entry["run_count"] for entry in entries),
            "entries": entries,
        }
    return {
        "schema_version": GENERATED_SCHEMA_VERSION,
        "generated_at": generated_at or _latest_created_at(runs),
        "groups": groups,
    }


def build_commit_history(
    runs: list[dict[str, Any]],
    *,
    results_root: str | Path = DEFAULT_RESULTS_ROOT,
    generated_at: str | None = None,
) -> dict[str, Any]:
    by_series: dict[tuple[str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        by_series[
            (
                str(run["benchmark_group"]),
                str(run["benchmark_id"]),
                str(run["strategy"]),
                int(run.get("seed", 0)),
            )
        ].append(run)

    series = []
    for (group, benchmark_id, strategy, seed), series_runs in sorted(by_series.items()):
        points = []
        for run in sorted(series_runs, key=_run_sort_key):
            metrics = _metrics(run)
            optagent = _optagent(run)
            points.append(
                {
                    "commit": optagent.get("commit"),
                    "commit_url": optagent.get("commit_url"),
                    "created_at": run.get("created_at"),
                    "run_id": run.get("run_id"),
                    "summary_path": run.get("_summary_path"),
                    "status": metrics.get("status"),
                    "feasible": metrics.get("feasible"),
                    "objective": _number(metrics.get("objective")),
                    "best_cost": _number(metrics.get("best_cost")),
                    "gap_rel": _number(metrics.get("gap_rel")),
                    "runtime_ms": _number(metrics.get("runtime_ms")),
                }
            )
        series.append(
            {
                "key": f"{group}/{benchmark_id}/{strategy}/seed-{seed}",
                "benchmark_group": group,
                "benchmark_id": benchmark_id,
                "strategy": strategy,
                "seed": seed,
                "metric": "best_cost",
                "points": points,
            }
        )
    return {
        "schema_version": GENERATED_SCHEMA_VERSION,
        "generated_at": generated_at or _latest_created_at(runs),
        "series": series,
    }


def build_strategy_comparison(
    runs: list[dict[str, Any]],
    *,
    results_root: str | Path = DEFAULT_RESULTS_ROOT,
    generated_at: str | None = None,
) -> dict[str, Any]:
    by_case_strategy: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        by_case_strategy[
            (
                str(run["benchmark_group"]),
                str(run["benchmark_id"]),
                str(run.get("tier") or ""),
                str(run["strategy"]),
            )
        ].append(run)

    comparison_map: dict[tuple[str, str, str], dict[str, Any]] = {}
    for (group, benchmark_id, tier, strategy), strategy_runs in sorted(by_case_strategy.items()):
        key = (group, benchmark_id, tier)
        comparison = comparison_map.setdefault(
            key,
            {
                "benchmark_group": group,
                "benchmark_id": benchmark_id,
                "tier": tier,
                "strategies": [],
            },
        )
        best_run = _best_run(strategy_runs)
        latest_run = max(strategy_runs, key=_run_sort_key)
        best_metrics = _metrics(best_run)
        latest_metrics = _metrics(latest_run)
        runtimes = [_number(_metrics(run).get("runtime_ms")) for run in strategy_runs]
        runtimes = [value for value in runtimes if value is not None]
        comparison["strategies"].append(
            {
                "strategy": strategy,
                "run_count": len(strategy_runs),
                "success_rate": _rate(strategy_runs, lambda run: _metrics(run).get("status") == "success"),
                "feasible_rate": _rate(strategy_runs, lambda run: _metrics(run).get("feasible") is True),
                "best_run_id": best_run.get("run_id"),
                "best_summary_path": best_run.get("_summary_path"),
                "best_objective": _number(best_metrics.get("objective")),
                "best_cost": _number(best_metrics.get("best_cost")),
                "best_gap_rel": _number(best_metrics.get("gap_rel")),
                "avg_runtime_ms": mean(runtimes) if runtimes else None,
                "latest_run_id": latest_run.get("run_id"),
                "latest_summary_path": latest_run.get("_summary_path"),
                "latest_status": latest_metrics.get("status"),
                "latest_feasible": latest_metrics.get("feasible"),
                "latest_created_at": latest_run.get("created_at"),
            }
        )

    comparisons = []
    for comparison in comparison_map.values():
        comparison["strategies"].sort(key=_strategy_summary_sort_key)
        comparisons.append(comparison)
    comparisons.sort(key=lambda item: (item["benchmark_group"], item["benchmark_id"], item["tier"]))
    return {
        "schema_version": GENERATED_SCHEMA_VERSION,
        "generated_at": generated_at or _latest_created_at(runs),
        "comparisons": comparisons,
    }


def build_runtime_quality(
    runs: list[dict[str, Any]],
    *,
    results_root: str | Path = DEFAULT_RESULTS_ROOT,
    generated_at: str | None = None,
) -> dict[str, Any]:
    points = []
    for run in runs:
        metrics = _metrics(run)
        optagent = _optagent(run)
        points.append(
            {
                "run_id": run.get("run_id"),
                "summary_path": run.get("_summary_path"),
                "benchmark_group": run.get("benchmark_group"),
                "benchmark_id": run.get("benchmark_id"),
                "family": run.get("family"),
                "tier": run.get("tier"),
                "strategy": run.get("strategy"),
                "strategy_profile": run.get("strategy_profile"),
                "seed": run.get("seed"),
                "created_at": run.get("created_at"),
                "optagent_commit": optagent.get("commit"),
                "optagent_commit_url": optagent.get("commit_url"),
                "status": metrics.get("status"),
                "feasible": metrics.get("feasible"),
                "runtime_ms": _number(metrics.get("runtime_ms")),
                "objective": _number(metrics.get("objective")),
                "best_cost": _number(metrics.get("best_cost")),
                "gap_rel": _number(metrics.get("gap_rel")),
                "time_to_first_feasible_ms": _number(metrics.get("time_to_first_feasible_ms")),
                "time_to_best_ms": _number(metrics.get("time_to_best_ms")),
                "evaluations_per_s": _number(metrics.get("evaluations_per_s")),
                "improvement_per_second": _number(metrics.get("improvement_per_second")),
            }
        )
    points.sort(key=lambda item: (str(item["benchmark_group"]), str(item["benchmark_id"]), str(item["strategy"]), str(item["created_at"]), str(item["run_id"])))
    return {
        "schema_version": GENERATED_SCHEMA_VERSION,
        "generated_at": generated_at or _latest_created_at(runs),
        "points": points,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate static dashboard index and aggregate JSON files.")
    parser.add_argument("--results-root", default=str(DEFAULT_RESULTS_ROOT))
    parser.add_argument("--aggregates-root", default=str(DEFAULT_AGGREGATES_ROOT))
    parser.add_argument("--generated-at")
    parser.add_argument("--check", action="store_true", help="fail if generated files differ from committed files")
    args = parser.parse_args()
    summary = generate_dashboard_data(
        results_root=args.results_root,
        aggregates_root=args.aggregates_root,
        generated_at=args.generated_at,
        check=args.check,
    )
    print(
        json.dumps(
            {
                "schema_version": summary["schema_version"],
                "generated_at": summary["generated_at"],
                "run_count": summary["run_count"],
                "output_paths": sorted(summary["outputs"]),
            },
            indent=2,
            ensure_ascii=True,
            sort_keys=True,
        )
    )
    return 0


def _is_generated_or_schema(path: Path, results_root: Path) -> bool:
    relative = path.relative_to(results_root)
    return relative.as_posix() == "index.json" or relative.parts[:1] == ("schema",)


def _is_run_summary(payload: Any) -> bool:
    return isinstance(payload, dict) and payload.get("schema_version") == 1 and isinstance(payload.get("run_id"), str)


def _validate_unique_run_ids(runs: list[dict[str, Any]]) -> None:
    seen: dict[str, str] = {}
    for run in runs:
        run_id = str(run["run_id"])
        summary_path = str(run["_summary_path"])
        if run_id in seen:
            raise ValueError(f"duplicate run_id {run_id}: {seen[run_id]} and {summary_path}")
        seen[run_id] = summary_path


def _dashboard_path(path: Path, results_root: Path) -> str:
    return "/results/" + path.relative_to(results_root).as_posix()


def _index_run_entry(run: dict[str, Any]) -> dict[str, Any]:
    metrics = _metrics(run)
    return {
        "run_id": run.get("run_id"),
        "benchmark_group": run.get("benchmark_group"),
        "benchmark_id": run.get("benchmark_id"),
        "family": run.get("family"),
        "tier": run.get("tier"),
        "strategy": run.get("strategy"),
        "strategy_profile": run.get("strategy_profile"),
        "seed": run.get("seed"),
        "optagent_commit": _optagent(run).get("commit"),
        "benchmark_commit": _benchmarks(run).get("commit"),
        "created_at": run.get("created_at"),
        "status": metrics.get("status"),
        "feasible": metrics.get("feasible"),
        "summary_path": run.get("_summary_path"),
    }


def _best_run(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not runs:
        raise ValueError("cannot select best run from empty run list")
    return sorted(runs, key=_quality_sort_key)[0]


def _quality_sort_key(run: dict[str, Any]) -> tuple[Any, ...]:
    metrics = _metrics(run)
    feasible = metrics.get("feasible") is True
    success = metrics.get("status") == "success"
    quality = _first_number(
        metrics.get("gap_rel"),
        metrics.get("objective"),
        metrics.get("best_cost"),
    )
    runtime = _number(metrics.get("runtime_ms"))
    return (
        not feasible,
        not success,
        quality is None,
        quality if quality is not None else float("inf"),
        runtime is None,
        runtime if runtime is not None else float("inf"),
        str(run.get("created_at") or ""),
        str(run.get("run_id") or ""),
    )


def _leaderboard_sort_key(entry: dict[str, Any]) -> tuple[Any, ...]:
    feasible = float(entry.get("feasible_rate") or 0.0)
    success = float(entry.get("success_rate") or 0.0)
    quality = _first_number(entry.get("best_gap_rel"), entry.get("best_objective"), entry.get("best_cost"))
    runtime = _number(entry.get("best_runtime_ms"))
    return (
        -feasible,
        -success,
        quality is None,
        quality if quality is not None else float("inf"),
        runtime is None,
        runtime if runtime is not None else float("inf"),
        str(entry.get("strategy") or ""),
    )


def _strategy_summary_sort_key(entry: dict[str, Any]) -> tuple[Any, ...]:
    feasible = float(entry.get("feasible_rate") or 0.0)
    success = float(entry.get("success_rate") or 0.0)
    quality = _first_number(entry.get("best_gap_rel"), entry.get("best_objective"), entry.get("best_cost"))
    return (
        -feasible,
        -success,
        quality is None,
        quality if quality is not None else float("inf"),
        str(entry.get("strategy") or ""),
    )


def _run_sort_key(run: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(run.get("benchmark_group") or ""),
        str(run.get("benchmark_id") or ""),
        str(run.get("strategy") or ""),
        str(run.get("created_at") or ""),
        str(run.get("run_id") or ""),
    )


def _latest_created_at(runs: list[dict[str, Any]]) -> str:
    timestamps = [str(run.get("created_at")) for run in runs if run.get("created_at")]
    if timestamps:
        return max(timestamps)
    return datetime.fromtimestamp(0, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _metrics(run: dict[str, Any]) -> dict[str, Any]:
    metrics = run.get("metrics")
    return metrics if isinstance(metrics, dict) else {}


def _optagent(run: dict[str, Any]) -> dict[str, Any]:
    optagent = run.get("optagent")
    return optagent if isinstance(optagent, dict) else {}


def _benchmarks(run: dict[str, Any]) -> dict[str, Any]:
    benchmarks = run.get("benchmarks")
    return benchmarks if isinstance(benchmarks, dict) else {}


def _rate(runs: list[dict[str, Any]], predicate: Any) -> float:
    if not runs:
        return 0.0
    return sum(1 for run in runs if predicate(run)) / len(runs)


def _number(value: Any) -> float | int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    return None


def _first_number(*values: Any) -> float | int | None:
    for value in values:
        number = _number(value)
        if number is not None:
            return number
    return None


def _check_outputs(outputs: dict[Path, Any]) -> list[Path]:
    mismatches: list[Path] = []
    for path, payload in outputs.items():
        expected = json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n"
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            mismatches.append(path)
    return mismatches


if __name__ == "__main__":
    raise SystemExit(main())
