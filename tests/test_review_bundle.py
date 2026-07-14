from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from benchmarks.review_bundle import load_review_bundle, publish_review_bundle
from benchmarks.telemetry_artifacts import publish_telemetry_artifacts


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "telemetry" / "phase0" / "native_search_minimal.json"
TIMES = tuple(float(value) for value in range(1, 21))


def _telemetry(*, case_id: str, family: str, seed: int, objective: float, strategy: str) -> dict:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["identity"]["strategy"] = strategy
    payload["identity"]["seed"] = str(seed)
    payload["instance"]["id"] = case_id
    payload["instance"]["family"] = family
    payload["budget"]["time_limit_s"] = {"status": "TELEMETRY_AVAILABLE", "number_value": 20.0}
    payload["outcome"]["objective_value"] = {"status": "TELEMETRY_AVAILABLE", "number_value": objective}
    return payload


def _context(*, case_id: str, family: str, objective: float, shift: float = 0.0) -> dict:
    snapshots = {}
    observations = []
    for second in range(1, 21):
        snapshot_id = f"snapshot-{second:04d}"
        value = objective + shift + (20 - second) * 0.1
        snapshots[snapshot_id] = {
            "snapshot_id": snapshot_id,
            "verification_passed": True,
            "verification_feasible": True,
            "verification_objective": value,
            "incumbent_found_at_s": second - 0.1,
        }
        observations.append(
            {
                "requested_time_s": float(second),
                "captured_at_s": float(second),
                "state": "feasible_incumbent",
                "snapshot_id": snapshot_id,
                "search_ended": False,
                "search_ended_at_s": 0.0,
                "termination_reason": "",
            }
        )
    return {
        "benchmark_id": case_id,
        "family": family,
        "reference_objective": objective,
        "observations": observations,
        "solution_snapshots": snapshots,
        "observation_verification_passed": True,
        "observation_verification_errors": [],
        "preset_id": "ga_anytime_fast",
        "preset_version": "1",
        "review_mode": "single_family_focus",
        "target_families": ["family-a"],
        "formal_checkpoints_s": [5.0, 10.0, 20.0],
        "observation_times_s": list(TIMES),
        "expected_seed_count": 2,
        "case_checksum": f"checksum:{case_id}",
    }


def _publish(
    tmp_path: Path,
    *,
    name: str,
    strategy: str,
    shift: float = 0.0,
    schedule: tuple[float, ...] = TIMES,
    verified: bool = True,
) -> Path:
    payloads = []
    contexts = []
    for case_id, family, objective in (("case-a", "family-a", 10.0), ("case-b", "family-b", 20.0)):
        for seed in (11, 23):
            payloads.append(
                _telemetry(case_id=case_id, family=family, seed=seed, objective=objective + shift, strategy=strategy)
            )
            context = _context(case_id=case_id, family=family, objective=objective, shift=shift)
            context["observation_verification_passed"] = verified
            context["observation_times_s"] = list(schedule)
            if schedule != TIMES:
                context["observations"] = [
                    item for item in context["observations"] if item["requested_time_s"] in schedule
                ]
            contexts.append(context)
    output = tmp_path / name
    publish_telemetry_artifacts(
        payloads,
        output,
        benchmark_contexts=contexts,
        optagent_commit=f"{strategy}-commit",
        benchmarks_commit="benchmarks-commit",
        created_at="2026-07-13T00:00:00+00:00",
    )
    return output


def test_publish_single_record_bundle_contains_case_trajectories(tmp_path: Path) -> None:
    current = _publish(tmp_path, name="current", strategy="ga")
    output = tmp_path / "review"

    publish_review_bundle(current, output, protocol_id="ga_anytime_fast_v1")

    bundle = load_review_bundle(output)
    assert bundle["index"]["review_schema_version"] == 2
    assert bundle["index"]["render_mode"] == "single"
    assert set(bundle["index"]["artifacts"]) == {"overview.json", "results.json", "runs.jsonl"}
    assert bundle["overview"]["target_families"] == ["family-a"]
    assert bundle["overview"]["preset"]["configuration"]["time_limit_s"] == 20.0
    assert bundle["overview"]["preset"]["configuration"]["observation_interval_s"] == 1.0
    family = bundle["results"]["families"][0]
    assert family["role"] == "target"
    case = family["cases"][0]
    assert len(case["trajectory"]) == 20
    assert [point["time_s"] for point in case["checkpoints"]] == [5.0, 10.0, 20.0]
    assert case["trajectory"][-1]["current"]["gap"]["median"] == pytest.approx(0.0)
    assert case["trajectory"][-1]["current"]["objective"]["median"] == pytest.approx(10.0)
    assert case["trajectory"][-1]["current"]["objective"]["p25"] == pytest.approx(10.0)
    assert case["trajectory"][-1]["current"]["objective"]["p75"] == pytest.approx(10.0)


def test_publish_comparison_uses_paired_seed_cohort_and_allows_strategy_change(tmp_path: Path) -> None:
    current = _publish(tmp_path, name="current", strategy="ga", shift=-1.0)
    baseline = _publish(tmp_path, name="baseline", strategy="alns")
    output = tmp_path / "review"

    publish_review_bundle(current, output, protocol_id="ga_anytime_fast_v1", baseline_artifact=baseline)

    bundle = load_review_bundle(output)
    assert bundle["overview"]["compatible"] is True
    assert bundle["overview"]["current"]["strategy"] == "ga"
    assert bundle["overview"]["baseline"]["strategy"] == "alns"
    point = bundle["results"]["families"][0]["cases"][0]["trajectory"][-1]
    assert point["paired_gap"]["sample_count"] == 2
    assert point["paired_gap"]["delta_pp"] < 0
    assert point["paired_gap"]["change"] == "improved"
    assert point["current"]["objective"]["median"] == pytest.approx(9.0)
    assert point["baseline"]["objective"]["median"] == pytest.approx(10.0)


def test_comparison_does_not_fall_back_to_unpaired_current_gap(tmp_path: Path) -> None:
    current = _publish(tmp_path, name="current", strategy="ga", shift=-1.0)
    baseline = _publish(tmp_path, name="baseline", strategy="alns", verified=False)
    output = tmp_path / "review"

    publish_review_bundle(current, output, protocol_id="ga_anytime_fast_v1", baseline_artifact=baseline)

    point = load_review_bundle(output)["results"]["families"][0]["cases"][0]["trajectory"][-1]
    assert point["current"]["valid"] == 0
    assert point["current"]["gap"]["median"] is None
    assert point["baseline"]["valid"] == 0
    assert point["paired_gap"] is None


def test_incompatible_observation_schedule_is_rejected(tmp_path: Path) -> None:
    current = _publish(tmp_path, name="current", strategy="ga")
    baseline = _publish(tmp_path, name="baseline", strategy="ga", schedule=(5.0, 10.0, 20.0))
    output = tmp_path / "review"

    with pytest.raises(ValueError, match="observation_times_s_mismatch"):
        publish_review_bundle(current, output, protocol_id="ga_anytime_fast_v1", baseline_artifact=baseline)


def test_artifact_with_mixed_preset_metadata_is_rejected(tmp_path: Path) -> None:
    current = _publish(tmp_path, name="current", strategy="ga")
    rows_path = current / "rows.jsonl"
    rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines()]
    rows[-1]["preset_version"] = "2"
    rows_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    manifest_path = current / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"]["rows.jsonl"]["sha256"] = hashlib.sha256(rows_path.read_bytes()).hexdigest()
    manifest["artifacts"]["rows.jsonl"]["bytes"] = rows_path.stat().st_size
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="inconsistent preset_version"):
        publish_review_bundle(current, tmp_path / "review", protocol_id="ga_anytime_fast_v1")


def test_review_bundle_detects_checksum_tampering(tmp_path: Path) -> None:
    current = _publish(tmp_path, name="current", strategy="ga")
    output = tmp_path / "review"
    publish_review_bundle(current, output, protocol_id="ga_anytime_fast_v1")
    (output / "results.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="checksum"):
        load_review_bundle(output)
