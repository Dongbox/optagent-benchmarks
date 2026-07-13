from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks.review_bundle import (
    ANYTIME_CHECKPOINTS,
    _aggregate_curves,
    _build_evidence,
    load_review_bundle,
    main as publish_review_main,
)
from benchmarks.telemetry_artifacts import publish_telemetry_artifacts


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "telemetry" / "phase0" / "native_search_minimal.json"


def _telemetry(
    *,
    instance_id: str,
    family: str,
    seed: int,
    objective: float,
    strategy: str = "ga",
    profile: str = "default",
) -> dict:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["identity"]["strategy"] = strategy
    payload["identity"]["strategy_profile"] = profile
    payload["identity"]["seed"] = str(seed)
    payload["instance"]["id"] = instance_id
    payload["instance"]["family"] = family
    payload["outcome"]["objective_value"] = {"status": "TELEMETRY_AVAILABLE", "number_value": objective}
    payload["progress"] = [
        {
            "elapsed_s": 0.1,
            "objective_value": {"status": "TELEMETRY_AVAILABLE", "number_value": objective + 2.0},
            "feasible": True,
            "event_kind": "initial_incumbent",
        },
        {
            "elapsed_s": 0.8,
            "objective_value": {"status": "TELEMETRY_AVAILABLE", "number_value": objective},
            "feasible": True,
            "event_kind": "termination",
        },
    ]
    return payload


def _publish_artifact(
    tmp_path: Path,
    *,
    name: str = "telemetry",
    commit: str = "current-commit",
    objective_shift: float = 0.0,
    seeds: tuple[int, ...] = (11, 23),
    profile: str = "default",
) -> Path:
    payloads = [
        _telemetry(
            instance_id=instance_id,
            family=family,
            seed=seed,
            objective=objective + objective_shift,
            profile=profile,
        )
        for instance_id, family, objective in (
            ("case-a", "family-a", 12.0),
            ("case-b", "family-b", 21.0),
        )
        for seed in seeds
    ]
    artifact_dir = tmp_path / name
    publish_telemetry_artifacts(
        payloads,
        artifact_dir,
        references={"case-a": 10.0, "case-b": 20.0},
        targets={"case-a": 10.0, "case-b": 20.0},
        optagent_commit=commit,
        benchmarks_commit="benchmarks-commit",
        created_at="2026-07-13T00:00:00+00:00",
    )
    return artifact_dir


def test_publish_review_builds_single_strategy_static_bundle(tmp_path: Path) -> None:
    current_dir = _publish_artifact(tmp_path)
    output_dir = tmp_path / "review"

    exit_code = publish_review_main(
        [
            "--current-artifact",
            str(current_dir),
            "--output-dir",
            str(output_dir),
            "--protocol-id",
            "ga_calibration_v1",
        ]
    )

    assert exit_code == 0
    bundle = load_review_bundle(output_dir)
    assert bundle["index"]["kind"] == "optagent_review_bundle"
    assert bundle["index"]["default_mode"] == "single"
    assert set(bundle["index"]["artifacts"]) == {
        "overview.json",
        "families.json",
        "anytime.json",
        "evidence.json",
        "runs.jsonl",
    }
    assert bundle["overview"]["strategies"] == ["ga"]
    assert bundle["overview"]["current"]["optagent_commit"] == "current-commit"
    assert bundle["overview"]["current"]["protocol_id"] == "ga_calibration_v1"
    assert set(bundle["overview"]["strategies_data"]["ga"]["core_metrics"]) == {
        "median_reference_gap",
        "normalized_primal_integral",
        "target_hit_ratio",
        "gap_cv",
        "candidate_throughput",
    }
    assert [row["family"] for row in bundle["families"]["by_strategy"]["ga"]] == [
        "family-a",
        "family-b",
    ]
    assert bundle["anytime"]["by_strategy"]["ga"]["overall"]
    assert bundle["evidence"]["by_strategy"]["ga"]["largest_gaps"][0]["instance_id"] == "case-a"
    assert len(bundle["runs"]) == 4


def test_publish_review_packages_compatible_baseline_comparison(tmp_path: Path) -> None:
    current_dir = _publish_artifact(tmp_path, objective_shift=-1.0)
    baseline_dir = _publish_artifact(tmp_path, name="baseline", commit="baseline-commit")
    output_dir = tmp_path / "review"

    exit_code = publish_review_main(
        [
            "--current-artifact",
            str(current_dir),
            "--baseline-artifact",
            str(baseline_dir),
            "--output-dir",
            str(output_dir),
            "--protocol-id",
            "ga_calibration_v1",
        ]
    )

    assert exit_code == 0
    bundle = load_review_bundle(output_dir)
    assert bundle["index"]["comparison"] == {"available": True, "reason": ""}
    assert "comparison.json" in bundle["index"]["artifacts"]
    comparison = bundle["comparison"]
    assert comparison["compatible"] is True
    assert comparison["baseline"]["optagent_commit"] == "baseline-commit"
    assert "verdict" not in comparison
    assert "promotable" not in comparison
    gap = comparison["by_strategy"]["ga"]["core_metrics"]["median_reference_gap"]
    assert gap["change"] == "improved"
    assert gap["delta"] < 0
    assert comparison["by_strategy"]["ga"]["family_comparisons"][0]["family"] == "family-a"


def test_publish_review_reports_incompatible_baseline_without_comparing(tmp_path: Path) -> None:
    current_dir = _publish_artifact(tmp_path)
    baseline_dir = _publish_artifact(tmp_path, name="baseline", commit="baseline-commit", seeds=(11,))
    output_dir = tmp_path / "review"

    publish_review_main(
        [
            "--current-artifact",
            str(current_dir),
            "--baseline-artifact",
            str(baseline_dir),
            "--output-dir",
            str(output_dir),
            "--protocol-id",
            "ga_calibration_v1",
        ]
    )

    comparison = load_review_bundle(output_dir)["comparison"]
    assert comparison["compatible"] is False
    assert comparison["by_strategy"] == {}
    assert comparison["compatibility_reasons"]


def test_publish_review_rejects_multiple_current_strategies(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "telemetry"
    publish_telemetry_artifacts(
        [
            _telemetry(instance_id="case-a", family="family-a", seed=11, objective=12.0),
            _telemetry(
                instance_id="case-a",
                family="family-a",
                seed=23,
                objective=12.0,
                strategy="other",
            ),
        ],
        artifact_dir,
        references={"case-a": 10.0},
    )

    with pytest.raises(ValueError, match="exactly one strategy"):
        publish_review_main(
            [
                "--current-artifact",
                str(artifact_dir),
                "--output-dir",
                str(tmp_path / "review"),
                "--protocol-id",
                "ga_calibration_v1",
            ]
        )


def test_publish_review_rejects_incomplete_source_manifest(tmp_path: Path) -> None:
    artifact_dir = _publish_artifact(tmp_path)
    manifest_path = artifact_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["artifacts"]["rows.jsonl"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="complete artifact set"):
        publish_review_main(
            [
                "--current-artifact",
                str(artifact_dir),
                "--output-dir",
                str(tmp_path / "review"),
                "--protocol-id",
                "ga_calibration_v1",
            ]
        )


def test_comparison_rejects_experiment_identity_drift(tmp_path: Path) -> None:
    current_dir = _publish_artifact(tmp_path)
    baseline_dir = _publish_artifact(tmp_path, name="baseline", profile="different")
    output_dir = tmp_path / "review"

    publish_review_main(
        [
            "--current-artifact",
            str(current_dir),
            "--baseline-artifact",
            str(baseline_dir),
            "--output-dir",
            str(output_dir),
            "--protocol-id",
            "ga_calibration_v1",
        ]
    )

    comparison = load_review_bundle(output_dir)["comparison"]
    assert comparison["compatible"] is False
    assert comparison["compatibility_reasons"] == ["experiment_identity_mismatch:4"]
    assert comparison["by_strategy"] == {}


def test_anytime_aggregation_does_not_use_future_points() -> None:
    rows = [{"run_id": "run-1", "time_budget_s": 1.0}]
    curves = [{"run_id": "run-1", "elapsed_s": 0.03, "gap_to_reference": 0.5}]

    result = _aggregate_curves({"run-1"}, curves, {"run-1": rows[0]})

    assert [point["budget_fraction"] for point in result] == [
        checkpoint for checkpoint in ANYTIME_CHECKPOINTS if checkpoint >= 0.03
    ]


def test_target_miss_evidence_hides_hits_and_unknown_targets() -> None:
    rows = [
        {"strategy": "ga", "instance_id": "miss", "family": "a", "gap_to_reference": 0.2, "target_hit": False},
        {"strategy": "ga", "instance_id": "hit", "family": "a", "gap_to_reference": 0.0, "target_hit": True},
        {"strategy": "ga", "instance_id": "unknown", "family": "a", "gap_to_reference": 0.1, "target_hit": None},
    ]

    evidence = _build_evidence(rows, ["ga"])["by_strategy"]["ga"]

    assert [row["instance_id"] for row in evidence["target_misses"]] == ["miss"]
