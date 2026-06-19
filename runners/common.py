from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_ROOT = REPO_ROOT / "docs" / "evals" / "benchmark-suite" / "runs"

MODEL_STYLE_BY_FAMILY = {
    "cumulative_resource_scheduling": "interval_var_cumulative_precedence",
    "exact_linear_mip": "mps_linear_mp",
    "interval_job_shop": "interval_var_sequence_no_overlap_precedence",
    "sequence_blackbox_tsp": "sequence_var_external_call",
    "sequence_quadratic_assignment": "sequence_var_external_call",
}

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
)


@dataclass(frozen=True)
class StrategyBudgetRequest:
    seed: int = 11
    max_iterations: int = 40
    time_limit_s: float = 5.0
    population_size: int = 10
    trace_limit: int = 8


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


def objective_gap(objective: float | int | None, reference: float | int | None) -> dict[str, float | None]:
    if objective is None or reference is None:
        return {"gap_abs": None, "gap_rel": None}
    gap_abs = float(objective) - float(reference)
    denominator = abs(float(reference))
    return {
        "gap_abs": gap_abs,
        "gap_rel": gap_abs / denominator if denominator else None,
    }


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
        exact_time_limit_s=exact_time_limit_s,
    )


def model_style_from_program(program: Any, *, family: str | None = None) -> str | None:
    metadata = getattr(program, "metadata", None)
    if isinstance(metadata, dict):
        model_style = metadata.get("model_style")
        if model_style is not None:
            return str(model_style)
    if family is not None:
        return MODEL_STYLE_BY_FAMILY.get(family)
    return None


def strategy_profile_name(
    *,
    family: str,
    strategy: str,
    model_style: str | None = None,
    kind: str | None = None,
) -> str:
    if kind == "exact_baseline":
        if strategy == "cpsat":
            return "cpsat_scheduling_exact_v1"
        if strategy in {"optx", "mathopt_mp"}:
            return f"{strategy}_mip_exact_v1"
        return f"{strategy}_exact_baseline_v1"
    if family in {"interval_job_shop", "cumulative_resource_scheduling"}:
        if strategy == "ga":
            return "ga_scheduling_feasibility_v1"
        if strategy == "alns":
            return "alns_scheduling_repair_v1"
        if strategy == "lns":
            return "lns_scheduling_repair_v1"
        return f"{strategy}_scheduling_smoke_v1"
    if family == "sequence_blackbox_tsp":
        if model_style == "sequence_var_sequence_transition_sum":
            return f"{strategy}_tsp_graph_v1"
        return f"{strategy}_tsp_blackbox_v1"
    if family == "sequence_quadratic_assignment":
        return f"{strategy}_qap_delta_v1"
    if family == "exact_linear_mip":
        return f"{strategy}_mip_exact_v1"
    return f"{strategy}_{family}_v1"


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
    return row


def summarize_solution_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "strategy",
        "strategy_source",
        "termination_reason",
        "iterations",
        "attempted_moves",
        "accepted_moves",
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
        "domain_qap_supported",
        "domain_qap_move_count",
        "budget",
        "budget_profile",
        "effective_budget",
        "seed",
    )
    return {key: metadata[key] for key in keys if key in metadata}


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
