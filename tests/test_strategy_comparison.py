from __future__ import annotations

import copy
from dataclasses import replace
import shutil

import pytest

from benchmarks.comparison_artifacts import load_run_artifact, publish_run_artifact
from benchmarks.cases.registry import benchmark_case_objects
from benchmarks.comparison_protocol import (
    ComparisonProfile,
    ComparisonProtocol,
    get_comparison_protocol,
    get_index_profile,
    index_profile_from_snapshot,
)
from benchmarks.strategy_comparison import compare_run_artifacts
from benchmarks.strategy_baselines import promote_comparison_baseline
from benchmarks.strategy_comparison_runner import (
    _install_wheel_environment,
    build_child_command,
    interleaved_execution_plan,
    planned_protocol_runs,
)


def test_ga_comparison_protocols_freeze_matrix_and_index_policy() -> None:
    smoke = get_comparison_protocol("ga_release_smoke_v1")
    calibration = get_comparison_protocol("ga_calibration_v1")
    holdout = get_comparison_protocol("ga_release_holdout_v1")
    index_policy = get_index_profile("ga_strategy_comparison_index_v1")

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
    assert index_policy.dimension_weights == {
        "quality": 0.4,
        "anytime": 0.3,
        "robustness": 0.2,
        "efficiency": 0.1,
    }
    assert index_policy.protocol_snapshot()["profile_id"] == "ga_strategy_comparison_index_v1"
    assert index_profile_from_snapshot(index_policy.protocol_snapshot()) == index_policy
    assert len(index_policy.checksum) == 71
    registered = {case.benchmark_id for case in benchmark_case_objects()}
    for protocol in (smoke, calibration, holdout):
        assert all(case_id in registered for profile in protocol.profiles for case_id in profile.case_ids)
    calibration_cases = {case_id for profile in calibration.profiles for case_id in profile.case_ids}
    holdout_cases = {case_id for profile in holdout.profiles for case_id in profile.case_ids}
    assert calibration_cases.isdisjoint(holdout_cases)


def test_run_artifact_is_immutable_complete_and_checksum_verified(tmp_path) -> None:
    protocol = _test_protocol()
    output_dir = tmp_path / "run-artifact"

    published = publish_run_artifact(
        [_run_row(objective=11.0)],
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
    loaded = load_run_artifact(output_dir)
    assert loaded.rows[0]["verification_passed"] is True
    assert loaded.telemetry[0]["identity"]["strategy"] == "ga"
    assert loaded.curves[0]["elapsed_s"] == 0.5

    with pytest.raises(FileExistsError):
        publish_run_artifact(
            [_run_row(objective=11.0)],
            output_dir,
            protocol=protocol,
            role="challenger",
            provenance={},
        )

    with (output_dir / "rows.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("{}\n")
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_run_artifact(output_dir)


def test_paired_comparison_produces_positive_index_statistics_and_feedback(tmp_path) -> None:
    protocol = _comparison_protocol()
    baseline_dir = tmp_path / "baseline"
    challenger_dir = tmp_path / "challenger"
    baseline_rows = [
        _run_row(case_id=case_id, seed=seed, objective=12.0 + seed / 100.0)
        for case_id in ("case-1", "case-2")
        for seed in (11, 23)
    ]
    challenger_rows = [
        _run_row(case_id=case_id, seed=seed, objective=10.5 + seed / 200.0)
        for case_id in ("case-1", "case-2")
        for seed in (11, 23)
    ]
    _publish_pair(protocol, baseline_rows, challenger_rows, baseline_dir, challenger_dir)

    result = compare_run_artifacts(baseline_dir, challenger_dir, tmp_path / "comparison")

    assert result["verdict"] == "improved"
    assert result["overall_delta_index"] > 10.0
    assert result["dimensions"]["quality"]["index"] > 0.0
    assert result["dimensions"]["anytime"]["index"] > 0.0
    assert result["profiles"]["test_family|test_style"]["verdict"] == "improved"
    assert result["statistical_evidence"]["final_gap_improvement_ci95"]["lower"] > 0.0
    assert result["diagnostic_feedback"]["largest_quality_improvements"][0]["improvement"] > 0.0
    assert (tmp_path / "comparison" / "feedback.md").read_text().startswith("# GA Strategy Comparison")
    assert set(path.name for path in (tmp_path / "comparison").iterdir()) == {
        "comparison_manifest.json",
        "dimension_metrics.json",
        "feedback.md",
        "paired_rows.jsonl",
        "delta_index.json",
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


def test_hard_gate_failure_cannot_be_offset_by_quality_index(tmp_path) -> None:
    protocol = _comparison_protocol()
    baseline_dir = tmp_path / "baseline"
    challenger_dir = tmp_path / "challenger"
    baseline_rows = [
        _run_row(case_id=case_id, seed=seed, objective=12.0) for case_id in ("case-1", "case-2") for seed in (11, 23)
    ]
    challenger_rows = [
        _run_row(
            case_id=case_id,
            seed=seed,
            objective=10.0,
            verification_passed=not (case_id == "case-2" and seed == 23),
        )
        for case_id in ("case-1", "case-2")
        for seed in (11, 23)
    ]
    _publish_pair(protocol, baseline_rows, challenger_rows, baseline_dir, challenger_dir)

    result = compare_run_artifacts(baseline_dir, challenger_dir, tmp_path / "comparison")

    assert result["verdict"] == "invalid"
    assert result["hard_gates"]["independent_verification"]["status"] == "failed"
    assert result["profiles"]["test_family|test_style"]["verdict"] == "invalid"
    assert result["promotable"] is False
    with pytest.raises(ValueError, match="improved promotable"):
        promote_comparison_baseline(
            tmp_path / "comparison",
            tmp_path / "baseline-registry.json",
            approved_by="maintainer@example.com",
        )


def test_baseline_verification_and_timeout_regressions_are_hard_gate_failures(tmp_path) -> None:
    protocol = _comparison_protocol()
    baseline_rows = [
        _run_row(
            case_id=case_id,
            seed=seed,
            objective=12.0,
            verification_passed=not (case_id == "case-1" and seed == 11),
        )
        for case_id in ("case-1", "case-2")
        for seed in (11, 23)
    ]
    challenger_rows = [
        _run_row(case_id=case_id, seed=seed, objective=10.0) for case_id in ("case-1", "case-2") for seed in (11, 23)
    ]
    challenger_rows[0]["status"] = "timeout"
    baseline_dir = tmp_path / "baseline"
    challenger_dir = tmp_path / "challenger"
    _publish_pair(protocol, baseline_rows, challenger_rows, baseline_dir, challenger_dir)

    result = compare_run_artifacts(baseline_dir, challenger_dir, tmp_path / "comparison")

    assert result["verdict"] == "invalid"
    assert result["hard_gates"]["independent_verification"]["status"] == "failed"
    assert result["hard_gates"]["timeouts"]["status"] == "failed"
    assert result["hard_gates"]["timeouts"]["baseline"] == 0
    assert result["hard_gates"]["timeouts"]["challenger"] == 1


def test_error_rows_produce_invalid_report_instead_of_statistics_exception(tmp_path) -> None:
    protocol = _comparison_protocol()
    baseline_rows = [
        _run_row(case_id=case_id, seed=seed, objective=12.0) for case_id in ("case-1", "case-2") for seed in (11, 23)
    ]
    challenger_rows = copy.deepcopy(baseline_rows)
    failed = challenger_rows[0]
    failed.update(
        {
            "status": "error",
            "feasible": False,
            "verification_status": "not_run",
            "verification_passed": False,
            "objective": None,
            "gap_rel": None,
        }
    )
    failed["telemetry"]["outcome"].update({"status": "failed", "feasible": False})
    failed["telemetry"]["progress"] = []
    baseline_dir = tmp_path / "baseline"
    challenger_dir = tmp_path / "challenger"
    _publish_pair(protocol, baseline_rows, challenger_rows, baseline_dir, challenger_dir)

    result = compare_run_artifacts(baseline_dir, challenger_dir, tmp_path / "comparison")

    assert result["verdict"] == "invalid"
    assert result["hard_gates"]["errors"]["status"] == "failed"
    assert (
        result["statistical_evidence"]["profiles"]["test_family|test_style"]["final_gap_improvement_ci95"][
            "availability"
        ]
        == "available"
    )


def test_smoke_protocol_cannot_claim_improvement_or_be_promoted(tmp_path) -> None:
    protocol = replace(_comparison_protocol(), kind="smoke")
    baseline_rows = [
        _run_row(case_id=case_id, seed=seed, objective=13.0) for case_id in ("case-1", "case-2") for seed in (11, 23)
    ]
    challenger_rows = [
        _run_row(case_id=case_id, seed=seed, objective=10.0) for case_id in ("case-1", "case-2") for seed in (11, 23)
    ]
    baseline_dir = tmp_path / "baseline"
    challenger_dir = tmp_path / "challenger"
    _publish_pair(protocol, baseline_rows, challenger_rows, baseline_dir, challenger_dir)

    result = compare_run_artifacts(baseline_dir, challenger_dir, tmp_path / "comparison")

    assert result["verdict"] == "neutral"
    assert result["promotable"] is False
    assert result["promotion_eligibility"]["status"] == "smoke_not_eligible"


def test_global_confidence_interval_preserves_equal_family_weighting(tmp_path) -> None:
    protocol = ComparisonProtocol(
        protocol_id="test_family_balance_v1",
        kind="calibration",
        index_profile_id="ga_strategy_comparison_index_v1",
        profiles=(
            ComparisonProfile("family-a", "style-a", ("case-a",)),
            ComparisonProfile("family-b", "style-b", ("case-b1", "case-b2", "case-b3")),
        ),
        seeds=(11, 23),
        wall_time_s=2.0,
        search_candidate_checkpoint=100,
        max_iterations=1000,
        population_size=8,
        trace_limit=32,
    )
    baseline_rows = []
    challenger_rows = []
    for profile in protocol.profiles:
        for case_id in profile.case_ids:
            for seed in protocol.seeds:
                baseline_rows.append(_run_row_for_profile(profile, case_id=case_id, seed=seed, objective=12.0))
                improvement = 1.0 if profile.family == "family-a" else -0.1
                challenger_rows.append(
                    _run_row_for_profile(
                        profile,
                        case_id=case_id,
                        seed=seed,
                        objective=12.0 - improvement,
                    )
                )
    baseline_dir = tmp_path / "baseline"
    challenger_dir = tmp_path / "challenger"
    _publish_pair(protocol, baseline_rows, challenger_rows, baseline_dir, challenger_dir)

    result = compare_run_artifacts(baseline_dir, challenger_dir, tmp_path / "comparison")
    interval = result["statistical_evidence"]["final_gap_improvement_ci95"]

    assert interval["estimand"] == "equal_family_mean_of_profile_medians"
    assert interval["median"] == pytest.approx(0.045)


def test_holm_correction_is_mapped_back_to_profiles(tmp_path) -> None:
    profiles = tuple(ComparisonProfile(f"family-{index}", f"style-{index}", (f"case-{index}",)) for index in range(3))
    protocol = replace(_comparison_protocol(), profiles=profiles)
    baseline_rows = [
        _run_row_for_profile(profile, case_id=profile.case_ids[0], seed=seed, objective=12.0)
        for profile in profiles
        for seed in protocol.seeds
    ]
    challenger_rows = [
        _run_row_for_profile(profile, case_id=profile.case_ids[0], seed=seed, objective=11.0)
        for profile in profiles
        for seed in protocol.seeds
    ]
    baseline_dir = tmp_path / "baseline"
    challenger_dir = tmp_path / "challenger"
    _publish_pair(protocol, baseline_rows, challenger_rows, baseline_dir, challenger_dir)

    result = compare_run_artifacts(baseline_dir, challenger_dir, tmp_path / "comparison")
    correction = result["statistical_evidence"]["multiple_comparison_correction"]

    assert set(correction["profiles"]) == {f"family-{index}|style-{index}" for index in range(3)}
    assert all("raw_p_value" in evidence for evidence in correction["profiles"].values())


def test_promotion_rejects_challenger_artifact_replaced_after_comparison(tmp_path) -> None:
    protocol = _comparison_protocol()
    baseline_rows = [
        _run_row(case_id=case_id, seed=seed, objective=13.0) for case_id in ("case-1", "case-2") for seed in (11, 23)
    ]
    challenger_rows = [
        _run_row(case_id=case_id, seed=seed, objective=10.0) for case_id in ("case-1", "case-2") for seed in (11, 23)
    ]
    baseline_dir = tmp_path / "baseline"
    challenger_dir = tmp_path / "challenger"
    _publish_pair(protocol, baseline_rows, challenger_rows, baseline_dir, challenger_dir)
    compare_run_artifacts(baseline_dir, challenger_dir, tmp_path / "comparison")

    shutil.rmtree(challenger_dir)
    replacement_rows = [
        _run_row(case_id=case_id, seed=seed, objective=11.0) for case_id in ("case-1", "case-2") for seed in (11, 23)
    ]
    publish_run_artifact(
        replacement_rows,
        challenger_dir,
        protocol=protocol,
        role="challenger",
        provenance={
            "benchmarks_commit": "b" * 40,
            "platform": "linux_x86_64",
            "optagent_commit": "c" * 40,
            "wheel_sha256": "sha256:" + "2" * 64,
        },
    )

    with pytest.raises(ValueError, match="challenger artifact changed after comparison"):
        promote_comparison_baseline(
            tmp_path / "comparison",
            tmp_path / "baseline-registry.json",
            approved_by="maintainer@example.com",
        )


def test_identical_evidence_is_centered_at_zero_and_neutral(tmp_path) -> None:
    protocol = _comparison_protocol()
    rows = [
        _run_row(case_id=case_id, seed=seed, objective=11.0 + seed / 100.0)
        for case_id in ("case-1", "case-2")
        for seed in (11, 23)
    ]
    baseline_dir = tmp_path / "baseline"
    challenger_dir = tmp_path / "challenger"
    _publish_pair(protocol, rows, copy.deepcopy(rows), baseline_dir, challenger_dir)

    result = compare_run_artifacts(baseline_dir, challenger_dir, tmp_path / "comparison")

    assert result["verdict"] == "neutral"
    assert result["overall_delta_index"] == pytest.approx(0.0)
    assert all(dimension["index"] == pytest.approx(0.0) for dimension in result["dimensions"].values())


def test_artifact_rejects_budget_drift_and_comparison_rejects_incompatible_config(tmp_path) -> None:
    protocol = _comparison_protocol()
    rows = [
        _run_row(case_id=case_id, seed=seed, objective=12.0) for case_id in ("case-1", "case-2") for seed in (11, 23)
    ]
    drifted = copy.deepcopy(rows)
    drifted[0]["effective_budget"]["time_limit_s"] = 3.0
    with pytest.raises(ValueError, match="protocol budget mismatch"):
        publish_run_artifact(
            drifted,
            tmp_path / "drifted",
            protocol=protocol,
            role="baseline",
            provenance={},
        )

    challenger_rows = copy.deepcopy(rows)
    for row in challenger_rows:
        row["strategy_config"] = {"population_size": 99}
    baseline_dir = tmp_path / "baseline"
    challenger_dir = tmp_path / "challenger"
    _publish_pair(protocol, rows, challenger_rows, baseline_dir, challenger_dir)

    result = compare_run_artifacts(baseline_dir, challenger_dir, tmp_path / "comparison")

    assert result["verdict"] == "incompatible"
    assert any("strategy_config differs" in reason for reason in result["compatibility_reasons"])


def test_artifact_rejects_incomplete_or_non_monotonic_incumbent_evidence(tmp_path) -> None:
    protocol = _test_protocol()
    truncated = _run_row(objective=11.0)
    truncated["telemetry"]["trace_overflow"]["omitted_incumbent_events"] = 1
    publish_run_artifact(
        [truncated],
        tmp_path / "truncated",
        protocol=protocol,
        role="baseline",
        provenance={},
    )
    assert load_run_artifact(tmp_path / "truncated").rows[0]["curve_complete"] is False

    non_monotonic = _run_row(objective=11.0)
    non_monotonic["telemetry"]["progress"][1]["objective_value"]["number_value"] = 20.0
    publish_run_artifact(
        [non_monotonic],
        tmp_path / "non-monotonic",
        protocol=protocol,
        role="baseline",
        provenance={},
    )
    assert load_run_artifact(tmp_path / "non-monotonic").rows[0]["curve_complete"] is False

    missing_overflow = _run_row(objective=11.0)
    del missing_overflow["telemetry"]["trace_overflow"]
    publish_run_artifact(
        [missing_overflow],
        tmp_path / "missing-overflow",
        protocol=protocol,
        role="baseline",
        provenance={},
    )
    assert load_run_artifact(tmp_path / "missing-overflow").rows[0]["curve_complete"] is False

    partial_overflow = _run_row(objective=11.0)
    partial_overflow["telemetry"]["trace_overflow"] = {}
    publish_run_artifact(
        [partial_overflow],
        tmp_path / "partial-overflow",
        protocol=protocol,
        role="baseline",
        provenance={},
    )
    assert load_run_artifact(tmp_path / "partial-overflow").rows[0]["curve_complete"] is False


def test_canonical_final_outcome_is_retained_as_termination_curve_point(tmp_path) -> None:
    protocol = _test_protocol()
    row = _run_row(objective=11.0)
    row["telemetry"]["progress"] = []

    publish_run_artifact(
        [row],
        tmp_path / "termination-only",
        protocol=protocol,
        role="baseline",
        provenance={},
    )

    artifact = load_run_artifact(tmp_path / "termination-only")
    assert artifact.rows[0]["curve_complete"] is True
    assert artifact.curves == [
        {
            "coordinate": "test_family|test_style|case-1|seed=11",
            "elapsed_s": 2.0,
            "evaluated_candidates": 200,
            "gap_rel": 0.1,
            "objective": 11.0,
        }
    ]


def test_termination_event_does_not_substitute_for_fixed_candidate_checkpoint(tmp_path) -> None:
    protocol = _comparison_protocol()
    rows = [
        _run_row(case_id=case_id, seed=seed, objective=11.0) for case_id in ("case-1", "case-2") for seed in (11, 23)
    ]
    for row in rows:
        row["telemetry"]["progress"] = []
    baseline_dir = tmp_path / "baseline"
    challenger_dir = tmp_path / "challenger"
    _publish_pair(protocol, rows, copy.deepcopy(rows), baseline_dir, challenger_dir)

    result = compare_run_artifacts(baseline_dir, challenger_dir, tmp_path / "comparison")

    assert result["verdict"] == "invalid"
    efficiency = result["profiles"]["test_family|test_style"]["dimensions"]["efficiency"]
    assert efficiency["components"]["fixed_search_candidate_elapsed"]["availability"] == "insufficient_data"


def test_protocol_runner_expands_matrix_and_interleaves_pair_order() -> None:
    protocol = _comparison_protocol()
    runs = planned_protocol_runs(protocol)
    plan = interleaved_execution_plan(protocol)

    assert len(runs) == 4
    assert len(plan) == 8
    assert all(plan[index].coordinate == plan[index + 1].coordinate for index in range(0, len(plan), 2))
    assert {plan[index].role for index in range(0, len(plan), 2)} == {"baseline", "challenger"}
    command = build_child_command("/tmp/python", runs[0], protocol, allow_download=False)
    assert command[0] == "/tmp/python"
    assert command[1].endswith("/benchmark.py")
    assert command[2:4] == ["run", "--case"]
    assert command[command.index("--model-style") + 1] == "test_style"
    assert command[command.index("--max-iterations") + 1] == "1000"
    assert command[-1] == "--no-download"


def test_protocol_environment_install_does_not_pollute_cli_stdout(monkeypatch, tmp_path) -> None:
    calls = []
    monkeypatch.setattr(
        "benchmarks.strategy_comparison_runner.subprocess.run",
        lambda command, **kwargs: calls.append((command, kwargs)),
    )

    _install_wheel_environment("/tmp/python", tmp_path / "optagent.whl", tmp_path / "venv")

    assert calls[1][1]["capture_output"] is True
    assert calls[1][1]["text"] is True


def _test_protocol() -> ComparisonProtocol:
    return ComparisonProtocol(
        protocol_id="test_ga_v1",
        kind="smoke",
        index_profile_id="ga_strategy_comparison_index_v1",
        profiles=(ComparisonProfile("test_family", "test_style", ("case-1",)),),
        seeds=(11,),
        wall_time_s=2.0,
        search_candidate_checkpoint=100,
        max_iterations=1000,
        population_size=8,
        trace_limit=32,
    )


def _comparison_protocol() -> ComparisonProtocol:
    return ComparisonProtocol(
        protocol_id="test_ga_comparison_v1",
        kind="calibration",
        index_profile_id="ga_strategy_comparison_index_v1",
        profiles=(ComparisonProfile("test_family", "test_style", ("case-1", "case-2")),),
        seeds=(11, 23),
        wall_time_s=2.0,
        search_candidate_checkpoint=100,
        max_iterations=1000,
        population_size=8,
        trace_limit=32,
    )


def _run_row(
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
        "verification_violations": [] if verification_passed else ["invalid challenger"],
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
            "outcome": {
                "status": "feasible",
                "feasible": True,
                "objective_sense": "minimize",
                "objective_value": {"status": "available", "number_value": objective},
            },
            "effort": {
                "wall_time_s": {"status": "available", "number_value": 2.0},
                "evaluated_candidates": {"status": "available", "integer_value": 200},
            },
            "progress": [
                {
                    "elapsed_s": 0.5,
                    "event_kind": "iteration",
                    "objective_value": {"status": "available", "number_value": objective + 1.0},
                    "feasible": True,
                    "evaluated_candidates": {"status": "available", "integer_value": 50},
                    "improved_best": True,
                },
                {
                    "elapsed_s": 1.5,
                    "event_kind": "candidate_checkpoint",
                    "objective_value": {"status": "available", "number_value": objective},
                    "feasible": True,
                    "evaluated_candidates": {"status": "available", "integer_value": 150},
                    "improved_best": True,
                },
            ],
            "trace_overflow": {
                "trace_truncated": False,
                "trace_event_limit": 32,
                "emitted_event_count": 2,
                "omitted_incumbent_events": 0,
                "checkpoint_policy": "candidate_checkpoints_and_incumbents",
            },
        },
    }


def _run_row_for_profile(
    profile: ComparisonProfile,
    *,
    case_id: str,
    seed: int,
    objective: float,
) -> dict:
    row = _run_row(case_id=case_id, seed=seed, objective=objective)
    row["family"] = profile.family
    row["model_style"] = profile.model_style
    row["telemetry"]["instance"]["family"] = profile.family
    return row


def _publish_pair(protocol, baseline_rows, challenger_rows, baseline_dir, challenger_dir) -> None:
    common = {
        "benchmarks_commit": "b" * 40,
        "platform": "linux_x86_64",
    }
    publish_run_artifact(
        baseline_rows,
        baseline_dir,
        protocol=protocol,
        role="baseline",
        provenance={**common, "optagent_commit": "a" * 40, "wheel_sha256": "sha256:" + "1" * 64},
    )
    publish_run_artifact(
        challenger_rows,
        challenger_dir,
        protocol=protocol,
        role="challenger",
        provenance={**common, "optagent_commit": "c" * 40, "wheel_sha256": "sha256:" + "2" * 64},
    )
