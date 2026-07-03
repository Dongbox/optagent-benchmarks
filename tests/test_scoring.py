"""Unit tests for scripts/benchmark/scoring.py."""

import json
import sys
from pathlib import Path

# Ensure benchmarks/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.scoring import (
    CV_THRESHOLD,
    DEFAULT_GAP_THRESHOLD,
    DimensionScores,
    IncumbentEvent,
    RunMetrics,
    WEIGHTS,
    aggregate_global,
    aggregate_group,
    aggregate_instance,
    composite_score,
    compute_gap_rel,
    compute_primal_integral,
    extract_metrics,
    score_all_runs,
    score_anytime,
    score_dynamics,
    score_efficiency,
    score_quality,
    score_run,
    score_stability,
)


# =============================================================================
# D1: Solution Quality
# =============================================================================


class TestScoreQuality:
    def test_optimal_solution(self):
        """Gap = 0 → 100 points."""
        assert score_quality(100.0, 100.0, True, "routing") == 100.0

    def test_better_than_reference(self):
        """Below reference → 100 points."""
        assert score_quality(90.0, 100.0, True, "routing") == 100.0

    def test_at_threshold(self):
        """Gap = threshold → 0 points."""
        # routing threshold = 0.20, so obj = 120 → gap = 0.20 → score = 0
        assert score_quality(120.0, 100.0, True, "routing") == 0.0

    def test_half_threshold(self):
        """Gap = threshold/2 → 50 points."""
        # routing threshold = 0.20, so gap = 0.10 → score = 50
        assert score_quality(110.0, 100.0, True, "routing") == 50.0

    def test_infeasible(self):
        """Infeasible → 0."""
        assert score_quality(100.0, 100.0, False, "routing") == 0.0

    def test_no_objective(self):
        """None objective → 0."""
        assert score_quality(None, 100.0, True, "routing") == 0.0

    def test_no_reference(self):
        """No reference cost → 50 (moderate default)."""
        assert score_quality(100.0, None, True, "routing") == 50.0


class TestComputeGapRel:
    def test_normal(self):
        gap = compute_gap_rel(110.0, 100.0, True)
        assert gap is not None
        assert abs(gap - 0.10) < 1e-10

    def test_infeasible(self):
        assert compute_gap_rel(110.0, 100.0, False) is None


# =============================================================================
# D2: Anytime Performance
# =============================================================================


class TestPrimalIntegral:
    def test_constant_at_reference(self):
        """Incumbent always at reference → integral = 0."""
        trace = [IncumbentEvent(0.0, 100.0)]
        integral = compute_primal_integral(trace, 100.0, 10.0)
        assert integral == 0.0

    def test_constant_gap(self):
        """Gap = 0.1 for full duration → integral = 0.1 * T."""
        trace = [IncumbentEvent(0.0, 110.0)]
        integral = compute_primal_integral(trace, 100.0, 10.0)
        assert abs(integral - 1.0) < 1e-10  # 0.1 * 10

    def test_step_improvement(self):
        """Gap drops from 0.2 to 0.0 halfway through."""
        trace = [
            IncumbentEvent(0.0, 120.0),   # gap = 0.2
            IncumbentEvent(5.0, 100.0),   # gap = 0.0
        ]
        integral = compute_primal_integral(trace, 100.0, 10.0)
        # 0.2 * 5 + 0.0 * 5 = 1.0
        assert abs(integral - 1.0) < 1e-10

    def test_empty_trace(self):
        assert compute_primal_integral([], 100.0, 10.0) == float("inf")


class TestScoreAnytime:
    def test_perfect_anytime(self):
        """Always at reference → score = 100."""
        trace = [IncumbentEvent(0.0, 100.0)]
        score, integral = score_anytime(trace, 100.0, 10.0, "routing", True)
        assert score == 100.0
        assert integral == 0.0

    def test_infeasible(self):
        trace = [IncumbentEvent(0.0, 100.0)]
        score, _ = score_anytime(trace, 100.0, 10.0, "routing", False)
        assert score == 0.0


# =============================================================================
# D3: Runtime Efficiency
# =============================================================================


class TestScoreEfficiency:
    def test_at_expected_throughput(self):
        """Throughput = expected → 100 points."""
        # routing expected = 100000 evals/s
        # 100000 evals in 1 second
        score = score_efficiency(1.0, 100_000, 0, "routing")
        assert abs(score - 100.0) < 1e-6

    def test_zero_wall_time(self):
        assert score_efficiency(0.0, 1000, 0, "routing") == 0.0

    def test_zero_candidates(self):
        assert score_efficiency(1.0, 0, 0, "routing") == 0.0

    def test_below_expected(self):
        """Lower throughput → lower score (log scale)."""
        # 10000 evals/s vs expected 100000
        # log10(10000) / log10(100000) = 4/5 = 0.8 → 80
        score = score_efficiency(1.0, 10_000, 0, "routing")
        assert abs(score - 80.0) < 1e-6


# =============================================================================
# D4: Stability
# =============================================================================


class TestScoreStability:
    def test_insufficient_seeds(self):
        """Fewer than 5 seeds → -1."""
        score = score_stability([100, 101, 102], None, 3, 3, "routing")
        assert score == -1.0

    def test_perfect_stability(self):
        """All identical objectives → high consistency."""
        objs = [100.0] * 10
        score = score_stability(objs, 100.0, 10, 10, "routing")
        # consistency = 100, feasibility = 100, worst_case = 100
        assert score == 100.0

    def test_all_infeasible(self):
        """All infeasible → low score (just feasibility=0)."""
        score = score_stability([], None, 0, 10, "routing")
        # 0.3 * 0 = 0
        assert score == 0.0


# =============================================================================
# D5: Search Dynamics
# =============================================================================


class TestScoreDynamics:
    def test_converged_diverse(self):
        """Converged with diversity → high score."""
        score = score_dynamics(
            total_iterations=1000,
            unimproved_iterations=100,
            diversity_at_termination=0.5,
            termination_reason="converged",
        )
        # diversity_score = min(100, 0.5 * 200) = 100
        # stagnation_score = max(0, 100 * (1 - 0.1/0.8)) = 87.5
        # termination_quality = 100
        # avg = (100 + 87.5 + 100) / 3 = 95.83
        assert abs(score - 95.83) < 0.1

    def test_stagnated(self):
        """High stagnation → low stagnation score."""
        score = score_dynamics(
            total_iterations=1000,
            unimproved_iterations=800,
            diversity_at_termination=0.0,
            termination_reason="stagnation",
        )
        # diversity = 0
        # stagnation = max(0, 100 * (1 - 0.8/0.8)) = 0
        # termination = 20
        # avg = (0 + 0 + 20) / 3 = 6.67
        assert abs(score - 6.67) < 0.1


# =============================================================================
# Composite Score
# =============================================================================


class TestCompositeScore:
    def test_all_hundred(self):
        dims = DimensionScores(100, 100, 100, 100, 100)
        assert abs(composite_score(dims) - 100.0) < 1e-6

    def test_all_zero(self):
        dims = DimensionScores(0, 0, 0, 0, 0)
        assert composite_score(dims) == 0.0

    def test_stability_unavailable(self):
        """Stability=-1 redistributes weight."""
        dims = DimensionScores(100, 100, 100, -1, 100)
        # All available dimensions are 100, so composite = 100
        assert abs(composite_score(dims) - 100.0) < 1e-6


# =============================================================================
# Full Pipeline
# =============================================================================


class TestScoreRun:
    def test_basic_run(self):
        metrics = RunMetrics(
            run_id="test-001",
            benchmark_group="routing",
            benchmark_id="tsp10",
            strategy="ga",
            seed=42,
            objective=110.0,
            feasible=True,
            reference_cost=100.0,
            incumbent_trace=[
                IncumbentEvent(0.0, 150.0),
                IncumbentEvent(1.0, 130.0),
                IncumbentEvent(3.0, 110.0),
            ],
            time_budget_s=10.0,
            wall_time_seconds=10.0,
            loop_candidates_evaluated=50000,
            construct_candidates_evaluated=1000,
            total_iterations=5000,
            unimproved_iterations=2000,
            diversity_at_termination=0.3,
            termination_reason="time_limit",
        )
        scored = score_run(metrics)
        assert scored.run_id == "test-001"
        assert scored.dimensions.quality == 50.0  # gap=0.1, threshold=0.2
        assert scored.dimensions.efficiency > 0
        assert scored.dimensions.dynamics > 0
        assert scored.composite > 0


class TestExtractMetrics:
    def test_extract_from_benchmark_run(self):
        run_data = {
            "run_id": "run-001",
            "benchmark_group": "scheduling",
            "benchmark_id": "steel_10",
            "strategy": "ga",
            "seed": 1,
            "strategy_config": {"time_limit_s": 30},
            "metrics": {
                "objective": 500.0,
                "feasible": True,
                "reference_cost": 400.0,
                "runtime_ms": 30000,
                "iterations": 10000,
            },
            "operator_diagnostics": {
                "incumbent_trace_json": '[{"elapsed_s":0.1,"objective":600},{"elapsed_s":5.0,"objective":500}]',
                "diversity_at_termination": 0.2,
                "unimproved_iterations": 5000,
                "termination_reason": "time_limit",
                "loop_candidates_evaluated": 80000,
                "construct_candidates_evaluated": 2000,
                "total_iterations": 10000,
            },
        }
        m = extract_metrics(run_data)
        assert m.run_id == "run-001"
        assert m.objective == 500.0
        assert m.feasible is True
        assert m.reference_cost == 400.0
        assert len(m.incumbent_trace) == 2
        assert m.incumbent_trace[0].elapsed_s == 0.1
        assert m.wall_time_seconds == 30.0
        assert m.loop_candidates_evaluated == 80000
        assert m.termination_reason == "time_limit"


class TestScoreAllRuns:
    def test_multi_strategy_scoring(self):
        runs = [
            {
                "run_id": f"run-ga-{seed}",
                "benchmark_group": "routing",
                "benchmark_id": "tsp10",
                "strategy": "ga",
                "seed": seed,
                "strategy_config": {"time_limit_s": 10},
                "metrics": {
                    "objective": 105.0 + seed,
                    "feasible": True,
                    "reference_cost": 100.0,
                    "runtime_ms": 10000,
                },
                "operator_diagnostics": {
                    "incumbent_trace_json": json.dumps([
                        {"elapsed_s": 0.1, "objective": 150.0},
                        {"elapsed_s": 2.0, "objective": 105.0 + seed},
                    ]),
                    "loop_candidates_evaluated": 50000,
                    "construct_candidates_evaluated": 1000,
                    "total_iterations": 5000,
                    "unimproved_iterations": 2000,
                    "diversity_at_termination": 0.3,
                    "termination_reason": "time_limit",
                },
            }
            for seed in range(8)
        ]

        output = score_all_runs(runs)
        assert output["schema_version"] == 1
        assert len(output["scores"]) >= 1

        # Should have global + group scores
        global_scores = [s for s in output["scores"] if s["benchmark_group"] == "all"]
        group_scores = [s for s in output["scores"] if s["benchmark_group"] == "routing"]
        assert len(global_scores) == 1
        assert len(group_scores) == 1
        assert global_scores[0]["strategy"] == "ga"
        assert global_scores[0]["composite"] > 0
        assert global_scores[0]["run_count"] == 8
        assert group_scores[0]["instance_count"] == 1
