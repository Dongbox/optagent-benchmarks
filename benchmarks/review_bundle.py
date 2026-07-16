from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import math
from pathlib import Path
from statistics import median
from typing import Any, Mapping, Sequence

from benchmarks.artifact_io import read_json, read_jsonl, sha256_file, write_json, write_jsonl
from benchmarks.telemetry_artifacts import load_published_artifacts


REVIEW_SCHEMA_VERSION = 2
INDEX_JSON = "review-index.json"
OVERVIEW_JSON = "overview.json"
RESULTS_JSON = "results.json"
RUNS_JSONL = "runs.jsonl"
DEFAULT_CHECKPOINTS = (5.0, 10.0, 20.0)


def publish_review_bundle(
    current_artifact: str | Path,
    output_dir: str | Path,
    *,
    protocol_id: str,
    baseline_artifact: str | Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    current_source = load_published_artifacts(current_artifact)
    baseline_source = load_published_artifacts(baseline_artifact) if baseline_artifact else None
    current_rows = [dict(row) for row in current_source["rows"]]
    baseline_rows = [dict(row) for row in baseline_source["rows"]] if baseline_source else []
    _validate_artifact_invariants(current_rows, "current")
    _require_single_strategy(current_rows, "current")
    if baseline_rows:
        _validate_artifact_invariants(baseline_rows, "baseline")
        _require_single_strategy(baseline_rows, "baseline")

    meta = _artifact_meta(current_rows)
    reasons = _compatibility_reasons(current_rows, baseline_rows) if baseline_rows else []
    if reasons:
        raise ValueError("incompatible review artifacts: " + ", ".join(reasons))
    compatible = True
    render_mode = "comparison" if baseline_rows else "single"
    results, review_runs = _build_results(
        current_rows,
        baseline_rows if compatible else [],
        meta=meta,
    )
    overview = _build_overview(
        current_source,
        baseline_source,
        current_rows,
        baseline_rows,
        results,
        meta=meta,
        protocol_id=protocol_id,
        render_mode=render_mode,
        compatible=compatible,
        compatibility_reasons=reasons,
    )

    out = Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"review bundle output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / OVERVIEW_JSON, overview)
    write_json(out / RESULTS_JSON, results)
    write_jsonl(out / RUNS_JSONL, review_runs)
    artifact_names = (OVERVIEW_JSON, RESULTS_JSON, RUNS_JSONL)
    index = {
        "review_schema_version": REVIEW_SCHEMA_VERSION,
        "kind": "optagent_review_bundle",
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "render_mode": render_mode,
        "comparison": {
            "available": bool(baseline_rows and compatible),
            "reason": "" if compatible else "incompatible_artifacts",
        },
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
    if set(artifacts) != {OVERVIEW_JSON, RESULTS_JSON, RUNS_JSONL}:
        raise ValueError("review bundle does not declare the required artifact set")
    for name, entry in artifacts.items():
        if entry.get("path") != name:
            raise ValueError(f"invalid review bundle artifact path: {name}")
        if sha256_file(root / name) != entry.get("sha256"):
            raise ValueError(f"review bundle checksum mismatch: {name}")
        if (root / name).stat().st_size != entry.get("bytes"):
            raise ValueError(f"review bundle byte count mismatch: {name}")
    return {
        "index": index,
        "overview": read_json(root / OVERVIEW_JSON),
        "results": read_json(root / RESULTS_JSON),
        "runs": read_jsonl(root / RUNS_JSONL),
    }


def _artifact_meta(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    first = rows[0] if rows else {}
    observation_times = tuple(float(value) for value in first.get("observation_times_s") or ())
    if not observation_times:
        observation_times = tuple(
            sorted(
                {
                    float(item.get("requested_time_s"))
                    for row in rows
                    for item in row.get("observations") or ()
                    if item.get("requested_time_s") is not None
                }
            )
        )
    checkpoints = tuple(float(value) for value in first.get("formal_checkpoints_s") or DEFAULT_CHECKPOINTS)
    target_families = tuple(str(value) for value in first.get("target_families") or ())
    raw_max_iterations = first.get("max_iterations")
    max_iterations = (
        int(raw_max_iterations) if isinstance(raw_max_iterations, (int, float)) and raw_max_iterations >= 0 else None
    )
    observation_interval = None
    if len(observation_times) >= 2:
        intervals = [right - left for left, right in zip(observation_times, observation_times[1:])]
        if intervals and all(math.isclose(value, intervals[0]) for value in intervals[1:]):
            observation_interval = intervals[0]
    return {
        "preset_id": str(first.get("preset_id") or "unidentified"),
        "preset_version": str(first.get("preset_version") or "0"),
        "review_mode": str(first.get("review_mode") or "single_family_focus"),
        "target_families": target_families,
        "observation_times_s": observation_times,
        "formal_checkpoints_s": checkpoints,
        "expected_seed_count": int(first.get("expected_seed_count") or len({row.get("seed") for row in rows})),
        "configuration": {
            "time_limit_s": _optional_float(first.get("time_budget_s")),
            "max_iterations": max_iterations,
            "population_size": _optional_int(first.get("population_size")),
            "thread_count": _optional_int(first.get("thread_count")),
            "observation_interval_s": observation_interval,
        },
    }


def _build_overview(
    current_source: Mapping[str, Any],
    baseline_source: Mapping[str, Any] | None,
    current_rows: Sequence[Mapping[str, Any]],
    baseline_rows: Sequence[Mapping[str, Any]],
    results: Mapping[str, Any],
    *,
    meta: Mapping[str, Any],
    protocol_id: str,
    render_mode: str,
    compatible: bool,
    compatibility_reasons: Sequence[str],
) -> dict[str, Any]:
    current_strategy = str(current_rows[0].get("strategy") or "unknown")
    baseline_strategy = str(baseline_rows[0].get("strategy") or "unknown") if baseline_rows else None
    return {
        "review_schema_version": REVIEW_SCHEMA_VERSION,
        "render_mode": render_mode,
        "protocol_id": protocol_id,
        "review_mode": meta["review_mode"],
        "target_families": list(meta["target_families"]),
        "preset": {
            "id": meta["preset_id"],
            "version": meta["preset_version"],
            "observation_times_s": list(meta["observation_times_s"]),
            "formal_checkpoints_s": list(meta["formal_checkpoints_s"]),
            "expected_seed_count": meta["expected_seed_count"],
            "configuration": meta["configuration"],
        },
        "current": _variant_identity(current_source, current_strategy),
        "baseline": _variant_identity(baseline_source, baseline_strategy) if baseline_source else None,
        "compatible": compatible,
        "compatibility_reasons": list(compatibility_reasons),
        "run_count": len(current_rows),
        "case_count": len({_case_id(row) for row in current_rows}),
        "family_count": len({str(row.get("family") or "unknown") for row in current_rows}),
        "family_checkpoints": [
            {
                "family": family["family"],
                "role": family["role"],
                "case_count": len(family["cases"]),
                "checkpoints": family["checkpoints"],
            }
            for family in results["families"]
        ],
        "metric_definitions": {
            "reference_gap": {
                "minimize": "(objective - reference) / abs(reference)",
                "maximize": "(reference - objective) / abs(reference)",
                "display_unit": "%",
                "direction": "lower",
                "zero_reference": "unavailable",
            },
            "reference_gap_change": {
                "formula": "current gap - baseline gap",
                "unit": "pp",
                "direction": "negative improves; positive regresses; zero unchanged",
            },
            "quantile": {
                "formula": "sorted linear interpolation at position (n - 1) * q",
                "p25_p75": "middle 50% of the displayed cohort",
            },
            "trajectory_cohort": {
                "comparison": "valid paired seeds where both sides are feasible at that second",
                "single": "valid feasible seeds at that second",
            },
        },
    }


def _build_results(
    current_rows: Sequence[Mapping[str, Any]],
    baseline_rows: Sequence[Mapping[str, Any]],
    *,
    meta: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    current = {_coordinate(row): row for row in current_rows}
    baseline = {_coordinate(row): row for row in baseline_rows}
    family_cases: dict[str, dict[str, list[tuple[Mapping[str, Any], Mapping[str, Any] | None]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    review_runs: list[dict[str, Any]] = []
    for coordinate, current_row in sorted(current.items()):
        baseline_row = baseline.get(coordinate)
        family = str(current_row.get("family") or "unknown")
        case_id = _case_id(current_row)
        family_cases[family][case_id].append((current_row, baseline_row))
        review_runs.append(_review_run(current_row, baseline_row))

    target_families = set(meta["target_families"])
    ordered_families = sorted(family_cases, key=lambda family: (family not in target_families, family))
    families: list[dict[str, Any]] = []
    for family in ordered_families:
        cases = [
            _case_result(case_id, family_cases[family][case_id], meta=meta) for case_id in sorted(family_cases[family])
        ]
        families.append(
            {
                "family": family,
                "role": "target" if family in target_families else "observation",
                "checkpoints": _family_checkpoints(cases, meta["formal_checkpoints_s"]),
                "cases": cases,
            }
        )
    return {
        "review_schema_version": REVIEW_SCHEMA_VERSION,
        "families": families,
    }, review_runs


def _case_result(
    case_id: str,
    pairs: Sequence[tuple[Mapping[str, Any], Mapping[str, Any] | None]],
    *,
    meta: Mapping[str, Any],
) -> dict[str, Any]:
    first = pairs[0][0]
    current_valid = [row for row, _ in pairs if _valid_run(row, meta["observation_times_s"])]
    paired_valid = [
        (current, baseline)
        for current, baseline in pairs
        if baseline is not None
        and _valid_run(current, meta["observation_times_s"])
        and _valid_run(baseline, meta["observation_times_s"])
    ]
    comparison = any(baseline is not None for _, baseline in pairs)
    trajectory = [
        _trajectory_point(
            time_s,
            current_valid=current_valid,
            paired_valid=paired_valid,
            expected=len(pairs),
            comparison=comparison,
        )
        for time_s in meta["observation_times_s"]
    ]
    by_time = {point["time_s"]: point for point in trajectory}
    return {
        "case_id": case_id,
        "family": str(first.get("family") or "unknown"),
        "objective_sense": str(first.get("objective_sense") or "minimize"),
        "reference_objective": first.get("reference_objective"),
        "valid_run_count": len(current_valid),
        "expected_run_count": len(pairs),
        "checkpoints": [
            by_time.get(float(value), _empty_point(float(value), len(pairs))) for value in meta["formal_checkpoints_s"]
        ],
        "trajectory": trajectory,
    }


def _trajectory_point(
    time_s: float,
    *,
    current_valid: Sequence[Mapping[str, Any]],
    paired_valid: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]],
    expected: int,
    comparison: bool,
) -> dict[str, Any]:
    if comparison:
        current_samples = [_sample(row, time_s) for row, _ in paired_valid]
        baseline_samples = [_sample(row, time_s) for _, row in paired_valid]
        current_feasible = [sample for sample in current_samples if sample and sample["feasible"]]
        baseline_feasible = [sample for sample in baseline_samples if sample and sample["feasible"]]
        both = [
            (current, baseline)
            for current, baseline in zip(current_samples, baseline_samples, strict=True)
            if current and baseline and current["feasible"] and baseline["feasible"]
        ]
        current_pair_gaps = [sample[0]["gap_percent"] for sample in both if sample[0]["gap_percent"] is not None]
        baseline_pair_gaps = [sample[1]["gap_percent"] for sample in both if sample[1]["gap_percent"] is not None]
        paired_gap = _paired_gap(current_pair_gaps, baseline_pair_gaps)
        valid_count = len(paired_valid)
        return {
            "time_s": float(time_s),
            "current": _side_point(current_feasible, valid_count, expected),
            "baseline": _side_point(baseline_feasible, valid_count, expected),
            "paired_gap": paired_gap,
        }
    samples = [_sample(row, time_s) for row in current_valid]
    feasible = [sample for sample in samples if sample and sample["feasible"]]
    return {
        "time_s": float(time_s),
        "current": _side_point(feasible, len(current_valid), expected),
        "baseline": None,
        "paired_gap": None,
    }


def _side_point(samples: Sequence[Mapping[str, Any]], valid: int, expected: int) -> dict[str, Any]:
    gaps = [float(sample["gap_percent"]) for sample in samples if sample.get("gap_percent") is not None]
    objectives = [float(sample["objective"]) for sample in samples if sample.get("objective") is not None]
    exits = [sample for sample in samples if sample.get("search_ended")]
    return {
        "valid": valid,
        "expected": expected,
        "feasible": len(samples),
        "gap": _stats(gaps),
        "objective": _stats(objectives),
        "search_ended": len(exits),
    }


def _paired_gap(current: Sequence[float], baseline: Sequence[float]) -> dict[str, Any] | None:
    if not current or len(current) != len(baseline):
        return None
    current_median = float(median(current))
    baseline_median = float(median(baseline))
    delta = current_median - baseline_median
    return {
        "current_median": current_median,
        "baseline_median": baseline_median,
        "current": _stats(current),
        "baseline": _stats(baseline),
        "delta_pp": delta,
        "change": "improved" if delta < 0 else "regressed" if delta > 0 else "unchanged",
        "sample_count": len(current),
    }


def _family_checkpoints(cases: Sequence[Mapping[str, Any]], checkpoints: Sequence[float]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for time_s in checkpoints:
        points = [point for case in cases for point in case["checkpoints"] if point["time_s"] == time_s]
        deltas = [point["paired_gap"]["delta_pp"] for point in points if point.get("paired_gap") is not None]
        current_case_gaps = [
            point["current"]["gap"]["median"] for point in points if point["current"]["gap"]["median"] is not None
        ]
        baseline_case_gaps = [
            point["baseline"]["gap"]["median"]
            for point in points
            if point.get("baseline") is not None and point["baseline"]["gap"]["median"] is not None
        ]
        result.append(
            {
                "time_s": time_s,
                "current": {
                    "gap": _stats(current_case_gaps),
                    "feasible": sum(point["current"]["feasible"] for point in points),
                    "valid": sum(point["current"]["valid"] for point in points),
                },
                "baseline": {
                    "gap": _stats(baseline_case_gaps),
                    "feasible": sum(point["baseline"]["feasible"] for point in points if point.get("baseline")),
                    "valid": sum(point["baseline"]["valid"] for point in points if point.get("baseline")),
                }
                if baseline_case_gaps
                else None,
                "case_delta_pp": _stats(deltas),
            }
        )
    return result


def _sample(row: Mapping[str, Any], time_s: float) -> dict[str, Any] | None:
    observations = {float(item.get("requested_time_s")): item for item in row.get("observations") or ()}
    observation = observations.get(float(time_s))
    if observation is None:
        return None
    snapshot_id = str(observation.get("snapshot_id") or "")
    snapshot = dict((row.get("solution_snapshots") or {}).get(snapshot_id) or {})
    feasible = bool(snapshot.get("verification_feasible")) and bool(snapshot.get("verification_passed"))
    objective = snapshot.get("verification_objective") if feasible else None
    return {
        "feasible": feasible,
        "objective": float(objective) if isinstance(objective, (int, float)) else None,
        "gap_percent": _reference_gap_percent(
            objective,
            row.get("reference_objective"),
            str(row.get("objective_sense") or "minimize"),
        ),
        "search_ended": bool(observation.get("search_ended")),
        "termination_reason": str(observation.get("termination_reason") or ""),
    }


def _valid_run(row: Mapping[str, Any], observation_times: Sequence[float]) -> bool:
    if row.get("observation_verification_passed") is not True:
        return False
    if str(row.get("status") or "").lower() in {
        "error",
        "cancelled",
        "external_cancelled",
        "infrastructure_interrupted",
        "verification_failed",
        "observation_verification_failed",
    }:
        return False
    actual = tuple(float(item.get("requested_time_s")) for item in row.get("observations") or ())
    return actual == tuple(observation_times)


def _review_run(current: Mapping[str, Any], baseline: Mapping[str, Any] | None) -> dict[str, Any]:
    return {
        "family": str(current.get("family") or "unknown"),
        "case_id": _case_id(current),
        "seed": current.get("seed"),
        "current": _run_side(current),
        "baseline": _run_side(baseline) if baseline is not None else None,
    }


def _run_side(row: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    snapshots = row.get("solution_snapshots") or {}
    observations = []
    for item in row.get("observations") or ():
        snapshot = snapshots.get(str(item.get("snapshot_id") or "")) or {}
        observations.append(
            {
                "time_s": item.get("requested_time_s"),
                "state": item.get("state"),
                "feasible": snapshot.get("verification_feasible"),
                "objective": snapshot.get("verification_objective"),
                "search_ended": item.get("search_ended"),
                "search_ended_at_s": item.get("search_ended_at_s"),
                "termination_reason": item.get("termination_reason"),
            }
        )
    return {
        "strategy": row.get("strategy"),
        "status": row.get("status"),
        "verification_passed": row.get("observation_verification_passed"),
        "verification_errors": list(row.get("observation_verification_errors") or ()),
        "observations": observations,
    }


def _compatibility_reasons(
    current_rows: Sequence[Mapping[str, Any]], baseline_rows: Sequence[Mapping[str, Any]]
) -> list[str]:
    current = {_coordinate(row): row for row in current_rows}
    baseline = {_coordinate(row): row for row in baseline_rows}
    if set(current) != set(baseline):
        return ["coordinate_set_mismatch"]
    reasons: list[str] = []
    invariant_fields = (
        "family",
        "instance_id",
        "reference_objective",
        "objective_sense",
        "time_budget_s",
        "thread_count",
        "preset_id",
        "preset_version",
        "review_mode",
        "target_families",
        "formal_checkpoints_s",
        "observation_times_s",
        "expected_seed_count",
        "case_checksum",
    )
    for coordinate in sorted(current):
        for field in invariant_fields:
            if current[coordinate].get(field) != baseline[coordinate].get(field):
                reasons.append(f"{field}_mismatch:{coordinate[0]}:{coordinate[1]}:{coordinate[2]}")
                break
    return reasons


def _variant_identity(source: Mapping[str, Any] | None, strategy: str | None) -> dict[str, Any] | None:
    if source is None:
        return None
    manifest = dict(source.get("manifest") or {})
    return {
        "strategy": strategy,
        "optagent_commit": manifest.get("optagent_commit") or "unknown",
        "benchmarks_commit": manifest.get("benchmarks_commit") or "unknown",
        "created_at": manifest.get("created_at") or "",
    }


def _stats(values: Sequence[float]) -> dict[str, Any]:
    materialized = [float(value) for value in values]
    return {
        "p25": _quantile(materialized, 0.25) if materialized else None,
        "median": _quantile(materialized, 0.5) if materialized else None,
        "p75": _quantile(materialized, 0.75) if materialized else None,
        "sample_count": len(materialized),
    }


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


def _reference_gap_percent(objective: Any, reference: Any, objective_sense: str) -> float | None:
    if not isinstance(objective, (int, float)) or not isinstance(reference, (int, float)) or reference == 0:
        return None
    delta = reference - objective if objective_sense == "maximize" else objective - reference
    return float(delta) / abs(float(reference)) * 100.0


def _optional_float(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _optional_int(value: Any) -> int | None:
    return int(value) if isinstance(value, (int, float)) else None


def _coordinate(row: Mapping[str, Any]) -> tuple[str, str, Any]:
    return (str(row.get("family") or "unknown"), _case_id(row), row.get("seed"))


def _case_id(row: Mapping[str, Any]) -> str:
    return str(row.get("benchmark_id") or row.get("instance_id") or "unknown")


def _require_single_strategy(rows: Sequence[Mapping[str, Any]], role: str) -> None:
    strategies = {str(row.get("strategy") or "unknown") for row in rows}
    if len(strategies) != 1:
        raise ValueError(f"{role} artifact must contain exactly one strategy variant")


def _validate_artifact_invariants(rows: Sequence[Mapping[str, Any]], role: str) -> None:
    if not rows:
        raise ValueError(f"{role} artifact must contain at least one run")
    coordinates = [_coordinate(row) for row in rows]
    if len(set(coordinates)) != len(coordinates):
        raise ValueError(f"{role} artifact contains duplicate family/case/seed coordinates")

    invariant_fields = (
        "preset_id",
        "preset_version",
        "review_mode",
        "target_families",
        "formal_checkpoints_s",
        "observation_times_s",
        "expected_seed_count",
    )
    first = rows[0]
    for field in invariant_fields:
        expected = first.get(field)
        if any(row.get(field) != expected for row in rows[1:]):
            raise ValueError(f"{role} artifact has inconsistent {field}")
    review_mode = first.get("review_mode")
    if review_mode not in {"single_family_focus", "multi_family_suite"}:
        raise ValueError(f"{role} artifact has unsupported review mode: {review_mode}")
    target_families = tuple(first.get("target_families") or ())
    if not target_families:
        raise ValueError(f"{role} artifact must declare at least one target family")
    if review_mode == "single_family_focus" and len(target_families) != 1:
        raise ValueError(f"{role} single-family artifact must declare exactly one target family")
    present_families = {str(row.get("family") or "unknown") for row in rows}
    missing_families = set(target_families) - present_families
    if missing_families:
        raise ValueError(f"{role} target families are not present in its runs: {sorted(missing_families)}")


def _empty_point(time_s: float, expected: int) -> dict[str, Any]:
    return {
        "time_s": time_s,
        "current": _side_point([], 0, expected),
        "baseline": None,
        "paired_gap": None,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish a static OptAgent strategy review bundle.")
    parser.add_argument("--current-artifact", required=True)
    parser.add_argument("--baseline-artifact")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--protocol-id", required=True)
    parser.add_argument("--created-at")
    args = parser.parse_args(argv)
    publish_review_bundle(
        args.current_artifact,
        args.output_dir,
        protocol_id=args.protocol_id,
        baseline_artifact=args.baseline_artifact,
        created_at=args.created_at,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
