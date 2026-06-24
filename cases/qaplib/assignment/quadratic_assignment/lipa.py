from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from benchmarks.runners.bootstrap import prefer_local_development_paths

prefer_local_development_paths()

from optagent import AdvancedGaConfig, AlnsConfig, ExternalCallbackContext, GaConfig, LocalSearchConfig, ModelBuilder, TabuConfig, solve

from benchmarks.cases.base import BenchmarkCase, StrategyDeclaration
from benchmarks.cases.common import model_style_from_program, objective_gap, strategy_profile_name, summarize_solution_metadata
from benchmarks.cases.qaplib.assignment.quadratic_assignment.raw.data import QapInstance, load_qap_case

CASE_MODULE = __name__
SOURCE = "QAPLIB"
SOURCE_KEY = "qaplib"
PROBLEM_TYPE = "assignment"
INSTANCE_TYPE = "quadratic_assignment"
FAMILY = "sequence_quadratic_assignment"
MODEL_STYLE = "sequence_var_external_call"
RAW_DIR = Path(__file__).resolve().parent / "raw"

DEFAULT_SEED = 11
DEFAULT_MAX_ITERATIONS = 40
DEFAULT_TIME_LIMIT_S = 5.0
DEFAULT_POPULATION_SIZE = 10
DEFAULT_TRACE_LIMIT = 8
DEFAULT_THREAD_COUNT = 1

QAP_GA = StrategyDeclaration("ga", "GaConfig", "ga_qap_delta_v1", config={"max_iterations": DEFAULT_MAX_ITERATIONS, "population_size": DEFAULT_POPULATION_SIZE})
QAP_ALNS = StrategyDeclaration("alns", "AlnsConfig", "alns_qap_delta_v1", config={"max_iterations": DEFAULT_MAX_ITERATIONS})
QAP_TABU = StrategyDeclaration("tabu", "TabuConfig", "tabu_qap_delta_v1", config={"max_iterations": DEFAULT_MAX_ITERATIONS})
DEFAULT_STRATEGIES = (QAP_GA, QAP_ALNS, QAP_TABU)


@dataclass(frozen=True)
class QapStrategyBudget:
    seed: int = DEFAULT_SEED
    max_iterations: int = DEFAULT_MAX_ITERATIONS
    time_limit_s: float = DEFAULT_TIME_LIMIT_S
    population_size: int = DEFAULT_POPULATION_SIZE
    trace_limit: int = DEFAULT_TRACE_LIMIT
    thread_count: int = DEFAULT_THREAD_COUNT


class QapCase(BenchmarkCase):
    def load_instance(self, **kwargs: Any) -> QapInstance:
        return load_instance(self.instance, **kwargs)

    def build_model(self, instance_data: Any | None = None, **kwargs: Any) -> "QapBenchmarkModel":
        data = instance_data if instance_data is not None else self.load_instance(**kwargs)
        return build_model(data, self.instance)


@dataclass(frozen=True)
class QapBenchmarkModel:
    program: Any
    program_spec: Any
    assignment_node_id: int
    default_assignment: list[int]
    instance: QapInstance


LIPA40A = QapCase(
    benchmark_id='qaplib_lipa40a',
    source='QAPLIB',
    problem_type=PROBLEM_TYPE,
    instance_type=INSTANCE_TYPE,
    instance='lipa40a',
    family='sequence_quadratic_assignment',
    tier='full',
    compare_key=f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/lipa40a",
    series_key=f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/lipa40a/{MODEL_STYLE}",
    size={'facilities': 40, 'locations': 40},
    data={'instance_page_url': 'https://qaplib.mgi.polymtl.ca/',
 'instance_url': 'https://qaplib.mgi.polymtl.ca/data.d/lipa40a.dat',
 'solution_page_url': 'https://qaplib.mgi.polymtl.ca/',
 'solution_url': 'https://qaplib.mgi.polymtl.ca/soln.d/lipa40a.sln'},
    reference={'objective': 31538,
 'source_label': 'Lipa40a',
 'source_url': 'https://qaplib.mgi.polymtl.ca/',
 'status': 'optimal',
 'value_kind': 'optimal'},
    problem_description='QAPLIB quadratic assignment instance lipa40a: assign 40 facilities to 40 locations. The cost is the sum of flow between facility pairs multiplied by distance between assigned locations. This is a permutation blackbox benchmark with a published optimum.',
    case_module=CASE_MODULE,
    modeling_notes={
        "model_style": MODEL_STYLE,
        "objective_sense": 'minimize',
        "public_api_primitives": tuple(['sequence_var', 'external_call']),
    },
    default_strategies=DEFAULT_STRATEGIES,
    extra={
        "modeling_form": 'sequence_var assignment permutation with external_call quadratic cost evaluator',
        "objective_sense": 'minimize',
        "optagent_modeling": {'constraints': ['sequence_var enforces a one-to-one facility-location assignment'],
 'data_mapping': 'Read QAPLIB flow and distance matrices.',
 'decision_variables': ['one sequence_var assignment of size 40; assignment[i] is the location '
                        'chosen for facility i'],
 'external_callback': 'qap_cost(ctx) computes sum(flow[i][j] * '
                      'distance[assignment[i]][assignment[j]]) over all facility pairs.',
 'objective': "builder.minimize(builder.external_call(qap_cost, name='assignment_cost'), "
              "name='assignment_cost')",
 'solver_routes': ['solve with GaConfig', 'solve with TabuConfig', 'solve with AlnsConfig']},
        "optagent_primitives": ['sequence_var', 'external_call'],
        "recommended_evaluation": {'budgets_seconds': {'calibration': 120, 'full': 600, 'smoke': 10},
 'primary_route': 'solve(..., strategy=GaConfig/TabuConfig/AlnsConfig); not a natural pure MILP '
                  'benchmark for OptAgent strategies',
 'strategy_candidates': ['ga', 'tabu', 'alns'],
 'target_metrics': ['gap_to_optimum', 'time_to_best', 'external_call_count', 'cache_hit_rate']},
    },
)

CASES = (LIPA40A,)

def load_instance(instance: str, *, allow_download: bool = True) -> QapInstance:
    return load_qap_case(_case_by_name(instance).to_row(), cache_dir=RAW_DIR, allow_download=allow_download)


def build_model(instance_data: QapInstance, instance: str) -> QapBenchmarkModel:
    case = _case_by_name(instance)
    default_assignment = list(range(instance_data.size))
    builder = ModelBuilder(metadata={"benchmark_id": case.benchmark_id, "family": FAMILY, "model_style": MODEL_STYLE, "source": SOURCE, "size": instance_data.size, "qap_flow_matrix": [list(row) for row in instance_data.flow], "qap_distance_matrix": [list(row) for row in instance_data.distance]})
    assignment = builder.sequence_var(size=instance_data.size, default=default_assignment, name="assignment")
    builder.metadata["qap_assignment_node_id"] = assignment.node_id

    def assignment_cost(ctx: ExternalCallbackContext) -> int:
        candidate = [int(item) for item in ctx.value(assignment)]
        return instance_data.assignment_cost(candidate)

    builder.minimize(builder.external_call(assignment_cost, name="assignment_cost", pure=True, deterministic=True, cacheable=True, timeout_ms=100, depends_on=(assignment,)), name="assignment_cost")
    program_spec = builder.to_program_spec()
    return QapBenchmarkModel(program=builder.freeze(), program_spec=program_spec, assignment_node_id=assignment.node_id, default_assignment=default_assignment, instance=instance_data)


def solve_case(instance: str, *, strategies: tuple[str, ...] | None = None, budget: Any = QapStrategyBudget(), allow_download: bool = True, **_: Any) -> list[dict[str, Any]]:
    case = _case_by_name(instance)
    case_row = case.to_row()
    strategy_names = strategies if strategies is not None else tuple(strategy.name for strategy in DEFAULT_STRATEGIES)
    effective_budget = _coerce_budget(budget)
    try:
        instance_data = load_instance(instance, allow_download=allow_download)
        model = build_model(instance_data, instance)
    except Exception as exc:
        return [_case_setup_error_row(case=case_row, strategy_name=strategy_name, exc=exc) for strategy_name in strategy_names]
    return [_run_strategy(case=case_row, model=model, strategy_name=strategy_name, budget=effective_budget) for strategy_name in strategy_names]


def _run_strategy(*, case: dict[str, Any], model: QapBenchmarkModel, strategy_name: str, budget: QapStrategyBudget) -> dict[str, Any]:
    strategy_config = _strategy_config(strategy_name, budget, model.instance.size)
    started = perf_counter()
    try:
        solution = solve(model.program, strategy=strategy_config, seed=budget.seed, time_limit_s=budget.time_limit_s, log_level="off", trace_output="full", trace_limit=budget.trace_limit)
        elapsed_seconds = perf_counter() - started
        assignment = [int(item) for item in solution.variable_values[model.assignment_node_id]]
        objective = model.instance.assignment_cost(assignment)
        reference = _reference_objective(case, model.instance)
        gap = objective_gap(objective, reference)
        return {"kind": "strategy_run", "benchmark_id": case["benchmark_id"], "family": case["family"], "tier": case["tier"], "instance": case["instance"], "strategy": strategy_name, "strategy_profile": strategy_profile_name(family=case["family"], strategy=strategy_name, kind="strategy_run"), "model_style": model_style_from_program(model.program, family=case["family"]), "strategy_config": asdict(strategy_config), "solver_name": solution.solver_name, "status": getattr(solution.status, "value", str(solution.status)), "feasible": bool(solution.feasible), "objective": float(objective), "reference_objective": float(reference) if reference is not None else None, "reference_kind": case.get("reference", {}).get("value_kind"), "gap_abs": gap["gap_abs"], "gap_rel": gap["gap_rel"], "elapsed_seconds": elapsed_seconds, "time_to_best_seconds": _time_to_best(solution.metadata, elapsed_seconds), "sequence_head": assignment[:20], "dimension": model.instance.size, "edge_weight_type": "qap_quadratic", "metadata": summarize_solution_metadata(solution.metadata)}
    except Exception as exc:
        elapsed_seconds = perf_counter() - started
        return {"kind": "strategy_run", "benchmark_id": case["benchmark_id"], "family": case["family"], "tier": case["tier"], "instance": case["instance"], "strategy": strategy_name, "strategy_profile": strategy_profile_name(family=case["family"], strategy=strategy_name, kind="strategy_run"), "model_style": model_style_from_program(model.program, family=case["family"]), "status": "error", "feasible": False, "objective": None, "reference_objective": _reference_objective(case, model.instance), "reference_kind": case.get("reference", {}).get("value_kind"), "gap_abs": None, "gap_rel": None, "elapsed_seconds": elapsed_seconds, "time_to_best_seconds": None, "dimension": model.instance.size, "edge_weight_type": "qap_quadratic", "error": {"type": type(exc).__name__, "message": str(exc)}}


def _strategy_config(strategy_name: str, budget: QapStrategyBudget, dimension: int) -> Any:
    if strategy_name in {"ga", "advanced_ga"}:
        population_size = max(4, budget.population_size)
        config_class = AdvancedGaConfig if strategy_name == "advanced_ga" else GaConfig
        return config_class(max_iterations=budget.max_iterations, population_size=population_size, mutation_count=max(2, population_size // 3), search_width=population_size, parallel_workers=budget.thread_count, duplicate_filter=True, mutation_portfolio=("sequence_two_opt", "sequence_block_move", "ruin_and_repair", "random_swap"), local_improvement_strategy="tabu", local_improvement_top_k=2)
    if strategy_name == "alns":
        return AlnsConfig(max_iterations=budget.max_iterations, destroy_count=max(2, min(8, dimension // 4)), repair_operators=("greedy", "beam"), acceptance="not_worse")
    if strategy_name == "tabu":
        return TabuConfig(max_iterations=budget.max_iterations, tabu_tenure=max(4, min(16, dimension)), unimproved_iteration_limit=None)
    if strategy_name == "local_search":
        return LocalSearchConfig(max_iterations=budget.max_iterations)
    raise ValueError(f"unsupported QAP strategy: {strategy_name}")


def _case_setup_error_row(*, case: dict[str, Any], strategy_name: str, exc: Exception) -> dict[str, Any]:
    return {"kind": "strategy_run", "benchmark_id": case["benchmark_id"], "family": case["family"], "tier": case["tier"], "instance": case["instance"], "strategy": strategy_name, "strategy_profile": strategy_profile_name(family=case["family"], strategy=strategy_name, kind="strategy_run"), "model_style": model_style_from_program(None, family=case["family"]), "status": "error", "feasible": False, "objective": None, "reference_objective": case.get("reference", {}).get("objective"), "reference_kind": case.get("reference", {}).get("value_kind"), "gap_abs": None, "gap_rel": None, "elapsed_seconds": 0.0, "time_to_best_seconds": None, "dimension": case.get("size", {}).get("facilities"), "edge_weight_type": "qap_quadratic", "error": {"type": type(exc).__name__, "message": str(exc)}}


def _case_by_name(instance: str) -> QapCase:
    for case in CASES:
        if case.instance == instance:
            return case
    supported = ", ".join(case.instance for case in CASES)
    raise KeyError(f"unsupported QAPLIB instance: {instance}; supported: {supported}")


def _coerce_budget(budget: Any) -> QapStrategyBudget:
    if isinstance(budget, QapStrategyBudget):
        return budget
    return QapStrategyBudget(seed=int(getattr(budget, "seed", DEFAULT_SEED)), max_iterations=int(getattr(budget, "max_iterations", DEFAULT_MAX_ITERATIONS)), time_limit_s=float(getattr(budget, "time_limit_s", DEFAULT_TIME_LIMIT_S)), population_size=int(getattr(budget, "population_size", DEFAULT_POPULATION_SIZE)), trace_limit=int(getattr(budget, "trace_limit", DEFAULT_TRACE_LIMIT)), thread_count=int(getattr(budget, "thread_count", DEFAULT_THREAD_COUNT)))


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
