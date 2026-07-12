"""Tests for Phase 4 telemetry artifact publication."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from benchmarks.presentation.dashboard import generate_dashboard
from benchmarks.telemetry_artifacts import (
    CURVES_JSONL,
    DASHBOARD_JSON,
    DASHBOARD_MD,
    MANIFEST_JSON,
    METRICS_JSON,
    ROWS_JSONL,
    STATISTICAL_TESTS_JSON,
    STRATEGY_OPTIMIZATION_FEEDBACK_JSON,
    THROUGHPUT_JSONL,
    load_published_artifacts,
    publish_telemetry_artifacts,
)


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "telemetry" / "phase0"
PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "benchmarks"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text())


def _fixture_payloads() -> list[dict]:
    return [
        _fixture("native_search_minimal.json"),
        _fixture("framework_extensions.json"),
        _fixture("exact_backend_callbacks.json"),
        _fixture("missing_data_and_overflow.json"),
    ]


def test_publish_complete_phase4_artifact_set(tmp_path):
    output_dir = tmp_path / "artifacts"

    result = publish_telemetry_artifacts(
        _fixture_payloads(),
        output_dir,
        references={
            "toy-001": 10.0,
            "alns-toy": 20.0,
            "exact-toy": 4.0,
        },
        created_at="2026-07-07T00:00:00+00:00",
        optagent_commit="optagent-test",
        benchmarks_commit="benchmarks-test",
    )

    expected = {
        MANIFEST_JSON,
        ROWS_JSONL,
        CURVES_JSONL,
        THROUGHPUT_JSONL,
        METRICS_JSON,
        STATISTICAL_TESTS_JSON,
        STRATEGY_OPTIMIZATION_FEEDBACK_JSON,
        DASHBOARD_JSON,
        DASHBOARD_MD,
    }
    assert expected == {path.name for path in output_dir.iterdir()}

    manifest = result["manifest"]
    assert manifest["manifest_schema_version"] == 1
    assert manifest["commits"]["opt-agent"] == "optagent-test"
    assert manifest["commits"]["benchmarks"] == "benchmarks-test"
    assert manifest["source"]["count"] == 4
    assert manifest["availability"]["available"] > 0
    assert manifest["availability"]["insufficient_data"] > 0
    assert manifest["availability"]["unsupported"] > 0
    assert manifest["availability"]["error"] > 0
    assert set(manifest["artifacts"]) == expected - {MANIFEST_JSON}

    for name, entry in manifest["artifacts"].items():
        path = output_dir / name
        assert entry["bytes"] == path.stat().st_size
        assert entry["sha256"] == _sha256(path)

    loaded = load_published_artifacts(output_dir)
    assert len(loaded["rows"]) == 4
    assert len(loaded["curves"]) == 5
    assert loaded["metrics"]["effectiveness"]["by_strategy"]["ga"]["mean_objective"]["value"] == 10.0
    assert loaded["statistical_tests"] == loaded["metrics"]["statistical_validity"]
    assert loaded["strategy_optimization_feedback"]["purpose"] == "strategy_optimization_feedback"
    assert "ga" in loaded["strategy_optimization_feedback"]["by_strategy"]


def test_dashboard_artifact_exposes_availability_and_provenance(tmp_path):
    output_dir = tmp_path / "artifacts"
    publish_telemetry_artifacts(
        _fixture_payloads(),
        output_dir,
        references={"toy-001": 10.0, "alns-toy": 20.0, "exact-toy": 4.0},
        created_at="2026-07-07T00:00:00+00:00",
        optagent_commit="optagent-test",
        benchmarks_commit="benchmarks-test",
    )

    dashboard = json.loads((output_dir / DASHBOARD_JSON).read_text())
    availability = dashboard["availability_summary"]
    assert availability["available"] > 0
    assert availability["insufficient_data"] > 0
    assert availability["unsupported"] > 0
    assert availability["error"] > 0

    effectiveness_metrics = dashboard["sections"]["effectiveness"]["metrics"]
    mean_objective = next(
        metric
        for metric in effectiveness_metrics
        if metric["path"] == "effectiveness.by_strategy.ga.mean_objective"
    )
    assert mean_objective["source_artifact"] == METRICS_JSON
    assert mean_objective["schema_version"] == 1
    assert mean_objective["provenance"][0] == "run-telemetry.pb"

    statistical_metrics = dashboard["sections"]["statistical_validity"]["metrics"]
    assert statistical_metrics
    assert all(metric["source_artifact"] == STATISTICAL_TESTS_JSON for metric in statistical_metrics)
    assert all(metric["schema_version"] == 1 for metric in statistical_metrics)
    assert all(metric["provenance"] for metric in statistical_metrics)
    assert dashboard["strategy_optimization_feedback"]["by_strategy"]["alns"]["recommended_focus"]

    markdown = (output_dir / DASHBOARD_MD).read_text()
    assert "OptAgent Telemetry Metrics Dashboard" in markdown
    assert "statistical_validity" in markdown


def test_presentation_dashboard_reads_only_published_artifacts(tmp_path):
    artifact_dir = tmp_path / "artifacts"
    publish_telemetry_artifacts(
        _fixture_payloads(),
        artifact_dir,
        references={"toy-001": 10.0, "alns-toy": 20.0, "exact-toy": 4.0},
        created_at="2026-07-07T00:00:00+00:00",
        optagent_commit="optagent-test",
        benchmarks_commit="benchmarks-test",
    )

    dashboard = generate_dashboard(
        artifact_dir,
        output_root=tmp_path / "dashboards",
        dashboard_id="artifact-dashboard",
    )

    output_dir = Path(dashboard["output_dir"])
    assert (output_dir / MANIFEST_JSON).exists()
    assert (output_dir / DASHBOARD_JSON).exists()
    assert (output_dir / DASHBOARD_MD).exists()
    assert dashboard["artifact_dir"] == str(artifact_dir)
    assert dashboard["source_artifacts"] == [
        ROWS_JSONL,
        CURVES_JSONL,
        THROUGHPUT_JSONL,
        METRICS_JSON,
        STATISTICAL_TESTS_JSON,
        STRATEGY_OPTIMIZATION_FEEDBACK_JSON,
    ]


def test_public_telemetry_modules_do_not_import_legacy_scoring():
    public_modules = [
        PACKAGE_ROOT / "telemetry_metrics.py",
        PACKAGE_ROOT / "telemetry_artifacts.py",
        PACKAGE_ROOT / "presentation" / "dashboard.py",
    ]

    for path in public_modules:
        source = path.read_text(encoding="utf-8")
        assert "from benchmarks.scoring" not in source
        assert "import benchmarks.scoring" not in source
        assert "from benchmarks.scoring_phase2" not in source
        assert "import benchmarks.scoring_phase2" not in source


def test_manifest_checksum_validation_rejects_modified_artifact(tmp_path):
    output_dir = tmp_path / "artifacts"
    publish_telemetry_artifacts(
        _fixture_payloads(),
        output_dir,
        references={"toy-001": 10.0, "alns-toy": 20.0, "exact-toy": 4.0},
        created_at="2026-07-07T00:00:00+00:00",
        optagent_commit="optagent-test",
        benchmarks_commit="benchmarks-test",
    )
    with (output_dir / ROWS_JSONL).open("a", encoding="utf-8") as handle:
        handle.write("{}\n")

    try:
        load_published_artifacts(output_dir)
    except ValueError as exc:
        assert "checksum mismatch" in str(exc)
    else:
        raise AssertionError("corrupted artifact was accepted")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()
