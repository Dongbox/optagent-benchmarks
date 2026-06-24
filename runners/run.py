from __future__ import annotations

import argparse
import json

from benchmarks.runners.bootstrap import prefer_local_development_paths


# 标准 benchmark suite 评测场景 CLI：
# - 只解析“跑哪些 family/case/tier/strategy、预算、缓存、输出目录”等运行声明。
# - 不直接导入任何具体 case 的建模/求解实现。
# - 具体 case 分派由 runners.suite 通过 cases.registry 完成。
# - 轻量本地单 case 测试请使用 `python -m benchmarks.run`。
def main() -> int:
    prefer_local_development_paths()
    from benchmarks.runners.suite import (
        DEFAULT_CANDIDATE_STRATEGIES,
        DEFAULT_PARALLEL_THREAD_COUNTS,
        DEFAULT_RUNNABLE_FAMILIES,
        DEFAULT_STRATEGIES,
        build_benchmark_inventory,
        run_calibration_suite,
        run_benchmark_suite,
    )
    from benchmarks.runners.common import DEFAULT_RUN_ROOT, ensure_run_dir, write_json

    parser = argparse.ArgumentParser(
        description=(
            "Run the standard artifact-writing OptAgent benchmark suite scenario. "
            "Use `python -m benchmarks.run` for lightweight local case tests."
        )
    )
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
        "--default-candidate-matrix",
        action="store_true",
        help=(
            "Emit a default strategy candidate ranking from strategy rows. "
            "When no --strategy is provided, runs local_search/alns/ga/tabu candidates."
        ),
    )
    parser.add_argument(
        "--model-style",
        action="append",
        dest="model_styles",
        help="TSP model style to run. Repeat to compare blackbox and graph-native rows.",
    )
    parser.add_argument(
        "--parallel-matrix",
        action="store_true",
        help="Run the default benchmark thread matrix: 1, 2, 4, 8, 16.",
    )
    parser.add_argument(
        "--thread-count",
        action="append",
        type=int,
        dest="thread_counts",
        help="Thread count for a parallel matrix run. Repeat to override the default matrix.",
    )
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument(
        "--calibration-seed",
        action="append",
        type=int,
        dest="calibration_seeds",
        help=(
            "Run a multi-seed calibration wrapper. Repeat for each seed. "
            "When set, --seed is ignored and the default tier remains calibration unless --tier is provided."
        ),
    )
    parser.add_argument("--max-iterations", type=int, default=40)
    parser.add_argument("--time-limit-s", type=float, default=5.0)
    parser.add_argument("--population-size", type=int, default=10)
    parser.add_argument("--trace-limit", type=int, default=8)
    parser.add_argument("--no-download", action="store_true", help="Fail when a required public instance is not already cached.")
    parser.add_argument("--output-root", default=str(DEFAULT_RUN_ROOT), help="Directory where benchmark run artifacts are written.")
    parser.add_argument(
        "--list-inventory",
        action="store_true",
        help="Write and print benchmark inventory without executing solver routes.",
    )
    parser.add_argument("--timestamp", help="Explicit run directory name, primarily for tests.")
    args = parser.parse_args()
    families = tuple(args.families or DEFAULT_RUNNABLE_FAMILIES)
    tiers = tuple(args.tiers or ("calibration" if args.calibration_seeds else "smoke",))
    benchmark_ids = tuple(args.cases or ())
    strategies = tuple(
        args.strategies
        or (DEFAULT_CANDIDATE_STRATEGIES if args.default_candidate_matrix else DEFAULT_STRATEGIES)
    )
    thread_counts = tuple(
        args.thread_counts
        or (DEFAULT_PARALLEL_THREAD_COUNTS if args.parallel_matrix else ())
    )
    if args.list_inventory:
        inventory = build_benchmark_inventory(
            families=families,
            tiers=tiers,
            benchmark_ids=benchmark_ids,
            strategies=strategies,
            seed=args.seed,
            max_iterations=args.max_iterations,
            time_limit_s=args.time_limit_s,
            population_size=args.population_size,
            trace_limit=args.trace_limit,
            thread_counts=thread_counts or (1,),
        )
        run_dir = ensure_run_dir(args.output_root, timestamp=args.timestamp)
        write_json(run_dir / "inventory.json", inventory)
        write_json(run_dir / "run_metadata.json", inventory["environment"])
        summary = {
            "run_dir": str(run_dir),
            "mode": "inventory",
            "selected_case_count": inventory["selected_case_count"],
            "families": inventory["requested_families"],
            "tiers": inventory["requested_tiers"],
            "strategies": inventory["requested_strategies"],
            "artifacts": {
                "inventory": str(run_dir / "inventory.json"),
                "run_metadata": str(run_dir / "run_metadata.json"),
            },
        }
        write_json(run_dir / "summary.json", summary)
        print(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True))
        return 0

    if args.calibration_seeds:
        summary = run_calibration_suite(
            output_root=args.output_root,
            families=families,
            tiers=tiers,
            benchmark_ids=benchmark_ids,
            strategies=strategies,
            seeds=tuple(args.calibration_seeds),
            max_iterations=args.max_iterations,
            time_limit_s=args.time_limit_s,
            population_size=args.population_size,
            trace_limit=args.trace_limit,
            allow_download=not args.no_download,
            model_styles=tuple(args.model_styles or ()),
            default_candidate_matrix=args.default_candidate_matrix,
            parallel_thread_counts=thread_counts,
            timestamp=args.timestamp,
        )
        print(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True))
        return 0

    summary = run_benchmark_suite(
        output_root=args.output_root,
        families=families,
        tiers=tiers,
        benchmark_ids=benchmark_ids,
        strategies=strategies,
        seed=args.seed,
        max_iterations=args.max_iterations,
        time_limit_s=args.time_limit_s,
        population_size=args.population_size,
        trace_limit=args.trace_limit,
        allow_download=not args.no_download,
        model_styles=tuple(args.model_styles or ()),
        default_candidate_matrix=args.default_candidate_matrix,
        parallel_thread_counts=thread_counts,
        timestamp=args.timestamp,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
