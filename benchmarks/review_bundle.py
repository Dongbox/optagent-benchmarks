from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import math
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Mapping, Sequence

from benchmarks.artifact_io import read_json, read_jsonl, sha256_file, write_json, write_jsonl
from benchmarks.telemetry_artifacts import load_published_artifacts


REVIEW_SCHEMA_VERSION = 1
INDEX_JSON = "review-index.json"
OVERVIEW_JSON = "overview.json"
FAMILIES_JSON = "families.json"
ANYTIME_JSON = "anytime.json"
EVIDENCE_JSON = "evidence.json"
RUNS_JSONL = "runs.jsonl"
COMPARISON_JSON = "comparison.json"

CORE_METRICS = {
    "median_reference_gap": ("effectiveness", "median_gap_to_reference", "lower", "gap"),
    "normalized_primal_integral": ("anytime", "mean_normalized_primal_integral", "lower", "gap"),
    "target_hit_ratio": ("anytime", "ecdf_target_hit_ratio", "higher", "ratio"),
    "gap_cv": ("robustness", "gap_cv", "lower", "ratio"),
    "candidate_throughput": ("efficiency", "candidate_throughput_per_s", "higher", "candidates/s"),
}

ANYTIME_CHECKPOINTS = (0.0025, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.5, 1.0)


def publish_review_bundle(
    current_artifact: str | Path,
    output_dir: str | Path,
    *,
    protocol_id: str,
    baseline_artifact: str | Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    source = load_published_artifacts(current_artifact)
    out = Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"review bundle output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    rows = [dict(row) for row in source["rows"]]
    curves = [dict(row) for row in source["curves"]]
    strategies = sorted({str(row.get("strategy") or "unknown") for row in rows})
    _require_single_strategy(strategies, role="current")
    overview = _build_overview(source, rows, strategies, protocol_id)
    families = _build_families(rows, strategies)
    anytime = _build_anytime(rows, curves, strategies)
    evidence = _build_evidence(rows, strategies)
    review_rows = [_review_run(row) for row in rows]

    write_json(out / OVERVIEW_JSON, overview)
    write_json(out / FAMILIES_JSON, families)
    write_json(out / ANYTIME_JSON, anytime)
    write_json(out / EVIDENCE_JSON, evidence)
    write_jsonl(out / RUNS_JSONL, review_rows)
    artifact_names = [OVERVIEW_JSON, FAMILIES_JSON, ANYTIME_JSON, EVIDENCE_JSON, RUNS_JSONL]
    comparison_status = {"available": False, "reason": "baseline_not_packaged"}
    if baseline_artifact is not None:
        baseline = load_published_artifacts(baseline_artifact)
        baseline_rows = [dict(row) for row in baseline["rows"]]
        baseline_strategies = sorted({str(row.get("strategy") or "unknown") for row in baseline_rows})
        _require_single_strategy(baseline_strategies, role="baseline")
        if baseline_strategies != strategies:
            raise ValueError("current and baseline strategy identities differ")
        baseline_overview = _build_overview(baseline, baseline_rows, baseline_strategies, protocol_id)
        baseline_families = _build_families(baseline_rows, baseline_strategies)
        baseline_anytime = _build_anytime(baseline_rows, [dict(row) for row in baseline["curves"]], baseline_strategies)
        comparison = _build_comparison(
            overview,
            rows,
            families,
            anytime,
            baseline_overview,
            baseline_rows,
            baseline_families,
            baseline_anytime,
        )
        write_json(out / COMPARISON_JSON, comparison)
        artifact_names.append(COMPARISON_JSON)
        comparison_status = {
            "available": bool(comparison["compatible"]),
            "reason": "" if comparison["compatible"] else "incompatible_baseline",
        }
    effective_created_at = created_at or datetime.now(timezone.utc).isoformat()
    index = {
        "review_schema_version": REVIEW_SCHEMA_VERSION,
        "kind": "optagent_review_bundle",
        "created_at": effective_created_at,
        "default_mode": "single",
        "comparison": comparison_status,
        "artifacts": {
            name: {
                "path": name,
                "bytes": (out / name).stat().st_size,
                "sha256": sha256_file(out / name),
            }
            for name in artifact_names
        },
    }
    write_json(out / INDEX_JSON, index)
    return {"output_dir": str(out), "index": index}


def load_review_bundle(path: str | Path) -> dict[str, Any]:
    root = Path(path)
    index = read_json(root / INDEX_JSON)
    if index.get("review_schema_version") != REVIEW_SCHEMA_VERSION:
        raise ValueError("unsupported review bundle schema")
    if index.get("kind") != "optagent_review_bundle":
        raise ValueError("unsupported review bundle kind")
    artifacts = dict(index.get("artifacts") or {})
    required = {OVERVIEW_JSON, FAMILIES_JSON, ANYTIME_JSON, EVIDENCE_JSON, RUNS_JSONL}
    allowed = required | {COMPARISON_JSON}
    if not required.issubset(artifacts) or not set(artifacts).issubset(allowed):
        raise ValueError("review bundle does not declare the required artifact set")
    for name, entry in artifacts.items():
        if entry.get("path") != name:
            raise ValueError(f"invalid review bundle artifact path: {name}")
        if sha256_file(root / name) != entry.get("sha256"):
            raise ValueError(f"review bundle checksum mismatch: {name}")
        if (root / name).stat().st_size != entry.get("bytes"):
            raise ValueError(f"review bundle byte count mismatch: {name}")
    bundle = {
        "index": index,
        "overview": read_json(root / OVERVIEW_JSON),
        "families": read_json(root / FAMILIES_JSON),
        "anytime": read_json(root / ANYTIME_JSON),
        "evidence": read_json(root / EVIDENCE_JSON),
        "runs": read_jsonl(root / RUNS_JSONL),
    }
    if COMPARISON_JSON in artifacts:
        bundle["comparison"] = read_json(root / COMPARISON_JSON)
    return bundle


def _build_comparison(
    current_overview: Mapping[str, Any],
    current_rows: Sequence[Mapping[str, Any]],
    current_families: Mapping[str, Any],
    current_anytime: Mapping[str, Any],
    baseline_overview: Mapping[str, Any],
    baseline_rows: Sequence[Mapping[str, Any]],
    baseline_families: Mapping[str, Any],
    baseline_anytime: Mapping[str, Any],
) -> dict[str, Any]:
    reasons = _compatibility_reasons(current_rows, baseline_rows)
    result: dict[str, Any] = {
        "review_schema_version": REVIEW_SCHEMA_VERSION,
        "compatible": not reasons,
        "compatibility_reasons": reasons,
        "baseline": dict(baseline_overview.get("current") or {}),
        "anytime": {
            "current": dict(current_anytime.get("by_strategy") or {}),
            "baseline": dict(baseline_anytime.get("by_strategy") or {}),
        },
        "by_strategy": {},
    }
    if reasons:
        return result
    current_strategy_data = dict(current_overview.get("strategies_data") or {})
    baseline_strategy_data = dict(baseline_overview.get("strategies_data") or {})
    current_family_data = dict(current_families.get("by_strategy") or {})
    baseline_family_data = dict(baseline_families.get("by_strategy") or {})
    by_strategy: dict[str, Any] = {}
    for strategy in sorted(current_strategy_data):
        current_metrics = dict(current_strategy_data[strategy].get("core_metrics") or {})
        baseline_metrics = dict(baseline_strategy_data[strategy].get("core_metrics") or {})
        family_comparisons = _family_comparisons(
            list(current_family_data.get(strategy) or []),
            list(baseline_family_data.get(strategy) or []),
        )
        by_strategy[strategy] = {
            "core_metrics": {
                name: _metric_comparison(current_metrics.get(name), baseline_metrics.get(name)) for name in CORE_METRICS
            },
            "family_comparisons": family_comparisons,
            "evidence": _paired_evidence(current_rows, baseline_rows, strategy),
        }
    result["by_strategy"] = by_strategy
    return result


def _compatibility_reasons(
    current_rows: Sequence[Mapping[str, Any]],
    baseline_rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    current = {_coordinate(row): row for row in current_rows}
    baseline = {_coordinate(row): row for row in baseline_rows}
    reasons: list[str] = []
    if set(current) != set(baseline):
        reasons.append("coordinate_set_mismatch")
        return reasons
    identity_fields = (
        "framework",
        "profile",
        "solver_name",
        "route",
        "dataset",
        "objective_sense",
        "reference_objective",
        "target_objective",
        "time_budget_s",
        "max_iterations",
        "population_size",
        "thread_count",
    )
    mismatches = [
        coordinate
        for coordinate in sorted(current)
        if any(current[coordinate].get(field) != baseline[coordinate].get(field) for field in identity_fields)
    ]
    if mismatches:
        reasons.append(f"experiment_identity_mismatch:{len(mismatches)}")
    return reasons


def _require_single_strategy(strategies: Sequence[str], *, role: str) -> None:
    if len(strategies) != 1:
        raise ValueError(f"{role} telemetry artifact must contain exactly one strategy")


def _coordinate(row: Mapping[str, Any]) -> tuple[str, str, str, Any]:
    return (
        str(row.get("strategy") or "unknown"),
        str(row.get("family") or "unknown"),
        str(row.get("instance_id") or "unknown"),
        row.get("seed"),
    )


def _metric_comparison(current: Any, baseline: Any) -> dict[str, Any]:
    current_entry = dict(current or {})
    baseline_entry = dict(baseline or {})
    current_value = current_entry.get("value")
    baseline_value = baseline_entry.get("value")
    direction = str(current_entry.get("direction") or baseline_entry.get("direction") or "lower")
    if not isinstance(current_value, (int, float)) or not isinstance(baseline_value, (int, float)):
        return {
            "availability": "insufficient_data",
            "current": current_value,
            "baseline": baseline_value,
            "delta": None,
            "direction": direction,
            "change": "unclear",
        }
    delta = float(current_value) - float(baseline_value)
    if abs(delta) <= 1e-12:
        change = "unchanged"
    else:
        improved = delta > 0 if direction == "higher" else delta < 0
        change = "improved" if improved else "regressed"
    return {
        "availability": "available",
        "current": float(current_value),
        "baseline": float(baseline_value),
        "delta": delta,
        "direction": direction,
        "unit": current_entry.get("unit") or baseline_entry.get("unit") or "",
        "change": change,
        "sample_count": current_entry.get("sample_count"),
    }


def _family_comparisons(
    current_rows: Sequence[Mapping[str, Any]],
    baseline_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    current = {str(row.get("family")): row for row in current_rows}
    baseline = {str(row.get("family")): row for row in baseline_rows}
    result: list[dict[str, Any]] = []
    metrics = {
        "median_reference_gap": "lower",
        "target_hit_ratio": "higher",
        "gap_cv": "lower",
        "candidate_throughput": "higher",
    }
    for family in sorted(current):
        result.append(
            {
                "family": family,
                "run_count": current[family].get("run_count"),
                "metrics": {
                    name: _metric_comparison(
                        {"value": current[family].get(name), "direction": direction},
                        {"value": baseline[family].get(name), "direction": direction},
                    )
                    for name, direction in metrics.items()
                },
            }
        )
    return result


def _paired_evidence(
    current_rows: Sequence[Mapping[str, Any]],
    baseline_rows: Sequence[Mapping[str, Any]],
    strategy: str,
) -> dict[str, Any]:
    current = {_coordinate(row): row for row in current_rows if row.get("strategy") == strategy}
    baseline = {_coordinate(row): row for row in baseline_rows if row.get("strategy") == strategy}
    pairs: list[dict[str, Any]] = []
    for coordinate in sorted(current):
        current_gap = current[coordinate].get("gap_to_reference")
        baseline_gap = baseline[coordinate].get("gap_to_reference")
        if not isinstance(current_gap, (int, float)) or not isinstance(baseline_gap, (int, float)):
            continue
        delta = float(current_gap) - float(baseline_gap)
        pairs.append(
            {
                "family": coordinate[1],
                "instance_id": coordinate[2],
                "seed": coordinate[3],
                "current_gap": float(current_gap),
                "baseline_gap": float(baseline_gap),
                "delta": delta,
                "change": "improved" if delta < 0 else "regressed" if delta > 0 else "unchanged",
            }
        )
    return {
        "largest_regressions": sorted(
            (item for item in pairs if item["delta"] > 0),
            key=lambda item: item["delta"],
            reverse=True,
        )[:10],
        "largest_improvements": sorted(
            (item for item in pairs if item["delta"] < 0),
            key=lambda item: item["delta"],
        )[:10],
        "pair_count": len(pairs),
        "confidence": "descriptive_only",
    }


def _build_overview(
    source: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    strategies: Sequence[str],
    protocol_id: str,
) -> dict[str, Any]:
    manifest = dict(source["manifest"])
    metrics = dict(source["metrics"])
    strategy_data: dict[str, Any] = {}
    for strategy in strategies:
        strategy_rows = [row for row in rows if row.get("strategy") == strategy]
        strategy_data[strategy] = {
            "run_count": len(strategy_rows),
            "feasible_count": sum(bool(row.get("feasible")) for row in strategy_rows),
            "case_count": len({str(row.get("instance_id")) for row in strategy_rows}),
            "seed_count": len({row.get("seed") for row in strategy_rows}),
            "families": sorted({str(row.get("family")) for row in strategy_rows if row.get("family")}),
            "budgets": _budget_summary(strategy_rows),
            "core_metrics": {
                name: _core_metric(metrics, strategy, section, metric, direction, unit)
                for name, (section, metric, direction, unit) in CORE_METRICS.items()
            },
        }
    return {
        "review_schema_version": REVIEW_SCHEMA_VERSION,
        "strategies": list(strategies),
        "current": {
            "optagent_commit": dict(manifest.get("commits") or {}).get("opt-agent", "unknown"),
            "benchmarks_commit": dict(manifest.get("commits") or {}).get("benchmarks", "unknown"),
            "created_at": manifest.get("created_at"),
            "protocol_id": protocol_id,
        },
        "strategies_data": strategy_data,
    }


def _core_metric(
    metrics: Mapping[str, Any],
    strategy: str,
    section: str,
    metric: str,
    direction: str,
    unit: str,
) -> dict[str, Any]:
    entry = dict(dict(dict(metrics.get(section) or {}).get("by_strategy") or {}).get(strategy, {}).get(metric) or {})
    return {
        "availability": entry.get("availability", "insufficient_data"),
        "value": entry.get("value"),
        "unit": entry.get("unit") or unit,
        "direction": direction,
        "sample_count": entry.get("sample_count"),
        "reason": entry.get("reason", ""),
    }


def _budget_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[Any]]:
    return {
        key: sorted({row.get(key) for row in rows if row.get(key) is not None})
        for key in ("time_budget_s", "max_iterations", "population_size", "thread_count")
    }


def _build_families(rows: Sequence[Mapping[str, Any]], strategies: Sequence[str]) -> dict[str, Any]:
    by_strategy: dict[str, list[dict[str, Any]]] = {}
    for strategy in strategies:
        grouped = _group_rows(row for row in rows if row.get("strategy") == strategy)
        summaries = [
            _row_group_summary(family=family, rows=family_rows) for family, family_rows in sorted(grouped.items())
        ]
        by_strategy[strategy] = summaries
    return {"review_schema_version": REVIEW_SCHEMA_VERSION, "by_strategy": by_strategy}


def _group_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("family") or "unknown")].append(row)
    return grouped


def _row_group_summary(*, family: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    gaps = _numbers(row.get("gap_to_reference") for row in rows)
    wall = sum(_numbers(row.get("wall_time_s") for row in rows))
    candidates = sum(_numbers(row.get("evaluated_candidates") for row in rows))
    target_values = [row.get("target_hit") for row in rows if row.get("target_hit") is not None]
    return {
        "family": family,
        "run_count": len(rows),
        "case_count": len({str(row.get("instance_id")) for row in rows}),
        "feasible_rate": sum(bool(row.get("feasible")) for row in rows) / len(rows) if rows else None,
        "median_reference_gap": median(gaps) if gaps else None,
        "mean_reference_gap": sum(gaps) / len(gaps) if gaps else None,
        "gap_cv": _cv(gaps),
        "target_hit_ratio": sum(bool(value) for value in target_values) / len(target_values) if target_values else None,
        "candidate_throughput": candidates / wall if wall > 0 else None,
    }


def _build_anytime(
    rows: Sequence[Mapping[str, Any]],
    curves: Sequence[Mapping[str, Any]],
    strategies: Sequence[str],
) -> dict[str, Any]:
    row_by_run = {str(row.get("run_id")): row for row in rows}
    by_strategy: dict[str, Any] = {}
    for strategy in strategies:
        strategy_run_ids = {str(row.get("run_id")) for row in rows if row.get("strategy") == strategy}
        overall = _aggregate_curves(strategy_run_ids, curves, row_by_run)
        families: dict[str, Any] = {}
        for family, family_rows in _group_rows(row for row in rows if row.get("strategy") == strategy).items():
            run_ids = {str(row.get("run_id")) for row in family_rows}
            families[family] = _aggregate_curves(run_ids, curves, row_by_run)
        by_strategy[strategy] = {"overall": overall, "families": families}
    return {"review_schema_version": REVIEW_SCHEMA_VERSION, "by_strategy": by_strategy}


def _aggregate_curves(
    run_ids: set[str],
    curves: Sequence[Mapping[str, Any]],
    row_by_run: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_run: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for point in curves:
        run_id = str(point.get("run_id"))
        if run_id in run_ids and point.get("gap_to_reference") is not None:
            by_run[run_id].append(point)
    result: list[dict[str, Any]] = []
    for checkpoint in ANYTIME_CHECKPOINTS:
        values: list[float] = []
        for run_id, points in by_run.items():
            ordered = sorted(points, key=lambda item: float(item.get("elapsed_s") or 0.0))
            if not ordered:
                continue
            budget = float(row_by_run.get(run_id, {}).get("time_budget_s") or ordered[-1].get("elapsed_s") or 1.0)
            elapsed = checkpoint * budget
            eligible = [point for point in ordered if float(point.get("elapsed_s") or 0.0) <= elapsed]
            if not eligible:
                continue
            selected = eligible[-1]
            values.append(float(selected["gap_to_reference"]))
        if values:
            result.append(
                {
                    "budget_fraction": checkpoint,
                    "p25": _quantile(values, 0.25),
                    "median": _quantile(values, 0.5),
                    "p75": _quantile(values, 0.75),
                    "sample_count": len(values),
                }
            )
    return result


def _build_evidence(rows: Sequence[Mapping[str, Any]], strategies: Sequence[str]) -> dict[str, Any]:
    by_strategy: dict[str, Any] = {}
    for strategy in strategies:
        by_instance: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for row in rows:
            if row.get("strategy") == strategy:
                by_instance[str(row.get("instance_id") or "unknown")].append(row)
        summaries = [
            _instance_summary(instance_id, instance_rows) for instance_id, instance_rows in by_instance.items()
        ]
        with_gaps = [item for item in summaries if item["mean_gap"] is not None]
        with_variability = [item for item in summaries if item["gap_cv"] is not None]
        target_misses = [
            item for item in summaries if item["target_hit_ratio"] is not None and item["target_hit_ratio"] < 1.0
        ]
        by_strategy[strategy] = {
            "largest_gaps": sorted(with_gaps, key=lambda item: item["mean_gap"], reverse=True)[:10],
            "highest_variability": sorted(with_variability, key=lambda item: item["gap_cv"], reverse=True)[:10],
            "target_misses": sorted(target_misses, key=lambda item: item["target_hit_ratio"])[:10],
        }
    return {"review_schema_version": REVIEW_SCHEMA_VERSION, "by_strategy": by_strategy}


def _instance_summary(instance_id: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    gaps = _numbers(row.get("gap_to_reference") for row in rows)
    target_values = [row.get("target_hit") for row in rows if row.get("target_hit") is not None]
    return {
        "instance_id": instance_id,
        "family": str(rows[0].get("family") or "unknown"),
        "run_count": len(rows),
        "mean_gap": sum(gaps) / len(gaps) if gaps else None,
        "max_gap": max(gaps) if gaps else None,
        "gap_cv": _cv(gaps),
        "target_hit_ratio": sum(bool(value) for value in target_values) / len(target_values) if target_values else None,
    }


def _review_run(row: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "run_id",
        "strategy",
        "family",
        "instance_id",
        "seed",
        "status",
        "feasible",
        "objective",
        "reference_objective",
        "gap_to_reference",
        "target_objective",
        "target_hit",
        "wall_time_s",
        "evaluated_candidates",
        "time_budget_s",
        "max_iterations",
        "population_size",
        "thread_count",
    )
    return {key: row.get(key) for key in keys}


def _numbers(values: Iterable[Any]) -> list[float]:
    return [float(value) for value in values if isinstance(value, (int, float)) and math.isfinite(float(value))]


def _cv(values: Sequence[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance) / abs(mean)


def _quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish a static OptAgent strategy review bundle.")
    parser.add_argument("--current-artifact", required=True)
    parser.add_argument("--baseline-artifact")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--protocol-id", required=True)
    parser.add_argument("--created-at")
    args = parser.parse_args(argv)
    result = publish_review_bundle(
        args.current_artifact,
        args.output_dir,
        protocol_id=args.protocol_id,
        baseline_artifact=args.baseline_artifact,
        created_at=args.created_at,
    )
    print(result["index"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
