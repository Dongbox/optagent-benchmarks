from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from benchmarks.cases.common import (
    MODEL_STYLE_BY_FAMILY,
    model_style_from_program,
    objective_gap,
    strategy_profile_name,
    summarize_solution_metadata,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_ROOT = REPO_ROOT / "docs" / "evals" / "benchmark-suite" / "runs"

SEARCH_DIAGNOSTIC_KEYS = (
    "construct_candidates_evaluated",
    "construct_candidates_accepted",
    "construct_best_improvements",
    "ga_scheduling_repair_count",
    "ga_scheduling_repair_success_count",
    "ga_infeasible_offspring_count",
    "ga_first_feasible_generation",
    "ga_repair_application_count",
    "lns_applications",
    "alns_repair_applications",
    "alns_repair_failures",
    "sequence_graph_delta_count",
    "full_root_eval_delta_count",
    "tsp_two_opt_moves_evaluated",
    "tsp_two_opt_improvements",
    "tsp_repair_insertions",
    "tsp_preserved_edge_ratio",
    "qap_swap_delta_count",
    "qap_swap_improvement_count",
    "qap_repair_assignment_count",
    "qap_common_assignment_preservation_ratio",
    "thread_count",
    "parallel_matrix_enabled",
    "ga_parallel_worker_count",
    "ga_parallel_batches",
    "ga_parallel_candidates_evaluated",
    "ga_offspring_generated",
    "ga_offspring_evaluated",
    "ga_duplicate_child_count",
    "ga_offspring_attempt_count",
    "ga_unique_offspring_count",
    "ga_duplicate_offspring_count",
    "ga_duplicate_fallback_generation_count",
    "ga_unique_offspring_retry_count",
    "ga_unique_offspring_retry_limit",
    "ga_duplicate_ratio",
    "ga_generation_duplicate_ratio_mean",
    "ga_generation_duplicate_ratio_max",
    "ga_generation_unique_offspring_mean",
    "ga_candidate_move_pool_hit_count",
    "ga_candidate_move_pool_miss_count",
    "ga_candidate_move_pool_rebuild_count",
    "ga_candidate_move_pool_skeleton_size",
    "ga_child_draft_batch_count",
    "ga_child_draft_count",
    "ga_mutation_draft_count",
    "ga_crossover_draft_count",
    "ga_full_snapshot_draft_count",
    "ga_child_draft_materialized_count",
    "ga_child_draft_accepted_count",
    "ga_generation_worker_count_effective",
    "ga_generation_worker_batches",
    "ga_generation_worker_draft_attempts",
    "ga_external_evaluation_mode",
    "ga_external_batch_count",
    "ga_external_batch_rows",
    "ga_external_parallel_batches",
    "ga_external_callback_wall_time_ms",
    "ga_external_candidate_set_count",
    "ga_external_candidate_set_rows",
    "ga_external_candidate_set_cache_hits",
    "ga_external_candidate_set_unique_miss_rows",
    "ga_external_candidate_set_coalesced_rows",
    "ga_external_candidate_set_batch_calls",
    "ga_external_candidate_set_fallback_count",
    "ga_external_candidate_set_fallback_reason",
    "ga_external_candidate_set_wall_time_ms",
    "external_batch_count",
    "external_rows_requested",
    "external_cache_hits",
    "external_cache_misses",
    "external_duplicate_rows_coalesced",
)


@dataclass(frozen=True)
class StrategyBudgetRequest:
    seed: int = 11
    max_iterations: int = 40
    time_limit_s: float = 5.0
    population_size: int = 10
    trace_limit: int = 8
    thread_count: int = 1


@dataclass(frozen=True)
class EffectiveStrategyBudget:
    family: str
    tier: str
    profile: str
    seed: int
    max_iterations: int
    time_limit_s: float
    population_size: int
    trace_limit: int
    thread_count: int = 1
    exact_time_limit_s: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


TIER_BUDGET_DEFAULTS: dict[str, dict[str, Any]] = {
    "smoke": {
        "max_iterations": 5,
        "time_limit_s": 2.0,
        "population_size": 8,
        "trace_limit": 4,
    },
    "calibration": {
        "max_iterations": 20,
        "time_limit_s": 5.0,
        "population_size": 16,
        "trace_limit": 8,
    },
    "full": {
        "max_iterations": 50,
        "time_limit_s": 10.0,
        "population_size": 32,
        "trace_limit": 8,
    },
}

FAMILY_TIER_BUDGET_OVERRIDES: dict[tuple[str, str], dict[str, Any]] = {
    ("exact_linear_mip", "smoke"): {
        "max_iterations": 0,
        "time_limit_s": 10.0,
        "population_size": 0,
        "trace_limit": 0,
        "exact_time_limit_s": 10.0,
    },
    ("exact_linear_mip", "calibration"): {
        "max_iterations": 0,
        "time_limit_s": 20.0,
        "population_size": 0,
        "trace_limit": 0,
        "exact_time_limit_s": 20.0,
    },
    ("exact_linear_mip", "full"): {
        "max_iterations": 0,
        "time_limit_s": 30.0,
        "population_size": 0,
        "trace_limit": 0,
        "exact_time_limit_s": 30.0,
    },
}

DISPLAY_EDGE_TYPE_BY_FAMILY = {
    "cumulative_resource_scheduling": "rcpsp_cumulative",
    "exact_linear_mip": "mps_linear_mip",
    "interval_job_shop": "job_shop_interval",
    "sequence_blackbox_tsp": "tsp_route",
    "sequence_quadratic_assignment": "qap_quadratic",
    "sequence_transition_penalty": "transition_penalty",
}


def utc_timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")


def ensure_run_dir(output_root: str | Path = DEFAULT_RUN_ROOT, *, timestamp: str | None = None) -> Path:
    run_dir = Path(output_root) / (timestamp or utc_timestamp())
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def write_json(path: str | Path, payload: Any) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    with Path(path).open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def resolve_family_tier_budget(
    *,
    family: str,
    tier: str,
    request: StrategyBudgetRequest,
) -> EffectiveStrategyBudget:
    defaults = {
        **TIER_BUDGET_DEFAULTS.get(tier, TIER_BUDGET_DEFAULTS["smoke"]),
        **FAMILY_TIER_BUDGET_OVERRIDES.get((family, tier), {}),
    }
    requested_max_iterations = max(0, int(request.max_iterations))
    default_max_iterations = max(0, int(defaults["max_iterations"]))
    requested_population = max(0, int(request.population_size))
    default_population = max(0, int(defaults["population_size"]))
    requested_trace = max(0, int(request.trace_limit))
    default_trace = max(0, int(defaults["trace_limit"]))
    requested_time = max(0.0, float(request.time_limit_s))
    default_time = max(0.0, float(defaults["time_limit_s"]))
    requested_thread_count = max(1, int(request.thread_count))
    exact_default = defaults.get("exact_time_limit_s")
    exact_time_limit_s = (
        min(requested_time, max(0.0, float(exact_default)))
        if exact_default is not None
        else None
    )
    return EffectiveStrategyBudget(
        family=family,
        tier=tier,
        profile=f"{family}_{tier}_budget_v1",
        seed=int(request.seed),
        max_iterations=min(requested_max_iterations, default_max_iterations),
        time_limit_s=min(requested_time, default_time),
        population_size=min(requested_population, default_population),
        trace_limit=min(requested_trace, default_trace),
        thread_count=requested_thread_count,
        exact_time_limit_s=exact_time_limit_s,
    )


def normalize_result_row(row: dict[str, Any]) -> dict[str, Any]:
    family = str(row.get("family") or "")
    strategy = str(row.get("strategy") or "")
    model_style = row.get("model_style")
    if model_style is None:
        model_style = MODEL_STYLE_BY_FAMILY.get(family)
    if model_style is not None:
        row["model_style"] = str(model_style)
    row.setdefault(
        "strategy_profile",
        strategy_profile_name(
            family=family,
            strategy=strategy,
            model_style=row.get("model_style"),
            kind=str(row.get("kind")) if row.get("kind") is not None else None,
        ),
    )
    metadata = row.get("metadata")
    if isinstance(metadata, dict):
        for key in SEARCH_DIAGNOSTIC_KEYS:
            if key in metadata:
                row.setdefault(key, metadata[key])
        if "budget_profile" in row:
            metadata.setdefault("budget_profile", row["budget_profile"])
    _derive_presentation_fields(row)
    return row


def _derive_presentation_fields(row: dict[str, Any]) -> None:
    family = str(row.get("family") or "")
    decoded = row.get("decoded_solution")
    if isinstance(decoded, dict):
        edge_weight_type = decoded.get("edge_weight_type")
        if edge_weight_type is not None:
            row.setdefault("edge_weight_type", str(edge_weight_type))
        sequence = decoded.get("sequence")
        if isinstance(sequence, list):
            row.setdefault("sequence_head", sequence[:20])
            row.setdefault("dimension", len(sequence))
        machine_orders = decoded.get("machine_orders")
        if isinstance(machine_orders, dict):
            row.setdefault(
                "machine_order_head",
                {
                    str(machine): order[:10]
                    for machine, order in sorted(machine_orders.items(), key=lambda item: str(item[0]))
                    if isinstance(order, list)
                },
            )
            machine_order_dimension = _machine_order_dimension(machine_orders)
            if machine_order_dimension is not None:
                row.setdefault("dimension", machine_order_dimension)
        activity_starts = decoded.get("activity_starts")
        if isinstance(activity_starts, list):
            row.setdefault("activity_start_head", activity_starts[:20])
            row.setdefault("dimension", len(activity_starts))
    case_size_dimension = _dimension_from_case_size(row.get("case_size"))
    if case_size_dimension is not None:
        row.setdefault("dimension", case_size_dimension)
    if "edge_weight_type" not in row and family in DISPLAY_EDGE_TYPE_BY_FAMILY:
        row["edge_weight_type"] = DISPLAY_EDGE_TYPE_BY_FAMILY[family]


def _machine_order_dimension(machine_orders: dict[Any, Any]) -> int | None:
    counts = [len(order) for order in machine_orders.values() if isinstance(order, list)]
    return sum(counts) if counts else None


def _dimension_from_case_size(case_size: Any) -> int | None:
    if not isinstance(case_size, dict):
        return None
    for key in ("nodes", "facilities", "activities", "operations", "variables", "coils", "locations"):
        value = case_size.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def metadata_highlights(metadata: dict[str, Any]) -> list[str]:
    highlights = []
    for key in (
        "iterations",
        "ga_generation_count",
        "alns_iterations",
        "construct_candidates_evaluated",
        "construct_best_improvements",
        "ga_scheduling_repair_count",
        "ga_scheduling_repair_success_count",
        "ga_infeasible_offspring_count",
        "ga_first_feasible_generation",
        "ga_repair_application_count",
        "lns_applications",
        "alns_repair_applications",
        "alns_repair_failures",
        "domain_sequence_graph_provenance",
        "sequence_graph_delta_count",
        "full_root_eval_delta_count",
        "tsp_two_opt_moves_evaluated",
        "tsp_two_opt_improvements",
        "tsp_repair_insertions",
        "tsp_preserved_edge_ratio",
        "qap_swap_delta_count",
        "qap_swap_improvement_count",
        "qap_repair_assignment_count",
        "qap_common_assignment_preservation_ratio",
        "thread_count",
        "parallel_matrix_enabled",
        "ga_parallel_worker_count",
        "ga_parallel_batches",
        "ga_parallel_candidates_evaluated",
        "ga_candidate_move_pool_hit_count",
        "ga_candidate_move_pool_miss_count",
        "ga_candidate_move_pool_rebuild_count",
        "ga_candidate_move_pool_skeleton_size",
        "ga_child_draft_batch_count",
        "ga_child_draft_count",
        "ga_mutation_draft_count",
        "ga_crossover_draft_count",
        "ga_full_snapshot_draft_count",
        "ga_child_draft_materialized_count",
        "ga_child_draft_accepted_count",
        "ga_generation_worker_count_effective",
        "ga_generation_worker_batches",
        "ga_generation_worker_draft_attempts",
        "ga_external_candidate_set_count",
        "ga_external_candidate_set_rows",
        "ga_external_candidate_set_cache_hits",
        "ga_external_candidate_set_unique_miss_rows",
        "ga_external_candidate_set_coalesced_rows",
        "ga_external_candidate_set_batch_calls",
        "ga_external_candidate_set_fallback_count",
        "ga_external_candidate_set_fallback_reason",
        "ga_external_candidate_set_wall_time_ms",
        "domain_qap_supported",
        "domain_qap_move_count",
        "external_rows_requested",
        "external_cache_hits",
        "external_cache_misses",
        "budget_profile",
        "backend_status_name",
        "best_objective_bound",
        "wall_time_seconds",
    ):
        if key in metadata:
            highlights.append(f"{key}={metadata[key]}")
    return highlights
