from __future__ import annotations

import argparse
import json

from benchmarks.runners.bootstrap import prefer_local_development_paths


def main() -> int:
    prefer_local_development_paths()
    from benchmarks.runners.suite import DEFAULT_RUNNABLE_FAMILIES, DEFAULT_STRATEGIES, run_benchmark_suite

    parser = argparse.ArgumentParser(description="Run the OptAgent modeling-native benchmark suite.")
    parser.add_argument("--family", action="append", dest="families", help="Benchmark family to run. Defaults to runnable smoke families.")
    parser.add_argument("--tier", action="append", dest="tiers", help="Benchmark tier to run. Defaults to smoke.")
    parser.add_argument("--case", action="append", dest="cases", help="Benchmark case id to run.")
    parser.add_argument(
        "--strategy",
        action="append",
        dest="strategies",
        help="Strategy to run. Defaults to family-aware ga/alns/tabu; scheduling tabu/lns requests are replaced by alns.",
    )
    parser.add_argument(
        "--model-style",
        action="append",
        dest="model_styles",
        help="TSP model style to run. Repeat to compare blackbox and graph-native rows.",
    )
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--max-iterations", type=int, default=40)
    parser.add_argument("--time-limit-s", type=float, default=5.0)
    parser.add_argument("--population-size", type=int, default=10)
    parser.add_argument("--trace-limit", type=int, default=8)
    parser.add_argument("--data-cache-dir")
    parser.add_argument("--no-download", action="store_true", help="Fail when a required public instance is not already cached.")
    parser.add_argument("--timestamp", help="Explicit run directory name, primarily for tests.")
    args = parser.parse_args()

    summary = run_benchmark_suite(
        families=tuple(args.families or DEFAULT_RUNNABLE_FAMILIES),
        tiers=tuple(args.tiers or ("smoke",)),
        benchmark_ids=tuple(args.cases or ()),
        strategies=tuple(args.strategies or DEFAULT_STRATEGIES),
        seed=args.seed,
        max_iterations=args.max_iterations,
        time_limit_s=args.time_limit_s,
        population_size=args.population_size,
        trace_limit=args.trace_limit,
        data_cache_dir=args.data_cache_dir,
        allow_download=not args.no_download,
        model_styles=tuple(args.model_styles or ()),
        timestamp=args.timestamp,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
