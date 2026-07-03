#!/usr/bin/env python3
"""Strategy performance scoring engine.

Accepts benchmark run results (from run.py JSON output) and computes
D1–D5 dimension scores + composite score per the scoring framework at
docs/plans/strategy-performance-scoring-2026-07-03.md.

Usage:
    # Score a single run result (pipe from run.py)
    python benchmarks/run.py --case jsplib_ft06 --strategy ga | python benchmarks/scoring.py

    # Score a saved JSON file
    python benchmarks/scoring.py results.json

    # Score and write dashboard-compatible strategy-scores.json
    python benchmarks/scoring.py results.json --output strategy-scores.json

    # Score multiple files
    python benchmarks/scoring.py run1.json run2.json --output scores.json
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


# ---------------------------------------------------------------------------
# Configuration — hardcoded per scoring plan (Phase 1)
# ---------------------------------------------------------------------------

# D1: Quality thresholds per problem group
GAP_THRESHOLDS: dict[str, float] = {
    "routing": 0.20,
    "scheduling": 0.50,
    "assignment": 0.30,
}
DEFAULT_GAP_THRESHOLD = 0.30

# D2: Anytime — max integral = gap_threshold × T (computed dynamically)

# D3: Efficiency — expected throughput baselines (evaluations/sec)
EXPECTED_THROUGHPUT: dict[str, float] = {
    "routing": 100_000,
    "scheduling": 10_000,
    "assignment": 50_000,
}
DEFAULT_EXPECTED_THROUGHPUT = 50_000

# D4: Stability
CV_THRESHOLD = 0.15

# D5: Termination quality mapping
TERMINATION_QUALITY_MAP: dict[str, float] = {
    "converged": 100.0,
    "optimal": 100.0,
    "diversity_exhausted": 80.0,
    "time_limit": 60.0,
    "iteration_limit": 40.0,
    "stagnation": 20.0,
}
DEFAULT_TERMINATION_QUALITY = 50.0

# Composite weights (Phase 1 — four dimensions active, D2 degraded without trace)
WEIGHTS = {
    "quality": 0.35,
    "anytime": 0.25,
    "efficiency": 0.15,
    "stability": 0.15,
    "dynamics": 0.10,
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DimensionScores:
    quality: float = 0.0
    anytime: float = 0.0
    efficiency: float = 0.0
    stability: float = 0.0
    dynamics: float = 0.0


@dataclass
class RunScore:
    benchmark_id: str
    strategy: str
    family: str = ""
    tier: str = ""
    composite: float = 0.0
    dimensions: DimensionScores = field(default_factory=DimensionScores)
    objective: float | None = None
    reference_cost: float | None = None
    gap_rel: float | None = None
    feasible: bool = False
    elapsed_seconds: float = 0.0
    time_to_best_seconds: float | None = None
    termination_reason: str = ""
    # Raw fields for aggregation
    evaluations: int = 0
    iterations: int = 0


@dataclass
class GroupScore:
    benchmark_group: str
    strategy: str
    composite: float = 0.0
    dimensions: DimensionScores = field(default_factory=DimensionScores)
    run_count: int = 0
    seed_count: int = 0
    instance_count: int = 0
    instances: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class StrategyScore:
    strategy: str
    benchmark_group: str  # "all" for global
    composite: float = 0.0
    dimensions: DimensionScores = field(default_factory=DimensionScores)
    run_count: int = 0
    seed_count: int = 0
    instance_count: int = 0


# ---------------------------------------------------------------------------
# Scoring functions — per dimension
# ---------------------------------------------------------------------------

def _infer_group(family: str) -> str:
    """Map family to benchmark_group."""
    if "tsp" in family or "routing" in family:
        return "routing"
    if "job_shop" in family or "scheduling" in family or "cumulative" in family or "transition_penalty" in family:
        return "scheduling"
    if "assignment" in family or "qap" in family:
        return "assignment"
    return "other"


def score_d1_quality(
    objective: float | None,
    reference_cost: float | None,
    feasible: bool,
    group: str,
) -> tuple[float, float | None]:
    """D1: Solution Quality. Returns (score, gap_rel)."""
    if not feasible or objective is None:
        return 0.0, None
    if reference_cost is None or reference_cost == 0:
        # No BKS — can't compute gap, give neutral score
        return 50.0, None
    gap_rel = (objective - reference_cost) / abs(reference_cost)
    threshold = GAP_THRESHOLDS.get(group, DEFAULT_GAP_THRESHOLD)
    score = max(0.0, 100.0 * (1.0 - gap_rel / threshold))
    return min(100.0, score), gap_rel


def score_d2_anytime(
    incumbent_trace: list[dict[str, float]] | None,
    reference_cost: float | None,
    time_budget_s: float,
    group: str,
) -> float:
    """D2: Anytime Performance (Primal Integral).

    If no incumbent_trace is available, degrades to a TTB-based heuristic.
    """
    if not incumbent_trace or not reference_cost or reference_cost == 0 or time_budget_s <= 0:
        # Degraded: no trace data available yet
        return -1.0  # Sentinel: exclude from scoring

    threshold = GAP_THRESHOLDS.get(group, DEFAULT_GAP_THRESHOLD)
    max_integral = threshold * time_budget_s

    # Compute primal integral using step function interpolation
    integral = 0.0
    prev_time = 0.0
    prev_gap = threshold  # assume worst before first feasible

    for event in incumbent_trace:
        t = event.get("elapsed_s", 0.0)
        obj = event.get("objective")
        if obj is None:
            continue
        gap = (obj - reference_cost) / abs(reference_cost)
        gap = max(0.0, min(gap, threshold))  # clamp

        # Area of rectangle from prev_time to t at prev_gap
        if t > prev_time:
            integral += prev_gap * (t - prev_time)
        prev_time = t
        prev_gap = gap

    # Final segment from last event to time_budget
    if time_budget_s > prev_time:
        integral += prev_gap * (time_budget_s - prev_time)

    if max_integral <= 0:
        return 100.0
    score = max(0.0, 100.0 * (1.0 - integral / max_integral))
    return min(100.0, score)


def score_d2_degraded(
    time_to_best_s: float | None,
    time_budget_s: float,
    quality_score: float,
) -> float:
    """D2 fallback when no incumbent trace: TTB ratio × quality."""
    if time_to_best_s is None or time_budget_s <= 0:
        # Can't compute — use quality as proxy
        return quality_score * 0.7  # penalized
    ttb_ratio = time_to_best_s / time_budget_s
    ttb_score = max(0.0, 100.0 * (1.0 - ttb_ratio))
    # Blend TTB with quality (early convergence to good solution = high score)
    return ttb_score * 0.6 + quality_score * 0.4


def score_d3_efficiency(
    evaluations: int,
    elapsed_seconds: float,
    group: str,
) -> float:
    """D3: Runtime Efficiency (throughput score)."""
    if elapsed_seconds <= 0 or evaluations <= 0:
        return 0.0
    eval_per_s = evaluations / elapsed_seconds
    expected = EXPECTED_THROUGHPUT.get(group, DEFAULT_EXPECTED_THROUGHPUT)
    if expected <= 1:
        return 50.0
    score = 100.0 * math.log10(max(1, eval_per_s)) / math.log10(expected)
    return min(100.0, max(0.0, score))


def score_d5_dynamics(
    termination_reason: str,
    diversity: float | None = None,
    unimproved_iterations: int | None = None,
    total_iterations: int | None = None,
) -> float:
    """D5: Search Dynamics."""
    # Sub-score 1: Diversity
    if diversity is not None:
        diversity_score = min(100.0, diversity * 200.0)
    else:
        diversity_score = 50.0  # neutral when unknown

    # Sub-score 2: Stagnation
    if unimproved_iterations is not None and total_iterations and total_iterations > 0:
        stagnation_ratio = unimproved_iterations / total_iterations
        stagnation_score = max(0.0, 100.0 * (1.0 - stagnation_ratio / 0.8))
    else:
        stagnation_score = 50.0  # neutral

    # Sub-score 3: Termination quality
    reason_key = termination_reason.lower().strip() if termination_reason else ""
    termination_score = TERMINATION_QUALITY_MAP.get(reason_key, DEFAULT_TERMINATION_QUALITY)

    return (diversity_score + stagnation_score + termination_score) / 3.0


# ---------------------------------------------------------------------------
# Per-run scoring
# ---------------------------------------------------------------------------

def score_run(run: dict[str, Any], *, time_budget_s: float | None = None) -> RunScore:
    """Score a single benchmark run result from run.py output."""
    benchmark_id = run.get("benchmark_id", "unknown")
    strategy = run.get("strategy", "unknown")
    family = run.get("family", "")
    tier = run.get("tier", "")
    group = _infer_group(family)

    objective = run.get("objective")
    reference_cost = run.get("reference_objective")
    feasible = bool(run.get("feasible", False))
    elapsed = float(run.get("elapsed_seconds", 0))
    ttb = run.get("time_to_best_seconds")

    # Extract metadata/diagnostics
    metadata = run.get("metadata", {}) or {}
    diagnostics = run.get("diagnostics", {}) or {}
    combined_meta = {**metadata, **diagnostics}

    termination_reason = str(combined_meta.get("termination_reason", run.get("termination_reason", "")))
    iterations = int(combined_meta.get("iterations", combined_meta.get("ga_generation_count", 0)) or 0)
    evaluations = int(
        combined_meta.get("ga_offspring_evaluated", 0)
        or combined_meta.get("alns_candidates_evaluated", 0)
        or combined_meta.get("loop_candidates_evaluated", 0)
        or 0
    )
    diversity = combined_meta.get("diversity")
    if diversity is not None:
        try:
            diversity = float(diversity)
        except (TypeError, ValueError):
            diversity = None
    unimproved = combined_meta.get("unimproved_iterations")
    if unimproved is not None:
        try:
            unimproved = int(unimproved)
        except (TypeError, ValueError):
            unimproved = None

    # Incumbent trace (if available)
    incumbent_trace = combined_meta.get("incumbent_trace")
    if isinstance(incumbent_trace, str):
        try:
            incumbent_trace = json.loads(incumbent_trace)
        except (json.JSONDecodeError, TypeError):
            incumbent_trace = None

    # Effective time budget
    budget = time_budget_s or elapsed or 5.0

    # --- Score each dimension ---
    d1, gap_rel = score_d1_quality(objective, reference_cost, feasible, group)

    d2_full = score_d2_anytime(incumbent_trace, reference_cost, budget, group)
    if d2_full < 0:
        # No trace — use degraded scoring
        d2 = score_d2_degraded(ttb, budget, d1)
    else:
        d2 = d2_full

    d3 = score_d3_efficiency(evaluations, elapsed, group)

    # D4 (Stability) requires multi-seed — computed at aggregation level
    d4 = -1.0  # sentinel: per-run cannot compute

    d5 = score_d5_dynamics(termination_reason, diversity, unimproved, iterations)

    # Composite (exclude D4 at per-run level, redistribute its weight)
    if d4 < 0:
        # Redistribute D4 weight proportionally to other dimensions
        active_weight = WEIGHTS["quality"] + WEIGHTS["anytime"] + WEIGHTS["efficiency"] + WEIGHTS["dynamics"]
        composite = (
            WEIGHTS["quality"] / active_weight * d1
            + WEIGHTS["anytime"] / active_weight * d2
            + WEIGHTS["efficiency"] / active_weight * d3
            + WEIGHTS["dynamics"] / active_weight * d5
        )
    else:
        composite = (
            WEIGHTS["quality"] * d1
            + WEIGHTS["anytime"] * d2
            + WEIGHTS["efficiency"] * d3
            + WEIGHTS["stability"] * d4
            + WEIGHTS["dynamics"] * d5
        )

    return RunScore(
        benchmark_id=benchmark_id,
        strategy=strategy,
        family=family,
        tier=tier,
        composite=round(composite, 1),
        dimensions=DimensionScores(
            quality=round(d1, 1),
            anytime=round(d2, 1),
            efficiency=round(d3, 1),
            stability=round(d4, 1) if d4 >= 0 else -1.0,
            dynamics=round(d5, 1),
        ),
        objective=objective,
        reference_cost=reference_cost,
        gap_rel=round(gap_rel, 4) if gap_rel is not None else None,
        feasible=feasible,
        elapsed_seconds=elapsed,
        time_to_best_seconds=ttb,
        termination_reason=termination_reason,
        evaluations=evaluations,
        iterations=iterations,
    )


# ---------------------------------------------------------------------------
# Aggregation — multi-run → per-instance / per-group / global
# ---------------------------------------------------------------------------

def score_d4_stability(objectives: list[float], reference_cost: float | None, group: str) -> float:
    """D4: Stability — computed from multiple seed runs."""
    if len(objectives) < 3:
        return -1.0  # insufficient data

    mean_obj = sum(objectives) / len(objectives)
    if mean_obj == 0:
        return 50.0

    # Consistency (CV)
    variance = sum((x - mean_obj) ** 2 for x in objectives) / len(objectives)
    std = math.sqrt(variance)
    cv = std / abs(mean_obj)
    consistency_score = max(0.0, 100.0 * (1.0 - cv / CV_THRESHOLD))

    # Feasibility rate — all provided objectives are feasible by definition
    feasibility_score = 100.0

    # Worst case
    if reference_cost and reference_cost != 0:
        threshold = GAP_THRESHOLDS.get(group, DEFAULT_GAP_THRESHOLD)
        worst = max(objectives)  # assuming minimization
        worst_gap = (worst - reference_cost) / abs(reference_cost)
        worst_case_score = max(0.0, 100.0 * (1.0 - worst_gap / threshold))
    else:
        worst_case_score = 50.0

    return 0.5 * consistency_score + 0.3 * feasibility_score + 0.2 * worst_case_score


def aggregate_scores(run_scores: list[RunScore]) -> list[StrategyScore]:
    """Aggregate per-run scores into per-group and global strategy scores."""
    from collections import defaultdict

    # Group by (strategy, group)
    by_strategy_group: dict[tuple[str, str], list[RunScore]] = defaultdict(list)
    for rs in run_scores:
        group = _infer_group(rs.family)
        by_strategy_group[(rs.strategy, group)].append(rs)

    results: list[StrategyScore] = []

    # Per-group scores
    strategy_totals: dict[str, list[StrategyScore]] = defaultdict(list)

    for (strategy, group), runs in sorted(by_strategy_group.items()):
        # Compute D4 from feasible objectives
        feasible_objectives = [r.objective for r in runs if r.feasible and r.objective is not None]
        ref = runs[0].reference_cost if runs else None
        d4 = score_d4_stability(feasible_objectives, ref, group)

        # Average D1, D2, D3, D5 across runs
        d1_avg = _mean([r.dimensions.quality for r in runs])
        d2_avg = _mean([r.dimensions.anytime for r in runs])
        d3_avg = _mean([r.dimensions.efficiency for r in runs])
        d5_avg = _mean([r.dimensions.dynamics for r in runs])

        # Composite
        if d4 >= 0:
            composite = (
                WEIGHTS["quality"] * d1_avg
                + WEIGHTS["anytime"] * d2_avg
                + WEIGHTS["efficiency"] * d3_avg
                + WEIGHTS["stability"] * d4
                + WEIGHTS["dynamics"] * d5_avg
            )
        else:
            active_w = WEIGHTS["quality"] + WEIGHTS["anytime"] + WEIGHTS["efficiency"] + WEIGHTS["dynamics"]
            composite = (
                WEIGHTS["quality"] / active_w * d1_avg
                + WEIGHTS["anytime"] / active_w * d2_avg
                + WEIGHTS["efficiency"] / active_w * d3_avg
                + WEIGHTS["dynamics"] / active_w * d5_avg
            )

        instances = set(r.benchmark_id for r in runs)
        seeds = len(runs)  # approximation

        gs = StrategyScore(
            strategy=strategy,
            benchmark_group=group,
            composite=round(composite, 1),
            dimensions=DimensionScores(
                quality=round(d1_avg, 1),
                anytime=round(d2_avg, 1),
                efficiency=round(d3_avg, 1),
                stability=round(d4, 1) if d4 >= 0 else -1.0,
                dynamics=round(d5_avg, 1),
            ),
            run_count=len(runs),
            seed_count=seeds,
            instance_count=len(instances),
        )
        results.append(gs)
        strategy_totals[strategy].append(gs)

    # Global per-strategy
    for strategy, group_scores in strategy_totals.items():
        total_runs = sum(gs.run_count for gs in group_scores)
        total_instances = sum(gs.instance_count for gs in group_scores)
        # Weighted average by run_count
        if total_runs > 0:
            composite = sum(gs.composite * gs.run_count for gs in group_scores) / total_runs
            d1 = sum(gs.dimensions.quality * gs.run_count for gs in group_scores) / total_runs
            d2 = sum(gs.dimensions.anytime * gs.run_count for gs in group_scores) / total_runs
            d3 = sum(gs.dimensions.efficiency * gs.run_count for gs in group_scores) / total_runs
            d4_vals = [gs.dimensions.stability for gs in group_scores if gs.dimensions.stability >= 0]
            d4 = _mean(d4_vals) if d4_vals else -1.0
            d5 = sum(gs.dimensions.dynamics * gs.run_count for gs in group_scores) / total_runs
        else:
            composite = d1 = d2 = d3 = d4 = d5 = 0.0

        results.append(StrategyScore(
            strategy=strategy,
            benchmark_group="all",
            composite=round(composite, 1),
            dimensions=DimensionScores(
                quality=round(d1, 1),
                anytime=round(d2, 1),
                efficiency=round(d3, 1),
                stability=round(d4, 1) if d4 >= 0 else -1.0,
                dynamics=round(d5, 1),
            ),
            run_count=total_runs,
            seed_count=total_runs,
            instance_count=total_instances,
        ))

    return results


def _mean(values: list[float]) -> float:
    valid = [v for v in values if v >= 0]
    return sum(valid) / len(valid) if valid else 0.0


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_terminal_report(run_scores: list[RunScore], strategy_scores: list[StrategyScore]) -> str:
    """Format a human-readable terminal report."""
    lines: list[str] = []
    lines.append("=" * 78)
    lines.append("  Strategy Performance Scoring Report")
    lines.append("=" * 78)

    # Global scores
    global_scores = [s for s in strategy_scores if s.benchmark_group == "all"]
    if global_scores:
        lines.append("")
        lines.append("  OVERALL SCORES")
        lines.append(f"  {'Strategy':<16} {'Composite':>9} {'Quality':>8} {'Anytime':>8} {'Effic.':>7} {'Stab.':>6} {'Dynam.':>7}")
        lines.append(f"  {'-'*72}")
        for s in sorted(global_scores, key=lambda x: -x.composite):
            stab = f"{s.dimensions.stability:.1f}" if s.dimensions.stability >= 0 else "n/a"
            lines.append(
                f"  {s.strategy:<16} {s.composite:>8.1f}  "
                f"{s.dimensions.quality:>7.1f} {s.dimensions.anytime:>7.1f} "
                f"{s.dimensions.efficiency:>6.1f} {stab:>5} {s.dimensions.dynamics:>6.1f}"
            )

    # Per-group
    group_scores = [s for s in strategy_scores if s.benchmark_group != "all"]
    groups = sorted(set(s.benchmark_group for s in group_scores))
    for group in groups:
        gs = [s for s in group_scores if s.benchmark_group == group]
        lines.append("")
        lines.append(f"  [{group.upper()}]")
        for s in sorted(gs, key=lambda x: -x.composite):
            lines.append(f"    {s.strategy:<14} composite={s.composite:.1f}  Q={s.dimensions.quality:.0f} A={s.dimensions.anytime:.0f} E={s.dimensions.efficiency:.0f} D={s.dimensions.dynamics:.0f}  ({s.run_count} runs)")

    # Per-run details
    if run_scores:
        lines.append("")
        lines.append("  PER-RUN DETAILS")
        lines.append(f"  {'Case':<24} {'Strategy':<12} {'Score':>6} {'Obj':>10} {'Gap%':>7} {'Time':>6} {'Term'}")
        lines.append(f"  {'-'*78}")
        for r in sorted(run_scores, key=lambda x: (x.strategy, x.benchmark_id)):
            obj_str = f"{r.objective:.1f}" if r.objective is not None else "n/a"
            gap_str = f"{r.gap_rel*100:.1f}%" if r.gap_rel is not None else "n/a"
            lines.append(
                f"  {r.benchmark_id:<24} {r.strategy:<12} {r.composite:>5.1f} "
                f"{obj_str:>10} {gap_str:>7} {r.elapsed_seconds:>5.2f}s {r.termination_reason}"
            )

    lines.append("")
    lines.append("=" * 78)
    return "\n".join(lines)


def to_dashboard_json(strategy_scores: list[StrategyScore], *, commit: str = "local") -> dict[str, Any]:
    """Convert scores to dashboard strategy-scores.json format."""
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z",
        "optagent_commit": commit,
        "config": {
            "weights": WEIGHTS,
            "thresholds": {
                "gap_thresholds": GAP_THRESHOLDS,
                "expected_throughput": EXPECTED_THROUGHPUT,
                "cv_threshold": CV_THRESHOLD,
            },
        },
        "scores": [
            {
                "strategy": s.strategy,
                "benchmark_group": s.benchmark_group,
                "composite": s.composite,
                "dimensions": asdict(s.dimensions),
                "run_count": s.run_count,
                "seed_count": s.seed_count,
                "instance_count": s.instance_count,
            }
            for s in strategy_scores
        ],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score benchmark run results (D1–D5 + composite).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "input",
        nargs="*",
        help="JSON file(s) containing run.py output. Reads stdin if omitted.",
    )
    parser.add_argument(
        "--output", "-o",
        help="Write strategy-scores.json to this path (dashboard format).",
    )
    parser.add_argument(
        "--time-budget", type=float, default=None,
        help="Override time budget (seconds) for D2 scoring.",
    )
    parser.add_argument(
        "--commit", default="local",
        help="OptAgent commit hash for the output JSON.",
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Suppress terminal report, only write --output.",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output per-run scores as JSON to stdout.",
    )
    args = parser.parse_args()

    # Load input
    runs: list[dict[str, Any]] = []
    if args.input:
        for path_str in args.input:
            path = Path(path_str)
            data = json.loads(path.read_text())
            if isinstance(data, list):
                runs.extend(data)
            else:
                runs.append(data)
    else:
        # Read from stdin
        raw = sys.stdin.read().strip()
        if not raw:
            print("Error: no input provided. Pipe from run.py or pass JSON files.", file=sys.stderr)
            return 1
        data = json.loads(raw)
        if isinstance(data, list):
            runs.extend(data)
        else:
            runs.append(data)

    if not runs:
        print("Error: no benchmark runs found in input.", file=sys.stderr)
        return 1

    # Filter out error runs without objectives (can still score partial data)
    scoreable = [r for r in runs if r.get("status") != "error" or r.get("objective") is not None]
    if not scoreable:
        print(f"Warning: all {len(runs)} runs are errors with no objective. Scoring error runs.", file=sys.stderr)
        scoreable = runs

    # Score each run
    run_scores = [score_run(r, time_budget_s=args.time_budget) for r in scoreable]

    # Aggregate
    strategy_scores = aggregate_scores(run_scores)

    # Output
    if args.json:
        output = [asdict(rs) for rs in run_scores]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    elif not args.quiet:
        report = format_terminal_report(run_scores, strategy_scores)
        print(report)

    # Write dashboard JSON
    if args.output:
        dashboard_data = to_dashboard_json(strategy_scores, commit=args.commit)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(dashboard_data, indent=2, ensure_ascii=False) + "\n")
        if not args.quiet:
            print(f"\n  Dashboard scores written to: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
