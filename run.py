from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from typing import Any, Iterable

from benchmarks.bootstrap import prefer_local_development_paths
from benchmarks.cases.base import CaseDeclaration, case_to_row
from benchmarks.cases.registry import benchmark_cases


@dataclass(frozen=True)
class LocalRunBudget:
    seed: int = 11
    max_iterations: int = 40
    time_limit_s: float = 5.0
    population_size: int = 10
    trace_limit: int = 8
    thread_count: int = 1
    cpsat_time_limit_s: float | None = None


def all_cases() -> list[dict[str, Any]]:
    """Collect benchmark cases from concrete case modules."""

    return benchmark_cases()


def list_cases() -> list[dict[str, Any]]:
    return all_cases()


def select_cases(
    cases: Iterable[CaseDeclaration],
    *,
    families: Iterable[str] | None = None,
    tiers: Iterable[str] | None = None,
    benchmark_ids: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    family_filter = set(families or ())
    tier_filter = set(tiers or ())
    id_filter = set(benchmark_ids or ())

    selected: list[dict[str, Any]] = []
    for case in cases:
        row = case_to_row(case)
        if family_filter and row.get("family") not in family_filter:
            continue
        if tier_filter and row.get("tier") not in tier_filter:
            continue
        if id_filter and row.get("benchmark_id") not in id_filter:
            continue
        selected.append(row)
    return selected


def case_by_id(benchmark_id: str) -> dict[str, Any]:
    for case in all_cases():
        if case["benchmark_id"] == benchmark_id:
            return case
    raise KeyError(f"benchmark case not found: {benchmark_id}")


def run_case(
    case: Any,
    *,
    strategies: tuple[Any, ...] | None = None,
    allow_download: bool = True,
    budget: Any | None = None,
    include_exact_baseline: bool = True,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    from benchmarks.cases.registry import run_case as run_registered_case

    case_declaration = case_by_id(case) if isinstance(case, str) else case
    return run_registered_case(
        case_declaration,
        strategies=strategies,
        allow_download=allow_download,
        budget=budget if budget is not None else LocalRunBudget(),
        include_exact_baseline=include_exact_baseline,
        **kwargs,
    )


def main() -> int:
    prefer_local_development_paths()
    parser = argparse.ArgumentParser(description="Run benchmark cases directly for local development.")
    parser.add_argument("--list-cases", action="store_true", help="List available benchmark cases and exit.")
    parser.add_argument("--case", dest="benchmark_id", help="Benchmark id to run, such as jsplib_abz5.")
    parser.add_argument("--family", action="append", dest="families", help="Filter --list-cases by family.")
    parser.add_argument("--tier", action="append", dest="tiers", help="Filter --list-cases by benchmark tier.")
    parser.add_argument("--strategy", action="append", dest="strategies", help="Strategy name to run. Repeat to run multiple strategies.")
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--max-iterations", type=int, default=40)
    parser.add_argument("--time-limit-s", type=float, default=5.0)
    parser.add_argument("--population-size", type=int, default=10)
    parser.add_argument("--trace-limit", type=int, default=8)
    parser.add_argument("--thread-count", type=int, default=1)
    parser.add_argument("--cpsat-time-limit-s", type=float)
    parser.add_argument("--no-download", action="store_true", help="Fail when a required public instance is not already cached.")
    parser.add_argument("--no-exact-baseline", action="store_true", help="Skip exact baseline rows when the case provides one.")
    args = parser.parse_args()

    if args.list_cases:
        selected_cases = select_cases(
            list_cases(),
            families=tuple(args.families or ()),
            tiers=tuple(args.tiers or ()),
            benchmark_ids=(args.benchmark_id,) if args.benchmark_id else (),
        )
        rows = [
            {
                "benchmark_id": case["benchmark_id"],
                "family": case.get("family"),
                "tier": case.get("tier"),
                "instance": case.get("instance"),
                "compare_key": case.get("compare_key"),
                "series_key": case.get("series_key"),
            }
            for case in selected_cases
        ]
        print(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True))
        return 0

    if not args.benchmark_id:
        parser.error("--case is required unless --list-cases is set")

    budget = LocalRunBudget(
        seed=args.seed,
        max_iterations=args.max_iterations,
        time_limit_s=args.time_limit_s,
        population_size=args.population_size,
        trace_limit=args.trace_limit,
        thread_count=args.thread_count,
        cpsat_time_limit_s=args.cpsat_time_limit_s,
    )
    rows = run_case(
        args.benchmark_id,
        strategies=tuple(args.strategies) if args.strategies else None,
        allow_download=not args.no_download,
        budget=budget,
        include_exact_baseline=not args.no_exact_baseline,
    )
    print(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
