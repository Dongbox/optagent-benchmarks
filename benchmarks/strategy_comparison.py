from __future__ import annotations

from collections import defaultdict
import math
from pathlib import Path
import statistics
from typing import Any, Iterable, Mapping, Sequence

from benchmarks.artifact_io import sha256_file
from benchmarks.comparison_artifacts import RunArtifact, load_run_artifact
from benchmarks.comparison_protocol import IndexProfile, MetricThreshold, index_profile_from_snapshot
from benchmarks.comparison_report import COMPARISON_SCHEMA_VERSION, publish_comparison
from benchmarks.comparison_statistics import build_statistical_evidence
from benchmarks.comparison_verdict import decide_profile_verdict, decide_verdict
from benchmarks.telemetry_metrics import build_metric_dataset


def compare_run_artifacts(
    baseline_path: str | Path,
    challenger_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    baseline = load_run_artifact(baseline_path)
    challenger = load_run_artifact(challenger_path)
    out = Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"comparison output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    compatibility_reasons = _compatibility_reasons(baseline, challenger)
    if compatibility_reasons:
        result = _incompatible_result(baseline, challenger, compatibility_reasons)
        publish_comparison(out, result, [], {}, result["statistical_evidence"])
        return result

    index_policy = index_profile_from_snapshot(dict(challenger.protocol["index_profile"]))
    pairs = _paired_metrics(baseline, challenger, index_policy)
    hard_gates = _hard_gates(baseline, challenger)
    profile_groups = _group_pairs(pairs)
    profile_results = {
        profile: _index_profile(profile_pairs, index_policy)
        for profile, profile_pairs in sorted(profile_groups.items())
    }
    statistical = build_statistical_evidence(profile_groups, index_policy)
    for profile, profile_result in profile_results.items():
        profile_gate_failures = _profile_gate_failures(profile_result, pairs, hard_gates)
        profile_result["hard_gate_failures"] = profile_gate_failures
        profile_result["verdict"] = decide_profile_verdict(
            profile_result,
            statistical["profiles"][profile],
            index_policy,
            profile_gate_failures,
        )
    dimensions = _aggregate_dimensions_by_family(profile_results)
    overall_index = _aggregate_overall_by_family(profile_results)
    diagnostic_feedback = _diagnostic_feedback(pairs, profile_results)
    protocol_kind = str(challenger.protocol["protocol"]["kind"])
    verdict = decide_verdict(
        overall_index,
        dimensions,
        profile_results,
        hard_gates,
        statistical,
        index_policy,
        protocol_kind,
    )
    promotion_eligibility = {
        "status": "eligible" if protocol_kind != "smoke" else "smoke_not_eligible",
        "protocol_kind": protocol_kind,
    }
    result = {
        "comparison_schema_version": COMPARISON_SCHEMA_VERSION,
        "verdict": verdict,
        "promotable": verdict == "improved",
        "promotion_eligibility": promotion_eligibility,
        "overall_delta_index": overall_index,
        "dimensions": dimensions,
        "profiles": profile_results,
        "hard_gates": hard_gates,
        "statistical_evidence": statistical,
        "diagnostic_feedback": diagnostic_feedback,
        "protocol_id": challenger.manifest["protocol_id"],
        "protocol_checksum": challenger.manifest["protocol_checksum"],
        "index_profile_id": challenger.manifest["index_profile_id"],
        "index_profile_checksum": challenger.manifest["index_profile_checksum"],
        "baseline": _artifact_identity(baseline),
        "challenger": _artifact_identity(challenger),
    }
    publish_comparison(out, result, pairs, dimensions, statistical)
    return result


def _paired_metrics(
    baseline: RunArtifact,
    challenger: RunArtifact,
    index_policy: IndexProfile,
) -> list[dict[str, Any]]:
    baseline_rows = {str(row["coordinate"]): row for row in baseline.rows}
    challenger_rows = {str(row["coordinate"]): row for row in challenger.rows}
    baseline_curves = _curves_by_coordinate(baseline.curves)
    challenger_curves = _curves_by_coordinate(challenger.curves)
    baseline_telemetry = {str(row["coordinate"]): row for row in baseline.telemetry}
    challenger_telemetry = {str(row["coordinate"]): row for row in challenger.telemetry}
    search_candidate_checkpoint = int(challenger.protocol["protocol"]["search_candidate_checkpoint"])
    time_budget = float(challenger.protocol["protocol"]["wall_time_s"])
    pairs = []
    for coordinate in sorted(baseline_rows):
        left = baseline_rows[coordinate]
        right = challenger_rows[coordinate]
        left_curve = baseline_curves.get(coordinate, [])
        right_curve = challenger_curves.get(coordinate, [])
        left_facts = _canonical_run_facts(left, baseline_telemetry[coordinate])
        right_facts = _canonical_run_facts(right, challenger_telemetry[coordinate])
        left_complete = bool(left.get("curve_complete"))
        right_complete = bool(right.get("curve_complete"))
        left_targets = _target_summary(left_curve, index_policy.target_gaps, time_budget) if left_complete else None
        right_targets = _target_summary(right_curve, index_policy.target_gaps, time_budget) if right_complete else None
        pairs.append(
            {
                "coordinate": coordinate,
                "family": right["family"],
                "model_style": right["model_style"],
                "benchmark_id": right["benchmark_id"],
                "seed": right["seed"],
                "baseline": {
                    "final_gap": left_facts["final_gap"],
                    "normalized_primal_integral": (
                        _normalized_primal_integral(left_curve, time_budget, index_policy) if left_complete else None
                    ),
                    "target_hit_rate": left_targets["hit_rate"] if left_targets else None,
                    "time_to_target": left_targets["mean_time"] if left_targets else None,
                    "search_candidate_throughput": left_facts["search_candidate_throughput"],
                    "fixed_search_candidate_elapsed": (
                        _fixed_search_candidate_elapsed(baseline_telemetry[coordinate], search_candidate_checkpoint)
                        if left_complete
                        else None
                    ),
                },
                "challenger": {
                    "final_gap": right_facts["final_gap"],
                    "normalized_primal_integral": (
                        _normalized_primal_integral(right_curve, time_budget, index_policy) if right_complete else None
                    ),
                    "target_hit_rate": right_targets["hit_rate"] if right_targets else None,
                    "time_to_target": right_targets["mean_time"] if right_targets else None,
                    "search_candidate_throughput": right_facts["search_candidate_throughput"],
                    "fixed_search_candidate_elapsed": (
                        _fixed_search_candidate_elapsed(challenger_telemetry[coordinate], search_candidate_checkpoint)
                        if right_complete
                        else None
                    ),
                },
            }
        )
    for pair in pairs:
        pair["improvement"] = {
            metric: _metric_improvement(metric, pair["baseline"].get(metric), pair["challenger"].get(metric))
            for metric in pair["baseline"]
        }
    return pairs


def _index_profile(pairs: list[dict[str, Any]], index_policy: IndexProfile) -> dict[str, Any]:
    base_gaps = _pair_values(pairs, "baseline", "final_gap")
    challenger_gaps = _pair_values(pairs, "challenger", "final_gap")
    win_rate = _paired_win_rate(pairs)
    consistency = _case_direction_consistency(pairs)
    component_values = {
        "median_final_gap": (_median(base_gaps), _median(challenger_gaps)),
        "paired_quality_win_rate": (0.5, win_rate),
        "normalized_primal_integral": (
            _median(_pair_values(pairs, "baseline", "normalized_primal_integral")),
            _median(_pair_values(pairs, "challenger", "normalized_primal_integral")),
        ),
        "target_hit_rate": (
            _mean(_pair_values(pairs, "baseline", "target_hit_rate")),
            _mean(_pair_values(pairs, "challenger", "target_hit_rate")),
        ),
        "time_to_target": (
            _median(_pair_values(pairs, "baseline", "time_to_target")),
            _median(_pair_values(pairs, "challenger", "time_to_target")),
        ),
        "p90_final_gap": (_percentile(base_gaps, 0.9), _percentile(challenger_gaps, 0.9)),
        "gap_mad": (_mad(base_gaps), _mad(challenger_gaps)),
        "case_direction_consistency": (0.5, consistency),
        "search_candidate_throughput": (
            _median(_pair_values(pairs, "baseline", "search_candidate_throughput")),
            _median(_pair_values(pairs, "challenger", "search_candidate_throughput")),
        ),
        "fixed_search_candidate_elapsed": (
            _median(_pair_values(pairs, "baseline", "fixed_search_candidate_elapsed")),
            _median(_pair_values(pairs, "challenger", "fixed_search_candidate_elapsed")),
        ),
    }
    components = {
        name: _component_index(name, baseline, challenger, index_policy.thresholds[name])
        for name, (baseline, challenger) in component_values.items()
    }
    dimensions = {}
    for dimension, weights in index_policy.component_weights.items():
        values = [components[name] for name in weights]
        available = [value for value in values if value["availability"] == "available"]
        index_value = (
            sum(components[name]["index"] * weight for name, weight in weights.items())
            if len(available) == len(values)
            else None
        )
        dimensions[dimension] = {
            "index": index_value,
            "availability": "available" if index_value is not None else "insufficient_data",
            "components": {name: components[name] for name in weights},
        }
    overall = (
        sum(dimensions[name]["index"] * weight for name, weight in index_policy.dimension_weights.items())
        if all(dimensions[name]["index"] is not None for name in index_policy.dimension_weights)
        else None
    )
    final_gap_improvements = [
        float(pair["baseline"]["final_gap"]) - float(pair["challenger"]["final_gap"])
        for pair in pairs
        if pair["baseline"]["final_gap"] is not None and pair["challenger"]["final_gap"] is not None
    ]
    worst_baseline = max(base_gaps) if base_gaps else None
    worst_challenger = max(challenger_gaps) if challenger_gaps else None
    worst_tolerance = max(0.01, abs(worst_baseline or 0.0) * 0.1)
    return {
        "family": pairs[0]["family"],
        "model_style": pairs[0]["model_style"],
        "pair_count": len(pairs),
        "overall_delta_index": overall,
        "dimensions": dimensions,
        "final_gap_median_improvement": _median(final_gap_improvements),
        "worst_gap_guard": {
            "baseline": worst_baseline,
            "challenger": worst_challenger,
            "tolerance": worst_tolerance,
            "triggered": (
                worst_baseline is not None
                and worst_challenger is not None
                and worst_challenger - worst_baseline > worst_tolerance
            ),
        },
    }


def _component_index(
    name: str,
    baseline: float | None,
    challenger: float | None,
    threshold: MetricThreshold,
) -> dict[str, Any]:
    if baseline is None or challenger is None:
        return {
            "availability": "insufficient_data",
            "baseline": baseline,
            "challenger": challenger,
            "index": None,
        }
    improvement = _metric_improvement(name, baseline, challenger)
    scale = _threshold_scale(baseline, threshold)
    index_value = max(-100.0, min(100.0, 100.0 * improvement / scale)) if scale > 0 else 0.0
    return {
        "availability": "available",
        "baseline": baseline,
        "challenger": challenger,
        "improvement": improvement,
        "meaningful_change_threshold": scale,
        "index": index_value,
    }


def _metric_improvement(name: str, baseline: float | None, challenger: float | None) -> float | None:
    if baseline is None or challenger is None:
        return None
    higher_is_better = name in {
        "paired_quality_win_rate",
        "target_hit_rate",
        "case_direction_consistency",
        "search_candidate_throughput",
    }
    return challenger - baseline if higher_is_better else baseline - challenger


def _threshold_scale(baseline: float, threshold: MetricThreshold) -> float:
    if threshold.mode == "absolute":
        return threshold.value
    relative = abs(baseline) * threshold.value
    if threshold.mode == "relative":
        return max(relative, 1e-12)
    return max(threshold.absolute_floor, relative)


def _hard_gates(baseline: RunArtifact, challenger: RunArtifact) -> dict[str, Any]:
    baseline_errors = sum(1 for row in baseline.rows if row.get("status") == "error")
    challenger_errors = sum(1 for row in challenger.rows if row.get("status") == "error")
    baseline_timeouts = [str(row["coordinate"]) for row in baseline.rows if _is_timeout(row)]
    challenger_timeouts = [str(row["coordinate"]) for row in challenger.rows if _is_timeout(row)]
    verification_failures = [
        f"{role}:{row['coordinate']}"
        for role, artifact in (("baseline", baseline), ("challenger", challenger))
        for row in artifact.rows
        if row.get("verification_status") != "passed" or not bool(row.get("verification_passed"))
    ]
    fallback_runs = [
        f"{role}:{row['coordinate']}"
        for role, artifact in (("baseline", baseline), ("challenger", challenger))
        for row in artifact.rows
        if _diagnostic_count(row, "fallback_attempts") > 0 or _diagnostic_count(row, "fallback_successes") > 0
    ]
    incomplete_curves = [
        f"{role}:{row['coordinate']}"
        for role, artifact in (("baseline", baseline), ("challenger", challenger))
        for row in artifact.rows
        if not bool(row.get("curve_complete"))
    ]
    return {
        "independent_verification": {
            "status": "passed" if not verification_failures else "failed",
            "failures": verification_failures,
        },
        "errors": {
            "status": "passed" if challenger_errors <= baseline_errors else "failed",
            "baseline": baseline_errors,
            "challenger": challenger_errors,
            "failures": [f"challenger:{row['coordinate']}" for row in challenger.rows if row.get("status") == "error"],
        },
        "timeouts": {
            "status": "passed" if len(challenger_timeouts) <= len(baseline_timeouts) else "failed",
            "baseline": len(baseline_timeouts),
            "challenger": len(challenger_timeouts),
            "failures": [f"challenger:{coordinate}" for coordinate in challenger_timeouts],
        },
        "explicit_strategy_fallback": {
            "status": "passed" if not fallback_runs else "failed",
            "failures": fallback_runs,
        },
        "curve_completeness": {
            "status": "passed" if not incomplete_curves else "failed",
            "failures": sorted(incomplete_curves),
        },
        "matrix_completeness": {"status": "passed"},
    }


def _compatibility_reasons(baseline: RunArtifact, challenger: RunArtifact) -> list[str]:
    reasons = []
    for field in ("protocol_checksum", "index_profile_checksum", "experiment_mode"):
        if baseline.manifest.get(field) != challenger.manifest.get(field):
            reasons.append(f"{field} differs")
    if baseline.manifest.get("role") != "baseline" or challenger.manifest.get("role") != "challenger":
        reasons.append("artifact roles must be baseline and challenger")
    mode = str(challenger.manifest.get("experiment_mode") or "")
    if mode not in {"implementation_comparison", "configuration_comparison"}:
        reasons.append(f"experiment mode is not promotable: {mode}")
    for field in ("coordinates", "platforms", "instance_checksums"):
        if baseline.manifest.get(field) != challenger.manifest.get(field):
            reasons.append(f"{field} differs")
    baseline_rows = {str(row["coordinate"]): row for row in baseline.rows}
    challenger_rows = {str(row["coordinate"]): row for row in challenger.rows}
    baseline_provenance = dict(baseline.manifest.get("provenance") or {})
    challenger_provenance = dict(challenger.manifest.get("provenance") or {})
    if baseline_provenance.get("benchmarks_commit") != challenger_provenance.get("benchmarks_commit"):
        reasons.append("benchmarks_commit differs")
    baseline_runtime = dict(baseline_provenance.get("installed_runtime") or {})
    challenger_runtime = dict(challenger_provenance.get("installed_runtime") or {})
    if baseline_runtime.get("python") != challenger_runtime.get("python"):
        reasons.append("Python runtime differs")
    if mode == "configuration_comparison":
        for field in ("optagent_commit", "wheel_sha256"):
            if baseline_provenance.get(field) != challenger_provenance.get(field):
                reasons.append(f"{field} must match for configuration comparison")
    for coordinate in sorted(set(baseline_rows) & set(challenger_rows)):
        left = baseline_rows[coordinate]
        right = challenger_rows[coordinate]
        for field in ("effective_budget", "thread_count", "platform"):
            if left.get(field) != right.get(field):
                reasons.append(f"{field} differs for {coordinate}")
        if mode == "implementation_comparison":
            if left.get("strategy_config") != right.get("strategy_config"):
                reasons.append(f"strategy_config differs for {coordinate}")
    return sorted(set(reasons))


def _profile_gate_failures(
    profile: Mapping[str, Any],
    pairs: Sequence[Mapping[str, Any]],
    hard_gates: Mapping[str, Any],
) -> list[str]:
    coordinates = {
        str(pair["coordinate"])
        for pair in pairs
        if pair["family"] == profile["family"] and pair["model_style"] == profile["model_style"]
    }
    failures = []
    for gate_name, gate in hard_gates.items():
        if gate.get("status") == "passed":
            continue
        gate_failures = [str(item) for item in gate.get("failures") or []]
        if not gate_failures or any(
            any(item.endswith(coordinate) for coordinate in coordinates) for item in gate_failures
        ):
            failures.append(gate_name)
    return sorted(failures)


def _aggregate_dimensions_by_family(profiles: dict[str, Any]) -> dict[str, Any]:
    dimensions = sorted(next(iter(profiles.values()))["dimensions"]) if profiles else []
    result = {}
    for dimension in dimensions:
        by_family: dict[str, list[float]] = defaultdict(list)
        for profile in profiles.values():
            index_value = profile["dimensions"][dimension]["index"]
            if index_value is not None:
                by_family[profile["family"]].append(float(index_value))
        family_indices = {family: _mean(values) for family, values in sorted(by_family.items())}
        result[dimension] = {
            "index": _mean([value for value in family_indices.values() if value is not None]),
            "family_indices": family_indices,
        }
    return result


def _aggregate_overall_by_family(profiles: dict[str, Any]) -> float | None:
    by_family: dict[str, list[float]] = defaultdict(list)
    for profile in profiles.values():
        if profile["overall_delta_index"] is not None:
            by_family[profile["family"]].append(float(profile["overall_delta_index"]))
    return _mean([_mean(values) for values in by_family.values() if values])


def _group_pairs(pairs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in pairs:
        grouped[f"{pair['family']}|{pair['model_style']}"].append(pair)
    return dict(grouped)


def _diagnostic_feedback(pairs: list[dict[str, Any]], profiles: Mapping[str, Any]) -> dict[str, Any]:
    quality_rows = [
        {
            "coordinate": pair["coordinate"],
            "family": pair["family"],
            "model_style": pair["model_style"],
            "benchmark_id": pair["benchmark_id"],
            "seed": pair["seed"],
            "improvement": pair["improvement"].get("final_gap"),
        }
        for pair in pairs
        if pair["improvement"].get("final_gap") is not None
    ]
    ordered = sorted(quality_rows, key=lambda row: float(row["improvement"]), reverse=True)
    profile_indices = [
        {
            "profile": name,
            "family": profile["family"],
            "model_style": profile["model_style"],
            "delta_index": profile["overall_delta_index"],
            "verdict": profile.get("verdict"),
        }
        for name, profile in profiles.items()
    ]
    profile_indices.sort(key=lambda row: float(row["delta_index"] or 0.0), reverse=True)
    return {
        "largest_quality_improvements": ordered[:5],
        "largest_quality_regressions": list(reversed(ordered[-5:])),
        "profile_contributions": profile_indices,
        "note": "Diagnostic feedback explains the index and does not add unversioned index weight.",
    }


def _normalized_primal_integral(
    curve: list[dict[str, Any]],
    time_budget: float,
    index_policy: IndexProfile,
) -> float:
    integral = 0.0
    previous_time = 0.0
    previous_gap = index_policy.unresolved_gap_penalty
    for point in sorted(curve, key=lambda item: float(item["elapsed_s"])):
        elapsed = min(time_budget, float(point["elapsed_s"]))
        if elapsed > previous_time:
            integral += min(index_policy.gap_cap, previous_gap) * (elapsed - previous_time)
        gap = point.get("gap_rel")
        previous_gap = index_policy.unresolved_gap_penalty if gap is None else max(0.0, float(gap))
        previous_time = elapsed
        if elapsed >= time_budget:
            break
    if previous_time < time_budget:
        integral += min(index_policy.gap_cap, previous_gap) * (time_budget - previous_time)
    return integral / time_budget


def _target_summary(curve: list[dict[str, Any]], targets: Sequence[float], budget: float) -> dict[str, float]:
    times = []
    hits = 0
    ordered = sorted(curve, key=lambda item: float(item["elapsed_s"]))
    for target in targets:
        hit = next(
            (
                float(point["elapsed_s"])
                for point in ordered
                if point.get("gap_rel") is not None and float(point["gap_rel"]) <= target
            ),
            None,
        )
        if hit is not None:
            hits += 1
            times.append(hit)
        else:
            times.append(budget)
    return {"hit_rate": hits / len(targets), "mean_time": float(statistics.mean(times))}


def _fixed_search_candidate_elapsed(
    telemetry: Mapping[str, Any],
    checkpoint: int,
) -> float | None:
    progress = telemetry.get("progress")
    for point in sorted(
        progress if isinstance(progress, list) else [],
        key=lambda item: float(item.get("elapsed_s") or 0.0),
    ):
        if not isinstance(point, Mapping) or point.get("event_kind") != "candidate_checkpoint":
            continue
        count = _telemetry_value(point.get("evaluated_candidates"))
        if count is not None and int(count) >= checkpoint:
            return _number(point.get("elapsed_s"))
    return None


def _canonical_run_facts(row: Mapping[str, Any], telemetry: Mapping[str, Any]) -> dict[str, float | None]:
    metric_row = build_metric_dataset([telemetry], provenance=["strategy-comparison-artifact"]).rows[0]
    reference = _number(row.get("reference_objective"))
    final_gap = None
    if metric_row.feasible and metric_row.objective is not None and reference is not None:
        denominator = max(abs(reference), 1e-12)
        raw_gap = (
            reference - metric_row.objective
            if metric_row.objective_sense == "maximize"
            else metric_row.objective - reference
        )
        final_gap = max(0.0, raw_gap / denominator)
    throughput = None
    if metric_row.wall_time_s and metric_row.wall_time_s > 0 and metric_row.evaluated_candidates is not None:
        throughput = metric_row.evaluated_candidates / metric_row.wall_time_s
    return {
        "final_gap": final_gap,
        "search_candidate_throughput": throughput,
    }


def _telemetry_value(value: Any) -> float | None:
    if isinstance(value, Mapping):
        return _number(value.get("number_value", value.get("integer_value")))
    return _number(value)


def _diagnostic_count(row: Mapping[str, Any], key: str) -> float:
    diagnostics = row.get("diagnostics")
    value = diagnostics.get(key) if isinstance(diagnostics, Mapping) else None
    if value is None:
        value = row.get(key)
    return _number(value) or 0.0


def _is_timeout(row: Mapping[str, Any]) -> bool:
    status = str(row.get("status") or "").lower()
    error = row.get("error")
    error_type = str(error.get("type") or "").lower() if isinstance(error, Mapping) else ""
    return status in {"timeout", "timed_out", "hard_timeout"} or error_type in {
        "timeout",
        "timed_out",
        "hard_timeout",
    }


def _curves_by_coordinate(curves: Iterable[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for point in curves:
        grouped[str(point["coordinate"])].append(dict(point))
    return dict(grouped)


def _pair_values(pairs: list[dict[str, Any]], side: str, metric: str) -> list[float]:
    return [float(pair[side][metric]) for pair in pairs if pair[side].get(metric) is not None]


def _paired_win_rate(pairs: Sequence[Mapping[str, Any]]) -> float | None:
    complete = [
        (float(pair["baseline"]["final_gap"]), float(pair["challenger"]["final_gap"]))
        for pair in pairs
        if pair["baseline"].get("final_gap") is not None and pair["challenger"].get("final_gap") is not None
    ]
    if not complete:
        return None
    wins = sum(1 for left, right in complete if right < left)
    ties = sum(1 for left, right in complete if math.isclose(right, left, abs_tol=1e-12))
    return (wins + 0.5 * ties) / len(complete)


def _case_direction_consistency(pairs: list[dict[str, Any]]) -> float | None:
    by_case: dict[str, list[float]] = defaultdict(list)
    for pair in pairs:
        left = pair["baseline"].get("final_gap")
        right = pair["challenger"].get("final_gap")
        if left is not None and right is not None:
            by_case[str(pair["benchmark_id"])].append(float(left) - float(right))
    if not by_case:
        return None
    outcomes = [_median(values) or 0.0 for values in by_case.values()]
    return (sum(value > 0 for value in outcomes) + 0.5 * sum(value == 0 for value in outcomes)) / len(outcomes)


def _gap_improvements(pairs: list[dict[str, Any]]) -> list[float]:
    return [
        float(pair["baseline"]["final_gap"]) - float(pair["challenger"]["final_gap"])
        for pair in pairs
        if pair["baseline"].get("final_gap") is not None and pair["challenger"].get("final_gap") is not None
    ]


def _win_tie_loss(improvements: list[float]) -> dict[str, Any]:
    return {
        "wins": sum(value > 1e-12 for value in improvements),
        "ties": sum(abs(value) <= 1e-12 for value in improvements),
        "losses": sum(value < -1e-12 for value in improvements),
        "pair_count": len(improvements),
    }


def _incompatible_result(
    baseline: RunArtifact,
    challenger: RunArtifact,
    reasons: list[str],
) -> dict[str, Any]:
    return {
        "comparison_schema_version": COMPARISON_SCHEMA_VERSION,
        "verdict": "incompatible",
        "promotable": False,
        "overall_delta_index": None,
        "dimensions": {},
        "profiles": {},
        "hard_gates": {},
        "compatibility_reasons": reasons,
        "statistical_evidence": {
            "final_gap_improvement_ci95": {
                "availability": "insufficient_data",
                "lower": None,
                "median": None,
                "upper": None,
            },
            "paired_outcomes": {"wins": 0, "ties": 0, "losses": 0, "pair_count": 0},
            "profiles": {},
        },
        "protocol_id": challenger.manifest.get("protocol_id"),
        "baseline": _artifact_identity(baseline),
        "challenger": _artifact_identity(challenger),
    }


def _artifact_identity(artifact: RunArtifact) -> dict[str, Any]:
    return {
        "path": str(artifact.root),
        "role": artifact.manifest.get("role"),
        "provenance": artifact.manifest.get("provenance"),
        "protocol_checksum": artifact.manifest.get("protocol_checksum"),
        "manifest_checksum": sha256_file(artifact.root / "manifest.json"),
    }


def _median(values: Sequence[float]) -> float | None:
    return float(statistics.median(values)) if values else None


def _mean(values: Sequence[float | None]) -> float | None:
    materialized = [float(value) for value in values if value is not None]
    return float(statistics.mean(materialized)) if materialized else None


def _mad(values: Sequence[float]) -> float | None:
    median = _median(values)
    return _median([abs(value - median) for value in values]) if median is not None else None


def _percentile(values: Sequence[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * quantile
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main(argv: Sequence[str] | None = None) -> int:
    from benchmarks.strategy_comparison_cli import main as cli_main

    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
