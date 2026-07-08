"""Tests for canonical telemetry based benchmark metrics."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.telemetry_metrics import (
    AVAILABLE,
    INSUFFICIENT_DATA,
    CurvePoint,
    MetricDataset,
    MetricRow,
    TelemetryInputError,
    bonferroni_correction,
    build_metric_dataset,
    calculate_anytime,
    calculate_effectiveness,
    calculate_statistical_validity,
    cliffs_delta,
    derive_five_dimensional_metrics,
    derive_strategy_optimization_feedback,
    friedman_test,
    holm_correction,
    load_run_telemetry,
    matched_normalized_outcomes,
    matched_objectives,
    vargha_delaney_a12,
    wilcoxon_signed_rank,
)


FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "telemetry" / "phase0"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text())


def _fixture_payloads() -> list[dict]:
    return [
        _fixture("native_search_minimal.json"),
        _fixture("framework_extensions.json"),
        _fixture("exact_backend_callbacks.json"),
        _fixture("missing_data_and_overflow.json"),
    ]


def test_canonical_fixture_ingestion_builds_rows_and_curves():
    dataset = build_metric_dataset(_fixture_payloads(), provenance=["phase0-fixtures"])

    assert dataset.source_count == 4
    assert len(dataset.rows) == 4
    assert len(dataset.curves) == 5
    assert {row.strategy for row in dataset.rows} == {"ga", "alns", "cp_sat"}

    ga = next(row for row in dataset.rows if row.strategy == "ga")
    assert ga.instance_id == "toy-001"
    assert ga.objective == 10.0
    assert ga.evaluated_candidates == 820
    assert ga.trace_event_count == 2

    failed = next(row for row in dataset.rows if row.instance_id == "missing-bks")
    assert failed.objective is None
    assert failed.objective_availability == "error"
    assert failed.trace_truncated is True


def test_derive_five_dimensions_from_fixture_telemetry():
    dataset = build_metric_dataset(_fixture_payloads())
    metrics = derive_five_dimensional_metrics(
        dataset,
        references={
            "toy-001": 10.0,
            "alns-toy": 20.0,
            "exact-toy": 4.0,
        },
    )

    assert set(metrics) == {
        "effectiveness",
        "efficiency",
        "robustness",
        "anytime",
        "statistical_validity",
    }
    assert metrics["effectiveness"]["by_strategy"]["ga"]["mean_gap_to_reference"]["availability"] == AVAILABLE
    assert metrics["efficiency"]["by_strategy"]["ga"]["candidate_throughput_per_s"]["value"] == 3280.0
    assert metrics["robustness"]["by_strategy"]["cp_sat"]["success_rate"]["value"] == 0.5
    assert metrics["anytime"]["by_strategy"]["ga"]["mean_primal_integral"]["availability"] == AVAILABLE
    assert metrics["statistical_validity"]["status"] == INSUFFICIENT_DATA

    metric_entry = metrics["effectiveness"]["by_strategy"]["ga"]["mean_objective"]
    assert metric_entry["source"] == "benchmarks"
    assert metric_entry["provenance"][0] == "run-telemetry.pb"


def test_strategy_optimization_feedback_translates_metrics_to_actionable_focus():
    dataset = build_metric_dataset(_fixture_payloads())
    metrics = derive_five_dimensional_metrics(
        dataset,
        references={
            "toy-001": 10.0,
            "alns-toy": 20.0,
            "exact-toy": 4.0,
        },
    )

    feedback = derive_strategy_optimization_feedback(dataset, metrics)

    assert feedback["purpose"] == "strategy_optimization_feedback"
    assert set(feedback["by_strategy"]) == {"ga", "alns", "cp_sat"}
    alns_focus = {item["focus"] for item in feedback["by_strategy"]["alns"]["recommended_focus"]}
    assert "solution_quality" in alns_focus
    cp_sat_focus = {item["focus"] for item in feedback["by_strategy"]["cp_sat"]["recommended_focus"]}
    assert "feasibility_and_repair" in cp_sat_focus
    assert feedback["by_strategy"]["ga"]["signals"]["effectiveness"]["solved_ratio"]["value"] == 1.0


def test_legacy_flat_diagnostics_are_rejected():
    legacy_inputs = [
        {"metadata": {"objective": 1.0}, "diagnostics": {"runtime_ms": 10}},
        {"benchmark_schema_version": 2, "kind": "strategy_run", "objective": 1.0},
        {"run_id": "old-row", "strategy": "ga", "objective": 1.0},
    ]

    for payload in legacy_inputs:
        try:
            load_run_telemetry(payload)
        except TelemetryInputError as exc:
            assert "legacy" in str(exc) or "unsupported" in str(exc)
        else:
            raise AssertionError("legacy input was accepted")


def test_unsupported_schema_version_is_rejected():
    payload = copy.deepcopy(_fixture("native_search_minimal.json"))
    payload["schema"]["schema_version"] = 999

    try:
        load_run_telemetry(payload)
    except TelemetryInputError as exc:
        assert "unsupported telemetry schema version" in str(exc)
    else:
        raise AssertionError("unsupported schema was accepted")


def test_statistical_effect_size_defaults_require_matched_sample_threshold():
    too_small = vargha_delaney_a12([1.0, 2.0], [2.0, 3.0])
    assert too_small["availability"] == INSUFFICIENT_DATA
    assert too_small["required"] == 10

    left = [float(value) for value in range(10)]
    right = [float(value + 10) for value in range(10)]
    a12 = vargha_delaney_a12(left, right)
    delta = cliffs_delta(left, right)

    assert a12["availability"] == AVAILABLE
    assert a12["value"] == 1.0
    assert delta["value"] == 1.0


def test_wilcoxon_and_multiple_comparison_thresholds():
    insufficient = wilcoxon_signed_rank([1.0, 2.0], [2.0, 3.0])
    assert insufficient["availability"] == INSUFFICIENT_DATA

    left = [float(value) for value in range(10)]
    right = [float(value + 1) for value in range(10)]
    result = wilcoxon_signed_rank(left, right)
    assert result["availability"] == AVAILABLE
    assert result["sample_count"] == 10
    assert 0.0 <= result["p_value"] <= 1.0

    assert holm_correction([0.01, 0.03])["availability"] == INSUFFICIENT_DATA
    assert bonferroni_correction([0.01, 0.02, 0.2])["availability"] == AVAILABLE


def test_friedman_uses_matched_normalized_dataset():
    dataset = _statistical_dataset(strategy_count=3, instance_count=10)

    result = friedman_test(dataset)

    assert result["availability"] == AVAILABLE
    assert result["n_strategies"] == 3
    assert result["n_instances"] == 10
    assert set(result["average_ranks"]) == {"s0", "s1", "s2"}


def test_statistical_validity_operates_on_matched_rows():
    dataset = _statistical_dataset(strategy_count=3, instance_count=10)

    left, right = matched_objectives(dataset, "s0", "s1")
    stats = calculate_statistical_validity(dataset)

    assert len(left) == 10
    assert len(right) == 10
    assert stats["status"] == AVAILABLE
    assert len(stats["pairwise"]) == 3
    assert stats["multiple_comparison_correction"]["holm"]["availability"] == AVAILABLE


def test_effectiveness_uses_objective_sense_for_best_objective():
    dataset = MetricDataset(
        rows=[
            _metric_row("s0:i0:0", "s0", "i0", objective=5.0, objective_sense="maximize"),
            _metric_row("s0:i1:0", "s0", "i1", objective=10.0, objective_sense="maximize"),
        ],
        source_count=2,
    )

    metrics = calculate_effectiveness(dataset, references={})

    assert metrics["by_strategy"]["s0"]["best_objective"]["value"] == 10.0


def test_matched_normalized_outcomes_use_reference_gap_scale():
    dataset = MetricDataset(
        rows=[
            _metric_row("a:i0:0", "a", "i0", objective=110.0),
            _metric_row("b:i0:0", "b", "i0", objective=120.0),
            _metric_row("a:i1:0", "a", "i1", objective=11000.0),
            _metric_row("b:i1:0", "b", "i1", objective=10500.0),
        ],
        source_count=4,
    )

    left, right = matched_normalized_outcomes(dataset, "a", "b", references={"i0": 100.0, "i1": 10000.0})

    assert left == [0.1, 0.1]
    assert right == [0.2, 0.05]


def test_anytime_counts_target_misses_at_budget():
    row = _metric_row("s0:i0:0", "s0", "i0", objective=20.0)
    dataset = MetricDataset(
        rows=[row],
        curves=[
            CurvePoint(
                run_id=row.run_id,
                strategy=row.strategy,
                instance_id=row.instance_id,
                seed=row.seed,
                elapsed_s=1.0,
                objective=20.0,
                objective_availability=AVAILABLE,
                feasible=True,
                iteration=1,
                evaluated_candidates=1,
                event_kind="incumbent",
            )
        ],
        source_count=1,
    )

    metrics = calculate_anytime(dataset, references={}, targets={"i0": 10.0})

    assert metrics["by_strategy"]["s0"]["mean_time_to_target_s"]["value"] == 1.0
    assert metrics["by_strategy"]["s0"]["ecdf_target_hit_ratio"]["value"] == 0.0


def test_friedman_ranks_maximize_objectives_as_higher_better():
    dataset = _statistical_dataset(strategy_count=3, instance_count=10, objective_sense="maximize")

    result = friedman_test(dataset)

    assert result["availability"] == AVAILABLE
    assert result["average_ranks"]["s2"] == 1.0
    assert result["average_ranks"]["s0"] == 3.0


def _statistical_dataset(
    *,
    strategy_count: int,
    instance_count: int,
    objective_sense: str = "minimize",
) -> MetricDataset:
    rows: list[MetricRow] = []
    for instance_index in range(instance_count):
        for strategy_index in range(strategy_count):
            rows.append(
                _metric_row(
                    f"s{strategy_index}:i{instance_index}:0",
                    f"s{strategy_index}",
                    f"i{instance_index}",
                    objective=float(100 + strategy_index + instance_index),
                    objective_sense=objective_sense,
                )
            )
    return MetricDataset(rows=rows, curves=[], source_count=len(rows))


def _metric_row(
    run_id: str,
    strategy: str,
    instance_id: str,
    *,
    objective: float,
    objective_sense: str = "minimize",
) -> MetricRow:
    return MetricRow(
        run_id=run_id,
        strategy=strategy,
        framework="test",
        profile="",
        solver_name="fixture",
        route="fixture",
        seed=0,
        instance_id=instance_id,
        instance_name="",
        dataset="",
        family="",
        objective_sense=objective_sense,
        status="feasible",
        feasible=True,
        objective=objective,
        objective_availability=AVAILABLE,
        best_bound=None,
        wall_time_s=1.0,
        cpu_time_s=None,
        peak_rss_bytes=None,
        iterations=None,
        evaluated_candidates=100,
        accepted_moves=None,
        improved_moves=None,
        attempted_moves=None,
        restarts=None,
        time_budget_s=1.0,
        trace_truncated=False,
        trace_event_count=0,
        source_schema_version=1,
    )
