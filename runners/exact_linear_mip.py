from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from benchmarks.runners.bootstrap import prefer_local_development_paths

prefer_local_development_paths()

from optagent import MilpConfig, solve_milp

from benchmarks.loaders.exact_linear_mip import load_miplib_case
from benchmarks.models.exact_linear_mip import MipBenchmarkModel, build_mip_model
from benchmarks.runners.common import objective_gap


@dataclass(frozen=True)
class MipExactBudget:
    seed: int = 11
    max_iterations: int = 0
    time_limit_s: float = 5.0
    population_size: int = 0
    trace_limit: int = 0
    backend: str = "optx"


def run_mip_case(
    case: dict[str, Any],
    *,
    strategies: tuple[str, ...] = (),
    budget: MipExactBudget = MipExactBudget(),
    data_cache_dir: str | None = None,
    allow_download: bool = True,
) -> list[dict[str, Any]]:
    del strategies
    load_kwargs: dict[str, Any] = {"allow_download": allow_download}
    if data_cache_dir is not None:
        load_kwargs["cache_dir"] = data_cache_dir
    try:
        instance = load_miplib_case(case, **load_kwargs)
        model = build_mip_model(case, instance)
    except Exception as exc:
        return [_case_setup_error_row(case=case, exc=exc)]
    return [_run_exact(case=case, model=model, budget=budget)]


def _run_exact(
    *,
    case: dict[str, Any],
    model: MipBenchmarkModel,
    budget: MipExactBudget,
) -> dict[str, Any]:
    started = perf_counter()
    try:
        solution = solve_milp(
            model.program,
            config=MilpConfig(
                backend=budget.backend,
                time_limit_s=budget.time_limit_s,
                threads=1,
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
            "strategy_config": {
                "backend": budget.backend,
                "time_limit_s": budget.time_limit_s,
                "threads": 1,
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
            "metadata": _exact_metadata(solution.metadata, model),
        }
    except Exception as exc:
        elapsed_seconds = perf_counter() - started
        return _error_row(case=case, model=model, exc=exc, elapsed_seconds=elapsed_seconds)


def _case_setup_error_row(*, case: dict[str, Any], exc: Exception) -> dict[str, Any]:
    return {
        "kind": "exact_baseline",
        "benchmark_id": case["benchmark_id"],
        "family": case["family"],
        "tier": case["tier"],
        "instance": case["instance"],
        "strategy": "optx",
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
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }


def _error_row(
    *,
    case: dict[str, Any],
    model: MipBenchmarkModel,
    exc: Exception,
    elapsed_seconds: float,
) -> dict[str, Any]:
    return {
        "kind": "exact_baseline",
        "benchmark_id": case["benchmark_id"],
        "family": case["family"],
        "tier": case["tier"],
        "instance": case["instance"],
        "strategy": "optx",
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
            "variables": model.instance.variable_count,
            "constraints": model.instance.constraint_count,
            "nonzeros": model.instance.nonzero_count,
        },
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }


def _reference_objective(case: dict[str, Any]) -> float | None:
    objective = case.get("reference", {}).get("objective")
    return float(objective) if objective is not None else None


def _exact_metadata(metadata: dict[str, Any], model: MipBenchmarkModel) -> dict[str, Any]:
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
        **{key: metadata[key] for key in keys if key in metadata},
        "variables": model.instance.variable_count,
        "binary_variables": model.instance.binary_count,
        "integer_variables": model.instance.integer_count,
        "continuous_variables": model.instance.continuous_count,
        "constraints": model.instance.constraint_count,
        "nonzeros": model.instance.nonzero_count,
    }
