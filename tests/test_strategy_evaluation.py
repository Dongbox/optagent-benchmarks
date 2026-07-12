from __future__ import annotations

import copy

import pytest

from benchmarks.evaluation_artifacts import load_evaluation_artifact, publish_evaluation_artifact
from benchmarks.cases.registry import benchmark_case_objects
from benchmarks.evaluation_protocol import (
    EvaluationProfile,
    EvaluationProtocol,
    get_evaluation_protocol,
    get_scoring_profile,
)
from benchmarks.strategy_evaluation import compare_evaluation_artifacts
from benchmarks.strategy_baselines import promote_comparison_baseline
from benchmarks.strategy_evaluation_runner import build_child_command, interleaved_execution_plan, planned_protocol_runs


def test_ga_evaluation_protocols_freeze_matrix_and_scoring_policy() -> None:
    smoke = get_evaluation_protocol("ga_release_smoke_v1")
    calibration = get_evaluation_protocol("ga_calibration_v1")
    holdout = get_evaluation_protocol("ga_release_holdout_v1")
    scoring = get_scoring_profile("ga_strategy_evaluation_v1")

    assert smoke.seeds == (11, 23, 47)
    assert calibration.seeds == (11, 23, 47, 59, 71, 83, 97, 101, 113, 127)
    assert holdout.seeds == calibration.seeds
    assert {profile.family for profile in calibration.profiles} == {
        "cumulative_resource_scheduling",
        "flexible_interval_job_shop",
        "interval_job_shop",
        "sequence_blackbox_tsp",
        "sequence_quadratic_assignment",
        "sequence_transition_penalty",
    }
    assert len(calibration.profiles) == 7
    assert scoring.dimension_weights == {
        "quality": 0.4,
        "anytime": 0.3,
        "robustness": 0.2,
        "efficiency": 0.1,
    }
    assert scoring.protocol_snapshot()["profile_id"] == "ga_strategy_evaluation_v1"
    assert len(scoring.checksum) == 71
    registered = {case.benchmark_id for case in benchmark_case_objects()}
    for protocol in (smoke, calibration, holdout):
        assert all(case_id in registered for profile in protocol.profiles for case_id in profile.case_ids)
    calibration_cases = {case_id for profile in calibration.profiles for case_id in profile.case_ids}
    holdout_cases = {case_id for profile in holdout.profiles for case_id in profile.case_ids}
    assert calibration_cases.isdisjoint(holdout_cases)


def test_evaluation_artifact_is_immutable_complete_and_checksum_verified(tmp_path) -> None:
    protocol = _test_protocol()
    output_dir = tmp_path / "evaluation"

    published = publish_evaluation_artifact(
        [_evaluation_row(objective=11.0)],
        output_dir,
        protocol=protocol,
        role="baseline",
        provenance={
            "optagent_commit": "a" * 40,
            "benchmarks_commit": "b" * 40,
            "wheel_sha256": "sha256:" + "c" * 64,
        },
    )

    assert published["manifest"]["status"] == "complete"
    assert published["manifest"]["row_count"] == 1
    assert published["manifest"]["curve_count"] == 2
    assert published["manifest"]["protocol_checksum"] == protocol.checksum
    loaded = load_evaluation_artifact(output_dir)
    assert loaded.rows[0]["verification_passed"] is True
    assert loaded.telemetry[0]["identity"]["strategy"] == "ga"
    assert loaded.curves[0]["elapsed_s"] == 0.5

    with pytest.raises(FileExistsError):
        publish_evaluation_artifact(
            [_evaluation_row(objective=11.0)],
            output_dir,
            protocol=protocol,
            role="candidate",
            provenance={},
        )

    with (output_dir / "rows.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("{}\n")
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_evaluation_artifact(output_dir)


def test_paired_comparison_produces_positive_score_statistics_and_feedback(tmp_path) -> None:
    protocol = _comparison_protocol()
    baseline_dir = tmp_path / "baseline"
    candidate_dir = tmp_path / "candidate"
    baseline_rows = [
        _evaluation_row(case_id=case_id, seed=seed, objective=12.0 + seed / 100.0)
        for case_id in ("case-1", "case-2")
        for seed in (11, 23)
    ]
    candidate_rows = [
        _evaluation_row(case_id=case_id, seed=seed, objective=10.5 + seed / 200.0)
        for case_id in ("case-1", "case-2")
        for seed in (11, 23)
    ]
    _publish_pair(protocol, baseline_rows, candidate_rows, baseline_dir, candidate_dir)

    result = compare_evaluation_artifacts(baseline_dir, candidate_dir, tmp_path / "comparison")

    assert result["verdict"] == "improved"
    assert result["overall_delta_score"] > 10.0
    assert result["dimensions"]["quality"]["score"] > 0.0
    assert result["dimensions"]["anytime"]["score"] > 0.0
    assert result["profiles"]["test_family|test_style"]["verdict"] == "improved"
    assert result["statistical_evidence"]["final_gap_improvement_ci95"]["lower"] > 0.0
    assert result["diagnostic_feedback"]["largest_quality_improvements"][0]["improvement"] > 0.0
    assert (tmp_path / "comparison" / "feedback.md").read_text().startswith("# GA Strategy Evaluation")
    assert set(path.name for path in (tmp_path / "comparison").iterdir()) == {
        "comparison_manifest.json",
        "dimension_metrics.json",
        "feedback.md",
        "paired_rows.jsonl",
        "score.json",
        "statistical_evidence.json",
    }
    promotion = promote_comparison_baseline(
        tmp_path / "comparison",
        tmp_path / "baseline-registry.json",
        approved_by="maintainer@example.com",
    )
    assert promotion["active"]["protocol_id"] == "test_ga_comparison_v1"
    assert promotion["active"]["approved_by"] == "maintainer@example.com"
    assert len(promotion["history"]) == 1


def test_hard_gate_failure_cannot_be_offset_by_quality_score(tmp_path) -> None:
    protocol = _comparison_protocol()
    baseline_dir = tmp_path / "baseline"
    candidate_dir = tmp_path / "candidate"
    baseline_rows = [
        _evaluation_row(case_id=case_id, seed=seed, objective=12.0)
        for case_id in ("case-1", "case-2")
        for seed in (11, 23)
    ]
    candidate_rows = [
        _evaluation_row(
            case_id=case_id,
            seed=seed,
            objective=10.0,
            verification_passed=not (case_id == "case-2" and seed == 23),
        )
        for case_id in ("case-1", "case-2")
        for seed in (11, 23)
    ]
    _publish_pair(protocol, baseline_rows, candidate_rows, baseline_dir, candidate_dir)

    result = compare_evaluation_artifacts(baseline_dir, candidate_dir, tmp_path / "comparison")

    assert result["verdict"] == "invalid"
    assert result["hard_gates"]["independent_verification"]["status"] == "failed"
    assert result["promotable"] is False
    with pytest.raises(ValueError, match="improved promotable"):
        promote_comparison_baseline(
            tmp_path / "comparison",
            tmp_path / "baseline-registry.json",
            approved_by="maintainer@example.com",
        )


def test_identical_evidence_is_centered_at_zero_and_neutral(tmp_path) -> None:
    protocol = _comparison_protocol()
    rows = [
        _evaluation_row(case_id=case_id, seed=seed, objective=11.0 + seed / 100.0)
        for case_id in ("case-1", "case-2")
        for seed in (11, 23)
    ]
    baseline_dir = tmp_path / "baseline"
    candidate_dir = tmp_path / "candidate"
    _publish_pair(protocol, rows, copy.deepcopy(rows), baseline_dir, candidate_dir)

    result = compare_evaluation_artifacts(baseline_dir, candidate_dir, tmp_path / "comparison")

    assert result["verdict"] == "neutral"
    assert result["overall_delta_score"] == pytest.approx(0.0)
    assert all(dimension["score"] == pytest.approx(0.0) for dimension in result["dimensions"].values())


def test_artifact_rejects_budget_drift_and_comparison_rejects_incompatible_config(tmp_path) -> None:
    protocol = _comparison_protocol()
    rows = [
        _evaluation_row(case_id=case_id, seed=seed, objective=12.0)
        for case_id in ("case-1", "case-2")
        for seed in (11, 23)
    ]
    drifted = copy.deepcopy(rows)
    drifted[0]["effective_budget"]["time_limit_s"] = 3.0
    with pytest.raises(ValueError, match="protocol budget mismatch"):
        publish_evaluation_artifact(
            drifted,
            tmp_path / "drifted",
            protocol=protocol,
            role="baseline",
            provenance={},
        )

    candidate_rows = copy.deepcopy(rows)
    for row in candidate_rows:
        row["strategy_config"] = {"population_size": 99}
    baseline_dir = tmp_path / "baseline"
    candidate_dir = tmp_path / "candidate"
    _publish_pair(protocol, rows, candidate_rows, baseline_dir, candidate_dir)

    result = compare_evaluation_artifacts(baseline_dir, candidate_dir, tmp_path / "comparison")

    assert result["verdict"] == "incompatible"
    assert any("strategy_config differs" in reason for reason in result["compatibility_reasons"])


def test_artifact_rejects_incomplete_or_non_monotonic_incumbent_evidence(tmp_path) -> None:
    protocol = _test_protocol()
    truncated = _evaluation_row(objective=11.0)
    truncated["telemetry"]["trace_overflow"]["omitted_incumbent_events"] = 1
    publish_evaluation_artifact(
        [truncated],
        tmp_path / "truncated",
        protocol=protocol,
        role="baseline",
        provenance={},
    )
    assert load_evaluation_artifact(tmp_path / "truncated").rows[0]["curve_complete"] is False

    non_monotonic = _evaluation_row(objective=11.0)
    non_monotonic["telemetry"]["progress"][1]["objective_value"]["number_value"] = 20.0
    publish_evaluation_artifact(
        [non_monotonic],
        tmp_path / "non-monotonic",
        protocol=protocol,
        role="baseline",
        provenance={},
    )
    assert load_evaluation_artifact(tmp_path / "non-monotonic").rows[0]["curve_complete"] is False


def test_protocol_runner_expands_matrix_and_interleaves_pair_order() -> None:
    protocol = _comparison_protocol()
    runs = planned_protocol_runs(protocol)
    plan = interleaved_execution_plan(protocol)

    assert len(runs) == 4
    assert len(plan) == 8
    assert all(plan[index].coordinate == plan[index + 1].coordinate for index in range(0, len(plan), 2))
    assert {plan[index].role for index in range(0, len(plan), 2)} == {"baseline", "candidate"}
    command = build_child_command("/tmp/python", runs[0], protocol, allow_download=False)
    assert command[:4] == ["/tmp/python", "-m", "benchmarks.run", "--case"]
    assert command[command.index("--model-style") + 1] == "test_style"
    assert command[command.index("--max-iterations") + 1] == "1000"
    assert command[-1] == "--no-download"


def _test_protocol() -> EvaluationProtocol:
    return EvaluationProtocol(
        protocol_id="test_ga_v1",
        kind="smoke",
        scoring_profile_id="ga_strategy_evaluation_v1",
        profiles=(EvaluationProfile("test_family", "test_style", ("case-1",)),),
        seeds=(11,),
        wall_time_s=2.0,
        candidate_checkpoint=100,
        max_iterations=1000,
        population_size=8,
        trace_limit=32,
    )


def _comparison_protocol() -> EvaluationProtocol:
    return EvaluationProtocol(
        protocol_id="test_ga_comparison_v1",
        kind="calibration",
        scoring_profile_id="ga_strategy_evaluation_v1",
        profiles=(EvaluationProfile("test_family", "test_style", ("case-1", "case-2")),),
        seeds=(11, 23),
        wall_time_s=2.0,
        candidate_checkpoint=100,
        max_iterations=1000,
        population_size=8,
        trace_limit=32,
    )


def _evaluation_row(
    *,
    objective: float,
    seed: int = 11,
    case_id: str = "case-1",
    verification_passed: bool = True,
) -> dict:
    return {
        "benchmark_id": case_id,
        "family": "test_family",
        "model_style": "test_style",
        "strategy": "ga",
        "solve_route": "native_search",
        "platform": "linux_x86_64",
        "seed": seed,
        "thread_count": 1,
        "status": "feasible",
        "feasible": True,
        "verification_status": "passed" if verification_passed else "failed",
        "verification_passed": verification_passed,
        "verification_violations": [] if verification_passed else ["invalid candidate"],
        "objective": objective,
        "reference_objective": 10.0,
        "gap_rel": (objective - 10.0) / 10.0,
        "elapsed_seconds": 2.0,
        "effective_budget": {
            "max_iterations": 1000,
            "time_limit_s": 2.0,
            "population_size": 8,
            "trace_limit": 32,
            "thread_count": 1,
        },
        "strategy_config": {"population_size": 8},
        "diagnostics": {
            "fallback_attempts": 0,
            "fallback_successes": 0,
            "evaluated_candidates": 200,
        },
        "telemetry": {
            "schema": {"schema_version": 1},
            "identity": {"strategy": "ga", "seed": seed},
            "instance": {"id": case_id, "family": "test_family", "checksum": f"sha256:{case_id}"},
            "budget": {},
            "outcome": {"status": "feasible", "feasible": True},
            "effort": {},
            "progress": [
                {
                    "elapsed_s": 0.5,
                    "objective_value": {"status": "available", "number_value": objective + 1.0},
                    "feasible": True,
                    "evaluated_candidates": {"status": "available", "integer_value": 50},
                    "improved_best": True,
                },
                {
                    "elapsed_s": 1.5,
                    "objective_value": {"status": "available", "number_value": objective},
                    "feasible": True,
                    "evaluated_candidates": {"status": "available", "integer_value": 150},
                    "improved_best": True,
                },
            ],
            "trace_overflow": {
                "trace_truncated": False,
                "omitted_incumbent_events": 0,
            },
        },
    }


def _publish_pair(protocol, baseline_rows, candidate_rows, baseline_dir, candidate_dir) -> None:
    common = {
        "benchmarks_commit": "b" * 40,
        "platform": "linux_x86_64",
    }
    publish_evaluation_artifact(
        baseline_rows,
        baseline_dir,
        protocol=protocol,
        role="baseline",
        provenance={**common, "optagent_commit": "a" * 40, "wheel_sha256": "sha256:" + "1" * 64},
    )
    publish_evaluation_artifact(
        candidate_rows,
        candidate_dir,
        protocol=protocol,
        role="candidate",
        provenance={**common, "optagent_commit": "c" * 40, "wheel_sha256": "sha256:" + "2" * 64},
    )
