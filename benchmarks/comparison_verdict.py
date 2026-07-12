from __future__ import annotations

from typing import Any, Mapping, Sequence

from benchmarks.comparison_protocol import IndexProfile


def decide_verdict(
    overall: float | None,
    dimensions: Mapping[str, Any],
    profiles: Mapping[str, Any],
    hard_gates: Mapping[str, Any],
    statistical: Mapping[str, Any],
    index_policy: IndexProfile,
    protocol_kind: str,
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
    if overall is None or any(item.get("index") is None for item in dimensions.values()):
        return "invalid"
    if any(profile["worst_gap_guard"]["triggered"] for profile in profiles.values()):
        return "regressed"
    dimension_indices = [float(item["index"]) for item in dimensions.values()]
    if any(index < index_policy.dimension_regression_limit for index in dimension_indices):
        return "regressed"
    interval = statistical["final_gap_improvement_ci95"]
    lower = interval.get("lower")
    upper = interval.get("upper")
    if overall <= -index_policy.verdict_threshold or (upper is not None and upper < 0):
        return "regressed"
    if (
        protocol_kind != "smoke"
        and overall >= index_policy.verdict_threshold
        and lower is not None
        and lower > 0
        and "improved" in profile_verdicts
    ):
        return "improved"
    if overall > 0 and any(index < 0 for index in dimension_indices):
        return "mixed"
    return "neutral"


def decide_profile_verdict(
    profile: Mapping[str, Any],
    statistical: Mapping[str, Any],
    index_policy: IndexProfile,
    hard_gate_failures: Sequence[str],
) -> str:
    if hard_gate_failures:
        return "invalid"
    overall = profile.get("overall_delta_index")
    if overall is None or profile["worst_gap_guard"]["triggered"]:
        return "invalid" if overall is None else "regressed"
    dimension_indices = [item.get("index") for item in profile["dimensions"].values()]
    if any(index is None for index in dimension_indices):
        return "invalid"
    numeric_indices = [float(index) for index in dimension_indices]
    if any(index < index_policy.dimension_regression_limit for index in numeric_indices):
        return "regressed"
    interval = statistical["final_gap_improvement_ci95"]
    lower = interval.get("lower")
    upper = interval.get("upper")
    if float(overall) <= -index_policy.verdict_threshold or (upper is not None and upper < 0):
        return "regressed"
    if float(overall) >= index_policy.verdict_threshold and lower is not None and lower > 0:
        return "improved"
    if float(overall) > 0 and any(index < 0 for index in numeric_indices):
        return "mixed"
    return "neutral"
