from __future__ import annotations

from typing import Any


# 这里放 case 求解入口共享的“问题语义”工具：
# - model_style 是 family row 的语义命名；
# - objective_gap 是 case 结果与公开 reference 的比较方式；
# - summarize_solution_metadata 是 case row 从公开 solution metadata 提取诊断字段。
# runner 侧只负责运行计划、预算、输出和汇总，不再作为 case solve 的工具库。

MODEL_STYLE_BY_FAMILY = {
    "capacitated_vehicle_routing_fixed_fleet": "binary_arc_single_commodity_flow",
    "capacitated_vehicle_routing_variable_fleet": "binary_arc_variable_fleet_single_commodity_flow",
    "cumulative_resource_scheduling": "interval_var_cumulative_precedence",
    "exact_linear_mip": "mps_linear_mp",
    "interval_job_shop": "interval_var_sequence_no_overlap_precedence",
    "flexible_interval_job_shop": "optional_interval_machine_choice_no_overlap_precedence",
    "sequence_blackbox_tsp": "sequence_var_external_call",
    "sequence_quadratic_assignment": "sequence_var_external_call",
    "sequence_transition_penalty": "sequence_var_external_transition_penalty",
    "sequence_weighted_tardiness_scheduling": "interval_var_sequence_setup_weighted_tardiness",
}


def objective_gap(objective: float | int | None, reference: float | int | None) -> dict[str, float | None]:
    if objective is None or reference is None:
        return {"gap_abs": None, "gap_rel": None}
    gap_abs = float(objective) - float(reference)
    denominator = abs(float(reference))
    return {
        "gap_abs": gap_abs,
        "gap_rel": gap_abs / denominator if denominator else None,
    }


def model_style_from_program(program: Any, *, family: str | None = None) -> str | None:
    metadata = getattr(program, "metadata", None)
    if isinstance(metadata, dict):
        model_style = metadata.get("model_style")
        if model_style is not None:
            return str(model_style)
    if family is not None:
        return MODEL_STYLE_BY_FAMILY.get(family)
    return None


def summarize_solution_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "strategy",
        "strategy_source",
        "termination_reason",
        "iterations",
        "attempted_moves",
        "accepted_moves",
        "improved_moves",
        "rejected_moves",
        "trace",
        "trace_entry_count",
        "domain_best_sequence_penalty",
        "domain_sequence_graph_provenance",
        "domain_sequence_graph_objective_ids_json",
        "domain_sequence_legacy_metadata_hint_available",
        "domain_sequence_legacy_metadata_hint_enabled",
        "domain_sequence_lower_bound_certified",
        "ga_generation_count",
        "ga_mutation_portfolio",
        "ga_offspring_generated",
        "ga_offspring_evaluated",
        "ga_duplicate_child_count",
        "ga_tabu_improvement_count",
        "ga_repair_application_count",
        "ga_scheduling_repair_count",
        "ga_scheduling_repair_success_count",
        "ga_infeasible_offspring_count",
        "ga_first_feasible_generation",
        "lns_applications",
        "alns_iterations",
        "alns_candidates_evaluated",
        "alns_candidates_accepted",
        "alns_repair_applications",
        "alns_repair_failures",
        "alns_acceptance_model",
        "external_batch_count",
        "external_rows_requested",
        "external_cache_hits",
        "external_cache_misses",
        "external_duplicate_rows_coalesced",
        "ga_external_candidate_set_count",
        "ga_external_candidate_set_rows",
        "ga_external_candidate_set_cache_hits",
        "ga_external_candidate_set_unique_miss_rows",
        "ga_external_candidate_set_coalesced_rows",
        "ga_external_candidate_set_batch_calls",
        "ga_external_candidate_set_fallback_count",
        "ga_external_candidate_set_fallback_reason",
        "ga_external_candidate_set_wall_time_ms",
        "construct_candidates_evaluated",
        "construct_candidates_accepted",
        "construct_best_improvements",
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
        "domain_qap_supported",
        "domain_qap_move_count",
        "budget",
        "budget_profile",
        "effective_budget",
        "seed",
    )
    return {key: metadata[key] for key in keys if key in metadata}
