from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any

from benchmarks.runners.bootstrap import prefer_local_development_paths

prefer_local_development_paths()

from optagent import AlnsConfig, CpSatConfig, GaConfig, SolveOptions, TabuConfig, solve, solve_cpsat

from benchmarks.loaders.cumulative_resource_scheduling import load_rcpsp_case
from benchmarks.models.cumulative_resource_scheduling import (
    RcpspBenchmarkModel,
    activity_start_head,
    build_rcpsp_model,
    makespan_from_solution,
)
from benchmarks.runners.common import objective_gap, summarize_solution_metadata


@dataclass(frozen=True)
class RcpspStrategyBudget:
    seed: int = 11
    max_iterations: int = 40
    time_limit_s: float = 5.0
    population_size: int = 10
    trace_limit: int = 8
    cpsat_time_limit_s: float | None = None

    @property
    def effective_cpsat_time_limit_s(self) -> float:
        return float(self.cpsat_time_limit_s if self.cpsat_time_limit_s is not None else self.time_limit_s)


def run_rcpsp_case(
    case: dict[str, Any],
    *,
    strategies: tuple[str, ...] = ("ga", "alns", "tabu"),
    budget: RcpspStrategyBudget = RcpspStrategyBudget(),
    data_cache_dir: str | None = None,
    allow_download: bool = True,
    include_exact_baseline: bool = True,
) -> list[dict[str, Any]]:
    load_kwargs: dict[str, Any] = {"allow_download": allow_download}
    if data_cache_dir is not None:
        load_kwargs["cache_dir"] = data_cache_dir
    try:
        instance = load_rcpsp_case(case, **load_kwargs)
        model = build_rcpsp_model(case, instance)
    except Exception as exc:
        rows = []
        if include_exact_baseline:
            rows.append(_case_setup_error_row(case=case, strategy_name="cpsat", exc=exc))
        rows.extend(_case_setup_error_row(case=case, strategy_name=strategy_name, exc=exc) for strategy_name in strategies)
        return rows

    rows: list[dict[str, Any]] = []
    if include_exact_baseline:
        rows.append(_run_cpsat_baseline(case=case, model=model, budget=budget))
    for strategy_name in strategies:
        rows.append(_run_strategy(case=case, model=model, strategy_name=strategy_name, budget=budget))
    return rows


def _run_cpsat_baseline(
    *,
    case: dict[str, Any],
    model: RcpspBenchmarkModel,
    budget: RcpspStrategyBudget,
) -> dict[str, Any]:
    started = perf_counter()
    try:
        solution = solve_cpsat(
            model.program,
            config=CpSatConfig(
                time_limit_s=budget.effective_cpsat_time_limit_s,
                workers=1,
                random_seed=budget.seed,
                log_to_stdout=False,
                enable_solution_callback=True,
                solution_event_limit=budget.trace_limit,
            ),
        )
        elapsed_seconds = perf_counter() - started
        raw_objective = _solution_objective(model, solution.variable_values, solution.objective_value)
        objective = raw_objective if solution.feasible else None
        reference = _reference_objective(case)
        gap = objective_gap(objective, reference)
        return {
            "kind": "exact_baseline",
            "benchmark_id": case["benchmark_id"],
            "family": case["family"],
            "tier": case["tier"],
            "instance": case["instance"],
            "strategy": "cpsat",
            "strategy_config": {
                "time_limit_s": budget.effective_cpsat_time_limit_s,
                "workers": 1,
                "random_seed": budget.seed,
                "solution_event_limit": budget.trace_limit,
            },
            "solver_name": solution.solver_name,
            "status": getattr(solution.status, "value", str(solution.status)),
            "feasible": bool(solution.feasible),
            "objective": float(objective) if objective is not None else None,
            "raw_objective": float(raw_objective) if raw_objective is not None else None,
            "reference_objective": float(reference) if reference is not None else None,
            "reference_kind": case.get("reference", {}).get("value_kind"),
            "gap_abs": gap["gap_abs"],
            "gap_rel": gap["gap_rel"],
            "elapsed_seconds": elapsed_seconds,
            "time_to_best_seconds": _time_to_best(solution.metadata, elapsed_seconds),
            "time_to_first_feasible_seconds": _time_to_first_feasible(solution.metadata),
            "dimension": model.instance.activity_count,
            "edge_weight_type": "rcpsp_cumulative",
            "metadata": {
                **_exact_metadata(solution.metadata),
                "activities": model.instance.activity_count,
                "renewable_resources": model.instance.resource_count,
                "horizon": model.horizon,
            },
            "activity_start_head": activity_start_head(model, solution.variable_values),
        }
    except Exception as exc:
        elapsed_seconds = perf_counter() - started
        return _error_row(
            kind="exact_baseline",
            case=case,
            model=model,
            strategy_name="cpsat",
            exc=exc,
            elapsed_seconds=elapsed_seconds,
        )


def _run_strategy(
    *,
    case: dict[str, Any],
    model: RcpspBenchmarkModel,
    strategy_name: str,
    budget: RcpspStrategyBudget,
) -> dict[str, Any]:
    strategy_config = _strategy_config(strategy_name, budget, model.instance.activity_count)
    started = perf_counter()
    try:
        solution = solve(
            model.program,
            SolveOptions(
                strategy=strategy_config,
                seed=budget.seed,
                time_limit_s=budget.time_limit_s,
                log_level="off",
                trace_output="summary",
                trace_limit=budget.trace_limit,
                exact_repair=strategy_name == "alns",
            ),
        )
        elapsed_seconds = perf_counter() - started
        raw_objective = _solution_objective(model, solution.variable_values, solution.objective_value)
        objective = raw_objective if solution.feasible else None
        reference = _reference_objective(case)
        gap = objective_gap(objective, reference)
        return {
            "kind": "strategy_run",
            "benchmark_id": case["benchmark_id"],
            "family": case["family"],
            "tier": case["tier"],
            "instance": case["instance"],
            "strategy": strategy_name,
            "strategy_config": asdict(strategy_config),
            "solver_name": solution.solver_name,
            "status": getattr(solution.status, "value", str(solution.status)),
            "feasible": bool(solution.feasible),
            "objective": float(objective) if objective is not None else None,
            "raw_objective": float(raw_objective) if raw_objective is not None else None,
            "reference_objective": float(reference) if reference is not None else None,
            "reference_kind": case.get("reference", {}).get("value_kind"),
            "gap_abs": gap["gap_abs"],
            "gap_rel": gap["gap_rel"],
            "elapsed_seconds": elapsed_seconds,
            "time_to_best_seconds": _time_to_best(solution.metadata, elapsed_seconds),
            "time_to_first_feasible_seconds": _time_to_first_feasible(solution.metadata),
            "dimension": model.instance.activity_count,
            "edge_weight_type": "rcpsp_cumulative",
            "metadata": summarize_solution_metadata(solution.metadata),
            "activity_start_head": activity_start_head(model, solution.variable_values),
        }
    except Exception as exc:
        elapsed_seconds = perf_counter() - started
        return _error_row(
            kind="strategy_run",
            case=case,
            model=model,
            strategy_name=strategy_name,
            exc=exc,
            elapsed_seconds=elapsed_seconds,
        )


def _strategy_config(strategy_name: str, budget: RcpspStrategyBudget, activity_count: int) -> Any:
    destroy_count = max(2, min(16, activity_count // 8))
    if strategy_name == "ga":
        population_size = max(4, budget.population_size)
        return GaConfig(
            max_iterations=budget.max_iterations,
            population_size=population_size,
            mutation_count=max(2, population_size // 3),
            search_width=population_size,
            parallel_workers=1,
            duplicate_filter=True,
            mutation_portfolio=("scheduling_lns", "ruin_and_repair", "random_swap"),
            local_improvement_strategy="lns",
            local_improvement_top_k=2,
        )
    if strategy_name == "alns":
        return AlnsConfig(
            max_iterations=budget.max_iterations,
            destroy_count=destroy_count,
            repair_operators=("greedy", "beam"),
            acceptance="not_worse",
            exact_repair_on_stall=True,
            exact_repair_max_calls=1,
            exact_repair_time_budget_s=min(1.0, max(0.1, budget.time_limit_s / 4.0)),
        )
    if strategy_name == "tabu":
        return TabuConfig(
            max_iterations=budget.max_iterations,
            tabu_tenure=max(4, min(30, activity_count // 4)),
            unimproved_iteration_limit=None,
        )
    raise ValueError(f"unsupported RCPSP strategy: {strategy_name}")


def _case_setup_error_row(
    *,
    case: dict[str, Any],
    strategy_name: str,
    exc: Exception,
) -> dict[str, Any]:
    return {
        "kind": "exact_baseline" if strategy_name == "cpsat" else "strategy_run",
        "benchmark_id": case["benchmark_id"],
        "family": case["family"],
        "tier": case["tier"],
        "instance": case["instance"],
        "strategy": strategy_name,
        "status": "error",
        "feasible": False,
        "objective": None,
        "raw_objective": None,
        "reference_objective": _reference_objective(case),
        "reference_kind": case.get("reference", {}).get("value_kind"),
        "gap_abs": None,
        "gap_rel": None,
        "elapsed_seconds": 0.0,
        "time_to_best_seconds": None,
        "time_to_first_feasible_seconds": None,
        "dimension": case.get("size", {}).get("activities"),
        "edge_weight_type": "rcpsp_cumulative",
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }


def _error_row(
    *,
    kind: str,
    case: dict[str, Any],
    model: RcpspBenchmarkModel,
    strategy_name: str,
    exc: Exception,
    elapsed_seconds: float,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "benchmark_id": case["benchmark_id"],
        "family": case["family"],
        "tier": case["tier"],
        "instance": case["instance"],
        "strategy": strategy_name,
        "status": "error",
        "feasible": False,
        "objective": None,
        "raw_objective": None,
        "reference_objective": _reference_objective(case),
        "reference_kind": case.get("reference", {}).get("value_kind"),
        "gap_abs": None,
        "gap_rel": None,
        "elapsed_seconds": elapsed_seconds,
        "time_to_best_seconds": None,
        "time_to_first_feasible_seconds": None,
        "dimension": model.instance.activity_count,
        "edge_weight_type": "rcpsp_cumulative",
        "metadata": {
            "activities": model.instance.activity_count,
            "renewable_resources": model.instance.resource_count,
            "horizon": model.horizon,
        },
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }


def _reference_objective(case: dict[str, Any]) -> float | None:
    objective = case.get("reference", {}).get("objective")
    return float(objective) if objective is not None else None


def _solution_objective(
    model: RcpspBenchmarkModel,
    variable_values: dict[int, Any],
    solution_objective: float | None,
) -> float | None:
    if solution_objective is not None:
        return float(solution_objective)
    makespan = makespan_from_solution(model, variable_values)
    return float(makespan) if makespan is not None else None


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


def _time_to_first_feasible(metadata: dict[str, Any]) -> float | None:
    callback = metadata.get("solution_callback")
    if isinstance(callback, dict):
        first = callback.get("first_solution_seconds")
        if first is not None:
            try:
                return float(first)
            except (TypeError, ValueError):
                return None
    for key in ("time_to_first_feasible_seconds", "first_solution_seconds"):
        if key in metadata:
            try:
                return float(metadata[key])
            except (TypeError, ValueError):
                return None
    return None


def _exact_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "backend",
        "backend_status",
        "backend_status_name",
        "wall_time_seconds",
        "best_objective_bound",
        "certified_bound",
        "certified_lower_bound",
        "certified_upper_bound",
        "num_branches",
        "num_conflicts",
        "incomplete_search",
        "reported_as_unknown",
        "response_has_incumbent",
        "solution_callback",
    )
    return {key: metadata[key] for key in keys if key in metadata}
