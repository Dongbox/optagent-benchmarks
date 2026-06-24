from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from benchmarks.runners.bootstrap import prefer_local_development_paths

prefer_local_development_paths()

from optagent import MilpConfig, ModelBuilder, solve_milp

from benchmarks.cases.base import BenchmarkCase, StrategyDeclaration
from benchmarks.cases.common import model_style_from_program, objective_gap, strategy_profile_name
from benchmarks.cases.miplib2017.exact.linear_mip.raw.data import MpsLinearConstraint, ParsedMpsInstance, load_miplib_case

CASE_MODULE = __name__
SOURCE = "MIPLIB 2017 benchmark-v2"
SOURCE_KEY = "miplib2017"
PROBLEM_TYPE = "exact"
INSTANCE_TYPE = "linear_mip"
FAMILY = "exact_linear_mip"
MODEL_STYLE = "mps_linear_mp"
RAW_DIR = Path(__file__).resolve().parent / "raw"

DEFAULT_SEED = 11
DEFAULT_TIME_LIMIT_S = 5.0
DEFAULT_THREAD_COUNT = 1

MIP_OPTX = StrategyDeclaration("optx", "MilpConfig", "optx_mip_exact_v1", kind="exact_baseline", config={"backend": "optx", "time_limit_s": DEFAULT_TIME_LIMIT_S, "threads": DEFAULT_THREAD_COUNT})
DEFAULT_STRATEGIES = (MIP_OPTX,)


@dataclass(frozen=True)
class MipExactBudget:
    seed: int = DEFAULT_SEED
    max_iterations: int = 0
    time_limit_s: float = DEFAULT_TIME_LIMIT_S
    population_size: int = 0
    trace_limit: int = 0
    thread_count: int = DEFAULT_THREAD_COUNT
    backend: str = "optx"


class MipCase(BenchmarkCase):
    def load_instance(self, **kwargs: Any) -> ParsedMpsInstance:
        return load_instance(self.instance, **kwargs)

    def build_model(self, instance_data: Any | None = None, **kwargs: Any) -> "MipBenchmarkModel":
        data = instance_data if instance_data is not None else self.load_instance(**kwargs)
        return build_model(data, self.instance)


@dataclass(frozen=True)
class MipBenchmarkModel:
    program: Any
    variable_node_ids: dict[str, int]
    instance: ParsedMpsInstance


CASE_50V_10 = MipCase(
    benchmark_id='miplib2017_50v-10',
    source='MIPLIB 2017 benchmark-v2',
    problem_type=PROBLEM_TYPE,
    instance_type=INSTANCE_TYPE,
    instance='50v-10',
    family='exact_linear_mip',
    tier='smoke',
    compare_key=f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/50v-10",
    series_key=f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/50v-10/{MODEL_STYLE}",
    size={'binaries': 1464,
 'constraints': 233,
 'continuous': 366,
 'integers': 183,
 'nonzeros': 2745,
 'variables': 2013},
    data={'benchmark_list_url': 'https://miplib.zib.de/downloads/benchmark-v2.test',
 'instance_archive_url': 'https://miplib.zib.de/downloads/benchmark.zip',
 'instance_detail_url': 'https://miplib.zib.de/instance_details_50v-10.html',
 'solution_url': 'https://miplib.zib.de/downloads/miplib2017-v36.solu'},
    reference={'download_page_url': 'https://miplib.zib.de/download.html',
 'miplib_status': 'easy',
 'notes': 'Use as MP/exact-backend baseline, not as the primary GA/ALNS benchmark family.',
 'objective': 3311.1799841,
 'source_url': 'https://miplib.zib.de/downloads/miplib2017-v36.solu',
 'status': 'opt',
 'tags': ['benchmark', 'decomposition', 'benchmark_suitable', 'mixed_binary', 'general_linear'],
 'value_kind': 'optimal'},
    problem_description='MIPLIB 2017 benchmark instance 50v-10: linear mixed-integer program with 2013 variables, 233 constraints, and tags [benchmark, decomposition, benchmark_suitable, mixed_binary, general_linear]. It is included as an exact MP/MPS backend benchmark rather than a primary GA/ALNS search case.',
    case_module=CASE_MODULE,
    modeling_notes={
        "model_style": MODEL_STYLE,
        "objective_sense": 'minimize',
        "public_api_primitives": tuple(['int_var', 'bool_var', 'float_var', 'linear_constraints']),
    },
    default_strategies=DEFAULT_STRATEGIES,
    extra={
        "modeling_form": 'MPS/MP rows and columns for exact backend evaluation',
        "objective_sense": 'minimize',
        "optagent_modeling": {'constraints': ['one linear constraint per MPS row using the parsed row sense and right-hand '
                 'side'],
 'data_mapping': 'Load the MPS instance through the benchmark MPS/MP loader and preserve row '
                 'sense, bounds, integrality, and objective coefficients.',
 'decision_variables': ['bool_var for binary columns',
                        'int_var for general integer columns',
                        'float_var for continuous columns'],
 'objective': "builder.minimize(parsed_linear_objective, name='mip_objective') unless the source "
              'sense states maximize',
 'solver_routes': ["solve_milp with backend='optx'",
                   "optional solve_milp with backend='mathopt_mp'"]},
        "optagent_primitives": ['int_var', 'bool_var', 'float_var', 'linear_constraints'],
        "recommended_evaluation": {'budgets_seconds': {'calibration': 300, 'full': 3600, 'smoke': 30},
 'primary_route': "solve_milp(..., backend='optx') and optional external mathopt_mp comparison",
 'strategy_candidates': ['exact_optx'],
 'target_metrics': ['optimality_match', 'time_to_optimal_or_gap', 'native_backend_status']},
    },
)

CASES = (CASE_50V_10,)

def load_instance(instance: str, *, allow_download: bool = True) -> ParsedMpsInstance:
    return load_miplib_case(_case_by_name(instance).to_row(), cache_dir=RAW_DIR, allow_download=allow_download)


def build_model(instance_data: ParsedMpsInstance, instance: str) -> MipBenchmarkModel:
    case = _case_by_name(instance)
    builder = ModelBuilder(metadata={"benchmark_id": case.benchmark_id, "family": FAMILY, "model_style": MODEL_STYLE, "source": "MIPLIB 2017", "variables": instance_data.variable_count, "constraints": instance_data.constraint_count, "nonzeros": instance_data.nonzero_count})
    const_cache: dict[float, Any] = {}
    variable_exprs: dict[str, Any] = {}

    def const_expr(value: float) -> Any:
        normalized = float(value)
        expr = const_cache.get(normalized)
        if expr is None:
            expr = builder.const(normalized)
            const_cache[normalized] = expr
        return expr

    for name, spec in instance_data.variables.items():
        if spec.is_binary:
            expr = builder.bool_var(default=False, name=name)
        elif spec.is_integer:
            lb = _coerce_int_bound(spec.lb)
            ub = _coerce_int_bound(spec.ub)
            expr = builder.int_var(default=_default_for_integer(lb, ub), lb=lb, ub=ub, name=name)
        else:
            lb = None if spec.lb is None else float(spec.lb)
            ub = None if spec.ub is None else float(spec.ub)
            expr = builder.float_var(default=_default_for_float(lb, ub), lb=lb, ub=ub, name=name)
        variable_exprs[name] = expr

    objective_expr = _weighted_sum(builder, const_expr, variable_exprs, instance_data.objective_terms)
    if instance_data.objective_sense == "max":
        builder.maximize(objective_expr, name=instance_data.objective_row)
    else:
        builder.minimize(objective_expr, name=instance_data.objective_row)

    for row in instance_data.constraints:
        _add_constraint(builder, const_expr, variable_exprs, row)
    return MipBenchmarkModel(program=builder.freeze(), variable_node_ids={name: expr.node_id for name, expr in variable_exprs.items()}, instance=instance_data)


def _add_constraint(builder: ModelBuilder, const_expr: Any, variable_exprs: dict[str, Any], row: MpsLinearConstraint) -> None:
    lhs = _weighted_sum(builder, const_expr, variable_exprs, row.terms)
    rhs = const_expr(row.rhs)
    if row.range_value is None:
        if row.sense == "L":
            builder.constraint(lhs <= rhs, name=row.name)
            return
        if row.sense == "G":
            builder.constraint(lhs >= rhs, name=row.name)
            return
        if row.sense == "E":
            builder.constraint(lhs == rhs, name=row.name)
            return
    lb, ub = _range_bounds(row)
    if lb is not None:
        builder.constraint(lhs >= const_expr(lb), name=f"{row.name}_range_lb")
    if ub is not None:
        builder.constraint(lhs <= const_expr(ub), name=f"{row.name}_range_ub")


def _range_bounds(row: MpsLinearConstraint) -> tuple[float | None, float | None]:
    if row.range_value is None:
        raise ValueError("range_value is required")
    rhs = float(row.rhs)
    span = abs(float(row.range_value))
    if row.sense == "L":
        return rhs - span, rhs
    if row.sense == "G":
        return rhs, rhs + span
    if row.sense == "E":
        if row.range_value >= 0:
            return rhs, rhs + span
        return rhs - span, rhs
    raise ValueError(f"unsupported row sense: {row.sense}")


def _weighted_sum(builder: ModelBuilder, const_expr: Any, variables: dict[str, Any], terms: tuple[tuple[str, float], ...]) -> Any:
    if not terms:
        return const_expr(0.0)
    exprs: list[Any] = []
    for variable_name, coefficient in terms:
        variable = variables[variable_name]
        if coefficient == 1:
            exprs.append(variable)
        elif coefficient == -1:
            exprs.append(-variable)
        else:
            exprs.append(variable * const_expr(coefficient))
    if len(exprs) == 1:
        return exprs[0]
    return builder.sum(*exprs)


def _coerce_int_bound(value: float | None) -> int | None:
    if value is None:
        return None
    rounded = int(round(value))
    if abs(float(value) - rounded) > 1e-9:
        raise ValueError(f"expected integer bound, got {value}")
    return rounded


def _default_for_integer(lb: int | None, ub: int | None) -> int:
    if lb is not None and ub is not None and lb == ub:
        return lb
    if lb is not None and lb > 0:
        return lb
    if ub is not None and ub < 0:
        return ub
    return 0


def _default_for_float(lb: float | None, ub: float | None) -> float:
    if lb is not None and ub is not None and abs(lb - ub) <= 1e-12:
        return lb
    if lb is not None and lb > 0.0:
        return lb
    if ub is not None and ub < 0.0:
        return ub
    return 0.0

def solve_case(
    instance: str,
    *,
    strategies: tuple[str, ...] | None = (),
    budget: MipExactBudget = MipExactBudget(),
    allow_download: bool = True,
    **_: Any,
) -> list[dict[str, Any]]:
    case = _case_by_name(instance).to_row()
    requested_strategies = tuple(strategies or ())
    effective_budget = _coerce_budget(budget)
    load_kwargs: dict[str, Any] = {"allow_download": allow_download}
    try:
        instance_data = load_instance(instance, **load_kwargs)
        model = build_model(instance_data, instance)
    except Exception as exc:
        return [_case_setup_error_row(case=case, exc=exc, requested_strategies=requested_strategies)]
    return [_run_exact(case=case, model=model, budget=effective_budget, requested_strategies=requested_strategies)]


def _run_exact(
    *,
    case: dict[str, Any],
    model: MipBenchmarkModel,
    budget: MipExactBudget,
    requested_strategies: tuple[str, ...],
) -> dict[str, Any]:
    started = perf_counter()
    try:
        solution = solve_milp(
            model.program,
            config=MilpConfig(
                backend=budget.backend,
                time_limit_s=budget.time_limit_s,
                threads=budget.thread_count,
            ),
        )
        elapsed_seconds = perf_counter() - started
        objective = solution.objective_value if solution.feasible else None
        raw_objective = solution.objective_value
        reference = _reference_objective(case)
        gap = objective_gap(objective, reference)
        return {
            "kind": "exact_baseline",
            "benchmark_id": case["benchmark_id"],
            "family": case["family"],
            "tier": case["tier"],
            "instance": case["instance"],
            "strategy": budget.backend,
            "strategy_profile": strategy_profile_name(family=case["family"], strategy=budget.backend, kind="exact_baseline"),
            "model_style": model_style_from_program(model.program, family=case["family"]),
            "strategy_config": {
                "backend": budget.backend,
                "time_limit_s": budget.time_limit_s,
                "threads": budget.thread_count,
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
            "time_to_best_seconds": elapsed_seconds if solution.feasible else None,
            "time_to_first_feasible_seconds": elapsed_seconds if solution.feasible else None,
            "dimension": model.instance.variable_count,
            "edge_weight_type": "mps_linear_mip",
            "metadata": _exact_metadata(solution.metadata, model, requested_strategies=requested_strategies),
        }
    except Exception as exc:
        elapsed_seconds = perf_counter() - started
        return _error_row(
            case=case,
            model=model,
            exc=exc,
            elapsed_seconds=elapsed_seconds,
            requested_strategies=requested_strategies,
        )


def _case_setup_error_row(
    *,
    case: dict[str, Any],
    exc: Exception,
    requested_strategies: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "kind": "exact_baseline",
        "benchmark_id": case["benchmark_id"],
        "family": case["family"],
        "tier": case["tier"],
        "instance": case["instance"],
        "strategy": "optx",
        "strategy_profile": strategy_profile_name(family=case["family"], strategy="optx", kind="exact_baseline"),
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
        "dimension": case.get("size", {}).get("variables"),
        "edge_weight_type": "mps_linear_mip",
        "metadata": _mip_heuristic_route_metadata(requested_strategies=requested_strategies),
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }


def _error_row(
    *,
    case: dict[str, Any],
    model: MipBenchmarkModel,
    exc: Exception,
    elapsed_seconds: float,
    requested_strategies: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "kind": "exact_baseline",
        "benchmark_id": case["benchmark_id"],
        "family": case["family"],
        "tier": case["tier"],
        "instance": case["instance"],
        "strategy": "optx",
        "strategy_profile": strategy_profile_name(family=case["family"], strategy="optx", kind="exact_baseline"),
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
        "dimension": model.instance.variable_count,
        "edge_weight_type": "mps_linear_mip",
        "metadata": {
            **_mip_heuristic_route_metadata(requested_strategies=requested_strategies),
            "variables": model.instance.variable_count,
            "constraints": model.instance.constraint_count,
            "nonzeros": model.instance.nonzero_count,
        },
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }


def _reference_objective(case: dict[str, Any]) -> float | None:
    objective = case.get("reference", {}).get("objective")
    return float(objective) if objective is not None else None


def _exact_metadata(
    metadata: dict[str, Any],
    model: MipBenchmarkModel,
    *,
    requested_strategies: tuple[str, ...],
) -> dict[str, Any]:
    keys = (
        "backend",
        "solver_status",
        "status",
        "objective_value",
        "best_bound",
        "mip_gap",
        "simplex_iteration_count",
        "node_count",
        "constraint_violation_policy",
        "max_constraint_violation",
    )
    return {
        **_mip_heuristic_route_metadata(requested_strategies=requested_strategies),
        **{key: metadata[key] for key in keys if key in metadata},
        "variables": model.instance.variable_count,
        "binary_variables": model.instance.binary_count,
        "integer_variables": model.instance.integer_count,
        "continuous_variables": model.instance.continuous_count,
        "constraints": model.instance.constraint_count,
        "nonzeros": model.instance.nonzero_count,
    }


def _mip_heuristic_route_metadata(*, requested_strategies: tuple[str, ...]) -> dict[str, Any]:
    return {
        "mip_heuristic_route_enabled": False,
        "mip_heuristic_route_decision": "exact_only",
        "mip_heuristic_route_reason": "no_dedicated_milp_native_heuristic",
        "exact_baseline_required": True,
        "requested_strategies": list(requested_strategies),
        "ignored_requested_strategies": list(requested_strategies),
    }



def _coerce_budget(budget: Any) -> MipExactBudget:
    if isinstance(budget, MipExactBudget):
        return budget
    return MipExactBudget(
        seed=int(getattr(budget, "seed", DEFAULT_SEED)),
        max_iterations=int(getattr(budget, "max_iterations", 0)),
        time_limit_s=float(getattr(budget, "time_limit_s", DEFAULT_TIME_LIMIT_S)),
        population_size=int(getattr(budget, "population_size", 0)),
        trace_limit=int(getattr(budget, "trace_limit", 0)),
        thread_count=int(getattr(budget, "thread_count", DEFAULT_THREAD_COUNT)),
        backend=str(getattr(budget, "backend", "optx")),
    )


def _case_by_name(instance: str) -> MipCase:
    for case in CASES:
        if case.instance == instance:
            return case
    supported = ", ".join(case.instance for case in CASES)
    raise KeyError(f"unsupported MIPLIB linear MIP instance: {instance}; supported: {supported}")
