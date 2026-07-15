"""Tests for Phase 4 telemetry artifact publication."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
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
    main as publish_telemetry_main,
    publish_telemetry_artifacts,
    _load_suite_telemetry,
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
        metric for metric in effectiveness_metrics if metric["path"] == "effectiveness.by_strategy.ga.mean_objective"
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
        imported_modules = _imported_modules(path)
        legacy_modules = {
            "benchmarks.scoring",
            "benchmarks.scoring_phase2",
        }
        assert not {
            module
            for module in imported_modules
            if any(module == legacy or module.startswith(f"{legacy}.") for legacy in legacy_modules)
        }


def test_import_parser_resolves_relative_benchmark_modules(tmp_path):
    package_root = tmp_path / "benchmarks"
    cases = [
        (package_root / "telemetry_metrics.py", "from . import scoring"),
        (package_root / "presentation" / "dashboard.py", "from ..scoring import legacy"),
        (package_root / "presentation" / "dashboard.py", "from .. import scoring"),
    ]

    for path, source in cases:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        imported_modules = _imported_modules(path, package_root=package_root)
        assert any(
            module == "benchmarks.scoring" or module.startswith("benchmarks.scoring.") for module in imported_modules
        )


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


def test_suite_workspace_exports_embedded_canonical_telemetry(tmp_path):
    run_dir = tmp_path / "suite"
    run_dir.mkdir()
    telemetry = _fixture("native_search_minimal.json")
    row = {
        "benchmark_id": "toy-001",
        "status": "feasible",
        "reference_objective": 10.0,
        "telemetry": telemetry,
    }
    (run_dir / "rows.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")

    payloads, contexts = _load_suite_telemetry(run_dir)

    assert payloads == [telemetry]
    assert contexts == [
        {
            "instance_id": "toy-001",
            "benchmark_id": "toy-001",
            "reference_objective": 10.0,
        }
    ]


def test_suite_publication_preserves_benchmark_context_when_telemetry_has_no_instance_id(tmp_path):
    run_dir = tmp_path / "suite"
    run_dir.mkdir()
    telemetry = _fixture("native_search_minimal.json")
    telemetry["instance"].pop("id")
    row = {
        "benchmark_id": "suite-toy-001",
        "family": "sequence_blackbox_tsp",
        "status": "feasible",
        "reference_objective": 10.0,
        "telemetry": telemetry,
    }
    (run_dir / "rows.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    output_dir = tmp_path / "artifacts"

    exit_code = publish_telemetry_main(
        [
            "--suite-run",
            str(run_dir),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    published = load_published_artifacts(output_dir)
    assert published["rows"][0]["instance_id"] == "suite-toy-001"
    assert published["rows"][0]["family"] == "sequence_blackbox_tsp"
    mean_gap = published["metrics"]["effectiveness"]["by_strategy"]["ga"]["mean_gap_to_reference"]
    assert mean_gap["availability"] == "available"
    assert mean_gap["value"] == 0.0


def test_direct_publication_without_benchmark_id_uses_canonical_instance_name(tmp_path):
    telemetry = _fixture("native_search_minimal.json")
    telemetry["instance"].pop("id")
    output_dir = tmp_path / "artifacts"

    result = publish_telemetry_artifacts([telemetry], output_dir)

    assert result["manifest"]["source"]["count"] == 1
    published = load_published_artifacts(output_dir)
    assert published["rows"][0]["instance_id"] == "toy"


def test_suite_publication_keeps_existing_canonical_instance_identity(tmp_path):
    run_dir = tmp_path / "suite"
    run_dir.mkdir()
    telemetry = _fixture("native_search_minimal.json")
    row = {
        "benchmark_id": "suite-alias",
        "family": "suite-family",
        "status": "feasible",
        "reference_objective": 10.0,
        "telemetry": telemetry,
    }
    (run_dir / "rows.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    output_dir = tmp_path / "artifacts"

    exit_code = publish_telemetry_main(
        [
            "--suite-run",
            str(run_dir),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    published = load_published_artifacts(output_dir)
    assert published["rows"][0]["instance_id"] == "toy-001"
    mean_gap = published["metrics"]["effectiveness"]["by_strategy"]["ga"]["mean_gap_to_reference"]
    assert mean_gap["availability"] == "available"
    assert mean_gap["value"] == 0.0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _imported_modules(path: Path, *, package_root: Path = PACKAGE_ROOT) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    relative_module = path.relative_to(package_root.parent).with_suffix("")
    package = ".".join(relative_module.parts[:-1])
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level > 0:
                module = importlib.util.resolve_name(f"{'.' * node.level}{module}", package)
            modules.update(f"{module}.{alias.name}" for alias in node.names)
    return modules
