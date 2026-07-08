from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.presentation.generate_dashboard_data import (
    build_dataset_manifest,
    build_runtime_quality,
    build_strategy_scores,
    build_strategy_scores_history,
)


def test_strategy_scores_are_generated_by_benchmark_aggregates() -> None:
    runs = [
        _run("run-ga-a", "ga", "routing", "case-a", gap=0.1, runtime_ms=100, accepted=3, improved=1),
        _run("run-ga-b", "ga", "routing", "case-b", gap=0.0, runtime_ms=200, accepted=2, improved=1),
        _run("run-alns-a", "alns", "routing", "case-a", gap=None, runtime_ms=150, feasible=False, accepted=0, improved=0),
    ]

    scores = build_strategy_scores(runs, generated_at="2026-07-07T00:00:00+00:00")
    history = build_strategy_scores_history(runs, generated_at="2026-07-07T00:00:00+00:00")
    runtime = build_runtime_quality(runs, generated_at="2026-07-07T00:00:00+00:00")

    assert scores["schema_version"] == 1
    assert scores["optagent_commit"] == "optagent-test"
    assert scores["config"]["thresholds"]["source"] == "benchmark dashboard aggregate"
    ga_global = next(entry for entry in scores["scores"] if entry["strategy"] == "ga" and entry["benchmark_group"] == "all")
    ga_group = next(entry for entry in scores["scores"] if entry["strategy"] == "ga" and entry["benchmark_group"] == "routing")
    assert ga_global["run_count"] == 2
    assert ga_group["instance_count"] == 2
    assert ga_global["dimensions"]["quality"] > 90
    assert ga_global["dimensions"]["dynamics"] >= 0

    assert len(history["entries"]) == 1
    assert history["entries"][0]["optagent_commit"] == "optagent-test"
    assert history["entries"][0]["scores"] == scores["scores"]

    first_point = next(point for point in runtime["points"] if point["run_id"] == "run-ga-a")
    assert first_point["moves_attempted"] == 5
    assert first_point["moves_accepted"] == 3
    assert first_point["moves_improved"] == 1
    assert first_point["trace_entry_count"] == 4


def test_dataset_manifest_summarizes_run_metadata_for_dashboard_selection() -> None:
    runs = [
        _run("run-ga-a", "ga", "routing", "case-a", gap=0.1, runtime_ms=100, accepted=3, improved=1),
        _run("run-ga-b", "ga", "routing", "case-b", gap=0.0, runtime_ms=200, accepted=2, improved=1),
        _run("run-alns-a", "alns", "routing", "case-a", gap=None, runtime_ms=150, feasible=False, accepted=0, improved=0),
    ]
    for run in runs:
        run["benchmarks"] = {
            "commit": "benchmarks-test",
            "commit_url": "https://example.invalid/benchmarks-test",
        }
        run["environment"] = {
            "cpu_count": 8,
            "machine": "arm64",
            "memory_total_bytes": 34359738368,
            "runner": "ci-bench",
            "platform": "darwin-arm64",
            "processor": "test-cpu",
            "python": "3.11",
        }
        run["budget"] = {
            "max_iterations": 5,
            "population_size": 8,
            "profile": "smoke-budget",
            "thread_count": 2,
            "time_limit_s": 2.0,
            "trace_limit": 4,
        }
        run["case_size"] = {"nodes": 10}

    manifest = build_dataset_manifest(
        runs,
        dataset_id="20260707-000000",
        generated_at="2026-07-07T00:00:00+00:00",
        source_run_dir="/tmp/suite-run",
    )

    assert manifest["dataset_id"] == "20260707-000000"
    assert manifest["paths"]["root"] == "/data/20260707-000000"
    assert manifest["counts"] == {
        "runs": 3,
        "strategies": 2,
        "benchmark_groups": 1,
        "instances": 2,
    }
    assert manifest["runtime"]["total_ms"] == 450.0
    assert manifest["runtime"]["by_strategy_ms"] == {"alns": 150.0, "ga": 300.0}
    assert manifest["runtime"]["run_count_by_strategy"] == {"alns": 1, "ga": 2}
    assert manifest["resources"]["cpu_count"] == 8
    assert manifest["resources"]["memory_total_bytes"] == 34359738368
    assert manifest["resources"]["thread_counts"] == [2]
    assert manifest["compute_parameters"]["budget_profiles"] == ["smoke-budget"]
    assert manifest["compute_parameters"]["time_limit_s"] == {"min": 2.0, "max": 2.0}
    assert manifest["commits"]["optagent"] == "optagent-test"
    assert manifest["commits"]["benchmarks"] == "benchmarks-test"
    assert manifest["environment"]["runner"] == "ci-bench"


def _run(
    run_id: str,
    strategy: str,
    group: str,
    benchmark_id: str,
    *,
    gap: float | None,
    runtime_ms: int,
    feasible: bool = True,
    accepted: int,
    improved: int,
) -> dict:
    return {
        "schema_version": 1,
        "run_id": run_id,
        "benchmark_group": group,
        "benchmark_id": benchmark_id,
        "family": "sequence_blackbox_tsp",
        "tier": "smoke",
        "strategy": strategy,
        "strategy_profile": strategy,
        "seed": 11,
        "optagent": {
            "commit": "optagent-test",
            "commit_url": "https://example.invalid/optagent-test",
        },
        "created_at": "2026-07-07T00:00:00+00:00",
        "metrics": {
            "objective": 100.0 if feasible else None,
            "best_cost": 100.0 if feasible else None,
            "gap_rel": gap,
            "runtime_ms": runtime_ms,
            "feasible": feasible,
            "status": "success" if feasible else "non_feasible",
            "time_to_best_ms": runtime_ms // 2,
            "moves_attempted": 5,
            "moves_accepted": accepted,
            "moves_improved": improved,
            "trace_entry_count": 4,
            "restarts": 1,
            "unimproved_iterations": 2,
            "diversity_at_termination": 0.5,
            "operator_weight_updates": 5,
        },
        "_summary_path": f"/results/{group}/{strategy}/{run_id}.json",
    }
