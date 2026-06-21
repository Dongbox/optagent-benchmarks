from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any

from benchmarks.runners.bootstrap import prefer_local_development_paths

prefer_local_development_paths()

from optagent import AlnsConfig, GaConfig, LocalSearchConfig, TabuConfig, solve

from benchmarks.loaders.sequence_quadratic_assignment import load_qap_case
from benchmarks.models.sequence_quadratic_assignment import QapBenchmarkModel, build_qap_model
from benchmarks.runners.common import model_style_from_program, objective_gap, strategy_profile_name, summarize_solution_metadata


@dataclass(frozen=True)
class QapStrategyBudget:
    seed: int = 11
    max_iterations: int = 40
    time_limit_s: float = 5.0
    population_size: int = 10
    trace_limit: int = 8
    thread_count: int = 1


def run_qap_case(
    case: dict[str, Any],
    *,
    strategies: tuple[str, ...] = ("ga", "alns", "tabu"),
    budget: QapStrategyBudget = QapStrategyBudget(),
    data_cache_dir: str | None = None,
    allow_download: bool = True,
) -> list[dict[str, Any]]:
    load_kwargs: dict[str, Any] = {"allow_download": allow_download}
    if data_cache_dir is not None:
        load_kwargs["cache_dir"] = data_cache_dir
    try:
        instance = load_qap_case(case, **load_kwargs)
        model = build_qap_model(case, instance)
    except Exception as exc:
        return [_case_setup_error_row(case=case, strategy_name=strategy_name, exc=exc) for strategy_name in strategies]

    return [
        _run_strategy(case=case, model=model, strategy_name=strategy_name, budget=budget)
        for strategy_name in strategies
    ]


def _run_strategy(
    *,
    case: dict[str, Any],
    model: QapBenchmarkModel,
    strategy_name: str,
    budget: QapStrategyBudget,
) -> dict[str, Any]:
    strategy_config = _strategy_config(strategy_name, budget, model.instance.size)
    started = perf_counter()
    try:
        solution = solve(
            model.program,
            strategy=strategy_config,
            seed=budget.seed,
            time_limit_s=budget.time_limit_s,
            log_level="off",
            trace_output="full",
            trace_limit=budget.trace_limit,
        )
        elapsed_seconds = perf_counter() - started
        assignment = [int(item) for item in solution.variable_values[model.assignment_node_id]]
        objective = model.instance.assignment_cost(assignment)
        reference = _reference_objective(case, model.instance)
        gap = objective_gap(objective, reference)
        return {
            "kind": "strategy_run",
            "benchmark_id": case["benchmark_id"],
            "family": case["family"],
            "tier": case["tier"],
            "instance": case["instance"],
            "strategy": strategy_name,
            "strategy_profile": strategy_profile_name(family=case["family"], strategy=strategy_name, kind="strategy_run"),
            "model_style": model_style_from_program(model.program, family=case["family"]),
            "strategy_config": asdict(strategy_config),
            "solver_name": solution.solver_name,
            "status": getattr(solution.status, "value", str(solution.status)),
            "feasible": bool(solution.feasible),
            "objective": float(objective),
            "reference_objective": float(reference) if reference is not None else None,
            "reference_kind": case.get("reference", {}).get("value_kind"),
            "gap_abs": gap["gap_abs"],
            "gap_rel": gap["gap_rel"],
            "elapsed_seconds": elapsed_seconds,
            "time_to_best_seconds": _time_to_best(solution.metadata, elapsed_seconds),
            "sequence_head": assignment[:20],
            "dimension": model.instance.size,
            "edge_weight_type": "qap_quadratic",
            "metadata": summarize_solution_metadata(solution.metadata),
        }
    except Exception as exc:
        elapsed_seconds = perf_counter() - started
        return {
            "kind": "strategy_run",
            "benchmark_id": case["benchmark_id"],
            "family": case["family"],
            "tier": case["tier"],
            "instance": case["instance"],
            "strategy": strategy_name,
            "strategy_profile": strategy_profile_name(family=case["family"], strategy=strategy_name, kind="strategy_run"),
            "model_style": model_style_from_program(model.program, family=case["family"]),
            "status": "error",
            "feasible": False,
            "objective": None,
            "reference_objective": _reference_objective(case, model.instance),
            "reference_kind": case.get("reference", {}).get("value_kind"),
            "gap_abs": None,
            "gap_rel": None,
            "elapsed_seconds": elapsed_seconds,
            "time_to_best_seconds": None,
            "dimension": model.instance.size,
            "edge_weight_type": "qap_quadratic",
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }


def _strategy_config(strategy_name: str, budget: QapStrategyBudget, dimension: int) -> Any:
    if strategy_name == "ga":
        population_size = max(4, budget.population_size)
        return GaConfig(
            max_iterations=budget.max_iterations,
            population_size=population_size,
            mutation_count=max(2, population_size // 3),
            search_width=population_size,
            parallel_workers=budget.thread_count,
            duplicate_filter=True,
            mutation_portfolio=(
                "sequence_two_opt",
                "sequence_block_move",
                "ruin_and_repair",
                "random_swap",
            ),
            local_improvement_strategy="tabu",
            local_improvement_top_k=2,
        )
    if strategy_name == "alns":
        return AlnsConfig(
            max_iterations=budget.max_iterations,
            destroy_count=max(2, min(8, dimension // 4)),
            repair_operators=("greedy", "beam"),
            acceptance="not_worse",
        )
    if strategy_name == "tabu":
        return TabuConfig(
            max_iterations=budget.max_iterations,
            tabu_tenure=max(4, min(16, dimension)),
            unimproved_iteration_limit=None,
        )
    if strategy_name == "local_search":
        return LocalSearchConfig(max_iterations=budget.max_iterations)
    raise ValueError(f"unsupported QAP strategy: {strategy_name}")


def _case_setup_error_row(
    *,
    case: dict[str, Any],
    strategy_name: str,
    exc: Exception,
) -> dict[str, Any]:
    return {
        "kind": "strategy_run",
        "benchmark_id": case["benchmark_id"],
        "family": case["family"],
        "tier": case["tier"],
        "instance": case["instance"],
        "strategy": strategy_name,
        "strategy_profile": strategy_profile_name(family=case["family"], strategy=strategy_name, kind="strategy_run"),
        "model_style": model_style_from_program(None, family=case["family"]),
        "status": "error",
        "feasible": False,
        "objective": None,
        "reference_objective": case.get("reference", {}).get("objective"),
        "reference_kind": case.get("reference", {}).get("value_kind"),
        "gap_abs": None,
        "gap_rel": None,
        "elapsed_seconds": 0.0,
        "time_to_best_seconds": None,
        "dimension": case.get("size", {}).get("facilities"),
        "edge_weight_type": "qap_quadratic",
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }


def _reference_objective(case: dict[str, Any], instance: QapInstance) -> float | None:
    if instance.reference_objective is not None:
        return float(instance.reference_objective)
    objective = case.get("reference", {}).get("objective")
    return float(objective) if objective is not None else None


def _time_to_best(metadata: dict[str, Any], elapsed_seconds: float) -> float | None:
    for key in ("time_to_best_seconds", "best_solution_time_seconds", "first_best_seconds"):
        if key in metadata:
            try:
                return float(metadata[key])
            except (TypeError, ValueError):
                return None
    if metadata.get("termination_reason"):
        return float(elapsed_seconds)
    return None
