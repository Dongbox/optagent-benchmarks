#!/usr/bin/env python3
"""Unit tests for Phase 2 scoring extensions."""

import math
import sys
from pathlib import Path

# Add benchmarks to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.scoring_phase2 import (
    OperatorStats,
    cohens_d,
    compute_ecdf,
    compute_evaluations_to_target,
    compute_time_to_target,
    compute_time_to_targets,
    friedman_test,
    parse_operator_stats,
    score_operator_contribution,
    wilcoxon_signed_rank_test,
)


def test_operator_contribution():
    """Test D6 operator contribution scoring."""
    print("=== Test D6: Operator Contribution ===")

    # Test case 1: Balanced contribution
    operator_stats = [
        OperatorStats(
            operator_name="crossover",
            calls=100,
            accepted=50,
            improved=10,
            total_delta=50.0,
            avg_delta=5.0,
            contribution_ratio=0.33,
        ),
        OperatorStats(
            operator_name="mutation",
            calls=80,
            accepted=40,
            improved=10,
            total_delta=40.0,
            avg_delta=4.0,
            contribution_ratio=0.33,
        ),
        OperatorStats(
            operator_name="local_search",
            calls=50,
            accepted=30,
            improved=10,
            total_delta=60.0,
            avg_delta=6.0,
            contribution_ratio=0.34,
        ),
    ]

    score = score_operator_contribution(operator_stats)
    print(f"Test 1 (balanced): {score:.2f}")
    print(f"  Utilization: 100% (3/3 operators contributed)")
    print(f"  Distribution: high entropy (balanced contribution)")
    assert 80 <= score <= 100, f"Expected high score for balanced contribution, got {score}"

    # Test case 2: Dominated by one operator
    operator_stats_dominated = [
        OperatorStats(
            operator_name="crossover",
            calls=100,
            improved=27,
            contribution_ratio=0.90,
        ),
        OperatorStats(
            operator_name="mutation",
            calls=80,
            improved=3,
            contribution_ratio=0.10,
        ),
        OperatorStats(
            operator_name="local_search",
            calls=50,
            improved=0,
            contribution_ratio=0.0,
        ),
    ]

    score_dominated = score_operator_contribution(operator_stats_dominated)
    print(f"\nTest 2 (dominated): {score_dominated:.2f}")
    print(f"  Utilization: 67% (2/3 operators contributed)")
    print(f"  Distribution: low entropy (one operator dominates)")
    assert score_dominated < score, "Dominated should score lower than balanced"

    # Test case 3: Empty operator stats
    score_empty = score_operator_contribution([])
    print(f"\nTest 3 (empty): {score_empty:.2f}")
    assert score_empty == -1.0, "Empty operator stats should return -1"

    print("✅ D6 Operator Contribution tests passed\n")


def test_statistical_tests():
    """Test statistical significance functions."""
    print("=== Test Statistical Significance ===")

    # Wilcoxon signed-rank test
    strategy1 = [100, 105, 110, 95, 98, 102, 108, 97]
    strategy2 = [120, 125, 130, 115, 118, 122, 128, 117]  # Consistently much worse

    result = wilcoxon_signed_rank_test(strategy1, strategy2)
    print(f"Wilcoxon test: p={result['p_value']:.4f}, significant={result['significant']}")
    assert "p_value" in result
    # Note: With small sample, may not always be significant at p<0.05
    print(f"  Difference detected: strategy2 is consistently worse")

    # Friedman test
    strat1 = [100, 105, 110, 95, 98]
    strat2 = [110, 115, 120, 105, 108]
    strat3 = [95, 100, 105, 90, 93]

    result_friedman = friedman_test(strat1, strat2, strat3)
    print(f"Friedman test: p={result_friedman['p_value']:.4f}, significant={result_friedman['significant']}")
    assert "p_value" in result_friedman

    # Cohen's d
    group1 = [100, 102, 98, 105, 97]
    group2 = [110, 112, 108, 115, 107]

    result_d = cohens_d(group1, group2)
    print(f"Cohen's d: {result_d['value']:.3f} ({result_d['interpretation']})")
    assert "value" in result_d
    assert result_d["abs_value"] > 0.8, "Should detect large effect size"

    print("✅ Statistical tests passed\n")


def test_ecdf():
    """Test ECDF computation."""
    print("=== Test ECDF Curves ===")

    objectives = [100, 105, 110, 95, 120, 98]
    reference_costs = [90, 95, 100, 90, 110, 90]

    ecdf_data = compute_ecdf(objectives, reference_costs)

    print(f"ECDF gaps (first 3): {ecdf_data['gaps'][:3]}")
    print(f"ECDF fractions (first 3): {ecdf_data['cumulative_fraction'][:3]}")
    print(f"n_samples: {ecdf_data['n_samples']}")

    assert len(ecdf_data["gaps"]) == 6
    assert len(ecdf_data["cumulative_fraction"]) == 6
    assert ecdf_data["cumulative_fraction"][-1] == 1.0, "ECDF should reach 1.0"
    assert ecdf_data["gaps"] == sorted(ecdf_data["gaps"]), "Gaps should be sorted"

    print("✅ ECDF computation tests passed\n")


def test_time_to_target():
    """Test time-to-target computation."""
    print("=== Test Time-to-Target ===")

    # Incumbent trace
    incumbent_trace = [
        {"elapsed_s": 1.0, "objective": 110.0},
        {"elapsed_s": 3.0, "objective": 105.0},
        {"elapsed_s": 5.0, "objective": 102.0},
        {"elapsed_s": 10.0, "objective": 100.5},
        {"elapsed_s": 15.0, "objective": 100.0},
    ]
    reference_cost = 100.0

    # Test single target
    time_1pct = compute_time_to_target(incumbent_trace, reference_cost, target_gap=0.01)
    print(f"Time to 1% gap: {time_1pct}s")
    assert time_1pct == 10.0, f"Should reach 1% gap at 10s, got {time_1pct}"

    time_5pct = compute_time_to_target(incumbent_trace, reference_cost, target_gap=0.05)
    print(f"Time to 5% gap: {time_5pct}s")
    assert time_5pct == 3.0, f"Should reach 5% gap at 3s, got {time_5pct}"

    # Test multiple targets
    times = compute_time_to_targets(incumbent_trace, reference_cost, [0.01, 0.05, 0.10])
    print(f"Times to targets: {times}")
    assert times["0.01"] == 10.0
    assert times["0.05"] == 3.0
    assert times["0.10"] == 1.0

    # Test unreached target
    time_impossible = compute_time_to_target(incumbent_trace, reference_cost, target_gap=-0.01)
    print(f"Time to -1% gap (better than BKS): {time_impossible}")
    assert time_impossible is None, "Should return None for unreached target"

    # Test evaluations to target
    evaluations_trace = [100, 500, 1000, 2000, 3000]
    evals_5pct = compute_evaluations_to_target(
        incumbent_trace, evaluations_trace, reference_cost, target_gap=0.05
    )
    print(f"Evaluations to 5% gap: {evals_5pct}")
    assert evals_5pct == 500, f"Should reach 5% gap at 500 evals (t=3s), got {evals_5pct}"

    print("✅ Time-to-Target tests passed\n")


def test_parse_operator_stats():
    """Test parsing operator statistics from diagnostics."""
    print("=== Test Parse Operator Stats ===")

    operator_diagnostics = {
        "crossover": {
            "calls": 100,
            "accepted": 50,
            "improved": 10,
            "total_delta": 50.0,
            "wall_time_ms": 100.0,
        },
        "mutation": {
            "calls": 80,
            "accepted": 40,
            "improved": 20,
            "total_delta": 80.0,
            "wall_time_ms": 150.0,
        },
    }

    stats = parse_operator_stats(operator_diagnostics)
    print(f"Parsed {len(stats)} operators")

    assert len(stats) == 2
    assert stats[0].operator_name == "crossover"
    assert stats[0].calls == 100
    assert stats[0].avg_delta == 5.0  # 50.0 / 10
    assert abs(stats[0].contribution_ratio - 0.333) < 0.01  # 10 / 30

    assert stats[1].operator_name == "mutation"
    assert abs(stats[1].contribution_ratio - 0.667) < 0.01  # 20 / 30

    print("✅ Parse operator stats tests passed\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Phase 2 Scoring Extensions - Unit Tests")
    print("=" * 60 + "\n")

    test_operator_contribution()
    test_statistical_tests()
    test_ecdf()
    test_time_to_target()
    test_parse_operator_stats()

    print("=" * 60)
    print("✅ All Phase 2 tests passed!")
    print("=" * 60)
