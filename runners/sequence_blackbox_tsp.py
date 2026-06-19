from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any

from benchmarks.runners.bootstrap import prefer_local_development_paths

prefer_local_development_paths()

from optagent import AlnsConfig, GaConfig, SolveOptions, TabuConfig, solve

from benchmarks.loaders.sequence_blackbox_tsp import TspInstance, load_tsp_case
from benchmarks.models.sequence_blackbox_tsp import TspBenchmarkModel, build_tsp_model
from benchmarks.models.sequence_graph_tsp import GRAPH_TSP_MODEL_STYLE, build_tsp_graph_model
from benchmarks.runners.common import model_style_from_program, objective_gap, strategy_profile_name, summarize_solution_metadata

BLACKBOX_TSP_MODEL_STYLE = "sequence_var_external_call"
DEFAULT_TSP_MODEL_STYLES = (BLACKBOX_TSP_MODEL_STYLE,)
SUPPORTED_TSP_MODEL_STYLES = (BLACKBOX_TSP_MODEL_STYLE, GRAPH_TSP_MODEL_STYLE)


@dataclass(frozen=True)
class TspStrategyBudget:
    seed: int = 11
    max_iterations: int = 40
    time_limit_s: float = 5.0
    population_size: int = 10
    trace_limit: int = 8


def run_tsp_case(
    case: dict[str, Any],
    *,
    strategies: tuple[str, ...] = ("ga", "alns", "tabu"),
    budget: TspStrategyBudget = TspStrategyBudget(),
    data_cache_dir: str | None = None,
    allow_download: bool = True,
    model_styles: tuple[str, ...] = DEFAULT_TSP_MODEL_STYLES,
) -> list[dict[str, Any]]:
    requested_model_styles = model_styles or DEFAULT_TSP_MODEL_STYLES
    load_kwargs: dict[str, Any] = {"allow_download": allow_download}
    if data_cache_dir is not None:
        load_kwargs["cache_dir"] = data_cache_dir
    try:
        instance = load_tsp_case(case, **load_kwargs)
        models = [_build_model_for_style(case, instance, model_style) for model_style in requested_model_styles]
    except Exception as exc:
        rows: list[dict[str, Any]] = []
        for model_style in requested_model_styles:
            rows.extend(
                _case_setup_error_row(case=case, strategy_name=strategy_name, exc=exc, model_style=model_style)
                for strategy_name in strategies
            )
        return rows

    rows: list[dict[str, Any]] = []
    for model in models:
        for strategy_name in strategies:
            rows.append(_run_strategy(case=case, model=model, strategy_name=strategy_name, budget=budget))
    return rows


def _build_model_for_style(case: dict[str, Any], instance: TspInstance, model_style: str) -> TspBenchmarkModel:
    if model_style == BLACKBOX_TSP_MODEL_STYLE:
        return build_tsp_model(case, instance)
    if model_style == GRAPH_TSP_MODEL_STYLE:
        return build_tsp_graph_model(case, instance)
    raise ValueError(f"unsupported TSP model style: {model_style}")


def _run_strategy(
    *,
    case: dict[str, Any],
    model: TspBenchmarkModel,
    strategy_name: str,
    budget: TspStrategyBudget,
) -> dict[str, Any]:
    strategy_config = _strategy_config(strategy_name, budget, model.instance.dimension)
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
            ),
        )
        elapsed_seconds = perf_counter() - started
        sequence = [int(item) for item in solution.variable_values[model.sequence_node_id]]
        objective = model.instance.tour_length(sequence, include_return_edge=True)
        reference = _reference_objective(case)
        gap = objective_gap(objective, reference)
        return {
            "kind": "strategy_run",
            "benchmark_id": case["benchmark_id"],
            "family": case["family"],
            "tier": case["tier"],
            "instance": case["instance"],
            "strategy": strategy_name,
            "strategy_profile": strategy_profile_name(
                family=case["family"],
                strategy=strategy_name,
                model_style=model_style_from_program(model.program, family=case["family"]),
                kind="strategy_run",
            ),
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
            "sequence_head": sequence[:20],
            "dimension": model.instance.dimension,
            "edge_weight_type": model.instance.edge_weight_type,
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
            "strategy_profile": strategy_profile_name(
                family=case["family"],
                strategy=strategy_name,
                model_style=model_style_from_program(model.program, family=case["family"]),
                kind="strategy_run",
            ),
            "model_style": model_style_from_program(model.program, family=case["family"]),
            "status": "error",
            "feasible": False,
            "objective": None,
            "reference_objective": _reference_objective(case),
            "reference_kind": case.get("reference", {}).get("value_kind"),
            "gap_abs": None,
            "gap_rel": None,
            "elapsed_seconds": elapsed_seconds,
            "time_to_best_seconds": None,
            "dimension": model.instance.dimension,
            "edge_weight_type": model.instance.edge_weight_type,
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }


def _strategy_config(strategy_name: str, budget: TspStrategyBudget, dimension: int) -> Any:
    if strategy_name == "ga":
        population_size = max(4, budget.population_size)
        return GaConfig(
            max_iterations=budget.max_iterations,
            population_size=population_size,
            mutation_count=max(2, population_size // 3),
            search_width=population_size,
            parallel_workers=1,
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
            destroy_count=max(2, min(12, dimension // 12)),
            repair_operators=("greedy", "beam"),
            acceptance="not_worse",
        )
    if strategy_name == "tabu":
        return TabuConfig(
            max_iterations=budget.max_iterations,
            tabu_tenure=max(5, min(25, dimension // 3)),
            unimproved_iteration_limit=None,
        )
    raise ValueError(f"unsupported TSP strategy: {strategy_name}")


def _case_setup_error_row(
    *,
    case: dict[str, Any],
    strategy_name: str,
    exc: Exception,
    model_style: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": "strategy_run",
        "benchmark_id": case["benchmark_id"],
        "family": case["family"],
        "tier": case["tier"],
        "instance": case["instance"],
        "strategy": strategy_name,
        "strategy_profile": strategy_profile_name(
            family=case["family"],
            strategy=strategy_name,
            model_style=model_style,
            kind="strategy_run",
        ),
        "model_style": model_style or model_style_from_program(None, family=case["family"]),
        "status": "error",
        "feasible": False,
        "objective": None,
        "reference_objective": _reference_objective(case),
        "reference_kind": case.get("reference", {}).get("value_kind"),
        "gap_abs": None,
        "gap_rel": None,
        "elapsed_seconds": 0.0,
        "time_to_best_seconds": None,
        "dimension": case.get("size", {}).get("nodes"),
        "edge_weight_type": None,
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }


def _reference_objective(case: dict[str, Any]) -> float | None:
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
