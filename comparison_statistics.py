from __future__ import annotations

from collections import defaultdict
import math
import random
import statistics
from typing import Any, Mapping, Sequence

from benchmarks.comparison_protocol import IndexProfile
from benchmarks.telemetry_metrics import holm_correction, wilcoxon_signed_rank


def build_statistical_evidence(
    profile_groups: Mapping[str, list[dict[str, Any]]],
    index_policy: IndexProfile,
) -> dict[str, Any]:
    profile_results = {}
    p_values: list[tuple[str, float | None]] = []
    for profile, pairs in sorted(profile_groups.items()):
        improvements = _gap_improvements(pairs)
        interval = _hierarchical_bootstrap_ci(pairs, index_policy.bootstrap_samples, index_policy.bootstrap_seed)
        complete = [
            pair
            for pair in pairs
            if pair["baseline"].get("final_gap") is not None and pair["challenger"].get("final_gap") is not None
        ]
        baseline_values = [float(pair["baseline"]["final_gap"]) for pair in complete]
        challenger_values = [float(pair["challenger"]["final_gap"]) for pair in complete]
        wilcoxon = wilcoxon_signed_rank(challenger_values, baseline_values)
        p_value = (
            float(wilcoxon["p_value"])
            if wilcoxon.get("availability") == "available" and wilcoxon.get("p_value") is not None
            else None
        )
        p_values.append((profile, p_value))
        profile_results[profile] = {
            "final_gap_improvement_ci95": interval,
            "paired_outcomes": _win_tie_loss(improvements),
            "wilcoxon": wilcoxon,
        }
    all_pairs = [pair for pairs in profile_groups.values() for pair in pairs]
    return {
        "final_gap_improvement_ci95": _family_balanced_bootstrap_ci(
            profile_groups, index_policy.bootstrap_samples, index_policy.bootstrap_seed
        ),
        "paired_outcomes": _win_tie_loss(_gap_improvements(all_pairs)),
        "profiles": profile_results,
        "multiple_comparison_correction": _holm_by_profile(p_values),
    }


def _hierarchical_bootstrap_ci(pairs: list[dict[str, Any]], samples: int, seed: int) -> dict[str, Any]:
    by_case = _improvements_by_case(pairs, include_profile=True)
    if not by_case:
        return _insufficient_interval()
    rng = random.Random(seed)
    estimates = []
    case_ids = sorted(by_case)
    for _ in range(max(1, samples)):
        values = []
        for _ in case_ids:
            selected_case = rng.choice(case_ids)
            seeds = by_case[selected_case]
            values.extend(rng.choice(seeds) for _ in range(len(seeds)))
        estimates.append(float(statistics.median(values)))
    return _interval(
        estimates,
        samples,
        resampling="case_then_seed",
        estimand="profile_median_final_gap_improvement",
    )


def _family_balanced_bootstrap_ci(
    profile_groups: Mapping[str, list[dict[str, Any]]],
    samples: int,
    seed: int,
) -> dict[str, Any]:
    by_family: dict[str, list[list[dict[str, Any]]]] = defaultdict(list)
    for pairs in profile_groups.values():
        if pairs:
            by_family[str(pairs[0]["family"])].append(pairs)
    if not by_family:
        return _insufficient_interval()
    rng = random.Random(seed)
    estimates = []
    for _ in range(max(1, samples)):
        family_estimates = []
        for family_profiles in by_family.values():
            profile_estimates = [_resampled_profile_median(pairs, rng) for pairs in family_profiles]
            available = [value for value in profile_estimates if value is not None]
            if available:
                family_estimates.append(statistics.mean(available))
        if family_estimates:
            estimates.append(statistics.mean(family_estimates))
    if not estimates:
        return _insufficient_interval()
    return _interval(
        estimates,
        samples,
        resampling="case_then_seed_with_fixed_equal_family_aggregation",
        estimand="equal_family_mean_of_profile_medians",
    )


def _resampled_profile_median(pairs: list[dict[str, Any]], rng: random.Random) -> float | None:
    by_case = _improvements_by_case(pairs, include_profile=False)
    if not by_case:
        return None
    values = []
    case_ids = sorted(by_case)
    for _ in case_ids:
        selected_case = rng.choice(case_ids)
        seeds = by_case[selected_case]
        values.extend(rng.choice(seeds) for _ in range(len(seeds)))
    return float(statistics.median(values))


def _improvements_by_case(
    pairs: Sequence[Mapping[str, Any]],
    *,
    include_profile: bool,
) -> dict[str, list[float]]:
    by_case: dict[str, list[float]] = defaultdict(list)
    for pair in pairs:
        baseline = pair["baseline"].get("final_gap")
        challenger = pair["challenger"].get("final_gap")
        if baseline is None or challenger is None:
            continue
        prefix = f"{pair['family']}|{pair['model_style']}|" if include_profile else ""
        by_case[f"{prefix}{pair['benchmark_id']}"].append(float(baseline) - float(challenger))
    return by_case


def _holm_by_profile(p_values: list[tuple[str, float | None]]) -> dict[str, Any]:
    available = [(profile, p_value) for profile, p_value in p_values if p_value is not None]
    correction = holm_correction([p_value for _, p_value in available])
    adjusted = correction.get("adjusted_p_values") or [None] * len(available)
    rejected = correction.get("rejected") or [None] * len(available)
    corrected = {
        profile: {"adjusted_p_value": adjusted[index], "rejected": rejected[index]}
        for index, (profile, _) in enumerate(available)
    }
    correction["profiles"] = {
        profile: {
            "raw_p_value": p_value,
            "adjusted_p_value": corrected.get(profile, {}).get("adjusted_p_value"),
            "rejected": corrected.get(profile, {}).get("rejected"),
        }
        for profile, p_value in p_values
    }
    return correction


def _gap_improvements(pairs: Sequence[Mapping[str, Any]]) -> list[float]:
    return [
        float(pair["baseline"]["final_gap"]) - float(pair["challenger"]["final_gap"])
        for pair in pairs
        if pair["baseline"].get("final_gap") is not None and pair["challenger"].get("final_gap") is not None
    ]


def _win_tie_loss(improvements: Sequence[float]) -> dict[str, Any]:
    return {
        "wins": sum(value > 1e-12 for value in improvements),
        "ties": sum(abs(value) <= 1e-12 for value in improvements),
        "losses": sum(value < -1e-12 for value in improvements),
        "pair_count": len(improvements),
    }


def _interval(estimates: list[float], samples: int, *, resampling: str, estimand: str) -> dict[str, Any]:
    estimates.sort()
    return {
        "availability": "available",
        "lower": _percentile(estimates, 0.025),
        "median": _percentile(estimates, 0.5),
        "upper": _percentile(estimates, 0.975),
        "bootstrap_samples": max(1, samples),
        "resampling": resampling,
        "estimand": estimand,
    }


def _insufficient_interval() -> dict[str, Any]:
    return {"availability": "insufficient_data", "lower": None, "median": None, "upper": None}


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
