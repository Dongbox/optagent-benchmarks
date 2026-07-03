#!/usr/bin/env python3
"""Strategy Performance Scoring Module.

Implements the 5-dimension scoring framework for OptAgent search strategies:
  D1: Solution Quality (35%) — gap relative to reference/BKS
  D2: Anytime Performance (25%) — Primal Integral of incumbent evolution
  D3: Runtime Efficiency (15%) — throughput + overhead ratio
  D4: Stability (15%) — multi-seed consistency + feasibility + worst-case
  D5: Search Dynamics (10%) — diversity, stagnation, termination quality

Usage:
  python -m benchmarks.scoring --input results/*.json --output strategy-scores.json
  python -m benchmarks.scoring --input-dir public/data/results/ --output scores.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# =============================================================================
# Configuration
# =============================================================================

# Dimension weights (Phase 1)
WEIGHTS = {
    "quality": 0.35,
    "anytime": 0.25,
    "efficiency": 0.15,
    "stability": 0.15,
    "dynamics": 0.10,
}

# Gap thresholds per benchmark group (used in D1 and D2 normalization)
GAP_THRESHOLDS: dict[str, float] = {
    "routing": 0.20,
    "scheduling": 0.50,
    "assignment": 0.30,
}
DEFAULT_GAP_THRESHOLD = 0.30

# Expected throughput (evaluations/s) per group — for D3 log-scale scoring
EXPECTED_THROUGHPUT: dict[str, float] = {
    "routing": 100_000,
    "scheduling": 10_000,
    "assignment": 50_000,
}
DEFAULT_EXPECTED_THROUGHPUT = 50_000

# D4: coefficient of variation threshold
CV_THRESHOLD = 0.15

# D4: minimum seeds required for stability calculation
MIN_SEEDS_FOR_STABILITY = 5

# Termination reason → D5 score mapping
TERMINATION_SCORES: dict[str, float] = {
    "converged": 100.0,
    "optimal": 100.0,
    "diversity_exhausted": 80.0,
    "time_limit": 60.0,
    "iteration_limit": 40.0,
    "stagnation": 20.0,
}
DEFAULT_TERMINATION_SCORE = 50.0


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class IncumbentEvent:
    elapsed_s: float
    objective: float


@dataclass
class RunMetrics:
    """Extracted metrics from a single benchmark run needed for scoring."""

    # Identity
    run_id: str = ""
    benchmark_group: str = ""
    benchmark_id: str = ""
    strategy: str = ""
    seed: int = 0

    # D1: Quality
    objective: float | None = None
    feasible: bool = False
    reference_cost: float | None = None

    # D2: Anytime
    incumbent_trace: list[IncumbentEvent] = field(default_factory=list)
    time_budget_s: float = 30.0

    # D3: Efficiency
    wall_time_seconds: float = 0.0
    loop_candidates_evaluated: int = 0
    construct_candidates_evaluated: int = 0

    # D5: Dynamics
    total_iterations: int = 0
    unimproved_iterations: int = 0
    diversity_at_termination: float = 0.0
    termination_reason: str = ""
    restarts: int = 0


@dataclass
class DimensionScores:
    quality: float = 0.0
    anytime: float = 0.0
    efficiency: float = 0.0
    stability: float = -1.0  # -1 = insufficient data
    dynamics: float = 0.0


@dataclass
class RunScore:
    """Score for a single run."""

    run_id: str = ""
    benchmark_group: str = ""
    benchmark_id: str = ""
    strategy: str = ""
    seed: int = 0
    composite: float = 0.0
    dimensions: DimensionScores = field(default_factory=DimensionScores)
    gap_rel: float | None = None
    objective: float | None = None
    reference_cost: float | None = None
    primal_integral: float | None = None
    incumbent_trace_path: str | None = None


@dataclass
class InstanceScore:
    """Aggregated score for a (benchmark_id, strategy) pair across seeds."""

    benchmark_id: str = ""
    strategy: str = ""
    benchmark_group: str = ""
    composite: float = 0.0
    dimensions: DimensionScores = field(default_factory=DimensionScores)
    # Per-seed statistics
    run_count: int = 0
    seed_count: int = 0
    objectives: list[float] = field(default_factory=list)
    gap_rels: list[float] = field(default_factory=list)
    reference_cost: float | None = None
    # Best run info
    best_objective: float | None = None
    best_gap_rel: float | None = None
    incumbent_trace_path: str | None = None


@dataclass
class StrategyScore:
    """Aggregated score for a strategy across benchmark groups."""

    strategy: str = ""
    benchmark_group: str = "all"  # "all" for global
    composite: float = 0.0
    dimensions: DimensionScores = field(default_factory=DimensionScores)
    run_count: int = 0
    seed_count: int = 0
    instance_count: int = 0
    instances: list[InstanceScore] = field(default_factory=list)


# =============================================================================
# D1: Solution Quality
# =============================================================================


def score_quality(objective: float | None, reference_cost: float | None,
                  feasible: bool, benchmark_group: str) -> float:
    """D1: Quality score based on relative gap to reference."""
    if not feasible or objective is None:
        return 0.0

    if reference_cost is None or reference_cost == 0.0:
        # No meaningful reference: give moderate default score if feasible
        return 50.0 if objective is not None else 0.0

    gap_rel = (objective - reference_cost) / abs(reference_cost)
    gap_threshold = GAP_THRESHOLDS.get(benchmark_group, DEFAULT_GAP_THRESHOLD)

    if gap_rel <= 0.0:
        return 100.0  # At or better than reference

    score = max(0.0, 100.0 * (1.0 - gap_rel / gap_threshold))
    return score


def compute_gap_rel(objective: float | None, reference_cost: float | None,
                    feasible: bool) -> float | None:
    """Compute relative gap."""
    if not feasible or objective is None or reference_cost is None or reference_cost == 0.0:
        return None
    return (objective - reference_cost) / abs(reference_cost)


# =============================================================================
# D2: Anytime Performance (Primal Integral)
# =============================================================================


def compute_primal_integral(trace: list[IncumbentEvent], reference_cost: float,
                            time_budget_s: float) -> float:
    """Compute primal integral: ∫₀ᵀ gap(t) dt using step function interpolation.

    Returns the integral value (lower is better).
    """
    if not trace or reference_cost == 0.0 or time_budget_s <= 0.0:
        return float("inf")

    integral = 0.0
    prev_time = 0.0
    prev_gap = GAP_THRESHOLDS.get("scheduling", DEFAULT_GAP_THRESHOLD)  # worst-case start

    # Use initial gap from first event's objective before any improvement
    if trace:
        first_gap = (trace[0].objective - reference_cost) / abs(reference_cost)
        prev_gap = max(0.0, first_gap)

    for event in trace:
        t = min(event.elapsed_s, time_budget_s)
        if t > prev_time:
            integral += prev_gap * (t - prev_time)
        gap = (event.objective - reference_cost) / abs(reference_cost)
        prev_gap = max(0.0, gap)
        prev_time = t
        if t >= time_budget_s:
            break

    # Fill remaining time with last known gap
    if prev_time < time_budget_s:
        integral += prev_gap * (time_budget_s - prev_time)

    return integral


def score_anytime(trace: list[IncumbentEvent], reference_cost: float | None,
                  time_budget_s: float, benchmark_group: str,
                  feasible: bool) -> tuple[float, float | None]:
    """D2: Anytime score from primal integral.

    Returns (score, primal_integral).
    """
    if not feasible or not trace or reference_cost is None or reference_cost == 0.0:
        return (0.0, None)

    gap_threshold = GAP_THRESHOLDS.get(benchmark_group, DEFAULT_GAP_THRESHOLD)
    primal_integral = compute_primal_integral(trace, reference_cost, time_budget_s)

    max_integral = gap_threshold * time_budget_s
    if max_integral <= 0.0:
        return (0.0, primal_integral)

    score = max(0.0, 100.0 * (1.0 - primal_integral / max_integral))
    return (score, primal_integral)


# =============================================================================
# D3: Runtime Efficiency
# =============================================================================


def score_efficiency(wall_time_seconds: float, loop_candidates: int,
                     construct_candidates: int, benchmark_group: str) -> float:
    """D3: Efficiency score from throughput.

    Uses log-scale scoring: throughput_score = min(100, 100 * log10(evals/s) / log10(expected))
    Cost balance simplified: just evaluating throughput for Phase 1.
    """
    total_candidates = loop_candidates + construct_candidates
    if wall_time_seconds <= 0.0 or total_candidates <= 0:
        return 0.0

    evaluations_per_s = total_candidates / wall_time_seconds
    expected = EXPECTED_THROUGHPUT.get(benchmark_group, DEFAULT_EXPECTED_THROUGHPUT)

    if evaluations_per_s <= 1.0:
        return 0.0

    throughput_score = min(100.0, 100.0 * math.log10(evaluations_per_s) / math.log10(expected))
    return max(0.0, throughput_score)


# =============================================================================
# D4: Stability (computed at instance level from multiple seeds)
# =============================================================================


def score_stability(objectives: list[float], reference_cost: float | None,
                    feasible_count: int, total_count: int,
                    benchmark_group: str) -> float:
    """D4: Stability score from multi-seed statistics.

    stability = 0.5 * consistency + 0.3 * feasibility + 0.2 * worst_case
    Returns -1 if insufficient seeds.
    """
    if total_count < MIN_SEEDS_FOR_STABILITY:
        return -1.0

    # Feasibility rate
    feasibility_score = (feasible_count / total_count) * 100.0

    if len(objectives) < 2:
        # All infeasible or only one feasible run
        return 0.3 * feasibility_score

    # Consistency (CV-based)
    mean_obj = sum(objectives) / len(objectives)
    if mean_obj == 0.0:
        consistency_score = 100.0  # Perfect consistency at zero
    else:
        variance = sum((o - mean_obj) ** 2 for o in objectives) / len(objectives)
        std_obj = math.sqrt(variance)
        cv = std_obj / abs(mean_obj)
        consistency_score = max(0.0, 100.0 * (1.0 - cv / CV_THRESHOLD))

    # Worst-case control
    worst_case_score = 50.0  # Default when no reference
    if reference_cost is not None and reference_cost != 0.0:
        worst_obj = max(objectives)
        worst_gap = (worst_obj - reference_cost) / abs(reference_cost)
        gap_threshold = GAP_THRESHOLDS.get(benchmark_group, DEFAULT_GAP_THRESHOLD)
        worst_case_score = max(0.0, 100.0 * (1.0 - worst_gap / gap_threshold))

    raw = 0.5 * consistency_score + 0.3 * feasibility_score + 0.2 * worst_case_score
    return min(100.0, raw)


def compute_statistics(objectives: list[float]) -> dict[str, float | None]:
    """Compute descriptive statistics for a list of objectives."""
    if not objectives:
        return {"mean": None, "median": None, "std": None, "best": None,
                "worst": None, "p5": None, "p95": None}

    sorted_objs = sorted(objectives)
    n = len(sorted_objs)
    mean = sum(sorted_objs) / n
    variance = sum((o - mean) ** 2 for o in sorted_objs) / n
    std = math.sqrt(variance)

    def percentile(data: list[float], p: float) -> float:
        idx = (p / 100.0) * (len(data) - 1)
        lower = int(math.floor(idx))
        upper = min(lower + 1, len(data) - 1)
        frac = idx - lower
        return data[lower] * (1 - frac) + data[upper] * frac

    return {
        "mean": mean,
        "median": percentile(sorted_objs, 50),
        "std": std,
        "best": sorted_objs[0],
        "worst": sorted_objs[-1],
        "p5": percentile(sorted_objs, 5),
        "p95": percentile(sorted_objs, 95),
    }


# =============================================================================
# D5: Search Dynamics
# =============================================================================


def score_dynamics(total_iterations: int, unimproved_iterations: int,
                   diversity_at_termination: float, termination_reason: str) -> float:
    """D5: Search dynamics health score.

    dynamics = (diversity_score + stagnation_score + termination_quality) / 3
    """
    # Diversity health
    diversity_score = min(100.0, diversity_at_termination * 200.0)

    # Stagnation control
    if total_iterations > 0:
        stagnation_ratio = unimproved_iterations / total_iterations
        stagnation_score = max(0.0, 100.0 * (1.0 - stagnation_ratio / 0.8))
    else:
        stagnation_score = 0.0

    # Termination quality
    termination_quality = TERMINATION_SCORES.get(
        termination_reason, DEFAULT_TERMINATION_SCORE
    )

    return (diversity_score + stagnation_score + termination_quality) / 3.0


# =============================================================================
# Composite Score
# =============================================================================


def composite_score(dimensions: DimensionScores) -> float:
    """Compute weighted composite score from dimensions.

    If stability is unavailable (-1), redistribute its weight proportionally.
    """
    scores = {
        "quality": dimensions.quality,
        "anytime": dimensions.anytime,
        "efficiency": dimensions.efficiency,
        "stability": dimensions.stability,
        "dynamics": dimensions.dynamics,
    }

    if dimensions.stability < 0:
        # Stability unavailable: redistribute weight to other dimensions
        available_weight = sum(v for k, v in WEIGHTS.items() if k != "stability")
        total = sum(
            scores[k] * (WEIGHTS[k] / available_weight)
            for k in WEIGHTS
            if k != "stability"
        )
    else:
        total = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)

    return total


# =============================================================================
# Per-Run Scoring
# =============================================================================


def score_run(metrics: RunMetrics) -> RunScore:
    """Score a single benchmark run across all dimensions."""
    # D1
    quality = score_quality(
        metrics.objective, metrics.reference_cost,
        metrics.feasible, metrics.benchmark_group
    )
    gap_rel = compute_gap_rel(metrics.objective, metrics.reference_cost, metrics.feasible)

    # D2
    anytime, primal_integral = score_anytime(
        metrics.incumbent_trace, metrics.reference_cost,
        metrics.time_budget_s, metrics.benchmark_group, metrics.feasible
    )

    # D3
    efficiency = score_efficiency(
        metrics.wall_time_seconds,
        metrics.loop_candidates_evaluated,
        metrics.construct_candidates_evaluated,
        metrics.benchmark_group,
    )

    # D5 (D4 is per-instance)
    dynamics = score_dynamics(
        metrics.total_iterations,
        metrics.unimproved_iterations,
        metrics.diversity_at_termination,
        metrics.termination_reason,
    )

    dimensions = DimensionScores(
        quality=quality,
        anytime=anytime,
        efficiency=efficiency,
        stability=-1.0,  # Per-instance only
        dynamics=dynamics,
    )

    return RunScore(
        run_id=metrics.run_id,
        benchmark_group=metrics.benchmark_group,
        benchmark_id=metrics.benchmark_id,
        strategy=metrics.strategy,
        seed=metrics.seed,
        composite=composite_score(dimensions),
        dimensions=dimensions,
        gap_rel=gap_rel,
        objective=metrics.objective,
        reference_cost=metrics.reference_cost,
        primal_integral=primal_integral,
    )


# =============================================================================
# Aggregation: Instance → Group → Global
# =============================================================================


def aggregate_instance(run_scores: list[RunScore], benchmark_group: str) -> InstanceScore:
    """Aggregate multiple seed runs of the same (benchmark_id, strategy) into an InstanceScore."""
    if not run_scores:
        return InstanceScore()

    first = run_scores[0]

    # Collect feasible objectives for stability
    feasible_objectives = [
        r.objective for r in run_scores
        if r.objective is not None and r.dimensions.quality > 0
    ]
    feasible_count = sum(1 for r in run_scores if r.dimensions.quality > 0)

    # D4: Stability
    stability = score_stability(
        feasible_objectives, first.reference_cost,
        feasible_count, len(run_scores),
        benchmark_group,
    )

    # Average dimension scores across seeds
    n = len(run_scores)
    avg_quality = sum(r.dimensions.quality for r in run_scores) / n
    avg_anytime = sum(r.dimensions.anytime for r in run_scores) / n
    avg_efficiency = sum(r.dimensions.efficiency for r in run_scores) / n
    avg_dynamics = sum(r.dimensions.dynamics for r in run_scores) / n

    dimensions = DimensionScores(
        quality=avg_quality,
        anytime=avg_anytime,
        efficiency=avg_efficiency,
        stability=stability,
        dynamics=avg_dynamics,
    )

    # Best run info
    best_run = min(run_scores, key=lambda r: r.objective if r.objective is not None else float("inf"))

    seeds = set(r.seed for r in run_scores)
    gap_rels = [r.gap_rel for r in run_scores if r.gap_rel is not None]

    return InstanceScore(
        benchmark_id=first.benchmark_id,
        strategy=first.strategy,
        benchmark_group=benchmark_group,
        composite=composite_score(dimensions),
        dimensions=dimensions,
        run_count=n,
        seed_count=len(seeds),
        objectives=feasible_objectives,
        gap_rels=gap_rels,
        reference_cost=first.reference_cost,
        best_objective=best_run.objective,
        best_gap_rel=best_run.gap_rel,
        incumbent_trace_path=best_run.incumbent_trace_path,
    )


def aggregate_group(instance_scores: list[InstanceScore], strategy: str,
                    benchmark_group: str) -> StrategyScore:
    """Aggregate InstanceScores into a group-level StrategyScore."""
    if not instance_scores:
        return StrategyScore(strategy=strategy, benchmark_group=benchmark_group)

    n = len(instance_scores)
    avg_quality = sum(i.dimensions.quality for i in instance_scores) / n
    avg_anytime = sum(i.dimensions.anytime for i in instance_scores) / n
    avg_efficiency = sum(i.dimensions.efficiency for i in instance_scores) / n
    avg_dynamics = sum(i.dimensions.dynamics for i in instance_scores) / n

    # Stability: average of available scores, skip -1
    stability_scores = [i.dimensions.stability for i in instance_scores if i.dimensions.stability >= 0]
    avg_stability = sum(stability_scores) / len(stability_scores) if stability_scores else -1.0

    dimensions = DimensionScores(
        quality=avg_quality,
        anytime=avg_anytime,
        efficiency=avg_efficiency,
        stability=avg_stability,
        dynamics=avg_dynamics,
    )

    total_runs = sum(i.run_count for i in instance_scores)
    total_seeds = max(i.seed_count for i in instance_scores) if instance_scores else 0

    return StrategyScore(
        strategy=strategy,
        benchmark_group=benchmark_group,
        composite=composite_score(dimensions),
        dimensions=dimensions,
        run_count=total_runs,
        seed_count=total_seeds,
        instance_count=n,
        instances=instance_scores,
    )


def aggregate_global(group_scores: list[StrategyScore], strategy: str) -> StrategyScore:
    """Aggregate multiple group scores into a global strategy score."""
    if not group_scores:
        return StrategyScore(strategy=strategy, benchmark_group="all")

    n = len(group_scores)
    avg_quality = sum(g.dimensions.quality for g in group_scores) / n
    avg_anytime = sum(g.dimensions.anytime for g in group_scores) / n
    avg_efficiency = sum(g.dimensions.efficiency for g in group_scores) / n
    avg_dynamics = sum(g.dimensions.dynamics for g in group_scores) / n

    stability_scores = [g.dimensions.stability for g in group_scores if g.dimensions.stability >= 0]
    avg_stability = sum(stability_scores) / len(stability_scores) if stability_scores else -1.0

    dimensions = DimensionScores(
        quality=avg_quality,
        anytime=avg_anytime,
        efficiency=avg_efficiency,
        stability=avg_stability,
        dynamics=avg_dynamics,
    )

    total_runs = sum(g.run_count for g in group_scores)
    total_seeds = max(g.seed_count for g in group_scores) if group_scores else 0
    total_instances = sum(g.instance_count for g in group_scores)

    return StrategyScore(
        strategy=strategy,
        benchmark_group="all",
        composite=composite_score(dimensions),
        dimensions=dimensions,
        run_count=total_runs,
        seed_count=total_seeds,
        instance_count=total_instances,
    )


# =============================================================================
# Metrics Extraction from Benchmark Run JSON
# =============================================================================


def extract_metrics(run_data: dict[str, Any]) -> RunMetrics:
    """Extract RunMetrics from a BenchmarkRun JSON object."""
    metrics = run_data.get("metrics", {})
    diag = run_data.get("operator_diagnostics", {})

    # Incumbent trace: check both diagnostics and metrics
    incumbent_trace: list[IncumbentEvent] = []
    trace_json = diag.get("incumbent_trace_json") or metrics.get("incumbent_trace_json")
    if isinstance(trace_json, str):
        try:
            raw_trace = json.loads(trace_json)
            incumbent_trace = [
                IncumbentEvent(elapsed_s=e["elapsed_s"], objective=e["objective"])
                for e in raw_trace
            ]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # Reference cost: from metrics or strategy_config
    reference_cost = metrics.get("reference_cost") or metrics.get("best_known_solution")
    if reference_cost is not None:
        reference_cost = float(reference_cost)

    # Time budget
    strategy_config = run_data.get("strategy_config", {})
    time_budget = metrics.get("time_budget_s") or strategy_config.get("time_limit_s", 30.0)

    # Termination reason: from diagnostics or metrics
    termination_reason = (
        diag.get("termination_reason")
        or metrics.get("termination_reason")
        or ""
    )

    return RunMetrics(
        run_id=run_data.get("run_id", ""),
        benchmark_group=run_data.get("benchmark_group", ""),
        benchmark_id=run_data.get("benchmark_id", ""),
        strategy=run_data.get("strategy", ""),
        seed=run_data.get("seed", 0),
        objective=_safe_float(metrics.get("objective") or metrics.get("best_cost")),
        feasible=bool(metrics.get("feasible", False)),
        reference_cost=reference_cost,
        incumbent_trace=incumbent_trace,
        time_budget_s=float(time_budget) if time_budget else 30.0,
        wall_time_seconds=_safe_float(metrics.get("runtime_ms", 0)) / 1000.0
        if metrics.get("runtime_ms") is not None
        else _safe_float(diag.get("wall_time_seconds", 0)),
        loop_candidates_evaluated=int(
            diag.get("loop_candidates_evaluated", 0)
            or metrics.get("loop_candidates_evaluated", 0)
            or diag.get("ga_offspring_evaluated", 0)
            or diag.get("alns_candidates_evaluated", 0)
        ),
        construct_candidates_evaluated=int(
            diag.get("construct_candidates_evaluated", 0)
            or metrics.get("construct_candidates_evaluated", 0)
        ),
        total_iterations=int(
            diag.get("total_iterations", 0)
            or metrics.get("iterations", 0)
        ),
        unimproved_iterations=int(
            diag.get("unimproved_iterations", 0)
            or metrics.get("unimproved_iterations", 0)
        ),
        diversity_at_termination=_safe_float(
            diag.get("diversity_at_termination", 0)
            or metrics.get("diversity_at_termination", 0)
        ),
        termination_reason=str(termination_reason),
        restarts=int(diag.get("restarts", 0) or metrics.get("restarts", 0)),
    )


def _safe_float(value: Any) -> float:
    """Safely convert to float, returning 0.0 on failure."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


# =============================================================================
# Full Pipeline
# =============================================================================


def score_all_runs(run_data_list: list[dict[str, Any]]) -> dict[str, Any]:
    """Score all runs and produce the complete strategy-scores.json output.

    Returns the StrategyScoreData dict ready for JSON serialization.
    """
    # Extract metrics and score each run
    run_scores: list[RunScore] = []
    for run_data in run_data_list:
        metrics = extract_metrics(run_data)
        if not metrics.strategy or not metrics.benchmark_group:
            continue
        scored = score_run(metrics)
        run_scores.append(scored)

    if not run_scores:
        return _empty_output()

    # Group by (strategy, benchmark_group, benchmark_id)
    # Level 2: per-instance
    from collections import defaultdict

    by_instance: dict[tuple[str, str, str], list[RunScore]] = defaultdict(list)
    for rs in run_scores:
        key = (rs.strategy, rs.benchmark_group, rs.benchmark_id)
        by_instance[key].append(rs)

    instance_scores: list[InstanceScore] = []
    for (strategy, group, bench_id), scores in by_instance.items():
        instance_scores.append(aggregate_instance(scores, group))

    # Level 3: per-group
    by_strategy_group: dict[tuple[str, str], list[InstanceScore]] = defaultdict(list)
    for inst in instance_scores:
        by_strategy_group[(inst.strategy, inst.benchmark_group)].append(inst)

    group_scores: list[StrategyScore] = []
    for (strategy, group), instances in by_strategy_group.items():
        group_scores.append(aggregate_group(instances, strategy, group))

    # Level 4: global per-strategy
    by_strategy: dict[str, list[StrategyScore]] = defaultdict(list)
    for gs in group_scores:
        by_strategy[gs.strategy].append(gs)

    global_scores: list[StrategyScore] = []
    for strategy, groups in by_strategy.items():
        global_scores.append(aggregate_global(groups, strategy))

    # Build output
    all_scores = global_scores + group_scores

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config": {
            "weights": WEIGHTS,
            "thresholds": {
                "gap_thresholds": GAP_THRESHOLDS,
                "expected_throughput": EXPECTED_THROUGHPUT,
                "cv_threshold": CV_THRESHOLD,
            },
        },
        "scores": [_strategy_score_to_dict(s) for s in all_scores],
    }


def _strategy_score_to_dict(s: StrategyScore) -> dict[str, Any]:
    """Convert StrategyScore to output dict."""
    result: dict[str, Any] = {
        "strategy": s.strategy,
        "benchmark_group": s.benchmark_group,
        "composite": round(s.composite, 1),
        "dimensions": {
            "quality": round(s.dimensions.quality, 1),
            "anytime": round(s.dimensions.anytime, 1),
            "efficiency": round(s.dimensions.efficiency, 1),
            "stability": round(s.dimensions.stability, 1),
            "dynamics": round(s.dimensions.dynamics, 1),
        },
        "run_count": s.run_count,
        "seed_count": s.seed_count,
        "instance_count": s.instance_count,
    }
    # Include instance details for group-level scores (not global)
    if s.benchmark_group != "all" and s.instances:
        result["instances"] = [
            {
                "benchmark_id": i.benchmark_id,
                "composite": round(i.composite, 1),
                "quality": round(i.dimensions.quality, 1),
                "anytime": round(i.dimensions.anytime, 1),
                "gap_rel": round(i.best_gap_rel, 4) if i.best_gap_rel is not None else None,
                "objective": i.best_objective,
                "reference_cost": i.reference_cost,
                "incumbent_trace_path": i.incumbent_trace_path,
            }
            for i in s.instances
        ]
    return result


def _empty_output() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config": {
            "weights": WEIGHTS,
            "thresholds": {
                "gap_thresholds": GAP_THRESHOLDS,
                "expected_throughput": EXPECTED_THROUGHPUT,
                "cv_threshold": CV_THRESHOLD,
            },
        },
        "scores": [],
    }


# =============================================================================
# CLI
# =============================================================================


def load_runs_from_paths(paths: list[str]) -> list[dict[str, Any]]:
    """Load benchmark run JSON files from paths."""
    runs = []
    for path_str in paths:
        path = Path(path_str)
        if path.is_dir():
            for json_file in sorted(path.rglob("*.json")):
                if json_file.name == "index.json":
                    continue
                try:
                    data = json.loads(json_file.read_text())
                    if "run_id" in data and "metrics" in data:
                        runs.append(data)
                except (json.JSONDecodeError, OSError):
                    continue
        elif path.is_file():
            try:
                data = json.loads(path.read_text())
                if isinstance(data, list):
                    runs.extend(data)
                elif "run_id" in data and "metrics" in data:
                    runs.append(data)
            except (json.JSONDecodeError, OSError):
                continue
    return runs


def main() -> int:
    parser = argparse.ArgumentParser(description="Strategy Performance Scoring")
    parser.add_argument(
        "--input", "-i", nargs="+",
        help="Input run JSON files or directories",
    )
    parser.add_argument(
        "--input-dir",
        help="Input directory containing benchmark results",
    )
    parser.add_argument(
        "--output", "-o", default="-",
        help="Output file path (- for stdout)",
    )
    parser.add_argument(
        "--commit",
        help="OptAgent commit hash to include in output",
    )
    parser.add_argument(
        "--calibrate", action="store_true",
        help="Output calibrated thresholds from input data (P75-based)",
    )

    args = parser.parse_args()

    # Collect input paths
    input_paths: list[str] = []
    if args.input:
        input_paths.extend(args.input)
    if args.input_dir:
        input_paths.append(args.input_dir)

    if not input_paths:
        print("Error: no input specified. Use --input or --input-dir.", file=sys.stderr)
        return 1

    runs = load_runs_from_paths(input_paths)
    if not runs:
        print(f"Warning: no valid run data found in {input_paths}", file=sys.stderr)

    # Calibration mode
    if args.calibrate:
        thresholds = calibrate_thresholds(runs)
        print(json.dumps(thresholds, indent=2, ensure_ascii=False))
        return 0

    output = score_all_runs(runs)

    # Add optional commit
    if args.commit:
        output["optagent_commit"] = args.commit

    # Write output
    output_json = json.dumps(output, indent=2, ensure_ascii=False)
    if args.output == "-":
        print(output_json)
    else:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output_json + "\n")
        print(f"Written: {args.output} ({len(output['scores'])} scores)", file=sys.stderr)

    return 0


# =============================================================================
# Calibration (Item 6)
# =============================================================================


def calibrate_thresholds(run_data_list: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute calibrated thresholds from real benchmark data.

    Uses P75 of gaps for gap_thresholds and P75 of throughput for expected_throughput.
    Call with a large set of diverse benchmark runs to get meaningful calibration.

    Returns a thresholds dict in the same format as the scoring config.
    """
    from collections import defaultdict

    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run_data in run_data_list:
        group = run_data.get("benchmark_group", "")
        if group:
            by_group[group].append(run_data)

    gap_thresholds: dict[str, float] = {}
    expected_throughput: dict[str, float] = {}
    cv_values: list[float] = []

    for group, runs in by_group.items():
        gaps: list[float] = []
        throughputs: list[float] = []
        objectives_by_instance: dict[str, list[float]] = defaultdict(list)

        for run_data in runs:
            metrics = run_data.get("metrics", {})
            diag = run_data.get("operator_diagnostics", {})

            obj = metrics.get("objective")
            ref = metrics.get("reference_cost") or metrics.get("best_known_solution")
            feasible = metrics.get("feasible", False)

            if feasible and obj is not None and ref and ref != 0:
                gap = (obj - ref) / abs(ref)
                if gap > 0:
                    gaps.append(gap)

            # Throughput
            wall = _safe_float(diag.get("wall_time_seconds", 0))
            evals = int(
                diag.get("ga_offspring_evaluated", 0)
                or diag.get("loop_candidates_evaluated", 0)
                or diag.get("alns_candidates_evaluated", 0)
                or 0
            )
            if wall > 0 and evals > 0:
                throughputs.append(evals / wall)

            # CV data
            bench_id = run_data.get("benchmark_id", "")
            if feasible and obj is not None:
                objectives_by_instance[bench_id].append(obj)

        # P75 gap threshold
        if gaps:
            gaps.sort()
            p75_idx = int(0.75 * (len(gaps) - 1))
            gap_thresholds[group] = round(gaps[p75_idx], 3)

        # P75 throughput
        if throughputs:
            throughputs.sort()
            p75_idx = int(0.75 * (len(throughputs) - 1))
            expected_throughput[group] = round(throughputs[p75_idx])

        # CV per instance
        for inst_objs in objectives_by_instance.values():
            if len(inst_objs) >= 3:
                mean = sum(inst_objs) / len(inst_objs)
                if mean != 0:
                    std = math.sqrt(sum((o - mean) ** 2 for o in inst_objs) / len(inst_objs))
                    cv_values.append(std / abs(mean))

    # CV threshold: P75 of observed CVs
    cv_threshold = CV_THRESHOLD
    if cv_values:
        cv_values.sort()
        p75_idx = int(0.75 * (len(cv_values) - 1))
        cv_threshold = round(cv_values[p75_idx], 3)

    return {
        "gap_thresholds": gap_thresholds or GAP_THRESHOLDS,
        "expected_throughput": expected_throughput or EXPECTED_THROUGHPUT,
        "cv_threshold": cv_threshold,
        "sample_size": len(run_data_list),
        "groups_calibrated": list(by_group.keys()),
    }


if __name__ == "__main__":
    sys.exit(main())
