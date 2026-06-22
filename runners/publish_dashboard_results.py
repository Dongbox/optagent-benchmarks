from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import sys
from typing import Any

from benchmarks.runners.common import write_json
from benchmarks.runners.generate_dashboard_data import (
    DEFAULT_AGGREGATES_ROOT,
    DEFAULT_RESULTS_ROOT,
    generate_dashboard_data,
)


FAMILY_GROUPS = {
    "interval_job_shop": "scheduling",
    "cumulative_resource_scheduling": "scheduling",
    "sequence_blackbox_tsp": "routing",
    "sequence_quadratic_assignment": "assignment",
    "exact_linear_mip": "exact-regression",
}


def publish_dashboard_results(
    run_dir: str | Path,
    *,
    results_root: str | Path = DEFAULT_RESULTS_ROOT,
    aggregates_root: str | Path = DEFAULT_AGGREGATES_ROOT,
    optagent_version: str,
    optagent_commit: str,
    optagent_commit_url: str,
    optagent_wheel_sha256: str,
    benchmarks_commit: str,
    benchmarks_commit_url: str,
    created_at: str | None = None,
    runner: str = "github-actions",
    overwrite: bool = False,
    regenerate: bool = True,
) -> dict[str, Any]:
    run_path = Path(run_dir)
    rows = _load_rows(run_path)
    if not rows:
        raise ValueError(f"no benchmark rows found in {run_path / 'results.jsonl'}")

    effective_created_at = created_at or _utc_created_at()
    results_path = Path(results_root)
    written: list[str] = []
    for row in rows:
        summary = _summary_from_row(
            row,
            optagent_version=optagent_version,
            optagent_commit=optagent_commit,
            optagent_commit_url=optagent_commit_url,
            optagent_wheel_sha256=optagent_wheel_sha256,
            benchmarks_commit=benchmarks_commit,
            benchmarks_commit_url=benchmarks_commit_url,
            created_at=effective_created_at,
            runner=runner,
        )
        summary_path = _summary_path(results_path, summary)
        if summary_path.exists() and not overwrite:
            raise FileExistsError(f"dashboard run summary already exists: {summary_path}")
        metrics_path = summary_path.with_suffix("") / "metrics.json"
        summary["artifacts"] = {"metrics": _repo_relative(metrics_path, results_path)}
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(metrics_path, summary["metrics"])
        write_json(summary_path, summary)
        written.append(str(summary_path))

    generated = None
    if regenerate:
        generated = generate_dashboard_data(
            results_root=results_path,
            aggregates_root=aggregates_root,
            generated_at=effective_created_at,
        )

    return {
        "schema_version": 1,
        "created_at": effective_created_at,
        "published_run_count": len(written),
        "published_paths": written,
        "generated_run_count": generated["run_count"] if generated is not None else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish benchmark suite rows as dashboard run summary JSON.")
    parser.add_argument("run_dir", help="Benchmark suite run directory containing results.jsonl.")
    parser.add_argument("--results-root", default=str(DEFAULT_RESULTS_ROOT))
    parser.add_argument("--aggregates-root", default=str(DEFAULT_AGGREGATES_ROOT))
    parser.add_argument("--optagent-version", required=True)
    parser.add_argument("--optagent-commit", required=True)
    parser.add_argument("--optagent-commit-url", required=True)
    parser.add_argument("--optagent-wheel-sha256", required=True)
    parser.add_argument("--benchmarks-commit", required=True)
    parser.add_argument("--benchmarks-commit-url", required=True)
    parser.add_argument("--created-at")
    parser.add_argument("--runner", default="github-actions")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--no-regenerate", action="store_true")
    args = parser.parse_args()

    summary = publish_dashboard_results(
        args.run_dir,
        results_root=args.results_root,
        aggregates_root=args.aggregates_root,
        optagent_version=args.optagent_version,
        optagent_commit=args.optagent_commit,
        optagent_commit_url=args.optagent_commit_url,
        optagent_wheel_sha256=args.optagent_wheel_sha256,
        benchmarks_commit=args.benchmarks_commit,
        benchmarks_commit_url=args.benchmarks_commit_url,
        created_at=args.created_at,
        runner=args.runner,
        overwrite=args.overwrite,
        regenerate=not args.no_regenerate,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True))
    return 0


def _load_rows(run_dir: Path) -> list[dict[str, Any]]:
    results_jsonl = run_dir / "results.jsonl"
    if not results_jsonl.exists():
        raise FileNotFoundError(f"benchmark results not found: {results_jsonl}")
    rows: list[dict[str, Any]] = []
    for line in results_jsonl.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _summary_from_row(
    row: dict[str, Any],
    *,
    optagent_version: str,
    optagent_commit: str,
    optagent_commit_url: str,
    optagent_wheel_sha256: str,
    benchmarks_commit: str,
    benchmarks_commit_url: str,
    created_at: str,
    runner: str,
) -> dict[str, Any]:
    family = str(row.get("family") or "unknown")
    strategy = str(row.get("strategy") or "unknown")
    benchmark_group = FAMILY_GROUPS.get(family, _slug(family))
    run_id = _run_id(
        group=benchmark_group,
        strategy=strategy,
        benchmark_id=str(row.get("benchmark_id") or "unknown"),
        created_at=created_at,
        optagent_commit=optagent_commit,
    )
    return {
        "schema_version": 1,
        "run_id": run_id,
        "benchmark_group": benchmark_group,
        "benchmark_id": str(row.get("benchmark_id") or "unknown"),
        "family": family,
        "tier": str(row.get("tier") or "unknown"),
        "strategy": strategy,
        "strategy_profile": str(row.get("strategy_profile") or f"{strategy}_{family}_v1"),
        "strategy_config": _strategy_config(row),
        "seed": int(row.get("seed") or _effective_budget(row).get("seed") or 0),
        "optagent": {
            "version": optagent_version,
            "commit": optagent_commit,
            "commit_url": optagent_commit_url,
            "wheel_sha256": optagent_wheel_sha256,
        },
        "benchmarks": {
            "commit": benchmarks_commit,
            "commit_url": benchmarks_commit_url,
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "runner": runner,
        },
        "metrics": _metrics(row),
        "artifacts": {},
        "created_at": created_at,
    }


def _metrics(row: dict[str, Any]) -> dict[str, Any]:
    runtime_ms = _ms(row.get("runtime_s"), row.get("elapsed_seconds"))
    feasible = row.get("feasible") is True
    status = str(row.get("status") or "")
    if status == "feasible" and feasible:
        status = "success"
    elif status in {"", "non_feasible"} and not feasible:
        status = "non_feasible"
    metrics = {
        "objective": _number(row.get("objective")),
        "best_cost": _number(row.get("best_cost"), row.get("objective")),
        "reference_cost": _number(row.get("reference_cost"), row.get("reference_objective")),
        "gap_rel": _number(row.get("gap_rel")),
        "runtime_ms": runtime_ms,
        "feasible": feasible,
        "status": status,
        "time_to_first_feasible_ms": _ms(row.get("time_to_first_feasible_seconds")),
        "time_to_best_ms": _ms(row.get("time_to_best_seconds")),
        "evaluations_per_s": _number(row.get("evaluations_per_s")),
        "improvement_per_second": _number(row.get("improvement_per_second")),
    }
    error = row.get("error")
    if isinstance(error, dict):
        metrics["error_type"] = str(error.get("type") or "BenchmarkError")
        metrics["error_message"] = str(error.get("message") or "")
    return metrics


def _strategy_config(row: dict[str, Any]) -> dict[str, Any]:
    config = row.get("strategy_config")
    if isinstance(config, dict):
        return config
    budget = _effective_budget(row)
    return {key: budget[key] for key in sorted(budget) if key in {"max_iterations", "population_size", "time_limit_s", "trace_limit", "thread_count"}}


def _effective_budget(row: dict[str, Any]) -> dict[str, Any]:
    budget = row.get("effective_budget")
    return budget if isinstance(budget, dict) else {}


def _summary_path(results_root: Path, summary: dict[str, Any]) -> Path:
    created = _parse_created_at(str(summary["created_at"]))
    return (
        results_root
        / str(summary["benchmark_group"])
        / str(summary["strategy"])
        / f"{created.year:04d}"
        / f"{created.month:02d}"
        / f"{summary['run_id']}.json"
    )


def _repo_relative(path: Path, results_root: Path) -> str:
    return "results/" + path.relative_to(results_root).as_posix()


def _run_id(*, group: str, strategy: str, benchmark_id: str, created_at: str, optagent_commit: str) -> str:
    created = _parse_created_at(created_at)
    short_commit = _short_commit(optagent_commit)
    identity_hash = hashlib.sha1(f"{group}/{strategy}/{benchmark_id}/{created_at}/{short_commit}".encode("utf-8")).hexdigest()[:7]
    return "-".join(
        [
            _slug(group),
            _slug(strategy),
            _slug(benchmark_id),
            created.strftime("%Y%m%d"),
            created.strftime("%H%M%S"),
            short_commit,
            identity_hash,
        ]
    )


def _parse_created_at(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).astimezone(timezone.utc)


def _utc_created_at() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short_commit(value: str) -> str:
    match = re.search(r"[a-fA-F0-9]{7,40}", value)
    return (match.group(0) if match else hashlib.sha1(value.encode("utf-8")).hexdigest())[:7].lower()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown"


def _number(*values: Any) -> float | int | None:
    for value in values:
        if isinstance(value, bool) or value is None:
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return value
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _ms(*values: Any) -> int:
    value = _number(*values)
    if value is None:
        return 0
    return max(0, int(round(float(value) * 1000)))


if __name__ == "__main__":
    raise SystemExit(main())
