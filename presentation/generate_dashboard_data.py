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
    aggregates["strategy-scores.json"] = build_strategy_scores(runs, generated_at=effective_generated_at)
    aggregates["strategy-scores-history.json"] = build_strategy_scores_history(
        runs,
        generated_at=effective_generated_at,
    )

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
                    "moves_attempted": _number(metrics.get("moves_attempted")),
                    "moves_accepted": _number(metrics.get("moves_accepted")),
                    "moves_improved": _number(metrics.get("moves_improved")),
                    "trace_entry_count": _number(metrics.get("trace_entry_count")),
                    "restarts": _number(metrics.get("restarts")),
                    "unimproved_iterations": _number(metrics.get("unimproved_iterations")),
                    "diversity_at_termination": _number(metrics.get("diversity_at_termination")),
                    "operator_weight_updates": _number(metrics.get("operator_weight_updates")),
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
                "moves_attempted": _number(metrics.get("moves_attempted")),
                "moves_accepted": _number(metrics.get("moves_accepted")),
                "moves_improved": _number(metrics.get("moves_improved")),
                "trace_entry_count": _number(metrics.get("trace_entry_count")),
                "restarts": _number(metrics.get("restarts")),
                "unimproved_iterations": _number(metrics.get("unimproved_iterations")),
                "diversity_at_termination": _number(metrics.get("diversity_at_termination")),
                "operator_weight_updates": _number(metrics.get("operator_weight_updates")),
            }
        )
    points.sort(key=lambda item: (str(item["benchmark_group"]), str(item["benchmark_id"]), str(item["strategy"]), str(item["created_at"]), str(item["run_id"])))
    return {
        "schema_version": GENERATED_SCHEMA_VERSION,
        "generated_at": generated_at or _latest_created_at(runs),
        "points": points,
    }


def build_strategy_scores(
    runs: list[dict[str, Any]],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": GENERATED_SCHEMA_VERSION,
        "generated_at": generated_at or _latest_created_at(runs),
        "optagent_commit": _latest_optagent_commit(runs),
        "config": _strategy_score_config(),
        "scores": _build_strategy_score_entries(runs),
    }


def build_strategy_scores_history(
    runs: list[dict[str, Any]],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    by_commit: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        optagent = _optagent(run)
        commit = str(optagent.get("commit") or "unknown")
        created_at = str(run.get("created_at") or "")
        by_commit[(created_at, commit)].append(run)

    entries = []
    for (created_at, commit), commit_runs in sorted(by_commit.items(), reverse=True):
        commit_url = ""
        for run in commit_runs:
            candidate = _optagent(run).get("commit_url")
            if candidate:
                commit_url = str(candidate)
                break
        entries.append(
            {
                "optagent_commit": commit,
                "optagent_commit_url": commit_url,
                "created_at": created_at,
                "scores": _build_strategy_score_entries(commit_runs),
            }
        )
    return {
        "schema_version": GENERATED_SCHEMA_VERSION,
        "generated_at": generated_at or _latest_created_at(runs),
        "entries": entries,
    }


def build_dataset_manifest(
    runs: list[dict[str, Any]],
    *,
    dataset_id: str,
    generated_at: str | None = None,
    source_run_dir: str | None = None,
) -> dict[str, Any]:
    effective_generated_at = generated_at or _latest_created_at(runs)
    optagent = _optagent(max(runs, key=_run_sort_key)) if runs else {}
    benchmarks = _benchmarks(max(runs, key=_run_sort_key)) if runs else {}
    environments = [_environment(run) for run in runs]
    by_strategy: dict[str, float] = defaultdict(float)
    by_strategy_runs: dict[str, int] = defaultdict(int)
    cpu_time_values: list[Any] = []
    peak_rss_values: list[Any] = []
    for run in runs:
        strategy = str(run.get("strategy") or "unknown")
        metrics = _metrics(run)
        runtime_ms = _number(metrics.get("runtime_ms"))
        if runtime_ms is not None:
            by_strategy[strategy] += float(runtime_ms)
        by_strategy_runs[strategy] += 1
        cpu_time_values.append(metrics.get("cpu_time_s"))
        peak_rss_values.append(metrics.get("peak_rss_bytes"))
    return {
        "schema_version": GENERATED_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "label": dataset_id,
        "created_at": effective_generated_at,
        "generated_at": effective_generated_at,
        "source_run_dir": source_run_dir,
        "paths": {
            "root": f"/data/{dataset_id}",
            "results": f"/data/{dataset_id}/results",
            "aggregates": f"/data/{dataset_id}/aggregates",
        },
        "counts": {
            "runs": len(runs),
            "strategies": len({run.get("strategy") for run in runs}),
            "benchmark_groups": len({run.get("benchmark_group") for run in runs}),
            "instances": len({run.get("benchmark_id") for run in runs}),
        },
        "runtime": {
            "total_ms": sum(by_strategy.values()),
            "by_strategy_ms": dict(sorted(by_strategy.items())),
            "run_count_by_strategy": dict(sorted(by_strategy_runs.items())),
            "cpu_time_s": _sum_numbers(cpu_time_values),
            "peak_rss_bytes": _max_number(peak_rss_values),
        },
        "resources": _resource_summary(runs, environments),
        "compute_parameters": _compute_parameter_summary(runs),
        "commits": {
            "optagent": optagent.get("commit") or "unknown",
            "optagent_url": optagent.get("commit_url") or "",
            "benchmarks": benchmarks.get("commit") or "unknown",
            "benchmarks_url": benchmarks.get("commit_url") or "",
        },
        "environment": _environment_summary(environments),
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


def _latest_optagent_commit(runs: list[dict[str, Any]]) -> str:
    if not runs:
        return "unknown"
    latest = max(runs, key=_run_sort_key)
    return str(_optagent(latest).get("commit") or "unknown")


def _strategy_score_config() -> dict[str, Any]:
    return {
        "weights": {
            "quality": 0.45,
            "anytime": 0.15,
            "efficiency": 0.2,
            "stability": 0.1,
            "dynamics": 0.1,
        },
        "thresholds": {
            "source": "benchmark dashboard aggregate",
            "note": "Generated by benchmarks.presentation.generate_dashboard_data from immutable run summaries.",
        },
    }


def _build_strategy_score_entries(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_strategy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_strategy_group: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        strategy = str(run.get("strategy") or "unknown")
        group = str(run.get("benchmark_group") or "unknown")
        by_strategy[strategy].append(run)
        by_strategy_group[(strategy, group)].append(run)

    entries = []
    for strategy in sorted(by_strategy):
        entries.append(_strategy_score_entry(strategy, "all", by_strategy[strategy]))
        for (entry_strategy, group), group_runs in sorted(by_strategy_group.items()):
            if entry_strategy == strategy:
                entries.append(_strategy_score_entry(strategy, group, group_runs))
    return entries


def _strategy_score_entry(strategy: str, benchmark_group: str, runs: list[dict[str, Any]]) -> dict[str, Any]:
    run_count = len(runs)
    feasible_count = sum(1 for run in runs if _metrics(run).get("feasible") is True)
    success_count = sum(1 for run in runs if _metrics(run).get("status") == "success")
    feasible_rate = feasible_count / run_count if run_count else 0.0
    success_rate = success_count / run_count if run_count else 0.0
    mean_gap = _mean(
        [_number(_metrics(run).get("gap_rel")) for run in runs],
    )
    mean_runtime_ms = _mean(
        [_number(_metrics(run).get("runtime_ms")) for run in runs],
    )
    quality = _quality_score(feasible_rate, mean_gap)
    efficiency = _runtime_score(mean_runtime_ms)
    stability = _clamp(success_rate * 100.0) if run_count >= 2 else -1.0
    dynamics = _dynamics_score(runs)
    anytime = quality if efficiency < 0 else _clamp(quality * 0.65 + efficiency * 0.35)
    dimensions = {
        "quality": quality,
        "anytime": anytime,
        "efficiency": efficiency,
        "stability": stability,
        "dynamics": dynamics,
    }
    return {
        "strategy": strategy,
        "benchmark_group": benchmark_group,
        "composite": _composite_score(dimensions),
        "dimensions": dimensions,
        "run_count": run_count,
        "seed_count": len({run.get("seed") for run in runs}),
        "instance_count": len({run.get("benchmark_id") for run in runs}),
        "instances": [_instance_score(run) for run in runs],
    }


def _instance_score(run: dict[str, Any]) -> dict[str, Any]:
    metrics = _metrics(run)
    objective = _number(metrics.get("objective"))
    gap_rel = _number(metrics.get("gap_rel"))
    reference_cost = 0.0
    if objective is not None and gap_rel is not None:
        reference_cost = float(objective) / (1.0 + max(0.0, float(gap_rel)))
    quality = _quality_score(1.0 if metrics.get("feasible") is True else 0.0, gap_rel)
    time_to_best_ms = _number(metrics.get("time_to_best_ms"))
    return {
        "benchmark_id": run.get("benchmark_id"),
        "composite": quality,
        "quality": quality,
        "anytime": quality if time_to_best_ms is None else _runtime_score(time_to_best_ms),
        "gap_rel": gap_rel,
        "objective": objective,
        "reference_cost": reference_cost,
        "incumbent_trace_path": None,
        "feasible": metrics.get("feasible"),
        "run_id": run.get("run_id"),
        "runtime_ms": _number(metrics.get("runtime_ms")),
        "time_to_first_feasible_ms": _number(metrics.get("time_to_first_feasible_ms")),
        "time_to_best_ms": _number(metrics.get("time_to_best_ms")),
        "evaluations_per_s": _number(metrics.get("evaluations_per_s")),
        "cpu_time_s": _number(metrics.get("cpu_time_s")),
        "peak_rss_bytes": _number(metrics.get("peak_rss_bytes")),
        "seed": run.get("seed"),
        "status": metrics.get("status"),
        "strategy_profile": run.get("strategy_profile"),
        "family": run.get("family"),
        "tier": run.get("tier"),
        "case_size": _case_size(run),
        "budget": _budget(run),
        "strategy_config": _strategy_config(run),
        "summary_path": run.get("_summary_path"),
    }


def _quality_score(feasible_rate: float, mean_gap: float | int | None) -> float:
    if feasible_rate <= 0:
        return 0.0
    if mean_gap is None:
        return _clamp(feasible_rate * 100.0)
    return _clamp(feasible_rate * 100.0 / (1.0 + max(0.0, float(mean_gap))))


def _runtime_score(mean_runtime_ms: float | int | None) -> float:
    if mean_runtime_ms is None:
        return -1.0
    import math

    return _clamp(100.0 - math.log10(max(1.0, float(mean_runtime_ms)) + 1.0) * 18.0)


def _dynamics_score(runs: list[dict[str, Any]]) -> float:
    values = [_point_dynamics_score(run) for run in runs]
    values = [value for value in values if value is not None]
    return _mean(values) if values else -1.0


def _point_dynamics_score(run: dict[str, Any]) -> float | None:
    metrics = _metrics(run)
    attempted = _positive_number(metrics.get("moves_attempted"))
    accepted = _non_negative_number(metrics.get("moves_accepted"))
    improved = _non_negative_number(metrics.get("moves_improved"))
    trace_entries = _non_negative_number(metrics.get("trace_entry_count"))
    diversity = _non_negative_number(metrics.get("diversity_at_termination"))
    parts: list[tuple[float, float, bool]] = []
    if attempted is not None and accepted is not None:
        parts.append((_healthy_acceptance_score(float(accepted) / float(attempted)), 0.3, True))
    if attempted is not None and improved is not None:
        parts.append((_improvement_activity_score(float(improved), float(attempted)), 0.4, True))
    if trace_entries is not None:
        parts.append((_clamp((float(trace_entries) / 8.0) * 100.0), 0.15, False))
    if diversity is not None:
        parts.append((_diversity_score(float(diversity)), 0.15, True))
    response = _stagnation_response_score(run)
    if response is not None:
        parts.append((response, 0.1, True))
    if not any(part[2] for part in parts):
        return None
    total_weight = sum(part[1] for part in parts)
    if total_weight <= 0:
        return None
    return sum(part[0] * part[1] for part in parts) / total_weight


def _healthy_acceptance_score(ratio: float) -> float:
    if ratio <= 0 or ratio >= 1:
        return 0.0
    target = 0.35
    if ratio <= target:
        return _clamp((ratio / target) * 100.0)
    return _clamp((1.0 - (ratio - target) / (1.0 - target)) * 100.0)


def _improvement_activity_score(improved: float, attempted: float) -> float:
    if improved <= 0 or attempted <= 0:
        return 0.0
    import math

    return _clamp((math.log10(improved + 1.0) / math.log10(attempted + 1.0)) * 100.0)


def _diversity_score(value: float) -> float:
    if value <= 0:
        return 0.0
    if value <= 1:
        return _clamp(value * 100.0)
    import math

    return _clamp(math.log10(value + 1.0) * 25.0)


def _stagnation_response_score(run: dict[str, Any]) -> float | None:
    metrics = _metrics(run)
    attempted = _positive_number(metrics.get("moves_attempted"))
    unimproved = _non_negative_number(metrics.get("unimproved_iterations"))
    restarts = _non_negative_number(metrics.get("restarts"))
    scores = []
    if attempted is not None and unimproved is not None:
        scores.append(_clamp((1.0 - min(float(unimproved) / float(attempted), 1.0)) * 100.0))
    if restarts is not None and restarts > 0:
        scores.append(_clamp((min(float(restarts), 3.0) / 3.0) * 100.0))
    return _mean(scores) if scores else None


def _composite_score(dimensions: dict[str, float]) -> float:
    weights = {
        "quality": 0.45,
        "anytime": 0.15,
        "efficiency": 0.2,
        "stability": 0.1,
        "dynamics": 0.1,
    }
    weighted = 0.0
    total_weight = 0.0
    for key, weight in weights.items():
        value = dimensions[key]
        if value >= 0:
            weighted += value * weight
            total_weight += weight
    return weighted / total_weight if total_weight > 0 else 0.0


def _mean(values: list[Any]) -> float | None:
    numbers = [float(value) for value in values if _number(value) is not None]
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def _non_negative_number(value: Any) -> float | int | None:
    number = _number(value)
    return number if number is not None and number >= 0 else None


def _positive_number(value: Any) -> float | int | None:
    number = _number(value)
    return number if number is not None and number > 0 else None


def _clamp(value: float) -> float:
    return min(100.0, max(0.0, value))


def _sum_numbers(values: list[Any]) -> float | None:
    numbers = [float(value) for value in values if _number(value) is not None]
    return sum(numbers) if numbers else None


def _max_number(values: list[Any]) -> float | int | None:
    numbers = [_number(value) for value in values]
    numbers = [value for value in numbers if value is not None]
    return max(numbers) if numbers else None


def _case_size(run: dict[str, Any]) -> dict[str, Any]:
    case_size = run.get("case_size")
    return case_size if isinstance(case_size, dict) else {}


def _budget(run: dict[str, Any]) -> dict[str, Any]:
    budget = run.get("budget")
    return budget if isinstance(budget, dict) else {}


def _strategy_config(run: dict[str, Any]) -> dict[str, Any]:
    config = run.get("strategy_config")
    return config if isinstance(config, dict) else {}


def _resource_summary(runs: list[dict[str, Any]], environments: list[dict[str, Any]]) -> dict[str, Any]:
    environment = _environment_summary(environments)
    metrics = [_metrics(run) for run in runs]
    return {
        "cpu_count": _first_environment_number(environment.get("cpu_count")),
        "processor": environment.get("processor"),
        "machine": environment.get("machine"),
        "memory_total_bytes": _first_environment_number(environment.get("memory_total_bytes")),
        "cpu_time_s": _sum_numbers([metric.get("cpu_time_s") for metric in metrics]),
        "peak_rss_bytes": _max_number([metric.get("peak_rss_bytes") for metric in metrics]),
        "thread_counts": _sorted_numeric_values([_budget(run).get("thread_count") or _strategy_config(run).get("parallel_workers") for run in runs]),
    }


def _compute_parameter_summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "tiers": sorted({str(run.get("tier")) for run in runs if run.get("tier")}),
        "families": sorted({str(run.get("family")) for run in runs if run.get("family")}),
        "budget_profiles": sorted({str(_budget(run).get("profile")) for run in runs if _budget(run).get("profile")}),
        "time_limit_s": _numeric_range([_budget(run).get("time_limit_s") for run in runs]),
        "max_iterations": _numeric_range([_budget(run).get("max_iterations") for run in runs]),
        "population_size": _numeric_range([_budget(run).get("population_size") for run in runs]),
        "trace_limit": _numeric_range([_budget(run).get("trace_limit") for run in runs]),
        "thread_count": _numeric_range([_budget(run).get("thread_count") for run in runs]),
    }


def _numeric_range(values: list[Any]) -> dict[str, float | int] | None:
    numbers = [_number(value) for value in values]
    numbers = [value for value in numbers if value is not None]
    if not numbers:
        return None
    return {"min": min(numbers), "max": max(numbers)}


def _sorted_numeric_values(values: list[Any]) -> list[float | int]:
    numbers = {_number(value) for value in values if _number(value) is not None}
    return sorted(numbers)


def _first_environment_number(value: Any) -> float | int | None:
    if isinstance(value, list):
        for item in value:
            number = _number(item)
            if number is None:
                number = _parse_number_text(item)
            if number is not None:
                return number
        return None
    return _number(value) or _parse_number_text(value)


def _parse_number_text(value: Any) -> float | int | None:
    if not isinstance(value, str):
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return int(number) if number.is_integer() else number


def _metrics(run: dict[str, Any]) -> dict[str, Any]:
    metrics = run.get("metrics")
    return metrics if isinstance(metrics, dict) else {}


def _optagent(run: dict[str, Any]) -> dict[str, Any]:
    optagent = run.get("optagent")
    return optagent if isinstance(optagent, dict) else {}


def _benchmarks(run: dict[str, Any]) -> dict[str, Any]:
    benchmarks = run.get("benchmarks")
    return benchmarks if isinstance(benchmarks, dict) else {}


def _environment(run: dict[str, Any]) -> dict[str, Any]:
    environment = run.get("environment")
    return environment if isinstance(environment, dict) else {}


def _environment_summary(environments: list[dict[str, Any]]) -> dict[str, Any]:
    if not environments:
        return {}
    keys = sorted({key for environment in environments for key in environment})
    summary: dict[str, Any] = {}
    for key in keys:
        values = sorted({str(environment.get(key)) for environment in environments if environment.get(key) is not None})
        if len(values) == 1:
            summary[key] = values[0]
        elif values:
            summary[key] = values
    return summary


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
