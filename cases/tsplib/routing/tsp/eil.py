from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from benchmarks.bootstrap import prefer_local_development_paths

prefer_local_development_paths()

from optagent import AdvancedGaConfig, AlnsConfig, ExternalCallbackContext, GaConfig, LocalSearchConfig, ModelBuilder, TabuConfig, solve

from benchmarks.cases.base import BenchmarkCase, StrategyDeclaration
from benchmarks.cases.common import model_style_from_program, objective_gap, strategy_profile_name, summarize_solution_metadata
from benchmarks.cases.tsplib.routing.tsp.raw.data import TspInstance, load_tsp_case

CASE_MODULE = __name__
SOURCE = "TSPLIB95"
SOURCE_KEY = "tsplib"
PROBLEM_TYPE = "routing"
INSTANCE_TYPE = "tsp"
FAMILY = "sequence_blackbox_tsp"
BLACKBOX_TSP_MODEL_STYLE = "sequence_var_external_call"
GRAPH_TSP_MODEL_STYLE = "sequence_var_sequence_transition_sum"
MODEL_STYLE = BLACKBOX_TSP_MODEL_STYLE
DEFAULT_TSP_MODEL_STYLES = (BLACKBOX_TSP_MODEL_STYLE,)
SUPPORTED_TSP_MODEL_STYLES = (BLACKBOX_TSP_MODEL_STYLE, GRAPH_TSP_MODEL_STYLE)
RAW_DIR = Path(__file__).resolve().parent / "raw"

DEFAULT_SEED = 11
DEFAULT_MAX_ITERATIONS = 40
DEFAULT_TIME_LIMIT_S = 5.0
DEFAULT_POPULATION_SIZE = 10
DEFAULT_TRACE_LIMIT = 8
DEFAULT_THREAD_COUNT = 1

TSP_GA = StrategyDeclaration("ga", "GaConfig", "ga_tsp_blackbox_v1", config={"max_iterations": DEFAULT_MAX_ITERATIONS, "population_size": DEFAULT_POPULATION_SIZE})
TSP_ALNS = StrategyDeclaration("alns", "AlnsConfig", "alns_tsp_blackbox_v1", config={"max_iterations": DEFAULT_MAX_ITERATIONS})
TSP_TABU = StrategyDeclaration("tabu", "TabuConfig", "tabu_tsp_blackbox_v1", config={"max_iterations": DEFAULT_MAX_ITERATIONS})
DEFAULT_STRATEGIES = (TSP_GA, TSP_ALNS, TSP_TABU)


@dataclass(frozen=True)
class TspStrategyBudget:
    seed: int = DEFAULT_SEED
    max_iterations: int = DEFAULT_MAX_ITERATIONS
    time_limit_s: float = DEFAULT_TIME_LIMIT_S
    population_size: int = DEFAULT_POPULATION_SIZE
    trace_limit: int = DEFAULT_TRACE_LIMIT
    thread_count: int = DEFAULT_THREAD_COUNT


class TspCase(BenchmarkCase):
    def load_instance(self, **kwargs: Any) -> TspInstance:
        return load_instance(self.instance, **kwargs)

    def build_model(self, instance_data: Any | None = None, **kwargs: Any) -> "TspBenchmarkModel":
        data = instance_data if instance_data is not None else self.load_instance(**kwargs)
        return build_model(data, self.instance, **kwargs)


@dataclass(frozen=True)
class TspBenchmarkModel:
    program: Any
    sequence_node_id: int
    default_tour: list[int]
    instance: TspInstance


EIL51 = TspCase(
    benchmark_id='tsplib_eil51',
    source='TSPLIB95',
    problem_type=PROBLEM_TYPE,
    instance_type=INSTANCE_TYPE,
    instance='eil51',
    family='sequence_blackbox_tsp',
    tier='smoke',
    compare_key=f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/eil51",
    series_key=f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/eil51/{MODEL_STYLE}",
    size={'nodes': 51},
    data={'instance_url': 'https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/eil51.tsp.gz',
 'mirror_urls': ['https://raw.githubusercontent.com/mastqe/tsplib/master/eil51.tsp'],
 'solution_url': 'https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/STSP.html'},
    reference={'notes': 'TSPLIB STSP page states all symmetric TSP instances are solved to optimality.',
 'objective': 426,
 'source_url': 'https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/STSP.html',
 'status': 'optimal',
 'value_kind': 'optimal'},
    problem_description='TSPLIB symmetric TSP instance eil51: find the shortest Hamiltonian cycle over 51 cities using the instance distance metric. The benchmark is a blackbox sequence optimization case with a published optimal tour length.',
    case_module=CASE_MODULE,
    modeling_notes={
        "model_style": MODEL_STYLE,
        "objective_sense": 'minimize',
        "public_api_primitives": tuple(['sequence_var', 'external_call']),
    },
    default_strategies=DEFAULT_STRATEGIES,
    extra={
        "modeling_form": 'sequence_var route with external_call distance evaluator',
        "objective_sense": 'minimize',
        "optagent_modeling": {'constraints': ['sequence_var represents a permutation, so no separate all-different constraint '
                 'is required'],
 'data_mapping': 'Read TSPLIB coordinates or explicit distances and implement the documented '
                 'TSPLIB distance metric in a callback.',
 'decision_variables': ['one sequence_var tour of size 51; the sequence is the city visit order'],
 'external_callback': 'route_cost(ctx) reads ctx.value(tour), sums consecutive arc costs, and adds '
                      'the return-to-start arc.',
 'objective': "builder.minimize(builder.external_call(route_cost, name='tour_length'), "
              "name='tour_length')",
 'solver_routes': ['solve with GaConfig', 'solve with TabuConfig', 'solve with AlnsConfig']},
        "optagent_primitives": ['sequence_var', 'external_call'],
        "recommended_evaluation": {'budgets_seconds': {'calibration': 60, 'full': 300, 'smoke': 10},
 'primary_route': 'solve(..., strategy=GaConfig/TabuConfig/AlnsConfig); exact route only for small '
                  'diagnostic comparisons',
 'strategy_candidates': ['ga', 'tabu', 'alns'],
 'target_metrics': ['gap_to_optimum', 'time_to_best', 'external_call_count', 'cache_hit_rate']},
    },
)

CASES = (EIL51,)

def load_instance(instance: str, *, allow_download: bool = True) -> TspInstance:
    return load_tsp_case(_case_by_name(instance).to_row(), cache_dir=RAW_DIR, allow_download=allow_download)


def build_model(instance_data: TspInstance, instance: str, *, model_style: str = BLACKBOX_TSP_MODEL_STYLE) -> TspBenchmarkModel:
    case = _case_by_name(instance)
    if model_style == BLACKBOX_TSP_MODEL_STYLE:
        return _build_blackbox_model(case.to_row(), instance_data)
    if model_style == GRAPH_TSP_MODEL_STYLE:
        return _build_graph_model(case.to_row(), instance_data)
    raise ValueError(f"unsupported TSP model style: {model_style}")


def solve_case(
    instance: str,
    *,
    strategies: tuple[str, ...] | None = None,
    budget: Any = TspStrategyBudget(),
    allow_download: bool = True,
    model_styles: tuple[str, ...] = DEFAULT_TSP_MODEL_STYLES,
    **_: Any,
) -> list[dict[str, Any]]:
    case = _case_by_name(instance)
    case_row = case.to_row()
    strategy_names = strategies if strategies is not None else tuple(strategy.name for strategy in DEFAULT_STRATEGIES)
    requested_model_styles = model_styles or DEFAULT_TSP_MODEL_STYLES
    effective_budget = _coerce_budget(budget)
    try:
        instance_data = load_instance(instance, allow_download=allow_download)
        models = [build_model(instance_data, instance, model_style=model_style) for model_style in requested_model_styles]
    except Exception as exc:
        rows: list[dict[str, Any]] = []
        for model_style in requested_model_styles:
            rows.extend(_case_setup_error_row(case=case_row, strategy_name=strategy_name, exc=exc, model_style=model_style) for strategy_name in strategy_names)
        return rows
    rows: list[dict[str, Any]] = []
    for model in models:
        for strategy_name in strategy_names:
            rows.append(_run_strategy(case=case_row, model=model, strategy_name=strategy_name, budget=effective_budget))
    return rows


def _build_blackbox_model(case: dict[str, Any], instance: TspInstance) -> TspBenchmarkModel:
    default_tour = list(range(instance.dimension))
    builder = ModelBuilder(metadata={"benchmark_id": case["benchmark_id"], "family": FAMILY, "model_style": BLACKBOX_TSP_MODEL_STYLE, "source": SOURCE, "dimension": instance.dimension, "edge_weight_type": instance.edge_weight_type})
    tour = builder.sequence_var(size=instance.dimension, default=default_tour, name="tour")

    def tour_length(ctx: ExternalCallbackContext) -> int:
        order = [int(item) for item in ctx.value(tour)]
        return instance.tour_length(order, include_return_edge=True)

    builder.minimize(builder.external_call(tour_length, name="tour_length", pure=True, deterministic=True, cacheable=True, timeout_ms=100, depends_on=(tour,)), name="tour_length")
    return TspBenchmarkModel(program=builder.freeze(), sequence_node_id=tour.node_id, default_tour=default_tour, instance=instance)


def _build_graph_model(case: dict[str, Any], instance: TspInstance) -> TspBenchmarkModel:
    default_tour = list(range(instance.dimension))
    distance_matrix = [[instance.distance(left, right) for right in range(instance.dimension)] for left in range(instance.dimension)]
    builder = ModelBuilder(metadata={"benchmark_id": case["benchmark_id"], "family": FAMILY, "model_style": GRAPH_TSP_MODEL_STYLE, "source": SOURCE, "dimension": instance.dimension, "edge_weight_type": instance.edge_weight_type, "sequence_graph_symmetric": _is_symmetric(distance_matrix), "sequence_graph_weight_format": "dense_matrix"})
    tour = builder.sequence_var(size=instance.dimension, default=default_tour, name="tour")
    builder.minimize(builder.sequence_transition_sum(tour, distance_matrix, include_return_edge=True, cost_semantics="distance"), name="tour_length")
    return TspBenchmarkModel(program=builder.freeze(), sequence_node_id=tour.node_id, default_tour=default_tour, instance=instance)


def _run_strategy(*, case: dict[str, Any], model: TspBenchmarkModel, strategy_name: str, budget: TspStrategyBudget) -> dict[str, Any]:
    strategy_config = _strategy_config(strategy_name, budget, model.instance.dimension)
    started = perf_counter()
    try:
        solution = solve(model.program, strategy=strategy_config, seed=budget.seed, time_limit_s=budget.time_limit_s, log_level="off", trace_output="full", trace_limit=budget.trace_limit)
        elapsed_seconds = perf_counter() - started
        sequence = [int(item) for item in solution.variable_values[model.sequence_node_id]]
        objective = model.instance.tour_length(sequence, include_return_edge=True)
        reference = _reference_objective(case)
        gap = objective_gap(objective, reference)
        return {"kind": "strategy_run", "benchmark_id": case["benchmark_id"], "family": case["family"], "tier": case["tier"], "instance": case["instance"], "strategy": strategy_name, "strategy_profile": strategy_profile_name(family=case["family"], strategy=strategy_name, model_style=model_style_from_program(model.program, family=case["family"]), kind="strategy_run"), "model_style": model_style_from_program(model.program, family=case["family"]), "strategy_config": asdict(strategy_config), "solver_name": solution.solver_name, "status": getattr(solution.status, "value", str(solution.status)), "feasible": bool(solution.feasible), "objective": float(objective), "reference_objective": float(reference) if reference is not None else None, "reference_kind": case.get("reference", {}).get("value_kind"), "gap_abs": gap["gap_abs"], "gap_rel": gap["gap_rel"], "elapsed_seconds": elapsed_seconds, "time_to_best_seconds": _time_to_best(solution.metadata, elapsed_seconds), "sequence_head": sequence[:20], "dimension": model.instance.dimension, "edge_weight_type": model.instance.edge_weight_type, "metadata": summarize_solution_metadata(solution.metadata)}
    except Exception as exc:
        elapsed_seconds = perf_counter() - started
        return {"kind": "strategy_run", "benchmark_id": case["benchmark_id"], "family": case["family"], "tier": case["tier"], "instance": case["instance"], "strategy": strategy_name, "strategy_profile": strategy_profile_name(family=case["family"], strategy=strategy_name, model_style=model_style_from_program(model.program, family=case["family"]), kind="strategy_run"), "model_style": model_style_from_program(model.program, family=case["family"]), "status": "error", "feasible": False, "objective": None, "reference_objective": _reference_objective(case), "reference_kind": case.get("reference", {}).get("value_kind"), "gap_abs": None, "gap_rel": None, "elapsed_seconds": elapsed_seconds, "time_to_best_seconds": None, "dimension": model.instance.dimension, "edge_weight_type": model.instance.edge_weight_type, "error": {"type": type(exc).__name__, "message": str(exc)}}


def _strategy_config(strategy_name: str, budget: TspStrategyBudget, dimension: int) -> Any:
    if strategy_name in {"ga", "advanced_ga"}:
        population_size = max(4, budget.population_size)
        config_class = AdvancedGaConfig if strategy_name == "advanced_ga" else GaConfig
        return config_class(max_iterations=budget.max_iterations, population_size=population_size, mutation_count=max(2, population_size // 3), search_width=population_size, parallel_workers=budget.thread_count, duplicate_filter=True, mutation_portfolio=("sequence_two_opt", "sequence_block_move", "ruin_and_repair", "random_swap"), local_improvement_strategy="tabu", local_improvement_top_k=2)
    if strategy_name == "alns":
        return AlnsConfig(max_iterations=budget.max_iterations, destroy_count=max(2, min(12, dimension // 12)), repair_operators=("greedy", "beam"), acceptance="not_worse")
    if strategy_name == "tabu":
        return TabuConfig(max_iterations=budget.max_iterations, tabu_tenure=max(5, min(25, dimension // 3)), unimproved_iteration_limit=None)
    if strategy_name == "local_search":
        return LocalSearchConfig(max_iterations=budget.max_iterations)
    raise ValueError(f"unsupported TSP strategy: {strategy_name}")


def _case_setup_error_row(*, case: dict[str, Any], strategy_name: str, exc: Exception, model_style: str | None = None) -> dict[str, Any]:
    return {"kind": "strategy_run", "benchmark_id": case["benchmark_id"], "family": case["family"], "tier": case["tier"], "instance": case["instance"], "strategy": strategy_name, "strategy_profile": strategy_profile_name(family=case["family"], strategy=strategy_name, model_style=model_style, kind="strategy_run"), "model_style": model_style or model_style_from_program(None, family=case["family"]), "status": "error", "feasible": False, "objective": None, "reference_objective": _reference_objective(case), "reference_kind": case.get("reference", {}).get("value_kind"), "gap_abs": None, "gap_rel": None, "elapsed_seconds": 0.0, "time_to_best_seconds": None, "dimension": case.get("size", {}).get("nodes"), "edge_weight_type": None, "error": {"type": type(exc).__name__, "message": str(exc)}}


def _case_by_name(instance: str) -> TspCase:
    for case in CASES:
        if case.instance == instance:
            return case
    supported = ", ".join(case.instance for case in CASES)
    raise KeyError(f"unsupported TSPLIB TSP instance: {instance}; supported: {supported}")


def _coerce_budget(budget: Any) -> TspStrategyBudget:
    if isinstance(budget, TspStrategyBudget):
        return budget
    return TspStrategyBudget(seed=int(getattr(budget, "seed", DEFAULT_SEED)), max_iterations=int(getattr(budget, "max_iterations", DEFAULT_MAX_ITERATIONS)), time_limit_s=float(getattr(budget, "time_limit_s", DEFAULT_TIME_LIMIT_S)), population_size=int(getattr(budget, "population_size", DEFAULT_POPULATION_SIZE)), trace_limit=int(getattr(budget, "trace_limit", DEFAULT_TRACE_LIMIT)), thread_count=int(getattr(budget, "thread_count", DEFAULT_THREAD_COUNT)))


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


def _is_symmetric(matrix: list[list[int]]) -> bool:
    for left, row in enumerate(matrix):
        for right, value in enumerate(row):
            if matrix[right][left] != value:
                return False
    return True
