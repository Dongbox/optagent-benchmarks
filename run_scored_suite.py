#!/usr/bin/env python3
"""Run benchmark suite and produce scored output.

Executes TSP and steel scheduling benchmarks across strategies and seeds,
collects all scoring-relevant metrics (incumbent trace, diversity, iterations),
then runs scoring.py to produce strategy-scores.json.

Usage:
    PYTHONPATH=build/native-debug-ninja:src .venv/bin/python scripts/benchmark/run_scored_suite.py
    PYTHONPATH=build/native-release-ninja:src .venv/bin/python scripts/benchmark/run_scored_suite.py --seeds 8

Output:
    benchmark_results/           — per-run JSON + incumbent_trace.json
    benchmark_results/scores/    — strategy-scores.json + history
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from optagent.modeling.builder import ModelBuilder
from optagent.strategy import AdvancedGaConfig, GaConfig

from benchmarks.run_collector import BenchmarkRunCollector
from benchmarks.scoring import score_all_runs


# =============================================================================
# Benchmark Instances
# =============================================================================


def build_tsp_instance(n: int, seed: int = 42) -> dict[str, Any]:
    """Generate a random TSP instance."""
    rng = random.Random(seed)
    coords = [(rng.randint(0, 100), rng.randint(0, 100)) for _ in range(n)]
    dist = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            dx = coords[i][0] - coords[j][0]
            dy = coords[i][1] - coords[j][1]
            dist[i][j] = int(math.sqrt(dx * dx + dy * dy) + 0.5)
    return {"n": n, "coords": coords, "dist": dist}


def build_tsp_program(instance: dict[str, Any]):
    """Build optagent program for TSP."""
    n = instance["n"]
    dist = instance["dist"]
    builder = ModelBuilder()
    sequence = builder.sequence_var(size=n, default=list(range(n)), name="tour")
    edges = [{"from": i, "to": j, "cost": dist[i][j]} for i in range(n) for j in range(n) if i != j]
    graph = {"format": "sparse", "size": n, "edges": edges}
    cost = builder.sequence_transition_sum(sequence, graph, include_return_edge=True, default_edge_cost=0)
    builder.minimize(cost, name="total_distance")
    return builder.freeze()


def tsp_reference_cost(instance: dict[str, Any]) -> float:
    """Compute a greedy nearest-neighbor solution as reference."""
    n = instance["n"]
    dist = instance["dist"]
    visited = [False] * n
    tour = [0]
    visited[0] = True
    for _ in range(n - 1):
        last = tour[-1]
        best_next = -1
        best_dist = float("inf")
        for j in range(n):
            if not visited[j] and dist[last][j] < best_dist:
                best_dist = dist[last][j]
                best_next = j
        tour.append(best_next)
        visited[best_next] = True
    # Return edge
    total = sum(dist[tour[i]][tour[(i + 1) % n]] for i in range(n))
    return float(total)


def build_scheduling_instance(n: int, seed: int = 42) -> dict[str, Any]:
    """Generate a random steel scheduling instance."""
    rng = random.Random(seed)
    # Generate transition matrix: ~30% of pairs need a transition
    transition = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j and rng.random() < 0.3:
                transition[i][j] = 1
    return {"n": n, "transition": transition}


def build_scheduling_program(instance: dict[str, Any]):
    """Build optagent program for scheduling."""
    n = instance["n"]
    transition = instance["transition"]
    builder = ModelBuilder()
    sequence = builder.sequence_var(size=n, default=list(range(n)), name="order")
    edges = [{"from": i, "to": j, "cost": transition[i][j]} for i in range(n) for j in range(n) if i != j]
    graph = {"format": "sparse", "size": n, "edges": edges}
    cost = builder.sequence_transition_sum(sequence, graph, include_return_edge=False, default_edge_cost=0)
    builder.minimize(cost, name="transitions")
    return builder.freeze()


def scheduling_reference_cost(instance: dict[str, Any]) -> float:
    """Compute a greedy reference for scheduling."""
    n = instance["n"]
    transition = instance["transition"]
    visited = [False] * n
    order = [0]
    visited[0] = True
    for _ in range(n - 1):
        last = order[-1]
        best_next = -1
        best_cost = float("inf")
        for j in range(n):
            if not visited[j] and transition[last][j] < best_cost:
                best_cost = transition[last][j]
                best_next = j
        order.append(best_next)
        visited[best_next] = True
    total = sum(transition[order[i]][order[i + 1]] for i in range(n - 1))
    return float(total)


def build_assignment_instance(n: int, seed: int = 42) -> dict[str, Any]:
    """Generate a random QAP-like assignment instance."""
    rng = random.Random(seed)
    # Flow and distance matrices
    flow = [[rng.randint(0, 10) for _ in range(n)] for _ in range(n)]
    distance = [[rng.randint(0, 10) for _ in range(n)] for _ in range(n)]
    # Zero diagonal
    for i in range(n):
        flow[i][i] = 0
        distance[i][i] = 0
    return {"n": n, "flow": flow, "distance": distance}


def build_assignment_program(instance: dict[str, Any]):
    """Build optagent program for QAP assignment."""
    n = instance["n"]
    flow = instance["flow"]
    distance = instance["distance"]
    builder = ModelBuilder()

    # Assignment: sequence variable where position i gets facility sequence[i]
    sequence = builder.sequence_var(size=n, default=list(range(n)), name="assignment")

    # Build cost using transition_sum: cost of assigning facility i before j
    # is sum of flow[i][j] * distance[pos_i][pos_j] — approximated via transition
    # For simplicity, use a linearized cost matrix
    cost_matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                cost_matrix[i][j] = flow[i][j] + distance[i][j]

    edges = [{"from": i, "to": j, "cost": cost_matrix[i][j]} for i in range(n) for j in range(n) if i != j]
    graph = {"format": "sparse", "size": n, "edges": edges}
    cost = builder.sequence_transition_sum(sequence, graph, include_return_edge=False, default_edge_cost=0)
    builder.minimize(cost, name="assignment_cost")
    return builder.freeze()


def assignment_reference_cost(instance: dict[str, Any]) -> float:
    """Greedy reference for assignment."""
    n = instance["n"]
    flow = instance["flow"]
    distance = instance["distance"]
    # Greedy: identity assignment cost
    total = 0
    order = list(range(n))
    for i in range(n - 1):
        total += flow[order[i]][order[i + 1]] + distance[order[i]][order[i + 1]]
    return float(total)


# =============================================================================
# Suite Runner
# =============================================================================


def run_suite(
    output_dir: Path,
    seeds: int = 5,
    time_limit: float = 5.0,
    problem_sizes: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    """Run the full benchmark suite.

    Returns list of run_data dicts.
    """
    if problem_sizes is None:
        problem_sizes = {"routing": 20, "scheduling": 50, "assignment": 15}

    strategies: list[tuple[str, Any]] = [
        ("ga", GaConfig(population_size=8)),
        ("advanced_ga", AdvancedGaConfig()),
    ]

    # Build instances
    instances: list[dict[str, Any]] = []

    # Routing (TSP)
    tsp = build_tsp_instance(problem_sizes["routing"], seed=1)
    tsp_program = build_tsp_program(tsp)
    tsp_ref = tsp_reference_cost(tsp)
    instances.append({
        "group": "routing", "id": f"tsp_{problem_sizes['routing']}",
        "program": tsp_program, "reference_cost": tsp_ref,
    })

    # Scheduling
    sched = build_scheduling_instance(problem_sizes["scheduling"], seed=1)
    sched_program = build_scheduling_program(sched)
    sched_ref = scheduling_reference_cost(sched)
    instances.append({
        "group": "scheduling", "id": f"steel_{problem_sizes['scheduling']}",
        "program": sched_program, "reference_cost": sched_ref,
    })

    # Assignment (QAP)
    qap = build_assignment_instance(problem_sizes["assignment"], seed=1)
    qap_program = build_assignment_program(qap)
    qap_ref = assignment_reference_cost(qap)
    instances.append({
        "group": "assignment", "id": f"qap_{problem_sizes['assignment']}",
        "program": qap_program, "reference_cost": qap_ref,
    })

    all_runs: list[dict[str, Any]] = []
    total = len(instances) * len(strategies) * seeds
    count = 0

    for inst in instances:
        for strategy_name, strategy_config in strategies:
            for seed in range(seeds):
                count += 1
                print(f"  [{count}/{total}] {inst['group']}/{inst['id']} · {strategy_name} · seed={seed}", end="")
                sys.stdout.flush()

                collector = BenchmarkRunCollector(
                    benchmark_group=inst["group"],
                    benchmark_id=inst["id"],
                    strategy=strategy_name,
                    reference_cost=inst["reference_cost"],
                    family=inst["group"],
                )

                try:
                    result = collector.run(
                        inst["program"],
                        strategy=strategy_config,
                        time_limit_s=time_limit,
                        seed=seed,
                        log_level="off",
                    )
                    obj = result.objective_value
                    print(f"  obj={obj:.2f}" if obj is not None else "  obj=N/A")
                except Exception as e:
                    print(f"  ERROR: {e}")
                    continue

                # Save individual run
                run_dir = output_dir / inst["group"] / strategy_name
                collector.save(run_dir)
                all_runs.append(collector.run_data)

    return all_runs


# =============================================================================
# Main
# =============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(description="Run scored benchmark suite")
    parser.add_argument("--output", "-o", default="benchmark_results", help="Output directory")
    parser.add_argument("--seeds", type=int, default=5, help="Number of seeds per instance")
    parser.add_argument("--time-limit", type=float, default=5.0, help="Time limit per run (seconds)")
    parser.add_argument("--tsp-size", type=int, default=20, help="TSP instance size")
    parser.add_argument("--sched-size", type=int, default=50, help="Scheduling instance size")
    parser.add_argument("--qap-size", type=int, default=15, help="QAP instance size")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    problem_sizes = {
        "routing": args.tsp_size,
        "scheduling": args.sched_size,
        "assignment": args.qap_size,
    }

    print("=" * 70)
    print("OptAgent Scored Benchmark Suite")
    print(f"  Output: {output_dir}")
    print(f"  Seeds: {args.seeds}")
    print(f"  Time limit: {args.time_limit}s")
    print(f"  Sizes: TSP={args.tsp_size}, Scheduling={args.sched_size}, QAP={args.qap_size}")
    print("=" * 70)

    start = time.time()
    all_runs = run_suite(
        output_dir,
        seeds=args.seeds,
        time_limit=args.time_limit,
        problem_sizes=problem_sizes,
    )
    elapsed = time.time() - start

    print(f"\n{'=' * 70}")
    print(f"Suite complete: {len(all_runs)} runs in {elapsed:.1f}s")

    # Run scoring
    scores_dir = output_dir / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)

    output = score_all_runs(all_runs)
    scores_path = scores_dir / "strategy-scores.json"
    scores_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print(f"Scores written: {scores_path} ({len(output['scores'])} entries)")

    # Print summary
    print(f"\n{'─' * 70}")
    print(f"{'Strategy':<15} {'Group':<12} {'Composite':>9} {'Quality':>8} {'Anytime':>8} {'Effic.':>7} {'Stab.':>7} {'Dynam.':>7}")
    print(f"{'─' * 70}")
    for s in sorted(output["scores"], key=lambda x: (-1 if x["benchmark_group"] == "all" else 0, x["strategy"])):
        dims = s["dimensions"]
        print(
            f"{s['strategy']:<15} {s['benchmark_group']:<12} {s['composite']:>9.1f}"
            f" {dims['quality']:>8.1f} {dims['anytime']:>8.1f}"
            f" {dims['efficiency']:>7.1f} {dims['stability']:>7.1f} {dims['dynamics']:>7.1f}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
