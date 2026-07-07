#!/usr/bin/env python3
"""Legacy Phase 2 extensions for strategy performance scoring.

Phase 3 benchmark statistics use ``benchmarks.telemetry_metrics`` as the
canonical telemetry-only entrypoint. This module is quarantined as a historical
row/diagnostics helper and should not be extended for new statistics paths.

Implements:
  - D6: Operator Contribution (算子贡献归因)
  - Statistical Significance Tests (统计显著性检验)
  - ECDF Curves (性能剖面图)
  - Time-to-Target (达到目标时间)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import stats


# =============================================================================
# D6: Operator Contribution
# =============================================================================


@dataclass
class OperatorStats:
    """Per-operator statistics for contribution analysis."""

    operator_name: str
    calls: int = 0
    accepted: int = 0
    improved: int = 0
    total_delta: float = 0.0
    avg_delta: float = 0.0
    wall_time_ms: float = 0.0
    contribution_ratio: float = 0.0


def parse_operator_stats(operator_diagnostics: dict[str, Any]) -> list[OperatorStats]:
    """Parse operator statistics from diagnostics dict.

    Expected format:
    {
      "operator_name": {
        "calls": int,
        "accepted": int,
        "improved": int,
        "total_delta": float,
        "wall_time_ms": float
      }
    }
    """
    stats = []
    total_improvements = sum(
        op_data.get("improved", 0) for op_data in operator_diagnostics.values()
    )

    for op_name, op_data in operator_diagnostics.items():
        calls = op_data.get("calls", 0)
        accepted = op_data.get("accepted", 0)
        improved = op_data.get("improved", 0)
        total_delta = op_data.get("total_delta", 0.0)
        wall_time_ms = op_data.get("wall_time_ms", 0.0)

        avg_delta = total_delta / improved if improved > 0 else 0.0
        contribution_ratio = improved / total_improvements if total_improvements > 0 else 0.0

        stats.append(
            OperatorStats(
                operator_name=op_name,
                calls=calls,
                accepted=accepted,
                improved=improved,
                total_delta=total_delta,
                avg_delta=avg_delta,
                wall_time_ms=wall_time_ms,
                contribution_ratio=contribution_ratio,
            )
        )

    return stats


def score_operator_contribution(operator_stats: list[OperatorStats]) -> float:
    """D6: Operator Contribution score.

    operator_score = 0.6 × utilization + 0.4 × distribution

    - utilization: fraction of operators that contributed improvements
    - distribution: entropy of contribution ratios (higher = more balanced)

    Returns score [0, 100], or -1 if no operator data.
    """
    if not operator_stats:
        return -1.0

    # Portfolio utilization: fraction with improvements
    operators_with_improvements = sum(1 for op in operator_stats if op.improved > 0)
    total_operators = len(operator_stats)
    utilization = 100.0 * operators_with_improvements / total_operators

    # Improvement distribution: entropy of contribution ratios
    contrib_ratios = [op.contribution_ratio for op in operator_stats if op.contribution_ratio > 0]
    if not contrib_ratios:
        return utilization * 0.6  # Only utilization, no distribution

    # Shannon entropy
    entropy = -sum(p * math.log(p) for p in contrib_ratios if p > 0)
    max_entropy = math.log(len(contrib_ratios))
    distribution = 100.0 * (entropy / max_entropy) if max_entropy > 0 else 0.0

    operator_score = 0.6 * utilization + 0.4 * distribution
    return operator_score


# =============================================================================
# Statistical Significance Tests
# =============================================================================


def wilcoxon_signed_rank_test(
    strategy1_objectives: list[float], strategy2_objectives: list[float]
) -> dict[str, Any]:
    """Wilcoxon signed-rank test for paired samples.

    Tests whether two strategies have significantly different performance on the
    same set of instances.

    Returns:
    {
      "test": "wilcoxon",
      "statistic": float,
      "p_value": float,
      "significant": bool (p < 0.05),
      "n_pairs": int
    }
    """
    if len(strategy1_objectives) != len(strategy2_objectives):
        raise ValueError("Strategies must have same number of results for paired test")

    if len(strategy1_objectives) < 2:
        return {
            "test": "wilcoxon",
            "error": "Insufficient samples (need ≥2)",
            "n_pairs": len(strategy1_objectives),
        }

    statistic, p_value = stats.wilcoxon(strategy1_objectives, strategy2_objectives)

    return {
        "test": "wilcoxon",
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "n_pairs": len(strategy1_objectives),
    }


def friedman_test(*strategy_objectives: list[float]) -> dict[str, Any]:
    """Friedman test for multiple strategies on multiple instances.

    Tests whether k strategies have significantly different performance.

    Returns:
    {
      "test": "friedman",
      "statistic": float,
      "p_value": float,
      "significant": bool (p < 0.05),
      "n_strategies": int,
      "n_instances": int
    }
    """
    if len(strategy_objectives) < 3:
        return {
            "test": "friedman",
            "error": "Need ≥3 strategies for Friedman test",
            "n_strategies": len(strategy_objectives),
        }

    # Check all have same length
    lengths = [len(objs) for objs in strategy_objectives]
    if len(set(lengths)) > 1:
        return {
            "test": "friedman",
            "error": "All strategies must have same number of instances",
            "lengths": lengths,
        }

    statistic, p_value = stats.friedmanchisquare(*strategy_objectives)

    return {
        "test": "friedman",
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "n_strategies": len(strategy_objectives),
        "n_instances": lengths[0],
    }


def cohens_d(group1: list[float], group2: list[float]) -> dict[str, Any]:
    """Cohen's d effect size for two groups.

    Measures practical significance (effect magnitude) independent of sample size.

    Interpretation:
      |d| < 0.2: small effect
      |d| < 0.5: medium effect
      |d| ≥ 0.8: large effect

    Returns:
    {
      "effect_size": "cohen_d",
      "value": float,
      "interpretation": str
    }
    """
    if len(group1) < 2 or len(group2) < 2:
        return {
            "effect_size": "cohen_d",
            "error": "Need ≥2 samples per group",
        }

    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))

    if pooled_std == 0:
        return {
            "effect_size": "cohen_d",
            "value": 0.0,
            "interpretation": "no variance",
        }

    d = (mean1 - mean2) / pooled_std

    # Interpretation
    abs_d = abs(d)
    if abs_d < 0.2:
        interpretation = "small"
    elif abs_d < 0.5:
        interpretation = "medium"
    elif abs_d < 0.8:
        interpretation = "large"
    else:
        interpretation = "very large"

    return {
        "effect_size": "cohen_d",
        "value": float(d),
        "abs_value": float(abs_d),
        "interpretation": interpretation,
    }


# =============================================================================
# ECDF Curves (Performance Profiles)
# =============================================================================


def compute_ecdf(
    objectives: list[float], reference_costs: list[float]
) -> dict[str, Any]:
    """Compute Empirical Cumulative Distribution Function for gap distribution.

    Returns ECDF data for visualization (COCO-style performance profile).

    Args:
        objectives: List of objective values from runs
        reference_costs: Corresponding reference costs (BKS)

    Returns:
    {
      "gaps": [sorted gap values],
      "cumulative_fraction": [0.0, ..., 1.0],
      "n_samples": int
    }
    """
    if len(objectives) != len(reference_costs):
        raise ValueError("objectives and reference_costs must have same length")

    if not objectives:
        return {
            "gaps": [],
            "cumulative_fraction": [],
            "n_samples": 0,
        }

    # Compute gaps
    gaps = [
        (obj - ref) / abs(ref) if ref != 0 else float("inf")
        for obj, ref in zip(objectives, reference_costs)
    ]

    # Sort and compute ECDF
    gaps_sorted = sorted(gaps)
    n = len(gaps_sorted)
    ecdf_y = [i / n for i in range(1, n + 1)]

    return {
        "gaps": gaps_sorted,
        "cumulative_fraction": ecdf_y,
        "n_samples": n,
    }


def compute_ecdf_by_time_slice(
    runs_data: list[dict[str, Any]], time_slices: list[float]
) -> dict[str, Any]:
    """Compute ECDF at different time slices (anytime ECDF).

    For each time slice, compute the ECDF of objectives achieved by that time.

    Args:
        runs_data: List of run data with incumbent_trace and reference_cost
        time_slices: Time points to evaluate (e.g., [1, 5, 10, 30, 60] seconds)

    Returns:
    {
      "time_slices": [1, 5, 10, 30, 60],
      "ecdf_per_slice": {
        "1": {"gaps": [...], "cumulative_fraction": [...]},
        "5": {...},
        ...
      }
    }
    """
    ecdf_per_slice = {}

    for t in time_slices:
        objectives_at_t = []
        reference_costs = []

        for run in runs_data:
            incumbent_trace = run.get("incumbent_trace", [])
            reference_cost = run.get("reference_cost")

            if not incumbent_trace or reference_cost is None:
                continue

            # Find objective at time t (last known value before or at t)
            obj_at_t = None
            for event in incumbent_trace:
                if event.get("elapsed_s", 0) <= t:
                    obj_at_t = event.get("objective")
                else:
                    break

            if obj_at_t is not None:
                objectives_at_t.append(obj_at_t)
                reference_costs.append(reference_cost)

        if objectives_at_t:
            ecdf_data = compute_ecdf(objectives_at_t, reference_costs)
            ecdf_per_slice[str(t)] = ecdf_data

    return {
        "time_slices": time_slices,
        "ecdf_per_slice": ecdf_per_slice,
    }


# =============================================================================
# Time-to-Target
# =============================================================================


def compute_time_to_target(
    incumbent_trace: list[dict[str, Any]],
    reference_cost: float,
    target_gap: float = 0.10,
) -> float | None:
    """Compute time to reach target gap.

    Args:
        incumbent_trace: List of {"elapsed_s": float, "objective": float}
        reference_cost: Reference cost (BKS)
        target_gap: Target gap threshold (default 10%)

    Returns:
        Time in seconds to reach target, or None if not reached
    """
    if not incumbent_trace or reference_cost == 0:
        return None

    for event in incumbent_trace:
        elapsed_s = event.get("elapsed_s", 0)
        objective = event.get("objective")

        if objective is None:
            continue

        gap = (objective - reference_cost) / abs(reference_cost)
        if gap <= target_gap:
            return elapsed_s

    return None  # Target not reached


def compute_time_to_targets(
    incumbent_trace: list[dict[str, Any]],
    reference_cost: float,
    target_gaps: list[float] | None = None,
) -> dict[str, float | None]:
    """Compute time to reach multiple target gaps.

    Args:
        incumbent_trace: Incumbent evolution trace
        reference_cost: Reference cost (BKS)
        target_gaps: List of target gaps (default: [0.01, 0.05, 0.10])

    Returns:
    {
      "0.01": time or None,
      "0.05": time or None,
      "0.10": time or None
    }
    """
    if target_gaps is None:
        target_gaps = [0.01, 0.05, 0.10]

    results = {}
    for gap in target_gaps:
        time_to_gap = compute_time_to_target(incumbent_trace, reference_cost, gap)
        results[f"{gap:.2f}"] = time_to_gap

    return results


def compute_evaluations_to_target(
    incumbent_trace: list[dict[str, Any]],
    evaluations_trace: list[int],
    reference_cost: float,
    target_gap: float = 0.10,
) -> int | None:
    """Compute evaluations to reach target gap.

    Hardware-independent alternative to time-to-target.

    Args:
        incumbent_trace: Incumbent evolution trace
        evaluations_trace: Number of evaluations at each incumbent event
        reference_cost: Reference cost
        target_gap: Target gap threshold

    Returns:
        Number of evaluations to reach target, or None if not reached
    """
    if not incumbent_trace or len(incumbent_trace) != len(evaluations_trace):
        return None

    if reference_cost == 0:
        return None

    for event, evals in zip(incumbent_trace, evaluations_trace):
        objective = event.get("objective")
        if objective is None:
            continue

        gap = (objective - reference_cost) / abs(reference_cost)
        if gap <= target_gap:
            return evals

    return None
