from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from benchmarks.bootstrap import prefer_local_development_paths

prefer_local_development_paths()

from optagent import AdvancedGaConfig, AlnsConfig, CpSatConfig, GaConfig, LnsConfig, LocalSearchConfig, ModelBuilder, TabuConfig, solve, solve_cpsat

from benchmarks.cases.base import BenchmarkCase, StrategyDeclaration
from benchmarks.cases.common import model_style_from_program, objective_gap, strategy_profile_name, summarize_solution_metadata
from benchmarks.cases.jsplib.scheduling.jobshop.raw.data import JobShopInstance, JobShopOperation, load_job_shop_case

CASE_MODULE = __name__
SOURCE = "JSPLIB via ScheduleOpt"
SOURCE_KEY = "jsplib"
PROBLEM_TYPE = "scheduling"
INSTANCE_TYPE = "jobshop"
FAMILY = "interval_job_shop"
MODEL_STYLE = "interval_var_sequence_no_overlap_precedence"
RAW_DIR = Path(__file__).resolve().parent / "raw"

DEFAULT_SEED = 11
DEFAULT_MAX_ITERATIONS = 40
DEFAULT_TIME_LIMIT_S = 5.0
DEFAULT_POPULATION_SIZE = 10
DEFAULT_TRACE_LIMIT = 8
DEFAULT_THREAD_COUNT = 1

JOBSHOP_CPSAT = StrategyDeclaration(
    name="cpsat",
    config_class="CpSatConfig",
    profile="cpsat_scheduling_exact_v1",
    kind="exact_baseline",
    config={
        "time_limit_s": DEFAULT_TIME_LIMIT_S,
        "workers": DEFAULT_THREAD_COUNT,
        "random_seed": DEFAULT_SEED,
        "log_to_stdout": False,
        "enable_solution_callback": True,
        "solution_event_limit": DEFAULT_TRACE_LIMIT,
    },
)
JOBSHOP_GA = StrategyDeclaration(
    name="ga",
    config_class="GaConfig",
    profile="ga_scheduling_feasibility_v1",
    config={
        "max_iterations": DEFAULT_MAX_ITERATIONS,
        "population_size": DEFAULT_POPULATION_SIZE,
        "duplicate_filter": True,
    },
)
JOBSHOP_ALNS = StrategyDeclaration(
    name="alns",
    config_class="AlnsConfig",
    profile="alns_scheduling_repair_v1",
    config={
        "max_iterations": DEFAULT_MAX_ITERATIONS,
        "repair_operators": ("greedy", "beam"),
        "acceptance": "not_worse",
    },
)
DEFAULT_STRATEGIES = (JOBSHOP_CPSAT, JOBSHOP_GA, JOBSHOP_ALNS)


@dataclass(frozen=True)
class JobShopStrategyBudget:
    seed: int = DEFAULT_SEED
    max_iterations: int = DEFAULT_MAX_ITERATIONS
    time_limit_s: float = DEFAULT_TIME_LIMIT_S
    population_size: int = DEFAULT_POPULATION_SIZE
    trace_limit: int = DEFAULT_TRACE_LIMIT
    thread_count: int = DEFAULT_THREAD_COUNT
    cpsat_time_limit_s: float | None = None

    @property
    def effective_cpsat_time_limit_s(self) -> float:
        return float(self.cpsat_time_limit_s if self.cpsat_time_limit_s is not None else self.time_limit_s)


class JobShopCase(BenchmarkCase):
    def load_instance(self, **kwargs: Any) -> JobShopInstance:
        return load_instance(self.instance, **kwargs)

    def build_model(self, instance_data: Any | None = None, **kwargs: Any) -> "JobShopBenchmarkModel":
        data = instance_data if instance_data is not None else self.load_instance(**kwargs)
        return build_model(data, self.instance)


@dataclass(frozen=True)
class JobShopBenchmarkModel:
    program: Any
    operation_node_ids: dict[tuple[int, int], int]
    machine_sequence_node_ids: dict[int, int]
    machine_operation_keys: dict[int, tuple[tuple[int, int], ...]]
    objective_node_id: int
    horizon: int
    instance: JobShopInstance


SWV01 = JobShopCase(
    benchmark_id='jsplib_swv01',
    source='JSPLIB via ScheduleOpt',
    problem_type=PROBLEM_TYPE,
    instance_type=INSTANCE_TYPE,
    instance='swv01',
    family='interval_job_shop',
    tier='full',
    compare_key=f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/swv01",
    series_key=f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/swv01/{MODEL_STYLE}",
    size={'jobs': 20, 'machines': 10, 'operations': 200},
    data={'documentation_url': 'https://scheduleopt.github.io/benchmarks/jsplib/',
 'instance_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/swv01.json',
 'solution_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/solutions/bks.json'},
    reference={'lower_bound': 1407,
 'objective': 1407,
 'reported_machine': 'i7-1185G7 @ 3.00GHz',
 'reported_solver': 'OptalCP',
 'reported_time_seconds': 1,
 'source_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/solutions/bks.json',
 'status': 'closed',
 'upper_bound': 1407,
 'value_kind': 'optimal'},
    problem_description='JSPLIB job-shop instance swv01: schedule 20 jobs across 10 machines. Each job has a fixed machine route and fixed operation durations; each machine can process at most one operation at a time. The benchmark objective is minimum makespan.',
    case_module=CASE_MODULE,
    modeling_notes={
        "model_style": MODEL_STYLE,
        "objective_sense": 'minimize',
        "public_api_primitives": tuple(['interval_var', 'sequence_var', 'no_overlap', 'precedence', 'max']),
    },
    default_strategies=DEFAULT_STRATEGIES,
    extra={
        "modeling_form": 'interval scheduling with machine sequences and job precedences',
        "objective_sense": 'minimize',
        "optagent_modeling": {'constraints': ['builder.no_overlap(machine_order[m], *operations_on_machine[m]) for every '
                 'machine',
                 'builder.precedence(operation[j,k], operation[j,k+1]) for every consecutive '
                 'operation in each job'],
 'data_mapping': 'Read ScheduleOpt JSPLIB JSON rows as operations with job, operation index, '
                 'machine, and duration.',
 'decision_variables': ['200 interval_var operation[j,k] with fixed duration and bounded start',
                        '10 sequence_var machine_order[m], each ordering operations assigned to '
                        'one machine'],
 'objective': 'builder.minimize(builder.max(*(builder.interval_end(last_operation[j]) for each '
              "job)), name='makespan')",
 'solver_routes': ['solve_cpsat', 'solve with AlnsConfig', 'solve with GaConfig']},
        "optagent_primitives": ['interval_var', 'sequence_var', 'no_overlap', 'precedence', 'max'],
        "recommended_evaluation": {'budgets_seconds': {'calibration': 60, 'full': 600, 'smoke': 10},
 'primary_route': 'solve_cpsat for exact baseline; solve(..., strategy=AlnsConfig/GaConfig) for '
                  'search',
 'strategy_candidates': ['alns', 'ga'],
 'target_metrics': ['gap_to_reference', 'time_to_first_feasible', 'time_to_best', 'feasible_rate']},
    },
)

CASES = (SWV01,)

def load_instance(instance: str, *, allow_download: bool = True) -> JobShopInstance:
    return load_job_shop_case(_case_by_name(instance).to_row(), cache_dir=RAW_DIR, allow_download=allow_download)


def build_model(instance_data: JobShopInstance, instance: str) -> JobShopBenchmarkModel:
    case = _case_by_name(instance)
    horizon = max(0, instance_data.horizon)
    builder = ModelBuilder(
        metadata={
            "benchmark_id": case.benchmark_id,
            "family": FAMILY,
            "model_style": MODEL_STYLE,
            "source": SOURCE,
            "jobs": instance_data.jobs,
            "machines": instance_data.machines,
            "operations": instance_data.operation_count,
            "horizon": horizon,
        }
    )

    operation_vars: dict[tuple[int, int], Any] = {}
    operation_node_ids: dict[tuple[int, int], int] = {}
    for operation in instance_data.operations:
        key = _operation_key(operation)
        interval = builder.interval_var(
            start=0,
            length=operation.duration,
            lb_start=0,
            ub_start=horizon,
            lb_length=operation.duration,
            ub_length=operation.duration,
            name=f"op_j{operation.job}_k{operation.operation}_m{operation.machine}",
        )
        operation_vars[key] = interval
        operation_node_ids[key] = interval.node_id

    machine_sequence_node_ids: dict[int, int] = {}
    machine_operation_keys: dict[int, tuple[tuple[int, int], ...]] = {}
    for machine, operations in instance_data.operations_by_machine().items():
        keys = tuple(_operation_key(operation) for operation in operations)
        sequence = builder.sequence_var(size=len(keys), default=list(range(len(keys))), name=f"machine_{machine}_order")
        machine_sequence_node_ids[machine] = sequence.node_id
        machine_operation_keys[machine] = keys
        builder.constraint(builder.no_overlap(sequence, *(operation_vars[key] for key in keys)), name=f"machine_{machine}_capacity")

    last_operation_ends = []
    for job, operations in instance_data.operations_by_job().items():
        if len(operations) != instance_data.machines:
            raise ValueError(f"job {job} has {len(operations)} operations, expected {instance_data.machines}")
        for before, after in zip(operations, operations[1:]):
            builder.constraint(
                builder.precedence(operation_vars[_operation_key(before)], operation_vars[_operation_key(after)], lag=0),
                name=f"job_{job}_op_{before.operation}_before_{after.operation}",
            )
        last_operation_ends.append(builder.interval_end(operation_vars[_operation_key(operations[-1])]))

    objective = builder.minimize(builder.max(*last_operation_ends), name="makespan")
    return JobShopBenchmarkModel(
        program=builder.freeze(),
        operation_node_ids=operation_node_ids,
        machine_sequence_node_ids=machine_sequence_node_ids,
        machine_operation_keys=machine_operation_keys,
        objective_node_id=objective.node_id,
        horizon=horizon,
        instance=instance_data,
    )

def solve_case(
    instance: str,
    *,
    strategies: tuple[str, ...] | None = None,
    budget: Any = JobShopStrategyBudget(),
    allow_download: bool = True,
    include_exact_baseline: bool = True,
    **_: Any,
) -> list[dict[str, Any]]:
    case = _case_by_name(instance)
    case_row = case.to_row()
    effective_budget = _coerce_budget(budget)
    strategy_names = strategies if strategies is not None else _default_strategy_names(include_exact=False)
    try:
        instance_data = load_instance(instance, allow_download=allow_download)
        model = build_model(instance_data, instance)
    except Exception as exc:
        rows = []
        if include_exact_baseline:
            rows.append(_case_setup_error_row(case=case_row, strategy_name="cpsat", exc=exc))
        rows.extend(_case_setup_error_row(case=case_row, strategy_name=strategy_name, exc=exc) for strategy_name in strategy_names)
        return rows

    rows: list[dict[str, Any]] = []
    if include_exact_baseline:
        rows.append(_run_cpsat_baseline(case=case_row, model=model, budget=effective_budget))
    for strategy_name in strategy_names:
        rows.append(_run_strategy(case=case_row, model=model, strategy_name=strategy_name, budget=effective_budget))
    return rows


def solve_swv01(**kwargs: Any) -> list[dict[str, Any]]:
    return solve_case("swv01", **kwargs)


def machine_order_from_solution(
    model: JobShopBenchmarkModel,
    variable_values: dict[int, Any],
) -> dict[int, list[tuple[int, int]]]:
    machine_orders: dict[int, list[tuple[int, int]]] = {}
    for machine, sequence_node_id in model.machine_sequence_node_ids.items():
        local_order = [int(item) for item in variable_values.get(sequence_node_id, [])]
        keys = model.machine_operation_keys[machine]
        machine_orders[machine] = [keys[index] for index in local_order if 0 <= index < len(keys)]
    return machine_orders


def makespan_from_solution(model: JobShopBenchmarkModel, variable_values: dict[int, Any]) -> int | None:
    ends: list[int] = []
    for node_id in model.operation_node_ids.values():
        raw = variable_values.get(node_id)
        if not isinstance(raw, dict) or "end" not in raw:
            return None
        ends.append(int(raw["end"]))
    return max(ends) if ends else None


def _run_cpsat_baseline(
    *,
    case: dict[str, Any],
    model: JobShopBenchmarkModel,
    budget: JobShopStrategyBudget,
) -> dict[str, Any]:
    started = perf_counter()
    try:
        solution = solve_cpsat(
            model.program,
            config=CpSatConfig(
                time_limit_s=budget.effective_cpsat_time_limit_s,
                workers=budget.thread_count,
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
            "strategy_profile": strategy_profile_name(family=case["family"], strategy="cpsat", kind="exact_baseline"),
            "model_style": model_style_from_program(model.program, family=case["family"]),
            "strategy_config": {
                "time_limit_s": budget.effective_cpsat_time_limit_s,
                "workers": budget.thread_count,
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
            "dimension": model.instance.operation_count,
            "edge_weight_type": "job_shop_interval",
            "metadata": {
                **_exact_metadata(solution.metadata),
                "jobs": model.instance.jobs,
                "machines": model.instance.machines,
                "horizon": model.horizon,
            },
            "machine_order_head": _machine_order_head(model, solution.variable_values),
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
    model: JobShopBenchmarkModel,
    strategy_name: str,
    budget: JobShopStrategyBudget,
) -> dict[str, Any]:
    strategy_config = _strategy_config(strategy_name, budget, model.instance.operation_count)
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
            "dimension": model.instance.operation_count,
            "edge_weight_type": "job_shop_interval",
            "metadata": summarize_solution_metadata(solution.metadata),
            "machine_order_head": _machine_order_head(model, solution.variable_values),
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


def _strategy_config(strategy_name: str, budget: JobShopStrategyBudget, operation_count: int) -> Any:
    destroy_count = max(2, min(12, operation_count // 10))
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
            mutation_portfolio=(
                "scheduling_lns",
                "ruin_and_repair",
                "random_swap",
            ),
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
            tabu_tenure=max(4, min(30, operation_count // 4)),
            unimproved_iteration_limit=None,
        )
    if strategy_name == "local_search":
        return LocalSearchConfig(max_iterations=budget.max_iterations)
    raise ValueError(f"unsupported job-shop strategy: {strategy_name}")


def _case_setup_error_row(
    *,
    case: dict[str, Any],
    strategy_name: str,
    exc: Exception,
) -> dict[str, Any]:
    kind = "exact_baseline" if strategy_name == "cpsat" else "strategy_run"
    return {
        "kind": kind,
        "benchmark_id": case["benchmark_id"],
        "family": case["family"],
        "tier": case["tier"],
        "instance": case["instance"],
        "strategy": strategy_name,
        "strategy_profile": strategy_profile_name(family=case["family"], strategy=strategy_name, kind=kind),
        "model_style": model_style_from_program(None, family=case["family"]),
        "status": "error",
        "feasible": False,
        "objective": None,
        "reference_objective": _reference_objective(case),
        "reference_kind": case.get("reference", {}).get("value_kind"),
        "gap_abs": None,
        "gap_rel": None,
        "elapsed_seconds": 0.0,
        "time_to_best_seconds": None,
        "time_to_first_feasible_seconds": None,
        "dimension": case.get("size", {}).get("operations"),
        "edge_weight_type": "job_shop_interval",
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }


def _error_row(
    *,
    kind: str,
    case: dict[str, Any],
    model: JobShopBenchmarkModel,
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
        "strategy_profile": strategy_profile_name(family=case["family"], strategy=strategy_name, kind=kind),
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
        "time_to_first_feasible_seconds": None,
        "dimension": model.instance.operation_count,
        "edge_weight_type": "job_shop_interval",
        "metadata": {
            "jobs": model.instance.jobs,
            "machines": model.instance.machines,
            "horizon": model.horizon,
        },
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }


def _case_by_name(instance: str) -> JobShopCase:
    for case in CASES:
        if case.instance == instance:
            return case
    supported = ", ".join(case.instance for case in CASES)
    raise KeyError(f"unsupported SWV JSPLIB instance: {instance}; supported: {supported}")


def _coerce_budget(budget: Any) -> JobShopStrategyBudget:
    if isinstance(budget, JobShopStrategyBudget):
        return budget
    return JobShopStrategyBudget(
        seed=int(getattr(budget, "seed", DEFAULT_SEED)),
        max_iterations=int(getattr(budget, "max_iterations", DEFAULT_MAX_ITERATIONS)),
        time_limit_s=float(getattr(budget, "time_limit_s", DEFAULT_TIME_LIMIT_S)),
        population_size=int(getattr(budget, "population_size", DEFAULT_POPULATION_SIZE)),
        trace_limit=int(getattr(budget, "trace_limit", DEFAULT_TRACE_LIMIT)),
        thread_count=int(getattr(budget, "thread_count", DEFAULT_THREAD_COUNT)),
        cpsat_time_limit_s=getattr(budget, "cpsat_time_limit_s", None),
    )


def _default_strategy_names(*, include_exact: bool) -> tuple[str, ...]:
    if include_exact:
        return tuple(strategy.name for strategy in DEFAULT_STRATEGIES)
    return tuple(strategy.name for strategy in DEFAULT_STRATEGIES if strategy.kind != "exact_baseline")


def _operation_key(operation: JobShopOperation) -> tuple[int, int]:
    return (int(operation.job), int(operation.operation))


def _reference_objective(case: dict[str, Any]) -> float | None:
    objective = case.get("reference", {}).get("objective")
    return float(objective) if objective is not None else None


def _solution_objective(
    model: JobShopBenchmarkModel,
    variable_values: dict[int, Any],
    solution_objective: float | None,
) -> float | None:
    if solution_objective is not None:
        return float(solution_objective)
    makespan = makespan_from_solution(model, variable_values)
    return float(makespan) if makespan is not None else None


def _machine_order_head(model: JobShopBenchmarkModel, variable_values: dict[int, Any]) -> dict[str, list[list[int]]]:
    orders = machine_order_from_solution(model, variable_values)
    return {
        str(machine): [[job, operation] for job, operation in order[:10]]
        for machine, order in sorted(orders.items())
    }


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
