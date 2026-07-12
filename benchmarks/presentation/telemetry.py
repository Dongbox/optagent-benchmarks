from __future__ import annotations

from pathlib import Path
from typing import Any

from benchmarks.presentation.common import append_jsonl


BENCHMARK_SCHEMA_VERSION = 2
ANYTIME_CHECKPOINT_SECONDS = (1, 5, 10, 30, 60, 300)


def normalize_telemetry(row: dict[str, Any]) -> dict[str, Any]:
    """Add benchmark schema v2 observability fields to one result row."""

    row["benchmark_schema_version"] = BENCHMARK_SCHEMA_VERSION
    elapsed_seconds = _optional_float(row.get("elapsed_seconds"))
    if elapsed_seconds is not None:
        row["runtime_s"] = elapsed_seconds
    row["best_cost"] = _best_cost(row)
    row["reference_cost"] = _optional_float(row.get("reference_objective"))

    metadata = row.get("metadata")
    if isinstance(metadata, dict):
        termination_reason = metadata.get("termination_reason")
        if termination_reason is not None:
            row.setdefault("termination_reason", str(termination_reason))

    if row.get("kind") == "strategy_run":
        initial_cost = _initial_cost(row, metadata if isinstance(metadata, dict) else {})
        if initial_cost is not None:
            row["initial_cost"] = initial_cost
        _normalize_search_counters(row, metadata if isinstance(metadata, dict) else {})
        _normalize_ga_observability(row, metadata if isinstance(metadata, dict) else {})
        _normalize_external_observability(row, metadata if isinstance(metadata, dict) else {})
        _normalize_counter_rates(row, elapsed_seconds)
        _normalize_improvement_metrics(row, elapsed_seconds)

    row["anytime"] = _build_anytime(row, metadata if isinstance(metadata, dict) else {})
    row["curve_summary"] = _curve_summary(row["anytime"])
    return row


def write_anytime_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    entries: list[dict[str, Any]] = []
    for row in rows:
        anytime = row.get("anytime")
        if not isinstance(anytime, list):
            continue
        entries.append(
            {
                "benchmark_schema_version": row.get("benchmark_schema_version"),
                "benchmark_id": row.get("benchmark_id"),
                "family": row.get("family"),
                "tier": row.get("tier"),
                "strategy": row.get("strategy"),
                "strategy_profile": row.get("strategy_profile"),
                "model_style": row.get("model_style"),
                "kind": row.get("kind"),
                "budget_profile": row.get("budget_profile"),
                "curve_summary": row.get("curve_summary"),
                "anytime": anytime,
            }
        )
    append_jsonl(path, entries)


def write_throughput_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    entries: list[dict[str, Any]] = []
    for row in rows:
        entry = _throughput_entry(row)
        if entry is not None:
            entries.append(entry)
    append_jsonl(path, entries)


def _throughput_entry(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("kind") != "strategy_run":
        return None
    throughput_fields = (
        "moves_attempted",
        "moves_accepted",
        "moves_improved",
        "evaluations",
        "delta_evaluations",
        "full_evaluations",
        "repairs_attempted",
        "repairs_succeeded",
        "moves_attempted_per_s",
        "moves_accepted_per_s",
        "evaluations_per_s",
        "delta_evaluations_per_s",
        "full_evaluations_per_s",
        "repairs_attempted_per_s",
        "repairs_succeeded_per_s",
        "ga_offspring_generated",
        "ga_offspring_evaluated",
        "ga_duplicate_child_count",
        "ga_offspring_attempt_count",
        "ga_duplicate_offspring_count",
        "ga_duplicate_ratio",
        "ga_unique_offspring_count",
        "ga_duplicate_fallback_generation_count",
        "ga_unique_offspring_retry_count",
        "ga_unique_offspring_retry_limit",
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
        "external_rows_requested",
        "external_cache_hits",
        "external_cache_misses",
        "external_duplicate_rows_coalesced",
        "external_callback_wall_time_ms",
    )
    values = {field: row.get(field) for field in throughput_fields if row.get(field) is not None}
    if not values:
        return None
    return {
        "benchmark_schema_version": row.get("benchmark_schema_version"),
        "benchmark_id": row.get("benchmark_id"),
        "family": row.get("family"),
        "tier": row.get("tier"),
        "strategy": row.get("strategy"),
        "strategy_profile": row.get("strategy_profile"),
        "model_style": row.get("model_style"),
        "kind": row.get("kind"),
        "budget_profile": row.get("budget_profile"),
        "runtime_s": row.get("runtime_s"),
        **values,
    }


def _normalize_search_counters(row: dict[str, Any], metadata: dict[str, Any]) -> None:
    moves_attempted = _first_number(row, metadata, ("moves_attempted", "attempted_moves", "move_count"))
    moves_accepted = _first_number(row, metadata, ("moves_accepted", "accepted_moves", "accepted_move_count"))
    moves_improved = _first_number(row, metadata, ("moves_improved", "improved_moves"))
    delta_evaluations = _sum_numbers(
        row,
        metadata,
        (
            "sequence_graph_delta_count",
            "qap_swap_delta_count",
        ),
    )
    full_evaluations = _first_number(row, metadata, ("full_evaluations", "full_root_eval_delta_count"))
    evaluations = _sum_numbers(
        row,
        metadata,
        (
            "ga_offspring_evaluated",
            "alns_candidates_evaluated",
            "construct_candidates_evaluated",
            "loop_candidates_evaluated",
            "sequence_graph_delta_count",
            "qap_swap_delta_count",
            "full_root_eval_delta_count",
        ),
    )
    repairs_attempted = _sum_numbers(
        row,
        metadata,
        (
            "ga_scheduling_repair_count",
            "alns_repair_applications",
            "qap_repair_assignment_count",
        ),
    )
    repairs_succeeded = _sum_numbers(
        row,
        metadata,
        (
            "ga_scheduling_repair_success_count",
            "alns_repair_applications",
            "qap_repair_assignment_count",
        ),
    )
    for key, value in (
        ("moves_attempted", moves_attempted),
        ("moves_accepted", moves_accepted),
        ("moves_improved", moves_improved),
        ("evaluations", evaluations),
        ("delta_evaluations", delta_evaluations),
        ("full_evaluations", full_evaluations),
        ("repairs_attempted", repairs_attempted),
        ("repairs_succeeded", repairs_succeeded),
    ):
        if value is not None:
            row[key] = value


def _normalize_ga_observability(row: dict[str, Any], metadata: dict[str, Any]) -> None:
    for key in (
        "ga_offspring_generated",
        "ga_offspring_evaluated",
        "ga_duplicate_child_count",
        "ga_offspring_attempt_count",
        "ga_unique_offspring_count",
        "ga_duplicate_offspring_count",
        "ga_duplicate_fallback_generation_count",
        "ga_unique_offspring_retry_count",
        "ga_unique_offspring_retry_limit",
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
        "ga_external_candidate_set_wall_time_ms",
    ):
        value = _first_number(row, metadata, (key,))
        if value is not None:
            row[key] = value
    mode = row.get("ga_external_evaluation_mode") or metadata.get("ga_external_evaluation_mode")
    if mode is not None:
        row["ga_external_evaluation_mode"] = str(mode)
    candidate_set_fallback = (
        row.get("ga_external_candidate_set_fallback_reason")
        or metadata.get("ga_external_candidate_set_fallback_reason")
    )
    if candidate_set_fallback is not None:
        row["ga_external_candidate_set_fallback_reason"] = str(candidate_set_fallback)
    attempts = _optional_float(row.get("ga_offspring_attempt_count"))
    generated = _optional_float(row.get("ga_offspring_generated"))
    duplicate_offspring = _optional_float(row.get("ga_duplicate_offspring_count"))
    legacy_duplicate = _optional_float(row.get("ga_duplicate_child_count"))
    if row.get("ga_unique_offspring_count") is None:
        denominator = attempts if attempts is not None else generated
        duplicate = duplicate_offspring if duplicate_offspring is not None else legacy_duplicate
        if denominator is not None and duplicate is not None:
            row["ga_unique_offspring_count"] = max(0.0, denominator - duplicate)
    explicit_ratio = _first_number(row, metadata, ("ga_duplicate_ratio",))
    if explicit_ratio is not None:
        row["ga_duplicate_ratio"] = explicit_ratio
    elif attempts and duplicate_offspring is not None:
        row["ga_duplicate_ratio"] = duplicate_offspring / attempts
    elif generated and legacy_duplicate is not None:
        row["ga_duplicate_ratio"] = legacy_duplicate / generated


def _normalize_external_observability(row: dict[str, Any], metadata: dict[str, Any]) -> None:
    for key in (
        "external_batch_count",
        "external_rows_requested",
        "external_cache_hits",
        "external_cache_misses",
        "external_duplicate_rows_coalesced",
        "external_callback_wall_time_ms",
    ):
        value = _first_number(row, metadata, (key,))
        if value is not None:
            row[key] = value
    mode = row.get("external_evaluation_mode") or metadata.get("external_evaluation_mode")
    if mode is None and any(key in row for key in ("external_rows_requested", "external_batch_count")):
        mode = "serial_external"
    if mode is not None:
        row["external_evaluation_mode"] = str(mode)


def _normalize_counter_rates(row: dict[str, Any], elapsed_seconds: float | None) -> None:
    if elapsed_seconds is None or elapsed_seconds <= 0:
        return
    for counter_key, rate_key in (
        ("moves_attempted", "moves_attempted_per_s"),
        ("moves_accepted", "moves_accepted_per_s"),
        ("evaluations", "evaluations_per_s"),
        ("delta_evaluations", "delta_evaluations_per_s"),
        ("full_evaluations", "full_evaluations_per_s"),
        ("repairs_attempted", "repairs_attempted_per_s"),
        ("repairs_succeeded", "repairs_succeeded_per_s"),
    ):
        value = _optional_float(row.get(counter_key))
        if value is not None:
            row[rate_key] = value / elapsed_seconds


def _normalize_improvement_metrics(row: dict[str, Any], elapsed_seconds: float | None) -> None:
    initial_cost = _optional_float(row.get("initial_cost"))
    best_cost = _optional_float(row.get("best_cost"))
    if initial_cost is None or best_cost is None:
        return
    improvement_abs = initial_cost - best_cost
    row["improvement_abs"] = improvement_abs
    denominator = abs(initial_cost)
    if denominator:
        row["improvement_rel"] = improvement_abs / denominator
    if elapsed_seconds is not None and elapsed_seconds > 0:
        row["improvement_per_second"] = improvement_abs / elapsed_seconds
    evaluations = _optional_float(row.get("evaluations"))
    if evaluations is not None and evaluations > 0:
        row["improvement_per_evaluation"] = improvement_abs / evaluations
    moves_attempted = _optional_float(row.get("moves_attempted"))
    if moves_attempted is not None and moves_attempted > 0:
        row["improvement_per_move"] = improvement_abs / moves_attempted


def _build_anytime(row: dict[str, Any], metadata: dict[str, Any]) -> list[dict[str, Any]]:
    time_limit = _optional_float(row.get("effective_time_limit_s"))
    if time_limit is None:
        time_limit = _optional_float(row.get("effective_exact_time_limit_s"))
    if time_limit is None:
        time_limit = _optional_float(row.get("elapsed_seconds"))
    if time_limit is None:
        return []

    events = _candidate_events(row, metadata)
    checkpoints = [value for value in ANYTIME_CHECKPOINT_SECONDS if value <= time_limit]
    if not checkpoints:
        return []

    reference = _optional_float(row.get("reference_objective"))
    anytime: list[dict[str, Any]] = []
    for checkpoint in checkpoints:
        best_cost = _best_event_cost_at(events, float(checkpoint))
        anytime.append(
            {
                "time_s": checkpoint,
                "best_cost": best_cost,
                "gap_rel": _gap_rel(best_cost, reference),
            }
        )
    return anytime


def _curve_summary(anytime: list[dict[str, Any]]) -> dict[str, Any]:
    if not anytime:
        return {
            "checkpoint_count": 0,
            "first_best_cost": None,
            "last_best_cost": None,
            "last_gap_rel": None,
        }
    return {
        "checkpoint_count": len(anytime),
        "first_time_s": anytime[0].get("time_s"),
        "last_time_s": anytime[-1].get("time_s"),
        "first_best_cost": anytime[0].get("best_cost"),
        "last_best_cost": anytime[-1].get("best_cost"),
        "last_gap_rel": anytime[-1].get("gap_rel"),
    }


def _candidate_events(row: dict[str, Any], metadata: dict[str, Any]) -> list[tuple[float, float]]:
    events: list[tuple[float, float]] = []
    if row.get("kind") == "exact_baseline":
        callback = metadata.get("solution_callback")
        if isinstance(callback, dict):
            samples = callback.get("samples")
            if isinstance(samples, list):
                for sample in samples:
                    if not isinstance(sample, dict):
                        continue
                    _append_event(
                        events,
                        sample.get("wall_time_seconds"),
                        sample.get("objective_value"),
                    )
    else:
        trace = metadata.get("trace")
        if isinstance(trace, list):
            for entry in trace:
                if not isinstance(entry, dict):
                    continue
                _append_event(events, entry.get("elapsed_seconds"), entry.get("best_score"))

    _append_event(events, row.get("elapsed_seconds"), row.get("best_cost"))
    events.sort(key=lambda item: item[0])
    return events


def _initial_cost(row: dict[str, Any], metadata: dict[str, Any]) -> float | None:
    if row.get("kind") != "strategy_run":
        return None
    trace = metadata.get("trace")
    if not isinstance(trace, list):
        return None
    events: list[tuple[float, float]] = []
    for entry in trace:
        if not isinstance(entry, dict):
            continue
        _append_event(events, entry.get("elapsed_seconds"), entry.get("best_score"))
    if not events:
        return None
    events.sort(key=lambda item: item[0])
    return events[0][1]


def _append_event(events: list[tuple[float, float]], seconds: Any, cost: Any) -> None:
    event_time = _optional_float(seconds)
    event_cost = _optional_float(cost)
    if event_time is None or event_time < 0 or event_cost is None:
        return
    events.append((event_time, event_cost))


def _best_event_cost_at(events: list[tuple[float, float]], checkpoint: float) -> float | None:
    best: float | None = None
    for event_time, cost in events:
        if event_time > checkpoint:
            break
        best = cost if best is None else min(best, cost)
    return best


def _best_cost(row: dict[str, Any]) -> float | None:
    if row.get("feasible") is not True:
        return None
    value = _optional_float(row.get("objective"))
    if value is not None:
        return value
    return _optional_float(row.get("raw_objective"))


def _gap_rel(value: float | None, reference: float | None) -> float | None:
    if value is None or reference is None:
        return None
    denominator = abs(reference)
    if denominator == 0:
        return None
    return (value - reference) / denominator


def _first_number(row: dict[str, Any], metadata: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = _optional_float(row.get(key))
        if value is not None:
            return value
        value = _optional_float(metadata.get(key))
        if value is not None:
            return value
    return None


def _sum_numbers(row: dict[str, Any], metadata: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    total = 0.0
    found = False
    for key in keys:
        value = _optional_float(row.get(key))
        if value is None:
            value = _optional_float(metadata.get(key))
        if value is None:
            continue
        total += value
        found = True
    return total if found else None


def _optional_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
