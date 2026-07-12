from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
from typing import Any, Iterable, Mapping, Sequence

from benchmarks.evaluation_artifacts import EvaluationArtifact, load_evaluation_artifact
from benchmarks.evaluation_protocol import MetricThreshold, ScoringProfile, get_scoring_profile
from benchmarks.telemetry_metrics import holm_correction, wilcoxon_signed_rank


COMPARISON_SCHEMA_VERSION = 1


def compare_evaluation_artifacts(
    baseline_path: str | Path,
    candidate_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    baseline = load_evaluation_artifact(baseline_path)
    candidate = load_evaluation_artifact(candidate_path)
    out = Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"comparison output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    compatibility_reasons = _compatibility_reasons(baseline, candidate)
    if compatibility_reasons:
        result = _incompatible_result(baseline, candidate, compatibility_reasons)
        _publish_comparison(out, result, [], {}, result["statistical_evidence"])
        return result

    scoring = get_scoring_profile(str(candidate.manifest["scoring_profile_id"]))
    pairs = _paired_metrics(baseline, candidate, scoring)
    hard_gates = _hard_gates(baseline, candidate)
    profile_groups = _group_pairs(pairs)
    profile_results = {
        profile: _score_profile(profile_pairs, scoring) for profile, profile_pairs in sorted(profile_groups.items())
    }
    statistical = _statistical_evidence(profile_groups, scoring)
    for profile, profile_result in profile_results.items():
        profile_result["verdict"] = _profile_verdict(
            profile_result,
            statistical["profiles"][profile],
            scoring,
        )
    dimensions = _aggregate_dimensions_by_family(profile_results)
    overall_score = _aggregate_overall_by_family(profile_results)
    diagnostic_feedback = _diagnostic_feedback(pairs, profile_results)
    verdict = _verdict(overall_score, dimensions, profile_results, hard_gates, statistical, scoring)
    result = {
        "comparison_schema_version": COMPARISON_SCHEMA_VERSION,
        "verdict": verdict,
        "promotable": verdict == "improved",
        "overall_delta_score": overall_score,
        "dimensions": dimensions,
        "profiles": profile_results,
        "hard_gates": hard_gates,
        "statistical_evidence": statistical,
        "diagnostic_feedback": diagnostic_feedback,
        "protocol_id": candidate.manifest["protocol_id"],
        "protocol_checksum": candidate.manifest["protocol_checksum"],
        "scoring_profile_id": candidate.manifest["scoring_profile_id"],
        "scoring_profile_checksum": candidate.manifest["scoring_profile_checksum"],
        "baseline": _artifact_identity(baseline),
        "candidate": _artifact_identity(candidate),
    }
    _publish_comparison(out, result, pairs, dimensions, statistical)
    return result


def _paired_metrics(
    baseline: EvaluationArtifact,
    candidate: EvaluationArtifact,
    scoring: ScoringProfile,
) -> list[dict[str, Any]]:
    baseline_rows = {str(row["coordinate"]): row for row in baseline.rows}
    candidate_rows = {str(row["coordinate"]): row for row in candidate.rows}
    baseline_curves = _curves_by_coordinate(baseline.curves)
    candidate_curves = _curves_by_coordinate(candidate.curves)
    baseline_telemetry = {str(row["coordinate"]): row for row in baseline.telemetry}
    candidate_telemetry = {str(row["coordinate"]): row for row in candidate.telemetry}
    candidate_checkpoint = int(candidate.protocol["protocol"]["candidate_checkpoint"])
    time_budget = float(candidate.protocol["protocol"]["wall_time_s"])
    pairs = []
    for coordinate in sorted(baseline_rows):
        left = baseline_rows[coordinate]
        right = candidate_rows[coordinate]
        left_curve = baseline_curves.get(coordinate, [])
        right_curve = candidate_curves.get(coordinate, [])
        left_complete = bool(left.get("curve_complete"))
        right_complete = bool(right.get("curve_complete"))
        left_targets = _target_summary(left_curve, scoring.target_gaps, time_budget) if left_complete else None
        right_targets = _target_summary(right_curve, scoring.target_gaps, time_budget) if right_complete else None
        pairs.append(
            {
                "coordinate": coordinate,
                "family": right["family"],
                "model_style": right["model_style"],
                "benchmark_id": right["benchmark_id"],
                "seed": right["seed"],
                "baseline": {
                    "final_gap": _final_gap(left),
                    "normalized_primal_integral": (
                        _normalized_primal_integral(left_curve, time_budget, scoring) if left_complete else None
                    ),
                    "target_hit_rate": left_targets["hit_rate"] if left_targets else None,
                    "time_to_target": left_targets["mean_time"] if left_targets else None,
                    "candidate_throughput": _candidate_throughput(left, baseline_telemetry[coordinate]),
                    "fixed_candidate_elapsed": (
                        _fixed_candidate_elapsed(baseline_telemetry[coordinate], candidate_checkpoint)
                        if left_complete
                        else None
                    ),
                },
                "candidate": {
                    "final_gap": _final_gap(right),
                    "normalized_primal_integral": (
                        _normalized_primal_integral(right_curve, time_budget, scoring) if right_complete else None
                    ),
                    "target_hit_rate": right_targets["hit_rate"] if right_targets else None,
                    "time_to_target": right_targets["mean_time"] if right_targets else None,
                    "candidate_throughput": _candidate_throughput(right, candidate_telemetry[coordinate]),
                    "fixed_candidate_elapsed": (
                        _fixed_candidate_elapsed(candidate_telemetry[coordinate], candidate_checkpoint)
                        if right_complete
                        else None
                    ),
                },
            }
        )
    for pair in pairs:
        pair["improvement"] = {
            metric: _metric_improvement(metric, pair["baseline"].get(metric), pair["candidate"].get(metric))
            for metric in pair["baseline"]
        }
    return pairs


def _score_profile(pairs: list[dict[str, Any]], scoring: ScoringProfile) -> dict[str, Any]:
    base_gaps = _pair_values(pairs, "baseline", "final_gap")
    candidate_gaps = _pair_values(pairs, "candidate", "final_gap")
    win_rate = _paired_win_rate(base_gaps, candidate_gaps)
    consistency = _case_direction_consistency(pairs)
    component_values = {
        "median_final_gap": (_median(base_gaps), _median(candidate_gaps)),
        "paired_quality_win_rate": (0.5, win_rate),
        "normalized_primal_integral": (
            _median(_pair_values(pairs, "baseline", "normalized_primal_integral")),
            _median(_pair_values(pairs, "candidate", "normalized_primal_integral")),
        ),
        "target_hit_rate": (
            _mean(_pair_values(pairs, "baseline", "target_hit_rate")),
            _mean(_pair_values(pairs, "candidate", "target_hit_rate")),
        ),
        "time_to_target": (
            _median(_pair_values(pairs, "baseline", "time_to_target")),
            _median(_pair_values(pairs, "candidate", "time_to_target")),
        ),
        "p90_final_gap": (_percentile(base_gaps, 0.9), _percentile(candidate_gaps, 0.9)),
        "gap_mad": (_mad(base_gaps), _mad(candidate_gaps)),
        "case_direction_consistency": (0.5, consistency),
        "candidate_throughput": (
            _median(_pair_values(pairs, "baseline", "candidate_throughput")),
            _median(_pair_values(pairs, "candidate", "candidate_throughput")),
        ),
        "fixed_candidate_elapsed": (
            _median(_pair_values(pairs, "baseline", "fixed_candidate_elapsed")),
            _median(_pair_values(pairs, "candidate", "fixed_candidate_elapsed")),
        ),
    }
    components = {
        name: _component_score(name, baseline, candidate, scoring.thresholds[name])
        for name, (baseline, candidate) in component_values.items()
    }
    dimensions = {}
    for dimension, weights in scoring.component_weights.items():
        values = [components[name] for name in weights]
        available = [value for value in values if value["availability"] == "available"]
        score = (
            sum(components[name]["score"] * weight for name, weight in weights.items())
            if len(available) == len(values)
            else None
        )
        dimensions[dimension] = {
            "score": score,
            "availability": "available" if score is not None else "insufficient_data",
            "components": {name: components[name] for name in weights},
        }
    overall = (
        sum(dimensions[name]["score"] * weight for name, weight in scoring.dimension_weights.items())
        if all(dimensions[name]["score"] is not None for name in scoring.dimension_weights)
        else None
    )
    final_gap_improvements = [
        float(pair["baseline"]["final_gap"]) - float(pair["candidate"]["final_gap"])
        for pair in pairs
        if pair["baseline"]["final_gap"] is not None and pair["candidate"]["final_gap"] is not None
    ]
    worst_baseline = max(base_gaps) if base_gaps else None
    worst_candidate = max(candidate_gaps) if candidate_gaps else None
    worst_tolerance = max(0.01, abs(worst_baseline or 0.0) * 0.1)
    return {
        "family": pairs[0]["family"],
        "model_style": pairs[0]["model_style"],
        "pair_count": len(pairs),
        "overall_delta_score": overall,
        "dimensions": dimensions,
        "final_gap_median_improvement": _median(final_gap_improvements),
        "worst_gap_guard": {
            "baseline": worst_baseline,
            "candidate": worst_candidate,
            "tolerance": worst_tolerance,
            "triggered": (
                worst_baseline is not None
                and worst_candidate is not None
                and worst_candidate - worst_baseline > worst_tolerance
            ),
        },
    }


def _component_score(
    name: str,
    baseline: float | None,
    candidate: float | None,
    threshold: MetricThreshold,
) -> dict[str, Any]:
    if baseline is None or candidate is None:
        return {
            "availability": "insufficient_data",
            "baseline": baseline,
            "candidate": candidate,
            "score": None,
        }
    improvement = _metric_improvement(name, baseline, candidate)
    scale = _threshold_scale(baseline, threshold)
    score = max(-100.0, min(100.0, 100.0 * improvement / scale)) if scale > 0 else 0.0
    return {
        "availability": "available",
        "baseline": baseline,
        "candidate": candidate,
        "improvement": improvement,
        "meaningful_change_threshold": scale,
        "score": score,
    }


def _metric_improvement(name: str, baseline: float | None, candidate: float | None) -> float | None:
    if baseline is None or candidate is None:
        return None
    higher_is_better = name in {
        "paired_quality_win_rate",
        "target_hit_rate",
        "case_direction_consistency",
        "candidate_throughput",
    }
    return candidate - baseline if higher_is_better else baseline - candidate


def _threshold_scale(baseline: float, threshold: MetricThreshold) -> float:
    if threshold.mode == "absolute":
        return threshold.value
    relative = abs(baseline) * threshold.value
    if threshold.mode == "relative":
        return max(relative, 1e-12)
    return max(threshold.absolute_floor, relative)


def _hard_gates(baseline: EvaluationArtifact, candidate: EvaluationArtifact) -> dict[str, Any]:
    baseline_errors = sum(1 for row in baseline.rows if row.get("status") == "error")
    candidate_errors = sum(1 for row in candidate.rows if row.get("status") == "error")
    verification_failures = [
        str(row["coordinate"])
        for row in candidate.rows
        if row.get("verification_status") != "passed" or not bool(row.get("verification_passed"))
    ]
    fallback_runs = [
        str(row["coordinate"])
        for row in candidate.rows
        if _diagnostic_count(row, "fallback_attempts") > 0 or _diagnostic_count(row, "fallback_successes") > 0
    ]
    incomplete_curves = [
        str(row["coordinate"]) for row in [*baseline.rows, *candidate.rows] if not bool(row.get("curve_complete"))
    ]
    return {
        "independent_verification": {
            "status": "passed" if not verification_failures else "failed",
            "failures": verification_failures,
        },
        "errors": {
            "status": "passed" if candidate_errors <= baseline_errors else "failed",
            "baseline": baseline_errors,
            "candidate": candidate_errors,
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


def _compatibility_reasons(baseline: EvaluationArtifact, candidate: EvaluationArtifact) -> list[str]:
    reasons = []
    for field in ("protocol_checksum", "scoring_profile_checksum", "experiment_mode"):
        if baseline.manifest.get(field) != candidate.manifest.get(field):
            reasons.append(f"{field} differs")
    if baseline.manifest.get("role") != "baseline" or candidate.manifest.get("role") != "candidate":
        reasons.append("artifact roles must be baseline and candidate")
    mode = str(candidate.manifest.get("experiment_mode") or "")
    if mode not in {"implementation_comparison", "configuration_comparison"}:
        reasons.append(f"experiment mode is not promotable: {mode}")
    for field in ("coordinates", "platforms", "instance_checksums"):
        if baseline.manifest.get(field) != candidate.manifest.get(field):
            reasons.append(f"{field} differs")
    baseline_rows = {str(row["coordinate"]): row for row in baseline.rows}
    candidate_rows = {str(row["coordinate"]): row for row in candidate.rows}
    baseline_provenance = dict(baseline.manifest.get("provenance") or {})
    candidate_provenance = dict(candidate.manifest.get("provenance") or {})
    if baseline_provenance.get("benchmarks_commit") != candidate_provenance.get("benchmarks_commit"):
        reasons.append("benchmarks_commit differs")
    baseline_runtime = dict(baseline_provenance.get("installed_runtime") or {})
    candidate_runtime = dict(candidate_provenance.get("installed_runtime") or {})
    if baseline_runtime.get("python") != candidate_runtime.get("python"):
        reasons.append("Python runtime differs")
    if mode == "configuration_comparison":
        for field in ("optagent_commit", "wheel_sha256"):
            if baseline_provenance.get(field) != candidate_provenance.get(field):
                reasons.append(f"{field} must match for configuration comparison")
    for coordinate in sorted(set(baseline_rows) & set(candidate_rows)):
        left = baseline_rows[coordinate]
        right = candidate_rows[coordinate]
        for field in ("effective_budget", "thread_count", "platform"):
            if left.get(field) != right.get(field):
                reasons.append(f"{field} differs for {coordinate}")
        if mode == "implementation_comparison":
            if left.get("strategy_config") != right.get("strategy_config"):
                reasons.append(f"strategy_config differs for {coordinate}")
    return sorted(set(reasons))


def _statistical_evidence(
    profile_groups: Mapping[str, list[dict[str, Any]]],
    scoring: ScoringProfile,
) -> dict[str, Any]:
    profile_results = {}
    p_values = []
    all_pairs = []
    for profile, pairs in sorted(profile_groups.items()):
        all_pairs.extend(pairs)
        improvements = _gap_improvements(pairs)
        ci = _hierarchical_bootstrap_ci(pairs, scoring.bootstrap_samples, scoring.bootstrap_seed)
        baseline_values = [float(pair["baseline"]["final_gap"]) for pair in pairs]
        candidate_values = [float(pair["candidate"]["final_gap"]) for pair in pairs]
        wilcoxon = wilcoxon_signed_rank(candidate_values, baseline_values)
        if wilcoxon.get("availability") == "available" and wilcoxon.get("p_value") is not None:
            p_values.append(float(wilcoxon["p_value"]))
        profile_results[profile] = {
            "final_gap_improvement_ci95": ci,
            "paired_outcomes": _win_tie_loss(improvements),
            "wilcoxon": wilcoxon,
        }
    return {
        "final_gap_improvement_ci95": _hierarchical_bootstrap_ci(
            all_pairs, scoring.bootstrap_samples, scoring.bootstrap_seed
        ),
        "paired_outcomes": _win_tie_loss(_gap_improvements(all_pairs)),
        "profiles": profile_results,
        "multiple_comparison_correction": holm_correction(p_values),
    }


def _hierarchical_bootstrap_ci(pairs: list[dict[str, Any]], samples: int, seed: int) -> dict[str, Any]:
    if not pairs:
        return {"availability": "insufficient_data", "lower": None, "median": None, "upper": None}
    by_case: dict[str, list[float]] = defaultdict(list)
    for pair in pairs:
        left = pair["baseline"].get("final_gap")
        right = pair["candidate"].get("final_gap")
        if left is not None and right is not None:
            case_key = f"{pair['family']}|{pair['model_style']}|{pair['benchmark_id']}"
            by_case[case_key].append(float(left) - float(right))
    if not by_case:
        return {"availability": "insufficient_data", "lower": None, "median": None, "upper": None}
    rng = random.Random(seed)
    case_ids = sorted(by_case)
    estimates = []
    for _ in range(max(1, samples)):
        values = []
        for _case_index in case_ids:
            selected_case = rng.choice(case_ids)
            seeds = by_case[selected_case]
            values.extend(rng.choice(seeds) for _ in range(len(seeds)))
        estimates.append(float(statistics.median(values)))
    estimates.sort()
    return {
        "availability": "available",
        "lower": _percentile(estimates, 0.025),
        "median": _percentile(estimates, 0.5),
        "upper": _percentile(estimates, 0.975),
        "bootstrap_samples": max(1, samples),
        "resampling": "case_then_seed",
    }


def _verdict(
    overall: float | None,
    dimensions: dict[str, Any],
    profiles: dict[str, Any],
    hard_gates: dict[str, Any],
    statistical: dict[str, Any],
    scoring: ScoringProfile,
) -> str:
    if any(gate.get("status") != "passed" for gate in hard_gates.values()):
        return "invalid"
    profile_verdicts = {profile.get("verdict") for profile in profiles.values()}
    if "invalid" in profile_verdicts:
        return "invalid"
    if "regressed" in profile_verdicts:
        return "regressed"
    if "mixed" in profile_verdicts:
        return "mixed"
    if overall is None or any(item.get("score") is None for item in dimensions.values()):
        return "invalid"
    if any(profile["worst_gap_guard"]["triggered"] for profile in profiles.values()):
        return "regressed"
    dimension_scores = [float(item["score"]) for item in dimensions.values()]
    if any(score < scoring.dimension_regression_limit for score in dimension_scores):
        return "regressed"
    ci = statistical["final_gap_improvement_ci95"]
    lower = ci.get("lower")
    upper = ci.get("upper")
    if overall <= -scoring.verdict_threshold or (upper is not None and upper < 0):
        return "regressed"
    if overall >= scoring.verdict_threshold and lower is not None and lower > 0 and "improved" in profile_verdicts:
        return "improved"
    if overall > 0 and any(score < 0 for score in dimension_scores):
        return "mixed"
    return "neutral"


def _profile_verdict(
    profile: Mapping[str, Any],
    statistical: Mapping[str, Any],
    scoring: ScoringProfile,
) -> str:
    overall = profile.get("overall_delta_score")
    if overall is None:
        return "invalid"
    if profile["worst_gap_guard"]["triggered"]:
        return "regressed"
    dimension_scores = [item.get("score") for item in profile["dimensions"].values()]
    if any(score is None for score in dimension_scores):
        return "invalid"
    numeric_scores = [float(score) for score in dimension_scores]
    if any(score < scoring.dimension_regression_limit for score in numeric_scores):
        return "regressed"
    ci = statistical["final_gap_improvement_ci95"]
    lower = ci.get("lower")
    upper = ci.get("upper")
    if float(overall) <= -scoring.verdict_threshold or (upper is not None and upper < 0):
        return "regressed"
    if float(overall) >= scoring.verdict_threshold and lower is not None and lower > 0:
        return "improved"
    if float(overall) > 0 and any(score < 0 for score in numeric_scores):
        return "mixed"
    return "neutral"


def _aggregate_dimensions_by_family(profiles: dict[str, Any]) -> dict[str, Any]:
    dimensions = sorted(next(iter(profiles.values()))["dimensions"]) if profiles else []
    result = {}
    for dimension in dimensions:
        by_family: dict[str, list[float]] = defaultdict(list)
        for profile in profiles.values():
            score = profile["dimensions"][dimension]["score"]
            if score is not None:
                by_family[profile["family"]].append(float(score))
        family_scores = {family: _mean(values) for family, values in sorted(by_family.items())}
        result[dimension] = {
            "score": _mean([value for value in family_scores.values() if value is not None]),
            "family_scores": family_scores,
        }
    return result


def _aggregate_overall_by_family(profiles: dict[str, Any]) -> float | None:
    by_family: dict[str, list[float]] = defaultdict(list)
    for profile in profiles.values():
        if profile["overall_delta_score"] is not None:
            by_family[profile["family"]].append(float(profile["overall_delta_score"]))
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
    profile_scores = [
        {
            "profile": name,
            "family": profile["family"],
            "model_style": profile["model_style"],
            "delta_score": profile["overall_delta_score"],
            "verdict": profile.get("verdict"),
        }
        for name, profile in profiles.items()
    ]
    profile_scores.sort(key=lambda row: float(row["delta_score"] or 0.0), reverse=True)
    return {
        "largest_quality_improvements": ordered[:5],
        "largest_quality_regressions": list(reversed(ordered[-5:])),
        "profile_contributions": profile_scores,
        "note": "Diagnostic feedback explains the score and does not add unversioned scoring weight.",
    }


def _normalized_primal_integral(
    curve: list[dict[str, Any]],
    time_budget: float,
    scoring: ScoringProfile,
) -> float:
    integral = 0.0
    previous_time = 0.0
    previous_gap = scoring.unresolved_gap_penalty
    for point in sorted(curve, key=lambda item: float(item["elapsed_s"])):
        elapsed = min(time_budget, float(point["elapsed_s"]))
        if elapsed > previous_time:
            integral += min(scoring.gap_cap, previous_gap) * (elapsed - previous_time)
        gap = point.get("gap_rel")
        previous_gap = scoring.unresolved_gap_penalty if gap is None else max(0.0, float(gap))
        previous_time = elapsed
        if elapsed >= time_budget:
            break
    if previous_time < time_budget:
        integral += min(scoring.gap_cap, previous_gap) * (time_budget - previous_time)
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


def _fixed_candidate_elapsed(telemetry: Mapping[str, Any], checkpoint: int) -> float | None:
    progress = telemetry.get("progress")
    for point in sorted(
        progress if isinstance(progress, list) else [],
        key=lambda item: float(item.get("elapsed_s") or 0.0),
    ):
        count = _telemetry_value(point.get("evaluated_candidates")) if isinstance(point, Mapping) else None
        if count is not None and int(count) >= checkpoint:
            return _number(point.get("elapsed_s"))
    return None


def _candidate_throughput(row: Mapping[str, Any], telemetry: Mapping[str, Any]) -> float | None:
    effort = telemetry.get("effort")
    elapsed = _telemetry_value(effort.get("wall_time_s")) if isinstance(effort, Mapping) else None
    count = _telemetry_value(effort.get("evaluated_candidates")) if isinstance(effort, Mapping) else None
    elapsed = elapsed if elapsed is not None else _number(row.get("elapsed_seconds"))
    count = count if count is not None else _diagnostic_count(row, "evaluated_candidates")
    return count / elapsed if elapsed and elapsed > 0 and count > 0 else None


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


def _final_gap(row: Mapping[str, Any]) -> float | None:
    gap = _number(row.get("gap_rel"))
    return max(0.0, gap) if gap is not None else None


def _curves_by_coordinate(curves: Iterable[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for point in curves:
        grouped[str(point["coordinate"])].append(dict(point))
    return dict(grouped)


def _pair_values(pairs: list[dict[str, Any]], side: str, metric: str) -> list[float]:
    return [float(pair[side][metric]) for pair in pairs if pair[side].get(metric) is not None]


def _paired_win_rate(baseline: list[float], candidate: list[float]) -> float | None:
    if len(baseline) != len(candidate) or not baseline:
        return None
    wins = sum(1 for left, right in zip(baseline, candidate) if right < left)
    ties = sum(1 for left, right in zip(baseline, candidate) if math.isclose(right, left, abs_tol=1e-12))
    return (wins + 0.5 * ties) / len(baseline)


def _case_direction_consistency(pairs: list[dict[str, Any]]) -> float | None:
    by_case: dict[str, list[float]] = defaultdict(list)
    for pair in pairs:
        left = pair["baseline"].get("final_gap")
        right = pair["candidate"].get("final_gap")
        if left is not None and right is not None:
            by_case[str(pair["benchmark_id"])].append(float(left) - float(right))
    if not by_case:
        return None
    outcomes = [_median(values) or 0.0 for values in by_case.values()]
    return (sum(value > 0 for value in outcomes) + 0.5 * sum(value == 0 for value in outcomes)) / len(outcomes)


def _gap_improvements(pairs: list[dict[str, Any]]) -> list[float]:
    return [
        float(pair["baseline"]["final_gap"]) - float(pair["candidate"]["final_gap"])
        for pair in pairs
        if pair["baseline"].get("final_gap") is not None and pair["candidate"].get("final_gap") is not None
    ]


def _win_tie_loss(improvements: list[float]) -> dict[str, Any]:
    return {
        "wins": sum(value > 1e-12 for value in improvements),
        "ties": sum(abs(value) <= 1e-12 for value in improvements),
        "losses": sum(value < -1e-12 for value in improvements),
        "pair_count": len(improvements),
    }


def _incompatible_result(
    baseline: EvaluationArtifact,
    candidate: EvaluationArtifact,
    reasons: list[str],
) -> dict[str, Any]:
    return {
        "comparison_schema_version": COMPARISON_SCHEMA_VERSION,
        "verdict": "incompatible",
        "promotable": False,
        "overall_delta_score": None,
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
        "protocol_id": candidate.manifest.get("protocol_id"),
        "baseline": _artifact_identity(baseline),
        "candidate": _artifact_identity(candidate),
    }


def _artifact_identity(artifact: EvaluationArtifact) -> dict[str, Any]:
    return {
        "path": str(artifact.root),
        "role": artifact.manifest.get("role"),
        "provenance": artifact.manifest.get("provenance"),
        "protocol_checksum": artifact.manifest.get("protocol_checksum"),
    }


def _publish_comparison(
    out: Path,
    result: dict[str, Any],
    pairs: list[dict[str, Any]],
    dimensions: dict[str, Any],
    statistical: dict[str, Any],
) -> None:
    _write_jsonl(out / "paired_rows.jsonl", pairs)
    _write_json(out / "dimension_metrics.json", {"dimensions": dimensions, "profiles": result.get("profiles", {})})
    _write_json(out / "statistical_evidence.json", statistical)
    _write_json(out / "score.json", result)
    (out / "feedback.md").write_text(_render_feedback(result), encoding="utf-8")
    artifact_names = (
        "paired_rows.jsonl",
        "dimension_metrics.json",
        "statistical_evidence.json",
        "score.json",
        "feedback.md",
    )
    manifest = {
        "comparison_schema_version": COMPARISON_SCHEMA_VERSION,
        "kind": "optagent_strategy_comparison",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verdict": result["verdict"],
        "protocol_id": result.get("protocol_id"),
        "artifacts": {
            name: {"sha256": _sha256(out / name), "bytes": (out / name).stat().st_size} for name in artifact_names
        },
    }
    _write_json(out / "comparison_manifest.json", manifest)


def _render_feedback(result: Mapping[str, Any]) -> str:
    lines = [
        "# GA Strategy Evaluation",
        "",
        f"- Verdict: `{result.get('verdict')}`",
        f"- Overall Delta Score: `{_display(result.get('overall_delta_score'))}`",
        f"- Promotable: `{str(bool(result.get('promotable'))).lower()}`",
        "",
        "## Dimensions",
        "",
        "| Dimension | Delta Score |",
        "| --- | ---: |",
    ]
    for name, value in dict(result.get("dimensions") or {}).items():
        lines.append(f"| {name} | {_display(value.get('score'))} |")
    lines.extend(["", "## Hard Gates", ""])
    for name, gate in dict(result.get("hard_gates") or {}).items():
        lines.append(f"- `{name}`: `{gate.get('status')}`")
    feedback = result.get("diagnostic_feedback")
    if isinstance(feedback, Mapping):
        lines.extend(["", "## Largest Quality Changes", ""])
        for row in feedback.get("largest_quality_improvements", [])[:3]:
            lines.append(f"- Improved `{row['coordinate']}` by `{_display(row['improvement'])}` gap units")
        for row in feedback.get("largest_quality_regressions", [])[:3]:
            if float(row.get("improvement") or 0.0) < 0:
                lines.append(f"- Regressed `{row['coordinate']}` by `{_display(-float(row['improvement']))}` gap units")
    reasons = result.get("compatibility_reasons")
    if reasons:
        lines.extend(["", "## Compatibility", ""])
        lines.extend(f"- {reason}" for reason in reasons)
    return "\n".join(lines).rstrip() + "\n"


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


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(dict(row), ensure_ascii=True, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _display(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.3f}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or compare OptAgent GA strategy evaluations.")
    commands = parser.add_subparsers(dest="command", required=True)
    compare = commands.add_parser("compare", help="Compare two immutable evaluation artifacts.")
    compare.add_argument("--baseline", required=True)
    compare.add_argument("--candidate", required=True)
    compare.add_argument("--output-dir", required=True)
    run_pair = commands.add_parser("run-pair", help="Run baseline and candidate wheels through one protocol.")
    run_pair.add_argument("--protocol", required=True)
    run_pair.add_argument("--baseline-wheel", required=True)
    run_pair.add_argument("--candidate-wheel", required=True)
    run_pair.add_argument("--output-dir", required=True)
    run_pair.add_argument("--python-executable", default=None)
    run_pair.add_argument("--baseline-commit", default="unknown")
    run_pair.add_argument("--candidate-commit", default="unknown")
    run_pair.add_argument("--allow-download", action="store_true")
    promote = commands.add_parser("promote", help="Explicitly promote an improved comparison to a baseline registry.")
    promote.add_argument("--comparison-dir", required=True)
    promote.add_argument("--registry", required=True)
    promote.add_argument("--approved-by", required=True)
    args = parser.parse_args()
    if args.command == "compare":
        result = compare_evaluation_artifacts(args.baseline, args.candidate, args.output_dir)
    elif args.command == "run-pair":
        import sys

        from benchmarks.evaluation_protocol import get_evaluation_protocol
        from benchmarks.strategy_evaluation_runner import run_protocol_pair

        result = run_protocol_pair(
            protocol=get_evaluation_protocol(args.protocol),
            baseline_wheel=args.baseline_wheel,
            candidate_wheel=args.candidate_wheel,
            output_dir=args.output_dir,
            bootstrap_python=args.python_executable or sys.executable,
            allow_download=bool(args.allow_download),
            baseline_commit=args.baseline_commit,
            candidate_commit=args.candidate_commit,
        )
    else:
        from benchmarks.strategy_baselines import promote_comparison_baseline

        result = promote_comparison_baseline(
            args.comparison_dir,
            args.registry,
            approved_by=args.approved_by,
        )
    print(json.dumps(result, indent=2, ensure_ascii=True, sort_keys=True))
    if args.command == "promote":
        return 0
    return 0 if result["verdict"] not in {"invalid", "incompatible", "regressed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
