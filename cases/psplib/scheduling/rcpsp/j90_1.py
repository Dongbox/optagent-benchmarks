from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from benchmarks.bootstrap import prefer_local_development_paths

prefer_local_development_paths()

from optagent import AdvancedGaConfig, AlnsConfig, GaConfig, LnsConfig, LocalSearchConfig, ModelBuilder, TabuConfig, solve

from benchmarks.cases.base import BenchmarkCase, StrategyDeclaration
from benchmarks.cases.common import model_style_from_program, objective_gap, strategy_profile_name, summarize_solution_metadata
from benchmarks.cases.psplib.scheduling.rcpsp.raw.data import RcpspInstance, load_rcpsp_case

CASE_MODULE = __name__
SOURCE = "PSPLIB j90 via ScheduleOpt"
SOURCE_KEY = "psplib"
PROBLEM_TYPE = "scheduling"
INSTANCE_TYPE = "rcpsp"
FAMILY = "cumulative_resource_scheduling"
MODEL_STYLE = "interval_var_cumulative_precedence"
RAW_DIR = Path(__file__).resolve().parent / "raw"

DEFAULT_SEED = 11
DEFAULT_MAX_ITERATIONS = 40
DEFAULT_TIME_LIMIT_S = 5.0
DEFAULT_POPULATION_SIZE = 10
DEFAULT_TRACE_LIMIT = 8
DEFAULT_THREAD_COUNT = 1

RCPSP_GA = StrategyDeclaration("ga", "GaConfig", "ga_scheduling_feasibility_v1", config={"max_iterations": DEFAULT_MAX_ITERATIONS, "population_size": DEFAULT_POPULATION_SIZE})
RCPSP_ALNS = StrategyDeclaration("alns", "AlnsConfig", "alns_scheduling_repair_v1", config={"max_iterations": DEFAULT_MAX_ITERATIONS})
DEFAULT_STRATEGIES = (RCPSP_GA, RCPSP_ALNS)


@dataclass(frozen=True)
class RcpspStrategyBudget:
    seed: int = DEFAULT_SEED
    max_iterations: int = DEFAULT_MAX_ITERATIONS
    time_limit_s: float = DEFAULT_TIME_LIMIT_S
    population_size: int = DEFAULT_POPULATION_SIZE
    trace_limit: int = DEFAULT_TRACE_LIMIT
    thread_count: int = DEFAULT_THREAD_COUNT


class RcpspCase(BenchmarkCase):
    def load_instance(self, **kwargs: Any) -> RcpspInstance:
        return load_instance(self.instance, **kwargs)

    def build_model(self, instance_data: Any | None = None, **kwargs: Any) -> "RcpspBenchmarkModel":
        data = instance_data if instance_data is not None else self.load_instance(**kwargs)
        return build_model(data, self.instance)


@dataclass(frozen=True)
class RcpspBenchmarkModel:
    program: Any
    activity_node_ids: dict[int, int]
    objective_node_id: int
    horizon: int
    instance: RcpspInstance


J90_1_1 = RcpspCase(
    benchmark_id='psplib_j90_1_1',
    source='PSPLIB j90 via ScheduleOpt',
    problem_type=PROBLEM_TYPE,
    instance_type=INSTANCE_TYPE,
    instance='j90_1_1',
    family='cumulative_resource_scheduling',
    tier='calibration',
    compare_key=f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/j90_1_1",
    series_key=f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/j90_1_1/{MODEL_STYLE}",
    size={'activities': 90, 'renewable_resources': 4},
    data={'bounds_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j90lb.sm',
 'instance_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j90/j90_1_1.rcp'},
    reference={'lower_bound': 73,
 'notes': 'Rows marked with * in j90lb.sm have verified LB=UB optimal makespan.',
 'objective': 73,
 'source_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j90lb.sm',
 'status': 'closed',
 'upper_bound': 73,
 'value_kind': 'optimal'},
    problem_description='PSPLIB RCPSP instance j90_1_1: schedule 90 project activities with precedence constraints and four renewable resources. The objective is minimum project makespan; this selected case has a verified optimum.',
    case_module=CASE_MODULE,
    modeling_notes={
        "model_style": MODEL_STYLE,
        "objective_sense": 'minimize',
        "public_api_primitives": tuple(['interval_var', 'precedence', 'cumulative', 'max']),
    },
    default_strategies=DEFAULT_STRATEGIES,
    extra={
        "modeling_form": 'interval project scheduling with renewable resource cumulative constraints',
        "objective_sense": 'minimize',
        "optagent_modeling": {'constraints': ['builder.precedence(activity[i], activity[j]) for every project precedence arc',
                 'builder.cumulative(intervals, demands_for_resource[r], capacity[r]) for each '
                 'renewable resource'],
 'data_mapping': 'Read PSPLIB .rcp activity durations, renewable-resource demands, capacities, and '
                 'successor lists.',
 'decision_variables': ['one interval_var activity[i] per non-dummy activity with fixed duration '
                        'and bounded start'],
 'objective': 'builder.minimize(builder.max(*(builder.interval_end(activity[i]) for terminal '
              "activities)), name='makespan')",
 'solver_routes': ['solve with AlnsConfig', 'solve with GaConfig']},
        "optagent_primitives": ['interval_var', 'precedence', 'cumulative', 'max'],
        "recommended_evaluation": {'budgets_seconds': {'calibration': 180, 'full': 900, 'smoke': 30},
 'primary_route': 'solve(..., '
                  'strategy=AlnsConfig/GaConfig) for search',
 'strategy_candidates': ['alns', 'ga'],
 'target_metrics': ['gap_to_upper_bound',
                    'gap_to_lower_bound',
                    'time_to_first_feasible',
                    'feasible_rate']},
    },
)


J90_1_8 = RcpspCase(
    benchmark_id='psplib_j90_1_8',
    source='PSPLIB j90 via ScheduleOpt',
    problem_type=PROBLEM_TYPE,
    instance_type=INSTANCE_TYPE,
    instance='j90_1_8',
    family='cumulative_resource_scheduling',
    tier='calibration',
    compare_key=f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/j90_1_8",
    series_key=f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/j90_1_8/{MODEL_STYLE}",
    size={'activities': 90, 'renewable_resources': 4},
    data={'bounds_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j90lb.sm',
 'instance_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j90/j90_1_8.rcp'},
    reference={'lower_bound': 95,
 'notes': 'Rows marked with * in j90lb.sm have verified LB=UB optimal makespan.',
 'objective': 95,
 'source_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j90lb.sm',
 'status': 'closed',
 'upper_bound': 95,
 'value_kind': 'optimal'},
    problem_description='PSPLIB RCPSP instance j90_1_8: schedule 90 project activities with precedence constraints and four renewable resources. The objective is minimum project makespan; this selected case has a verified optimum.',
    case_module=CASE_MODULE,
    modeling_notes={
        "model_style": MODEL_STYLE,
        "objective_sense": 'minimize',
        "public_api_primitives": tuple(['interval_var', 'precedence', 'cumulative', 'max']),
    },
    default_strategies=DEFAULT_STRATEGIES,
    extra={
        "modeling_form": 'interval project scheduling with renewable resource cumulative constraints',
        "objective_sense": 'minimize',
        "optagent_modeling": {'constraints': ['builder.precedence(activity[i], activity[j]) for every project precedence arc',
                 'builder.cumulative(intervals, demands_for_resource[r], capacity[r]) for each '
                 'renewable resource'],
 'data_mapping': 'Read PSPLIB .rcp activity durations, renewable-resource demands, capacities, and '
                 'successor lists.',
 'decision_variables': ['one interval_var activity[i] per non-dummy activity with fixed duration '
                        'and bounded start'],
 'objective': 'builder.minimize(builder.max(*(builder.interval_end(activity[i]) for terminal '
              "activities)), name='makespan')",
 'solver_routes': ['solve with AlnsConfig', 'solve with GaConfig']},
        "optagent_primitives": ['interval_var', 'precedence', 'cumulative', 'max'],
        "recommended_evaluation": {'budgets_seconds': {'calibration': 180, 'full': 900, 'smoke': 30},
 'primary_route': 'solve(..., '
                  'strategy=AlnsConfig/GaConfig) for search',
 'strategy_candidates': ['alns', 'ga'],
 'target_metrics': ['gap_to_upper_bound',
                    'gap_to_lower_bound',
                    'time_to_first_feasible',
                    'feasible_rate']},
    },
)

CASES = (J90_1_1, J90_1_8,)

def load_instance(instance: str, *, allow_download: bool = True) -> RcpspInstance:
    return load_rcpsp_case(_case_by_name(instance).to_row(), cache_dir=RAW_DIR, allow_download=allow_download)


def build_model(instance_data: RcpspInstance, instance: str) -> RcpspBenchmarkModel:
    case = _case_by_name(instance)
    horizon = max(0, instance_data.horizon)
    builder = ModelBuilder(metadata={"benchmark_id": case.benchmark_id, "family": FAMILY, "model_style": MODEL_STYLE, "source": SOURCE, "activities": instance_data.activity_count, "non_dummy_activities": instance_data.non_dummy_activity_count, "renewable_resources": instance_data.resource_count, "horizon": horizon})
    activity_vars: dict[int, Any] = {}
    activity_node_ids: dict[int, int] = {}
    for activity in instance_data.activities:
        interval = builder.interval_var(start=0, length=activity.duration, lb_start=0, ub_start=horizon, lb_length=activity.duration, ub_length=activity.duration, name=f"activity_{activity.activity_id + 1}")
        activity_vars[activity.activity_id] = interval
        activity_node_ids[activity.activity_id] = interval.node_id
    for activity in instance_data.activities:
        before = activity_vars[activity.activity_id]
        for successor_id in activity.successors:
            builder.constraint(builder.precedence(before, activity_vars[successor_id], lag=0), name=f"activity_{activity.activity_id + 1}_before_{successor_id + 1}")
    for resource_id, capacity in enumerate(instance_data.capacities):
        intervals = []
        demands = []
        for activity in instance_data.activities:
            demand = activity.demands[resource_id]
            if demand <= 0 or activity.duration <= 0:
                continue
            intervals.append(activity_vars[activity.activity_id])
            demands.append(builder.const(demand))
        builder.constraint(builder.cumulative(intervals, demands, builder.const(capacity)), name=f"resource_{resource_id + 1}_capacity")
    objective = builder.minimize(builder.interval_end(activity_vars[instance_data.sink_activity_id]), name="makespan")
    return RcpspBenchmarkModel(program=builder.freeze(), activity_node_ids=activity_node_ids, objective_node_id=objective.node_id, horizon=horizon, instance=instance_data)


def makespan_from_solution(model: RcpspBenchmarkModel, variable_values: dict[int, Any]) -> int | None:
    sink = variable_values.get(model.activity_node_ids[model.instance.sink_activity_id])
    if not isinstance(sink, dict) or "end" not in sink:
        return None
    return int(sink["end"])


def activity_start_head(model: RcpspBenchmarkModel, variable_values: dict[int, Any], *, limit: int = 20) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for activity_id in sorted(model.activity_node_ids)[:limit]:
        raw = variable_values.get(model.activity_node_ids[activity_id])
        if isinstance(raw, dict) and "start" in raw and "end" in raw:
            rows.append({"activity": activity_id + 1, "start": int(raw["start"]), "end": int(raw["end"])})
    return rows

def solve_case(
    instance: str,
    *,
    strategies: tuple[str, ...] = ("ga", "alns"),
    budget: RcpspStrategyBudget = RcpspStrategyBudget(),
    allow_download: bool = True,
) -> list[dict[str, Any]]:
    case = _case_by_name(instance).to_row()
    effective_budget = _coerce_budget(budget)
    load_kwargs: dict[str, Any] = {"allow_download": allow_download}
    try:
        instance_data = load_instance(instance, **load_kwargs)
        model = build_model(instance_data, instance)
    except Exception as exc:
        return [_case_setup_error_row(case=case, strategy_name=strategy_name, exc=exc) for strategy_name in strategies]

    rows: list[dict[str, Any]] = []
    for strategy_name in strategies:
        rows.append(_run_strategy(case=case, model=model, strategy_name=strategy_name, budget=effective_budget))
    return rows


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
            strategy=strategy_config,
            seed=budget.seed,
            time_limit_s=budget.time_limit_s,
            log_level="off",
            trace_output="full",
            trace_limit=budget.trace_limit,
            exact_repair=strategy_name == "alns",
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
            "strategy_profile": strategy_profile_name(family=case["family"], strategy=strategy_name, kind="strategy_run"),
            "model_style": model_style_from_program(model.program, family=case["family"]),
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
            case=case,
            model=model,
            strategy_name=strategy_name,
            exc=exc,
            elapsed_seconds=elapsed_seconds,
        )


def _strategy_config(strategy_name: str, budget: RcpspStrategyBudget, activity_count: int) -> Any:
    destroy_count = max(2, min(16, activity_count // 8))
    if strategy_name in {"ga", "advanced_ga"}:
        population_size = max(4, budget.population_size)
        config_class = AdvancedGaConfig if strategy_name == "advanced_ga" else GaConfig
        return config_class(
            max_iterations=budget.max_iterations,
            population_size=population_size,
            mutation_count=max(2, population_size // 3),
            search_width=population_size,
            parallel_workers=budget.thread_count,
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
    if strategy_name == "lns":
        return LnsConfig(
            max_iterations=budget.max_iterations,
            destroy_count=destroy_count,
            lns_every=1,
        )
    if strategy_name == "tabu":
        return TabuConfig(
            max_iterations=budget.max_iterations,
            tabu_tenure=max(4, min(30, activity_count // 4)),
            unimproved_iteration_limit=None,
        )
    if strategy_name == "local_search":
        return LocalSearchConfig(max_iterations=budget.max_iterations)
    raise ValueError(f"unsupported RCPSP strategy: {strategy_name}")


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
    case: dict[str, Any],
    model: RcpspBenchmarkModel,
    strategy_name: str,
    exc: Exception,
    elapsed_seconds: float,
) -> dict[str, Any]:
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


def _coerce_budget(budget: Any) -> RcpspStrategyBudget:
    if isinstance(budget, RcpspStrategyBudget):
        return budget
    return RcpspStrategyBudget(
        seed=int(getattr(budget, "seed", DEFAULT_SEED)),
        max_iterations=int(getattr(budget, "max_iterations", DEFAULT_MAX_ITERATIONS)),
        time_limit_s=float(getattr(budget, "time_limit_s", DEFAULT_TIME_LIMIT_S)),
        population_size=int(getattr(budget, "population_size", DEFAULT_POPULATION_SIZE)),
        trace_limit=int(getattr(budget, "trace_limit", DEFAULT_TRACE_LIMIT)),
        thread_count=int(getattr(budget, "thread_count", DEFAULT_THREAD_COUNT)),
    )


def _case_by_name(instance: str) -> RcpspCase:
    for case in CASES:
        if case.instance == instance:
            return case
    supported = ", ".join(case.instance for case in CASES)
    raise KeyError(f"unsupported PSPLIB RCPSP instance: {instance}; supported: {supported}")
