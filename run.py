from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from time import perf_counter
from typing import Any, Iterable

from benchmarks.bootstrap import prefer_local_development_paths
from benchmarks.cases.base import BenchmarkCase, CaseDeclaration, case_to_row, ensure_benchmark_case
from benchmarks.cases.common import objective_gap, strategy_profile_name, summarize_solution_metadata
from benchmarks.cases.registry import benchmark_cases


@dataclass(frozen=True)
class LocalRunBudget:
    seed: int = 11
    max_iterations: int = 40
    time_limit_s: float = 5.0
    population_size: int = 10
    trace_limit: int = 8
    thread_count: int = 1


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


def case_object_by_id(benchmark_id: str) -> BenchmarkCase:
    from benchmarks.cases.registry import benchmark_case_objects

    for case in benchmark_case_objects():
        if case.benchmark_id == benchmark_id:
            return case
    raise KeyError(f"benchmark case not found: {benchmark_id}")


def run_case(
    case: Any,
    *,
    strategies: tuple[Any, ...] | None = None,
    allow_download: bool = True,
    budget: Any | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    case_declaration = case_object_by_id(case) if isinstance(case, str) else ensure_benchmark_case(case)
    return run_benchmark_case(
        case_declaration,
        strategies=strategies,
        allow_download=allow_download,
        budget=budget if budget is not None else LocalRunBudget(),
        **kwargs,
    )


def run_benchmark_case(
    case: BenchmarkCase,
    *,
    strategies: tuple[Any, ...] | None = None,
    allow_download: bool = True,
    budget: Any | None = None,
    model_styles: tuple[str, ...] | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    effective_budget = budget if budget is not None else LocalRunBudget()
    strategy_names = tuple(str(item) for item in strategies) if strategies is not None else default_strategy_names_for_family(case.family)
    if case.family == "exact_linear_mip":
        strategy_names = strategy_names or ("optx",)
    model_style_values = tuple(model_styles or ())
    if not model_style_values and case.family == "sequence_blackbox_tsp":
        model_style_values = ("sequence_var_external_call",)
    if not model_style_values:
        model_style_values = (None,)

    rows: list[dict[str, Any]] = []
    for model_style in model_style_values:
        build_kwargs = dict(kwargs)
        build_kwargs["allow_download"] = allow_download
        if model_style is not None:
            build_kwargs["model_style"] = model_style
        for strategy_name in strategy_names:
            rows.append(_run_single_strategy(case, strategy_name=strategy_name, budget=effective_budget, build_kwargs=build_kwargs))
    return rows


def default_strategy_names_for_family(family: str) -> tuple[str, ...]:
    if family in {"interval_job_shop", "cumulative_resource_scheduling"}:
        return ("ga", "alns")
    if family in {"sequence_blackbox_tsp", "sequence_quadratic_assignment"}:
        return ("ga", "alns", "tabu")
    if family == "exact_linear_mip":
        return ("optx",)
    return ("local_search",)


def build_strategy_config(*, case: BenchmarkCase, strategy_name: str, budget: Any) -> Any:
    from optagent import AdvancedGaConfig, AlnsConfig, GaConfig, LnsConfig, LocalSearchConfig, MilpConfig, TabuConfig

    max_iterations = int(getattr(budget, "max_iterations", 40))
    population_size = max(4, int(getattr(budget, "population_size", 10)))
    thread_count = int(getattr(budget, "thread_count", 1))
    time_limit_s = float(getattr(budget, "time_limit_s", 5.0))
    size = dict(case.size)
    family = case.family
    dimension = int(size.get("nodes") or size.get("facilities") or size.get("activities") or size.get("operations") or size.get("variables") or 10)

    if family == "exact_linear_mip" or strategy_name in {"optx", "milp", "mathopt_mp"}:
        backend = "mathopt_mp" if strategy_name == "mathopt_mp" else "optx"
        return MilpConfig(backend=backend, time_limit_s=time_limit_s, threads=thread_count)
    if strategy_name in {"ga", "advanced_ga"}:
        config_class = AdvancedGaConfig if strategy_name == "advanced_ga" else GaConfig
        if family in {"interval_job_shop", "cumulative_resource_scheduling"}:
            return config_class(
                max_iterations=max_iterations,
                population_size=population_size,
                mutation_count=max(2, population_size // 3),
                search_width=population_size,
                parallel_workers=thread_count,
                duplicate_filter=True,
                mutation_portfolio=("scheduling_lns", "ruin_and_repair", "random_swap"),
                local_improvement_strategy="lns",
                local_improvement_top_k=2,
            )
        return config_class(
            max_iterations=max_iterations,
            population_size=population_size,
            mutation_count=max(2, population_size // 3),
            search_width=population_size,
            parallel_workers=thread_count,
            duplicate_filter=True,
            mutation_portfolio=("sequence_two_opt", "sequence_block_move", "ruin_and_repair", "random_swap"),
            local_improvement_strategy="tabu",
            local_improvement_top_k=2,
        )
    if strategy_name == "alns":
        destroy_count = max(2, min(16, dimension // (8 if family in {"interval_job_shop", "cumulative_resource_scheduling"} else 12)))
        kwargs: dict[str, Any] = {
            "max_iterations": max_iterations,
            "destroy_count": destroy_count,
            "repair_operators": ("greedy", "beam"),
            "acceptance": "not_worse",
        }
        if family in {"interval_job_shop", "cumulative_resource_scheduling"}:
            kwargs.update(
                {
                    "exact_repair_on_stall": True,
                    "exact_repair_max_calls": 1,
                    "exact_repair_time_budget_s": min(1.0, max(0.1, time_limit_s / 4.0)),
                }
            )
        return AlnsConfig(**kwargs)
    if strategy_name == "lns":
        return LnsConfig(max_iterations=max_iterations, destroy_count=max(2, min(16, dimension // 8)), lns_every=1)
    if strategy_name == "tabu":
        return TabuConfig(max_iterations=max_iterations, tabu_tenure=max(4, min(30, dimension // 4)), unimproved_iteration_limit=None)
    if strategy_name == "local_search":
        return LocalSearchConfig(max_iterations=max_iterations)
    raise ValueError(f"unsupported strategy for {case.benchmark_id}: {strategy_name}")


def _run_single_strategy(
    case: BenchmarkCase,
    *,
    strategy_name: str,
    budget: Any,
    build_kwargs: dict[str, Any],
) -> dict[str, Any]:
    started = perf_counter()
    strategy_config: Any | None = None
    try:
        model = case.build_model(**build_kwargs)
        strategy_config = build_strategy_config(case=case, strategy_name=strategy_name, budget=budget)
        solution = _solve_model(case, model, strategy_name=strategy_name, strategy_config=strategy_config, budget=budget)
        elapsed_seconds = perf_counter() - started
        summary = case.solution_summary(solution, **build_kwargs)
        return _result_row(case, strategy_name=strategy_name, strategy_config=strategy_config, summary=summary, elapsed_seconds=elapsed_seconds)
    except Exception as exc:
        elapsed_seconds = perf_counter() - started
        return _error_row(case, strategy_name=strategy_name, strategy_config=strategy_config, exc=exc, elapsed_seconds=elapsed_seconds)


def _solve_model(case: BenchmarkCase, model: Any, *, strategy_name: str, strategy_config: Any, budget: Any) -> Any:
    from optagent import solve, solve_milp

    time_limit_s = float(getattr(budget, "time_limit_s", 5.0))
    thread_count = int(getattr(budget, "thread_count", 1))
    if case.family == "exact_linear_mip" or strategy_name in {"optx", "milp", "mathopt_mp"}:
        return solve_milp(model, config=strategy_config)
    return solve(
        model,
        strategy=strategy_config,
        seed=int(getattr(budget, "seed", 11)),
        time_limit_s=time_limit_s,
        threads=thread_count,
        log_level="off",
        trace_output="full",
        trace_limit=int(getattr(budget, "trace_limit", 8)),
        exact_repair=strategy_name == "alns" and case.family in {"interval_job_shop", "cumulative_resource_scheduling"},
    )


def _result_row(
    case: BenchmarkCase,
    *,
    strategy_name: str,
    strategy_config: Any,
    summary: dict[str, Any],
    elapsed_seconds: float,
) -> dict[str, Any]:
    objective = summary.get("objective")
    reference = summary.get("reference_objective", case.reference_objective())
    gap = objective_gap(objective, reference)
    kind = "exact_baseline" if case.family == "exact_linear_mip" or strategy_name in {"optx", "milp", "mathopt_mp"} else "strategy_run"
    metadata = summarize_solution_metadata(dict(summary.get("metadata") or {}))
    if case.family == "exact_linear_mip":
        metadata = dict(summary.get("metadata") or {})
    row = {
        "kind": kind,
        "benchmark_id": case.benchmark_id,
        "family": case.family,
        "tier": case.tier,
        "instance": case.instance,
        "strategy": strategy_name,
        "strategy_profile": strategy_profile_name(family=case.family, strategy=strategy_name, model_style=summary.get("model_style"), kind=kind),
        "model_style": summary.get("model_style"),
        "strategy_config": _strategy_config_dict(strategy_config),
        "solver_name": summary.get("solver_name"),
        "status": summary.get("status"),
        "feasible": bool(summary.get("feasible")),
        "objective": float(objective) if objective is not None else None,
        "reference_objective": float(reference) if reference is not None else None,
        "reference_kind": case.reference.get("value_kind"),
        "gap_abs": gap["gap_abs"],
        "gap_rel": gap["gap_rel"],
        "elapsed_seconds": elapsed_seconds,
        "time_to_best_seconds": _time_to_best(dict(summary.get("metadata") or {}), elapsed_seconds),
        "metadata": metadata,
    }
    for key, value in summary.items():
        if key not in row and key not in {"metadata", "solver_name", "status", "feasible", "objective", "reference_objective"}:
            row[key] = value
    return row


def _error_row(
    case: BenchmarkCase,
    *,
    strategy_name: str,
    strategy_config: Any | None,
    exc: Exception,
    elapsed_seconds: float,
) -> dict[str, Any]:
    kind = "exact_baseline" if case.family == "exact_linear_mip" or strategy_name in {"optx", "milp", "mathopt_mp"} else "strategy_run"
    return {
        "kind": kind,
        "benchmark_id": case.benchmark_id,
        "family": case.family,
        "tier": case.tier,
        "instance": case.instance,
        "strategy": strategy_name,
        "strategy_profile": strategy_profile_name(family=case.family, strategy=strategy_name, kind=kind),
        "model_style": case.modeling_notes.get("model_style"),
        "strategy_config": _strategy_config_dict(strategy_config) if strategy_config is not None else {},
        "status": "error",
        "feasible": False,
        "objective": None,
        "reference_objective": case.reference_objective(),
        "reference_kind": case.reference.get("value_kind"),
        "gap_abs": None,
        "gap_rel": None,
        "elapsed_seconds": elapsed_seconds,
        "time_to_best_seconds": None,
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }


def _strategy_config_dict(strategy_config: Any) -> dict[str, Any]:
    try:
        row = asdict(strategy_config)
    except TypeError:
        return {}
    name = getattr(strategy_config, "name", None)
    if name is not None:
        row["name"] = name
    return row


def _time_to_best(metadata: dict[str, Any], elapsed_seconds: float) -> float | None:
    callback = metadata.get("solution_callback")
    if isinstance(callback, dict):
        best = callback.get("last_solution_seconds")
        if best is not None:
            try:
                return float(best)
            except (TypeError, ValueError):
                pass
    for key in ("time_to_best_seconds", "best_solution_time_seconds", "first_best_seconds"):
        if key in metadata:
            try:
                return float(metadata[key])
            except (TypeError, ValueError):
                return None
    if metadata.get("termination_reason") or metadata.get("backend_status_name"):
        return float(elapsed_seconds)
    return None


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
    parser.add_argument("--no-download", action="store_true", help="Fail when a required public instance is not already cached.")
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
    )
    rows = run_case(
        args.benchmark_id,
        strategies=tuple(args.strategies) if args.strategies else None,
        allow_download=not args.no_download,
        budget=budget,
    )
    print(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
