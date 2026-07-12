"""Canonical telemetry ingestion and five-dimensional metric derivation.

This module is the Phase 3 benchmark statistics entrypoint. It accepts only the
canonical OptAgent runtime telemetry schema, normalizes run facts into typed
rows and curves, then derives benchmark-owned metrics. Legacy flat diagnostics,
old ad-hoc rows, and direct dashboard summaries are intentionally rejected.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence


SUPPORTED_SCHEMA_VERSION = 1

AVAILABLE = "available"
NULL = "null"
UNSUPPORTED = "unsupported"
INSUFFICIENT_DATA = "insufficient_data"
ERROR = "error"

_STATUS_MAP = {
    "TELEMETRY_AVAILABLE": AVAILABLE,
    "TELEMETRY_NULL": NULL,
    "TELEMETRY_UNSUPPORTED": UNSUPPORTED,
    "TELEMETRY_INSUFFICIENT_DATA": INSUFFICIENT_DATA,
    "TELEMETRY_ERROR": ERROR,
    AVAILABLE: AVAILABLE,
    NULL: NULL,
    UNSUPPORTED: UNSUPPORTED,
    INSUFFICIENT_DATA: INSUFFICIENT_DATA,
    ERROR: ERROR,
}


class TelemetryInputError(ValueError):
    """Raised when benchmark statistics receive non-canonical telemetry."""


@dataclass(frozen=True)
class AvailabilityValue:
    status: str
    value: Any = None
    reason: str = ""
    source: str = ""

    @property
    def available(self) -> bool:
        return self.status == AVAILABLE


@dataclass(frozen=True)
class MetricRow:
    run_id: str
    strategy: str
    framework: str
    profile: str
    solver_name: str
    route: str
    seed: int | None
    instance_id: str
    instance_name: str
    dataset: str
    family: str
    objective_sense: str
    status: str
    feasible: bool
    objective: float | None
    objective_availability: str
    best_bound: float | None
    wall_time_s: float | None
    cpu_time_s: float | None
    peak_rss_bytes: int | None
    iterations: int | None
    evaluated_candidates: int | None
    accepted_moves: int | None
    improved_moves: int | None
    attempted_moves: int | None
    restarts: int | None
    time_budget_s: float | None
    trace_truncated: bool
    trace_event_count: int
    source_schema_version: int


@dataclass(frozen=True)
class CurvePoint:
    run_id: str
    strategy: str
    instance_id: str
    seed: int | None
    elapsed_s: float
    objective: float | None
    objective_availability: str
    feasible: bool
    iteration: int | None
    evaluated_candidates: int | None
    event_kind: str


@dataclass
class MetricDataset:
    rows: list[MetricRow] = field(default_factory=list)
    curves: list[CurvePoint] = field(default_factory=list)
    source_count: int = 0
    schema_version: int = SUPPORTED_SCHEMA_VERSION
    provenance: list[str] = field(default_factory=list)

    def rows_by_strategy(self) -> dict[str, list[MetricRow]]:
        grouped: dict[str, list[MetricRow]] = {}
        for row in self.rows:
            grouped.setdefault(row.strategy, []).append(row)
        return grouped

    def curves_by_run(self) -> dict[str, list[CurvePoint]]:
        grouped: dict[str, list[CurvePoint]] = {}
        for point in self.curves:
            grouped.setdefault(point.run_id, []).append(point)
        return grouped


def load_run_telemetry(payload: Any) -> dict[str, Any]:
    """Return a canonical telemetry dict or raise ``TelemetryInputError``.

    ``payload`` may be a protobuf message or a generated JSON diagnostics
    projection. The projection must preserve canonical schema blocks.
    """

    if not isinstance(payload, Mapping):
        payload = _protobuf_to_dict(payload)
    if not isinstance(payload, Mapping):
        raise TelemetryInputError("telemetry input must be a mapping or protobuf message")

    data = dict(payload)
    if _looks_like_legacy_input(data):
        raise TelemetryInputError("legacy diagnostics, runner rows, and dashboard summaries are not supported")

    schema = data.get("schema")
    if not isinstance(schema, Mapping):
        raise TelemetryInputError("canonical telemetry requires a schema block")

    version = _parse_int(schema.get("schema_version"))
    if version != SUPPORTED_SCHEMA_VERSION:
        raise TelemetryInputError(f"unsupported telemetry schema version: {version}")

    for block in ("identity", "instance", "outcome", "effort"):
        if not isinstance(data.get(block), Mapping):
            raise TelemetryInputError(f"canonical telemetry missing required block: {block}")

    return data


def build_metric_dataset(
    payloads: Iterable[Any],
    *,
    provenance: Sequence[str] | None = None,
) -> MetricDataset:
    """Normalize canonical telemetry payloads into benchmark rows and curves."""

    dataset = MetricDataset(provenance=list(provenance or ["run-telemetry.pb"]))
    for index, payload in enumerate(payloads):
        telemetry = load_run_telemetry(payload)
        row = _build_row(telemetry, index)
        dataset.rows.append(row)
        dataset.curves.extend(_build_curves(telemetry, row))
        dataset.source_count += 1
    return dataset


def derive_five_dimensional_metrics(
    dataset: MetricDataset,
    *,
    references: Mapping[str, float | Mapping[str, Any]] | None = None,
    targets: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Derive the five optimization performance dimensions from a dataset."""

    normalized_refs = _normalize_references(references or {})
    return {
        "effectiveness": calculate_effectiveness(dataset, references=normalized_refs),
        "efficiency": calculate_efficiency(dataset),
        "robustness": calculate_robustness(dataset, references=normalized_refs),
        "anytime": calculate_anytime(dataset, references=normalized_refs, targets=targets or {}),
        "statistical_validity": calculate_statistical_validity(dataset, references=normalized_refs),
    }


def derive_strategy_optimization_feedback(
    dataset: MetricDataset,
    metrics: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive actionable strategy-tuning feedback from five-dimensional metrics.

    The five dimensions remain the measurement layer. This feedback layer turns
    those measurements into conservative optimization focus areas for strategy
    maintainers without changing runtime ownership of facts.
    """

    by_strategy: dict[str, dict[str, Any]] = {}
    statistical = metrics.get("statistical_validity") if isinstance(metrics.get("statistical_validity"), Mapping) else {}
    for strategy, rows in dataset.rows_by_strategy().items():
        signals = _strategy_feedback_signals(strategy, metrics)
        recommendations = _strategy_recommendations(signals)
        guards = _strategy_regression_guards(signals)
        confidence = _strategy_feedback_confidence(strategy, statistical)
        by_strategy[strategy] = {
            "availability": AVAILABLE,
            "strategy": strategy,
            "run_count": len(rows),
            "sample_context": {
                "seed_count": len({row.seed for row in rows}),
                "instance_count": len({row.instance_id for row in rows}),
                "families": sorted({row.family for row in rows if row.family}),
            },
            "signals": signals,
            "recommended_focus": recommendations,
            "regression_guards": guards,
            "confidence": confidence,
            "provenance": _metric_provenance("rows", "five_dimensional_metrics", "strategy_optimization_feedback"),
        }
    return {
        "schema_version": 1,
        "source": "benchmarks",
        "purpose": "strategy_optimization_feedback",
        "by_strategy": by_strategy,
    }


def calculate_effectiveness(
    dataset: MetricDataset,
    *,
    references: Mapping[str, float],
) -> dict[str, Any]:
    by_strategy: dict[str, dict[str, Any]] = {}
    for strategy, rows in dataset.rows_by_strategy().items():
        feasible = [row for row in rows if row.feasible and row.objective is not None]
        objectives = [row.objective for row in feasible if row.objective is not None]
        gaps = [
            gap
            for row in feasible
            if (gap := _row_reference_gap(row, references)) is not None
        ]
        by_strategy[strategy] = {
            "run_count": metric_entry(len(rows), unit="runs"),
            "feasible_runs": metric_entry(len(feasible), unit="runs"),
            "solved_ratio": metric_entry(len(feasible) / len(rows) if rows else None, unit="ratio")
            if rows
            else metric_entry(None, availability=INSUFFICIENT_DATA, reason="no_runs"),
            "best_objective": _numeric_metric(_best_objective(feasible, references), rows, "objective"),
            "mean_objective": _numeric_metric(_mean(objectives), rows, "objective"),
            "mean_gap_to_reference": _numeric_metric(_mean(gaps), rows, "gap")
            if gaps
            else metric_entry(
                None,
                availability=INSUFFICIENT_DATA,
                reason="missing_reference_or_objective",
                source="benchmarks",
                provenance=_metric_provenance("rows", "references"),
            ),
            "median_gap_to_reference": _numeric_metric(_median(gaps), rows, "gap")
            if gaps
            else metric_entry(
                None,
                availability=INSUFFICIENT_DATA,
                reason="missing_reference_or_objective",
                source="benchmarks",
                provenance=_metric_provenance("rows", "references"),
            ),
            "best_gap_to_reference": _numeric_metric(min(gaps) if gaps else None, rows, "gap")
            if gaps
            else metric_entry(
                None,
                availability=INSUFFICIENT_DATA,
                reason="missing_reference_or_objective",
                source="benchmarks",
                provenance=_metric_provenance("rows", "references"),
            ),
        }
    return {"by_strategy": by_strategy}


def calculate_efficiency(dataset: MetricDataset) -> dict[str, Any]:
    by_strategy: dict[str, dict[str, Any]] = {}
    for strategy, rows in dataset.rows_by_strategy().items():
        wall_times = [row.wall_time_s for row in rows if row.wall_time_s is not None]
        candidates = [row.evaluated_candidates for row in rows if row.evaluated_candidates is not None]
        throughputs = [
            row.evaluated_candidates / row.wall_time_s
            for row in rows
            if row.evaluated_candidates is not None and row.wall_time_s and row.wall_time_s > 0
        ]
        by_strategy[strategy] = {
            "mean_wall_time_s": _numeric_metric(_mean(wall_times), rows, "wall_time_s", unit="s"),
            "mean_evaluated_candidates": _numeric_metric(_mean(candidates), rows, "evaluated_candidates"),
            "candidate_throughput_per_s": _numeric_metric(_mean(throughputs), rows, "throughput", unit="candidates/s")
            if throughputs
            else metric_entry(
                None,
                availability=UNSUPPORTED,
                reason="wall_time_or_candidate_count_unavailable",
                source="benchmarks",
                provenance=_metric_provenance("rows"),
            ),
        }
    return {"by_strategy": by_strategy}


def calculate_robustness(
    dataset: MetricDataset,
    *,
    references: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    normalized_refs = references or {}
    by_strategy: dict[str, dict[str, Any]] = {}
    for strategy, rows in dataset.rows_by_strategy().items():
        objectives = [row.objective for row in rows if row.feasible and row.objective is not None]
        gaps = [
            gap
            for row in rows
            if (gap := _row_reference_gap(row, normalized_refs)) is not None
        ]
        success_rate = len(objectives) / len(rows) if rows else None
        by_strategy[strategy] = {
            "run_count": metric_entry(len(rows), unit="runs"),
            "success_rate": metric_entry(success_rate, unit="ratio")
            if success_rate is not None
            else metric_entry(None, availability=INSUFFICIENT_DATA, reason="no_runs"),
            "objective_mean": _numeric_metric(_mean(objectives), rows, "objective"),
            "objective_median": _numeric_metric(_median(objectives), rows, "objective"),
            "objective_stddev": _sample_stat_metric(objectives, min_samples=2, stat="stddev"),
            "objective_variance": _sample_stat_metric(objectives, min_samples=2, stat="variance"),
            "objective_cv": _coefficient_of_variation_metric(objectives, min_samples=5),
            "objective_mean_ci95": _mean_ci95_metric(objectives, min_samples=10),
            "gap_mean": _numeric_metric(_mean(gaps), rows, "gap")
            if gaps
            else metric_entry(
                None,
                availability=INSUFFICIENT_DATA,
                reason="missing_reference_or_objective",
                source="benchmarks",
                provenance=_metric_provenance("rows", "references"),
            ),
            "gap_median": _numeric_metric(_median(gaps), rows, "gap")
            if gaps
            else metric_entry(
                None,
                availability=INSUFFICIENT_DATA,
                reason="missing_reference_or_objective",
                source="benchmarks",
                provenance=_metric_provenance("rows", "references"),
            ),
            "gap_stddev": _sample_stat_metric(gaps, min_samples=2, stat="stddev"),
            "gap_cv": _coefficient_of_variation_metric(gaps, min_samples=5),
            "gap_mean_ci95": _mean_ci95_metric(gaps, min_samples=10),
        }
    return {"by_strategy": by_strategy}


def calculate_anytime(
    dataset: MetricDataset,
    *,
    references: Mapping[str, float],
    targets: Mapping[str, float],
) -> dict[str, Any]:
    curves_by_run = dataset.curves_by_run()
    by_strategy: dict[str, dict[str, Any]] = {}
    for strategy, rows in dataset.rows_by_strategy().items():
        integrals: list[float] = []
        normalized_integrals: list[float] = []
        time_to_targets: list[float] = []
        target_hits = 0
        target_total = 0
        for row in rows:
            curve = sorted(curves_by_run.get(row.run_id, []), key=lambda point: point.elapsed_s)
            reference = references.get(row.instance_id)
            budget = _effective_time_budget(row)
            if reference is not None:
                integral = primal_integral(curve, reference, budget, row.objective_sense)
                if integral is not None:
                    integrals.append(integral)
                    if budget and budget > 0:
                        normalized_integrals.append(integral / budget)
            target = targets.get(row.instance_id, reference)
            if target is not None:
                target_total += 1
                elapsed = time_to_target(curve, target, row.objective_sense)
                if elapsed is not None:
                    target_hits += 1
                    time_to_targets.append(elapsed)
                elif budget is not None:
                    time_to_targets.append(budget)
        by_strategy[strategy] = {
            "mean_primal_integral": _numeric_metric(_mean(integrals), rows, "primal_integral")
            if integrals
            else metric_entry(
                None,
                availability=INSUFFICIENT_DATA,
                reason="missing_reference_or_progress_curve",
                source="benchmarks",
                provenance=_metric_provenance("curves", "references"),
            ),
            "mean_normalized_primal_integral": _numeric_metric(
                _mean(normalized_integrals),
                rows,
                "normalized_primal_integral",
                unit="gap",
            )
            if normalized_integrals
            else metric_entry(
                None,
                availability=INSUFFICIENT_DATA,
                reason="missing_reference_or_progress_curve",
                source="benchmarks",
                provenance=_metric_provenance("curves", "references"),
            ),
            "mean_time_to_target_s": _numeric_metric(_mean(time_to_targets), rows, "time_to_target", unit="s")
            if time_to_targets
            else metric_entry(
                None,
                availability=INSUFFICIENT_DATA,
                reason="missing_target_or_budget",
                source="benchmarks",
                provenance=_metric_provenance("curves", "targets"),
            ),
            "ecdf_target_hit_ratio": metric_entry(
                target_hits / target_total if target_total else None,
                availability=AVAILABLE if target_total else INSUFFICIENT_DATA,
                reason="" if target_total else "missing_targets",
                unit="ratio",
                source="benchmarks",
                provenance=_metric_provenance("curves", "targets"),
            ),
        }
    return {"by_strategy": by_strategy}


def calculate_statistical_validity(
    dataset: MetricDataset,
    *,
    references: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    normalized_refs = references or {}
    strategies = sorted(dataset.rows_by_strategy())
    if len(strategies) < 2:
        return {
            "status": INSUFFICIENT_DATA,
            "reason": "requires_at_least_two_strategies",
            "pairwise": [],
            "omnibus": metric_entry(None, availability=INSUFFICIENT_DATA, reason="requires_three_strategies"),
        }

    pairs: list[dict[str, Any]] = []
    for left_index, left in enumerate(strategies):
        for right in strategies[left_index + 1 :]:
            left_values, right_values = matched_normalized_outcomes(
                dataset,
                left,
                right,
                references=normalized_refs,
            )
            pairs.append(
                {
                    "strategies": [left, right],
                    "matched_pairs": len(left_values),
                    "comparison_metric": "relative_gap_or_pairwise_regret",
                    "a12": vargha_delaney_a12(left_values, right_values),
                    "cliffs_delta": cliffs_delta(left_values, right_values),
                    "wilcoxon": wilcoxon_signed_rank(left_values, right_values),
                }
            )

    p_values = [
        pair["wilcoxon"]["p_value"]
        for pair in pairs
        if pair["wilcoxon"].get("availability") == AVAILABLE and pair["wilcoxon"].get("p_value") is not None
    ]
    corrections = {
        "holm": holm_correction(p_values),
        "bonferroni": bonferroni_correction(p_values),
    }
    return {
        "status": AVAILABLE if any(pair["a12"].get("availability") == AVAILABLE for pair in pairs) else INSUFFICIENT_DATA,
        "pairwise": pairs,
        "omnibus": friedman_test(dataset),
        "multiple_comparison_correction": corrections,
    }


def matched_objectives(dataset: MetricDataset, strategy_a: str, strategy_b: str) -> tuple[list[float], list[float]]:
    """Return matched per-instance objectives for a paired comparison."""

    grouped: dict[tuple[str, str], list[float]] = {}
    for row in dataset.rows:
        if row.strategy not in (strategy_a, strategy_b) or not row.feasible or row.objective is None:
            continue
        grouped.setdefault((row.strategy, row.instance_id), []).append(row.objective)

    instances_a = {instance for strategy, instance in grouped if strategy == strategy_a}
    instances_b = {instance for strategy, instance in grouped if strategy == strategy_b}
    matched_instances = sorted(instances_a & instances_b)
    left: list[float] = []
    right: list[float] = []
    for instance in matched_instances:
        left.append(_mean(grouped[(strategy_a, instance)]))
        right.append(_mean(grouped[(strategy_b, instance)]))
    return left, right


def matched_normalized_outcomes(
    dataset: MetricDataset,
    strategy_a: str,
    strategy_b: str,
    *,
    references: Mapping[str, float] | None = None,
) -> tuple[list[float], list[float]]:
    """Return matched scale-free outcomes where lower is better.

    If a benchmark reference is available, outcomes are relative gaps to that
    reference. Otherwise the matched pair is normalized by the pairwise best
    objective for the instance, which keeps statistical comparisons from being
    dominated by large-scale instances.
    """

    grouped: dict[tuple[str, str], list[MetricRow]] = {}
    for row in dataset.rows:
        if row.strategy not in (strategy_a, strategy_b) or not row.feasible or row.objective is None:
            continue
        grouped.setdefault((row.strategy, row.instance_id), []).append(row)

    instances_a = {instance for strategy, instance in grouped if strategy == strategy_a}
    instances_b = {instance for strategy, instance in grouped if strategy == strategy_b}
    matched_instances = sorted(instances_a & instances_b)
    left: list[float] = []
    right: list[float] = []
    normalized_refs = references or {}
    for instance in matched_instances:
        left_objective = _mean([row.objective for row in grouped[(strategy_a, instance)] if row.objective is not None])
        right_objective = _mean([row.objective for row in grouped[(strategy_b, instance)] if row.objective is not None])
        if left_objective is None or right_objective is None:
            continue
        objective_sense = _instance_objective_sense([*grouped[(strategy_a, instance)], *grouped[(strategy_b, instance)]])
        reference = normalized_refs.get(instance)
        if reference is not None:
            left.append(_relative_gap(left_objective, reference, objective_sense))
            right.append(_relative_gap(right_objective, reference, objective_sense))
            continue
        left_regret, right_regret = _pairwise_relative_regret(left_objective, right_objective, objective_sense)
        left.append(left_regret)
        right.append(right_regret)
    return left, right


def vargha_delaney_a12(group_a: Sequence[float], group_b: Sequence[float]) -> dict[str, Any]:
    """A12 effect size for minimization objectives.

    The value is the probability that strategy A has a lower objective than
    strategy B, plus half the probability of a tie.
    """

    if len(group_a) < 10 or len(group_b) < 10:
        return {
            "availability": INSUFFICIENT_DATA,
            "reason": "requires_at_least_10_matched_pairs",
            "required": 10,
            "actual": min(len(group_a), len(group_b)),
            "effect_size": "vargha_delaney_a12",
        }
    wins = ties = 0.0
    for a in group_a:
        for b in group_b:
            if a < b:
                wins += 1.0
            elif a == b:
                ties += 1.0
    value = (wins + 0.5 * ties) / (len(group_a) * len(group_b))
    return {
        "availability": AVAILABLE,
        "effect_size": "vargha_delaney_a12",
        "value": value,
        "interpretation": _a12_interpretation(value),
        "sample_count": min(len(group_a), len(group_b)),
    }


def cliffs_delta(group_a: Sequence[float], group_b: Sequence[float]) -> dict[str, Any]:
    if len(group_a) < 10 or len(group_b) < 10:
        return {
            "availability": INSUFFICIENT_DATA,
            "reason": "requires_at_least_10_matched_pairs",
            "required": 10,
            "actual": min(len(group_a), len(group_b)),
            "effect_size": "cliffs_delta",
        }
    wins = losses = 0.0
    for a in group_a:
        for b in group_b:
            if a < b:
                wins += 1.0
            elif a > b:
                losses += 1.0
    value = (wins - losses) / (len(group_a) * len(group_b))
    return {
        "availability": AVAILABLE,
        "effect_size": "cliffs_delta",
        "value": value,
        "sample_count": min(len(group_a), len(group_b)),
    }


def wilcoxon_signed_rank(group_a: Sequence[float], group_b: Sequence[float]) -> dict[str, Any]:
    if len(group_a) != len(group_b):
        raise ValueError("Wilcoxon signed-rank requires matched samples")
    if len(group_a) < 10:
        return {
            "availability": INSUFFICIENT_DATA,
            "test": "wilcoxon_signed_rank",
            "reason": "requires_at_least_10_matched_pairs",
            "required": 10,
            "actual": len(group_a),
        }

    differences = [a - b for a, b in zip(group_a, group_b) if a != b]
    if not differences:
        return {
            "availability": AVAILABLE,
            "test": "wilcoxon_signed_rank",
            "statistic": 0.0,
            "p_value": 1.0,
            "sample_count": len(group_a),
            "significant": False,
        }

    ranks = _rank_abs(differences)
    positive = sum(rank for rank, diff in zip(ranks, differences) if diff > 0)
    negative = sum(rank for rank, diff in zip(ranks, differences) if diff < 0)
    statistic = min(positive, negative)
    n = len(differences)
    mean = n * (n + 1) / 4.0
    variance = n * (n + 1) * (2 * n + 1) / 24.0
    z = (statistic - mean) / math.sqrt(variance) if variance > 0 else 0.0
    p_value = 2.0 * (1.0 - _normal_cdf(abs(z)))
    return {
        "availability": AVAILABLE,
        "test": "wilcoxon_signed_rank",
        "statistic": statistic,
        "p_value": max(0.0, min(1.0, p_value)),
        "sample_count": len(group_a),
        "significant": p_value < 0.05,
    }


def friedman_test(dataset: MetricDataset) -> dict[str, Any]:
    strategies = sorted(dataset.rows_by_strategy())
    if len(strategies) < 3:
        return {
            "availability": INSUFFICIENT_DATA,
            "test": "friedman",
            "reason": "requires_at_least_3_strategies",
            "required_strategies": 3,
            "actual_strategies": len(strategies),
        }

    per_instance: dict[str, dict[str, list[float]]] = {}
    for row in dataset.rows:
        if row.feasible and row.objective is not None:
            per_instance.setdefault(row.instance_id, {}).setdefault(row.strategy, []).append(row.objective)

    matched_instances = [
        instance for instance, values in per_instance.items() if all(strategy in values for strategy in strategies)
    ]
    if len(matched_instances) < 10:
        return {
            "availability": INSUFFICIENT_DATA,
            "test": "friedman",
            "reason": "requires_at_least_10_matched_instances",
            "required_instances": 10,
            "actual_instances": len(matched_instances),
            "actual_strategies": len(strategies),
        }

    rank_sums = {strategy: 0.0 for strategy in strategies}
    for instance in matched_instances:
        rows_for_instance = [row for row in dataset.rows if row.instance_id == instance]
        objective_sense = _instance_objective_sense(rows_for_instance)
        values = [
            (strategy, _rankable_objective(_mean(per_instance[instance][strategy]), objective_sense))
            for strategy in strategies
        ]
        for strategy, rank in _rank_values(values):
            rank_sums[strategy] += rank

    n = len(matched_instances)
    k = len(strategies)
    statistic = (12.0 * n / (k * (k + 1))) * sum(
        (rank_sums[strategy] / n - (k + 1) / 2.0) ** 2 for strategy in strategies
    )
    p_value = _chi_square_sf(statistic, k - 1)
    return {
        "availability": AVAILABLE,
        "test": "friedman",
        "statistic": statistic,
        "p_value": p_value,
        "significant": p_value < 0.05,
        "n_strategies": k,
        "n_instances": n,
        "average_ranks": {strategy: rank_sums[strategy] / n for strategy in strategies},
    }


def holm_correction(p_values: Sequence[float], *, alpha: float = 0.05) -> dict[str, Any]:
    if len(p_values) < 3:
        return {
            "availability": INSUFFICIENT_DATA,
            "method": "holm",
            "reason": "requires_at_least_3_comparisons",
            "required": 3,
            "actual": len(p_values),
        }
    ordered = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [0.0] * len(p_values)
    previous = 0.0
    for rank, (index, p_value) in enumerate(ordered, start=1):
        corrected = min(1.0, (len(p_values) - rank + 1) * p_value)
        previous = max(previous, corrected)
        adjusted[index] = previous
    return {
        "availability": AVAILABLE,
        "method": "holm",
        "alpha": alpha,
        "adjusted_p_values": adjusted,
        "rejected": [p <= alpha for p in adjusted],
    }


def bonferroni_correction(p_values: Sequence[float], *, alpha: float = 0.05) -> dict[str, Any]:
    if len(p_values) < 3:
        return {
            "availability": INSUFFICIENT_DATA,
            "method": "bonferroni",
            "reason": "requires_at_least_3_comparisons",
            "required": 3,
            "actual": len(p_values),
        }
    adjusted = [min(1.0, p * len(p_values)) for p in p_values]
    return {
        "availability": AVAILABLE,
        "method": "bonferroni",
        "alpha": alpha,
        "adjusted_p_values": adjusted,
        "rejected": [p <= alpha for p in adjusted],
    }


def primal_integral(
    curve: Sequence[CurvePoint],
    reference: float,
    time_budget_s: float | None,
    objective_sense: str,
) -> float | None:
    available_points = [point for point in curve if point.objective is not None]
    if not available_points or reference == 0 or not time_budget_s or time_budget_s <= 0:
        return None
    integral = 0.0
    previous_time = 0.0
    previous_gap = _relative_gap(available_points[0].objective, reference, objective_sense)
    for point in available_points:
        elapsed = min(point.elapsed_s, time_budget_s)
        if elapsed > previous_time:
            integral += previous_gap * (elapsed - previous_time)
        previous_gap = _relative_gap(point.objective, reference, objective_sense)
        previous_time = elapsed
        if elapsed >= time_budget_s:
            break
    if previous_time < time_budget_s:
        integral += previous_gap * (time_budget_s - previous_time)
    return integral


def time_to_target(curve: Sequence[CurvePoint], target: float, objective_sense: str) -> float | None:
    for point in sorted(curve, key=lambda item: item.elapsed_s):
        if point.objective is None:
            continue
        if _meets_target(point.objective, target, objective_sense):
            return point.elapsed_s
    return None


def _build_row(telemetry: Mapping[str, Any], index: int) -> MetricRow:
    schema = telemetry["schema"]
    identity = telemetry["identity"]
    instance = telemetry["instance"]
    outcome = telemetry["outcome"]
    effort = telemetry["effort"]
    budget = telemetry.get("budget") if isinstance(telemetry.get("budget"), Mapping) else {}
    search = telemetry.get("search") if isinstance(telemetry.get("search"), Mapping) else {}
    backend = telemetry.get("backend") if isinstance(telemetry.get("backend"), Mapping) else {}
    trace_overflow = telemetry.get("trace_overflow") if isinstance(telemetry.get("trace_overflow"), Mapping) else {}

    strategy = str(identity.get("strategy") or "unknown_strategy")
    instance_id = str(instance.get("id") or instance.get("name") or f"instance-{index}")
    seed = _parse_int(identity.get("seed"))
    run_id = f"{strategy}:{instance_id}:{seed if seed is not None else 'seedless'}:{index}"
    objective = _telemetry_value(outcome.get("objective_value"))
    bound = _telemetry_value(outcome.get("best_objective_bound"))
    return MetricRow(
        run_id=run_id,
        strategy=strategy,
        framework=str(identity.get("strategy_framework") or ""),
        profile=str(identity.get("strategy_profile") or ""),
        solver_name=str(identity.get("solver_name") or backend.get("name") or ""),
        route=str(identity.get("run_route") or backend.get("route") or ""),
        seed=seed,
        instance_id=instance_id,
        instance_name=str(instance.get("name") or ""),
        dataset=str(instance.get("dataset") or ""),
        family=str(instance.get("family") or ""),
        objective_sense=str(outcome.get("objective_sense") or "minimize").lower(),
        status=str(outcome.get("status") or ""),
        feasible=bool(outcome.get("feasible", False)),
        objective=_as_float(objective.value) if objective.available else None,
        objective_availability=objective.status,
        best_bound=_as_float(bound.value) if bound.available else None,
        wall_time_s=_value_as_float(effort.get("wall_time_s")),
        cpu_time_s=_value_as_float(effort.get("cpu_time_s")),
        peak_rss_bytes=_value_as_int(effort.get("peak_rss_bytes")),
        iterations=_value_as_int(effort.get("iterations")),
        evaluated_candidates=_value_as_int(effort.get("evaluated_candidates")),
        accepted_moves=_value_as_int(search.get("accepted_moves")),
        improved_moves=_value_as_int(search.get("improved_moves")),
        attempted_moves=_value_as_int(search.get("attempted_moves")),
        restarts=_value_as_int(search.get("restarts")),
        time_budget_s=_value_as_float(budget.get("time_limit_s")),
        trace_truncated=bool(trace_overflow.get("trace_truncated", False)),
        trace_event_count=_parse_int(trace_overflow.get("emitted_event_count")) or 0,
        source_schema_version=_parse_int(schema.get("schema_version")) or SUPPORTED_SCHEMA_VERSION,
    )


def _build_curves(telemetry: Mapping[str, Any], row: MetricRow) -> list[CurvePoint]:
    curves: list[CurvePoint] = []
    progress = telemetry.get("progress") or []
    if not isinstance(progress, Sequence) or isinstance(progress, (str, bytes)):
        return curves
    for event in progress:
        if not isinstance(event, Mapping):
            continue
        objective = _telemetry_value(event.get("objective_value"))
        curves.append(
            CurvePoint(
                run_id=row.run_id,
                strategy=row.strategy,
                instance_id=row.instance_id,
                seed=row.seed,
                elapsed_s=_as_float(event.get("elapsed_s")) or 0.0,
                objective=_as_float(objective.value) if objective.available else None,
                objective_availability=objective.status,
                feasible=bool(event.get("feasible", False)),
                iteration=_value_as_int(event.get("iteration")),
                evaluated_candidates=_value_as_int(event.get("evaluated_candidates")),
                event_kind=str(event.get("event_kind") or ""),
            )
        )
    return curves


def _protobuf_to_dict(payload: Any) -> dict[str, Any] | None:
    try:
        from google.protobuf.json_format import MessageToDict
        from google.protobuf.message import Message
    except Exception:
        return None
    if isinstance(payload, Message):
        return MessageToDict(payload, preserving_proto_field_name=True)
    return None


def _looks_like_legacy_input(payload: Mapping[str, Any]) -> bool:
    if "benchmark_schema_version" in payload:
        return True
    if "diagnostics" in payload and "schema" not in payload:
        return True
    if "metadata" in payload and "schema" not in payload:
        return True
    if "dashboard" in payload and "schema" not in payload:
        return True
    if "run_id" in payload and "outcome" not in payload:
        return True
    return False


def _telemetry_value(raw: Any) -> AvailabilityValue:
    if not isinstance(raw, Mapping):
        return AvailabilityValue(NULL, reason="missing")
    status = _STATUS_MAP.get(str(raw.get("status") or ""), ERROR)
    value = None
    if status == AVAILABLE:
        if "number_value" in raw:
            value = raw.get("number_value")
        elif "integer_value" in raw:
            value = raw.get("integer_value")
        elif "bool_value" in raw:
            value = raw.get("bool_value")
        elif "string_value" in raw:
            value = raw.get("string_value")
    return AvailabilityValue(
        status=status,
        value=value,
        reason=str(raw.get("reason") or ""),
        source=str(raw.get("source") or ""),
    )


def _value_as_float(raw: Any) -> float | None:
    value = _telemetry_value(raw)
    return _as_float(value.value) if value.available else None


def _value_as_int(raw: Any) -> int | None:
    value = _telemetry_value(raw)
    return _parse_int(value.value) if value.available else None


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _mean(values: Sequence[float | int]) -> float | None:
    return float(statistics.fmean(values)) if values else None


def _median(values: Sequence[float]) -> float | None:
    return float(statistics.median(values)) if values else None


def _numeric_metric(
    value: float | int | None,
    rows: Sequence[MetricRow],
    field: str,
    *,
    unit: str = "",
) -> dict[str, Any]:
    if value is None:
        return metric_entry(
            None,
            availability=INSUFFICIENT_DATA,
            reason=f"no_available_{field}",
            source="benchmarks",
            provenance=_metric_provenance("rows"),
            sample_count=len(rows),
            unit=unit,
        )
    return metric_entry(
        float(value),
        source="benchmarks",
        provenance=_metric_provenance("rows"),
        sample_count=len(rows),
        unit=unit,
    )


def _sample_stat_metric(values: Sequence[float], *, min_samples: int, stat: str) -> dict[str, Any]:
    if len(values) < min_samples:
        return metric_entry(
            None,
            availability=INSUFFICIENT_DATA,
            reason=f"requires_{min_samples}_runs",
            required=min_samples,
            actual=len(values),
            source="benchmarks",
            provenance=_metric_provenance("rows"),
        )
    value = statistics.stdev(values) if stat == "stddev" else statistics.variance(values)
    return metric_entry(value, source="benchmarks", provenance=_metric_provenance("rows"), sample_count=len(values))


def _coefficient_of_variation_metric(values: Sequence[float], *, min_samples: int) -> dict[str, Any]:
    if len(values) < min_samples:
        return metric_entry(
            None,
            availability=INSUFFICIENT_DATA,
            reason=f"requires_{min_samples}_runs",
            required=min_samples,
            actual=len(values),
            source="benchmarks",
            provenance=_metric_provenance("rows"),
        )
    mean = statistics.fmean(values)
    if mean == 0:
        return metric_entry(None, availability=UNSUPPORTED, reason="zero_mean")
    return metric_entry(
        statistics.stdev(values) / abs(mean),
        unit="ratio",
        source="benchmarks",
        provenance=_metric_provenance("rows"),
        sample_count=len(values),
    )


def _mean_ci95_metric(values: Sequence[float], *, min_samples: int) -> dict[str, Any]:
    if len(values) < min_samples:
        return metric_entry(
            None,
            availability=INSUFFICIENT_DATA,
            reason=f"requires_{min_samples}_samples",
            required=min_samples,
            actual=len(values),
            source="benchmarks",
            provenance=_metric_provenance("rows"),
        )
    mean = statistics.fmean(values)
    half_width = 1.96 * statistics.stdev(values) / math.sqrt(len(values))
    return metric_entry(
        {"low": mean - half_width, "mean": mean, "high": mean + half_width},
        source="benchmarks",
        provenance=_metric_provenance("rows"),
        sample_count=len(values),
    )


def metric_entry(
    value: Any,
    *,
    availability: str = AVAILABLE,
    reason: str = "",
    unit: str = "",
    source: str = "benchmarks",
    provenance: Sequence[str] | None = None,
    sample_count: int | None = None,
    required: int | None = None,
    actual: int | None = None,
) -> dict[str, Any]:
    entry = {
        "availability": availability,
        "value": value,
        "unit": unit,
        "reason": reason,
        "source": source,
        "provenance": list(provenance or _metric_provenance("rows")),
    }
    if sample_count is not None:
        entry["sample_count"] = sample_count
    if required is not None:
        entry["required"] = required
    if actual is not None:
        entry["actual"] = actual
    return entry


def _metric_provenance(*steps: str) -> list[str]:
    return ["run-telemetry.pb", *steps, "five_dimensional_metrics"]


def _normalize_references(references: Mapping[str, float | Mapping[str, Any]]) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for instance, value in references.items():
        if isinstance(value, Mapping):
            objective = _as_float(value.get("objective") or value.get("best_known") or value.get("reference"))
        else:
            objective = _as_float(value)
        if objective is not None:
            normalized[str(instance)] = objective
    return normalized


def _strategy_feedback_signals(strategy: str, metrics: Mapping[str, Any]) -> dict[str, Any]:
    effectiveness = _strategy_metric_block(metrics, "effectiveness", strategy)
    efficiency = _strategy_metric_block(metrics, "efficiency", strategy)
    robustness = _strategy_metric_block(metrics, "robustness", strategy)
    anytime = _strategy_metric_block(metrics, "anytime", strategy)
    return {
        "effectiveness": {
            "solved_ratio": _metric_value(effectiveness, "solved_ratio"),
            "mean_gap_to_reference": _metric_value(effectiveness, "mean_gap_to_reference"),
            "median_gap_to_reference": _metric_value(effectiveness, "median_gap_to_reference"),
            "best_gap_to_reference": _metric_value(effectiveness, "best_gap_to_reference"),
        },
        "efficiency": {
            "mean_wall_time_s": _metric_value(efficiency, "mean_wall_time_s"),
            "mean_evaluated_candidates": _metric_value(efficiency, "mean_evaluated_candidates"),
            "candidate_throughput_per_s": _metric_value(efficiency, "candidate_throughput_per_s"),
        },
        "robustness": {
            "success_rate": _metric_value(robustness, "success_rate"),
            "gap_stddev": _metric_value(robustness, "gap_stddev"),
            "gap_cv": _metric_value(robustness, "gap_cv"),
        },
        "anytime": {
            "mean_normalized_primal_integral": _metric_value(anytime, "mean_normalized_primal_integral"),
            "mean_time_to_target_s": _metric_value(anytime, "mean_time_to_target_s"),
            "ecdf_target_hit_ratio": _metric_value(anytime, "ecdf_target_hit_ratio"),
        },
    }


def _strategy_recommendations(signals: Mapping[str, Any]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    solved_ratio = _signal_number(signals, "effectiveness", "solved_ratio")
    mean_gap = _signal_number(signals, "effectiveness", "mean_gap_to_reference")
    median_gap = _signal_number(signals, "effectiveness", "median_gap_to_reference")
    throughput = _signal_number(signals, "efficiency", "candidate_throughput_per_s")
    mean_candidates = _signal_number(signals, "efficiency", "mean_evaluated_candidates")
    gap_cv = _signal_number(signals, "robustness", "gap_cv")
    target_hit = _signal_number(signals, "anytime", "ecdf_target_hit_ratio")
    normalized_integral = _signal_number(signals, "anytime", "mean_normalized_primal_integral")

    if solved_ratio is not None and solved_ratio < 1.0:
        recommendations.append(
            _focus(
                "feasibility_and_repair",
                "high",
                "Some runs do not return feasible objective-bearing solutions.",
                ["effectiveness.solved_ratio", "robustness.success_rate"],
            )
        )
    if median_gap is not None and median_gap > 0.05:
        recommendations.append(
            _focus(
                "solution_quality",
                "high" if median_gap > 0.2 else "medium",
                "Median reference gap is still material; tune operators that improve incumbent quality.",
                ["effectiveness.median_gap_to_reference"],
            )
        )
    elif mean_gap is not None and mean_gap > 0.05:
        recommendations.append(
            _focus(
                "solution_quality_tail",
                "medium",
                "Mean reference gap is worse than median or threshold; inspect hard instances and tail behavior.",
                ["effectiveness.mean_gap_to_reference", "effectiveness.median_gap_to_reference"],
            )
        )
    if target_hit is not None and target_hit < 1.0:
        recommendations.append(
            _focus(
                "anytime_target_reaching",
                "high" if target_hit < 0.5 else "medium",
                "Not all runs reach the target within budget; improve early construction, repair, or acceptance schedules.",
                ["anytime.ecdf_target_hit_ratio", "anytime.mean_time_to_target_s"],
            )
        )
    if normalized_integral is not None and mean_gap is not None and normalized_integral > max(mean_gap, 0.01):
        recommendations.append(
            _focus(
                "early_search_progress",
                "medium",
                "Normalized primal integral is worse than final gap, suggesting improvements arrive late.",
                ["anytime.mean_normalized_primal_integral", "effectiveness.mean_gap_to_reference"],
            )
        )
    if throughput is None:
        recommendations.append(
            _focus(
                "effort_instrumentation",
                "medium",
                "Candidate throughput is unavailable; add or fix evaluated-candidate telemetry before tuning efficiency.",
                ["efficiency.candidate_throughput_per_s"],
            )
        )
    elif mean_candidates is not None and mean_gap is not None and mean_gap > 0.05 and mean_candidates > 0:
        recommendations.append(
            _focus(
                "candidate_quality",
                "medium",
                "Search spends candidate evaluations but retains material gap; tune generation, repair, or local improvement quality.",
                ["efficiency.mean_evaluated_candidates", "effectiveness.mean_gap_to_reference"],
            )
        )
    if gap_cv is not None and gap_cv > 0.25:
        recommendations.append(
            _focus(
                "random_seed_robustness",
                "medium",
                "Gap coefficient of variation is high; tune stochastic controls, population diversity, or restart policy.",
                ["robustness.gap_cv"],
            )
        )
    if not recommendations:
        recommendations.append(
            _focus(
                "controlled_experiment",
                "low",
                "No dominant weakness is visible from aggregate metrics; compare against a baseline or expand matched samples.",
                ["statistical_validity"],
            )
        )
    return recommendations


def _strategy_regression_guards(signals: Mapping[str, Any]) -> list[dict[str, Any]]:
    guards: list[dict[str, Any]] = []
    for dimension, metric, threshold, direction, description in [
        ("effectiveness", "solved_ratio", 1.0, "below", "Do not accept changes that reduce solved ratio without explicit scope."),
        ("effectiveness", "median_gap_to_reference", 0.0, "above", "Do not trade away median gap unless another primary objective explicitly improves."),
        ("anytime", "ecdf_target_hit_ratio", 1.0, "below", "Do not regress target hit ratio when target-reaching is a benchmark goal."),
        ("robustness", "gap_cv", 0.25, "above", "Treat high gap variance as a default-strategy release risk."),
    ]:
        value = _signal_number(signals, dimension, metric)
        if value is None:
            continue
        triggered = value < threshold if direction == "below" else value > threshold
        guards.append(
            {
                "metric": f"{dimension}.{metric}",
                "value": value,
                "threshold": threshold,
                "condition": direction,
                "triggered": triggered,
                "guidance": description,
            }
        )
    return guards


def _strategy_feedback_confidence(strategy: str, statistical: Mapping[str, Any]) -> dict[str, Any]:
    comparisons: list[dict[str, Any]] = []
    pairwise = statistical.get("pairwise", [])
    for pair in pairwise if isinstance(pairwise, list) else []:
        if not isinstance(pair, Mapping):
            continue
        strategies = pair.get("strategies")
        if not isinstance(strategies, list) or strategy not in strategies:
            continue
        a12 = pair.get("a12") if isinstance(pair.get("a12"), Mapping) else {}
        wilcoxon = pair.get("wilcoxon") if isinstance(pair.get("wilcoxon"), Mapping) else {}
        comparisons.append(
            {
                "strategies": strategies,
                "matched_pairs": pair.get("matched_pairs"),
                "comparison_metric": pair.get("comparison_metric"),
                "a12": a12.get("value"),
                "a12_interpretation": a12.get("interpretation"),
                "wilcoxon_p_value": wilcoxon.get("p_value"),
                "significant": wilcoxon.get("significant"),
                "availability": wilcoxon.get("availability") or a12.get("availability") or INSUFFICIENT_DATA,
            }
        )
    available = [item for item in comparisons if item.get("availability") == AVAILABLE]
    return {
        "availability": AVAILABLE if available else INSUFFICIENT_DATA,
        "reason": "" if available else "insufficient_matched_statistical_evidence",
        "comparisons": comparisons,
    }


def _strategy_metric_block(metrics: Mapping[str, Any], dimension: str, strategy: str) -> Mapping[str, Any]:
    dimension_payload = metrics.get(dimension)
    if not isinstance(dimension_payload, Mapping):
        return {}
    by_strategy = dimension_payload.get("by_strategy")
    if not isinstance(by_strategy, Mapping):
        return {}
    block = by_strategy.get(strategy)
    return block if isinstance(block, Mapping) else {}


def _metric_value(block: Mapping[str, Any], metric: str) -> dict[str, Any]:
    entry = block.get(metric)
    if isinstance(entry, Mapping):
        return {
            "availability": entry.get("availability", INSUFFICIENT_DATA),
            "value": entry.get("value"),
            "unit": entry.get("unit", ""),
            "reason": entry.get("reason", ""),
            "sample_count": entry.get("sample_count"),
        }
    return {
        "availability": INSUFFICIENT_DATA,
        "value": None,
        "unit": "",
        "reason": "metric_unavailable",
    }


def _signal_number(signals: Mapping[str, Any], dimension: str, metric: str) -> float | None:
    section = signals.get(dimension)
    if not isinstance(section, Mapping):
        return None
    entry = section.get(metric)
    if not isinstance(entry, Mapping) or entry.get("availability") != AVAILABLE:
        return None
    return _as_float(entry.get("value"))


def _focus(focus: str, priority: str, reason: str, source_metrics: Sequence[str]) -> dict[str, Any]:
    return {
        "focus": focus,
        "priority": priority,
        "reason": reason,
        "source_metrics": list(source_metrics),
    }


def _effective_time_budget(row: MetricRow) -> float | None:
    if row.time_budget_s is not None and row.time_budget_s > 0:
        return row.time_budget_s
    if row.wall_time_s is not None and row.wall_time_s > 0:
        return row.wall_time_s
    return None


def _row_reference_gap(row: MetricRow, references: Mapping[str, float]) -> float | None:
    if not row.feasible or row.objective is None:
        return None
    reference = references.get(row.instance_id)
    if reference is None:
        return None
    return _relative_gap(row.objective, reference, row.objective_sense)


def _best_objective(rows: Sequence[MetricRow], references: Mapping[str, float]) -> float | None:
    feasible = [row for row in rows if row.feasible and row.objective is not None]
    if not feasible:
        return None

    with_references = [(gap, row) for row in feasible if (gap := _row_reference_gap(row, references)) is not None]
    if with_references:
        return min(with_references, key=lambda item: item[0])[1].objective

    objective_sense = _instance_objective_sense(feasible)
    objectives = [row.objective for row in feasible if row.objective is not None]
    if objective_sense == "maximize":
        return max(objectives)
    return min(objectives)


def _instance_objective_sense(rows: Sequence[MetricRow]) -> str:
    senses = {row.objective_sense for row in rows if row.objective_sense}
    return "maximize" if senses == {"maximize"} else "minimize"


def _rankable_objective(objective: float | None, objective_sense: str) -> float:
    if objective is None:
        return float("inf")
    return -objective if objective_sense == "maximize" else objective


def _pairwise_relative_regret(left: float, right: float, objective_sense: str) -> tuple[float, float]:
    best = max(left, right) if objective_sense == "maximize" else min(left, right)
    denominator = abs(best) if best != 0 else 1.0
    if objective_sense == "maximize":
        return max(0.0, (best - left) / denominator), max(0.0, (best - right) / denominator)
    return max(0.0, (left - best) / denominator), max(0.0, (right - best) / denominator)


def _relative_gap(objective: float, reference: float, objective_sense: str) -> float:
    if reference == 0:
        return 0.0 if objective == reference else float("inf")
    if objective_sense == "maximize":
        return max(0.0, (reference - objective) / abs(reference))
    return max(0.0, (objective - reference) / abs(reference))


def _meets_target(objective: float, target: float, objective_sense: str) -> bool:
    if objective_sense == "maximize":
        return objective >= target
    return objective <= target


def _a12_interpretation(value: float) -> str:
    if value >= 0.71:
        return "large_a_better"
    if value >= 0.64:
        return "medium_a_better"
    if value >= 0.56:
        return "small_a_better"
    if value <= 0.29:
        return "large_b_better"
    if value <= 0.36:
        return "medium_b_better"
    if value <= 0.44:
        return "small_b_better"
    return "negligible"


def _rank_abs(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(abs(value) for value in values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        end = index + 1
        while end < len(indexed) and indexed[end][1] == indexed[index][1]:
            end += 1
        average_rank = (index + 1 + end) / 2.0
        for position in range(index, end):
            original_index, _ = indexed[position]
            ranks[original_index] = average_rank
        index = end
    return ranks


def _rank_values(values: Sequence[tuple[str, float]]) -> list[tuple[str, float]]:
    indexed = sorted(values, key=lambda item: item[1])
    ranks: list[tuple[str, float]] = []
    index = 0
    while index < len(indexed):
        end = index + 1
        while end < len(indexed) and indexed[end][1] == indexed[index][1]:
            end += 1
        average_rank = (index + 1 + end) / 2.0
        for position in range(index, end):
            ranks.append((indexed[position][0], average_rank))
        index = end
    return ranks


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _chi_square_sf(statistic: float, degrees_of_freedom: int) -> float:
    if statistic <= 0:
        return 1.0
    if degrees_of_freedom <= 0:
        return 1.0
    # Wilson-Hilferty normal approximation. Sufficient for benchmark gating;
    # exact statistical backends can replace this without changing callers.
    z = ((statistic / degrees_of_freedom) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * degrees_of_freedom))) / math.sqrt(
        2.0 / (9.0 * degrees_of_freedom)
    )
    return max(0.0, min(1.0, 1.0 - _normal_cdf(z)))
