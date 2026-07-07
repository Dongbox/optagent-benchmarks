"""Immutable artifact publication for canonical telemetry metrics.

Phase 4 publishes benchmark-owned artifacts that dashboards can read without
runner-private rows or legacy diagnostics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from benchmarks.telemetry_metrics import (
    AVAILABLE,
    CurvePoint,
    MetricDataset,
    MetricRow,
    build_metric_dataset,
    derive_five_dimensional_metrics,
)


ARTIFACT_SCHEMA_VERSION = 1
GENERATOR_NAME = "benchmarks.telemetry_artifacts"
GENERATOR_VERSION = "phase4-v1"

ROWS_JSONL = "rows.jsonl"
CURVES_JSONL = "curves.jsonl"
THROUGHPUT_JSONL = "throughput.jsonl"
METRICS_JSON = "five_dimensional_metrics.json"
STATISTICAL_TESTS_JSON = "statistical_tests.json"
DASHBOARD_JSON = "dashboard.json"
DASHBOARD_MD = "dashboard.md"
MANIFEST_JSON = "manifest.json"


def publish_telemetry_artifacts(
    payloads: Iterable[Any],
    output_dir: str | Path,
    *,
    references: Mapping[str, float | Mapping[str, Any]] | None = None,
    targets: Mapping[str, float] | None = None,
    source_label: str = "run-telemetry.pb",
    created_at: str | None = None,
    optagent_commit: str | None = None,
    benchmarks_commit: str | None = None,
) -> dict[str, Any]:
    """Build and publish the complete Phase 4 artifact set."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    dataset = build_metric_dataset(payloads, provenance=[source_label])
    metrics = derive_five_dimensional_metrics(dataset, references=references, targets=targets)
    statistical_tests = metrics["statistical_validity"]
    effective_created_at = created_at or datetime.now(timezone.utc).isoformat()

    rows = [row_to_artifact(row) for row in dataset.rows]
    curves = [curve_to_artifact(point) for point in dataset.curves]
    throughput = build_throughput_rows(dataset)
    dashboard = build_dashboard_artifact(
        rows=rows,
        curves=curves,
        throughput=throughput,
        metrics=metrics,
        statistical_tests=statistical_tests,
        created_at=effective_created_at,
    )

    _write_jsonl(out / ROWS_JSONL, rows)
    _write_jsonl(out / CURVES_JSONL, curves)
    _write_jsonl(out / THROUGHPUT_JSONL, throughput)
    _write_json(out / METRICS_JSON, metrics)
    _write_json(out / STATISTICAL_TESTS_JSON, statistical_tests)
    _write_json(out / DASHBOARD_JSON, dashboard)
    (out / DASHBOARD_MD).write_text(render_dashboard_markdown(dashboard), encoding="utf-8")

    manifest = build_manifest(
        output_dir=out,
        created_at=effective_created_at,
        source_count=dataset.source_count,
        source_label=source_label,
        optagent_commit=optagent_commit or _git_commit(Path(__file__).resolve().parents[1]),
        benchmarks_commit=benchmarks_commit or _git_commit(Path(__file__).resolve().parents[0]),
        availability=dashboard["availability_summary"],
    )
    _write_json(out / MANIFEST_JSON, manifest)
    return {
        "output_dir": str(out),
        "manifest": manifest,
        "dashboard": dashboard,
    }


def load_published_artifacts(artifact_dir: str | Path) -> dict[str, Any]:
    """Load dashboard-facing artifacts and validate manifest checksums."""

    root = Path(artifact_dir)
    manifest = _read_json(root / MANIFEST_JSON)
    for name, entry in manifest.get("artifacts", {}).items():
        path = root / name
        expected = entry.get("sha256")
        if expected and _sha256(path) != expected:
            raise ValueError(f"artifact checksum mismatch: {name}")
    return {
        "manifest": manifest,
        "rows": _read_jsonl(root / ROWS_JSONL),
        "curves": _read_jsonl(root / CURVES_JSONL),
        "throughput": _read_jsonl(root / THROUGHPUT_JSONL),
        "metrics": _read_json(root / METRICS_JSON),
        "statistical_tests": _read_json(root / STATISTICAL_TESTS_JSON),
        "dashboard": _read_json(root / DASHBOARD_JSON),
    }


def row_to_artifact(row: MetricRow) -> dict[str, Any]:
    data = asdict(row)
    return {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "source_artifact": "run-telemetry.pb",
        "provenance": ["run-telemetry.pb", ROWS_JSONL],
        **data,
    }


def curve_to_artifact(point: CurvePoint) -> dict[str, Any]:
    data = asdict(point)
    return {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "source_artifact": ROWS_JSONL,
        "provenance": ["run-telemetry.pb", ROWS_JSONL, CURVES_JSONL],
        **data,
    }


def build_throughput_rows(dataset: MetricDataset) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in dataset.rows:
        values: dict[str, Any] = {}
        if row.wall_time_s and row.wall_time_s > 0:
            if row.evaluated_candidates is not None:
                values["candidate_throughput_per_s"] = row.evaluated_candidates / row.wall_time_s
            if row.attempted_moves is not None:
                values["attempted_moves_per_s"] = row.attempted_moves / row.wall_time_s
            if row.accepted_moves is not None:
                values["accepted_moves_per_s"] = row.accepted_moves / row.wall_time_s
            if row.improved_moves is not None:
                values["improved_moves_per_s"] = row.improved_moves / row.wall_time_s
        rows.append(
            {
                "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
                "run_id": row.run_id,
                "strategy": row.strategy,
                "instance_id": row.instance_id,
                "seed": row.seed,
                "availability": AVAILABLE if values else "unsupported",
                "reason": "" if values else "wall_time_or_counters_unavailable",
                "wall_time_s": row.wall_time_s,
                "provenance": ["run-telemetry.pb", ROWS_JSONL, THROUGHPUT_JSONL],
                **values,
            }
        )
    return rows


def build_dashboard_artifact(
    *,
    rows: Sequence[Mapping[str, Any]],
    curves: Sequence[Mapping[str, Any]],
    throughput: Sequence[Mapping[str, Any]] = (),
    metrics: Mapping[str, Any],
    statistical_tests: Mapping[str, Any],
    created_at: str,
) -> dict[str, Any]:
    """Build a dashboard summary from published artifact payloads only."""

    strategies = sorted({str(row.get("strategy")) for row in rows})
    sections = {
        dimension: _dimension_section(dimension, payload)
        for dimension, payload in metrics.items()
        if dimension != "statistical_validity"
    }
    sections["statistical_validity"] = _statistical_section(statistical_tests)
    return {
        "dashboard_schema_version": ARTIFACT_SCHEMA_VERSION,
        "created_at": created_at,
        "source_artifacts": [
            ROWS_JSONL,
            CURVES_JSONL,
            THROUGHPUT_JSONL,
            METRICS_JSON,
            STATISTICAL_TESTS_JSON,
        ],
        "strategy_count": len(strategies),
        "run_count": len(rows),
        "curve_point_count": len(curves),
        "strategies": strategies,
        "sections": sections,
        "availability_summary": availability_summary(
            {
                "rows": rows,
                "curves": curves,
                "throughput": throughput,
                "metrics": metrics,
                "statistical_tests": statistical_tests,
            }
        ),
    }


def render_dashboard_markdown(dashboard: Mapping[str, Any]) -> str:
    lines = [
        "# OptAgent Telemetry Metrics Dashboard",
        "",
        f"- Schema: `{dashboard.get('dashboard_schema_version')}`",
        f"- Runs: {dashboard.get('run_count')}",
        f"- Strategies: {dashboard.get('strategy_count')}",
        f"- Curve points: {dashboard.get('curve_point_count')}",
        "",
        "## Availability",
        "",
        "| State | Count |",
        "| --- | ---: |",
    ]
    for state, count in sorted((dashboard.get("availability_summary") or {}).items()):
        lines.append(f"| `{state}` | {count} |")
    lines.extend(["", "## Metric Sections", ""])
    for name, section in (dashboard.get("sections") or {}).items():
        lines.append(f"### {name}")
        lines.append("")
        lines.append("| Metric | Availability | Value | Unit | Samples | Required | Actual |")
        lines.append("| --- | --- | ---: | --- | ---: | ---: | ---: |")
        for metric in section.get("metrics", []):
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{metric.get('path')}`",
                        f"`{metric.get('availability')}`",
                        _display_value(metric.get("value")),
                        str(metric.get("unit") or ""),
                        _display_value(metric.get("sample_count")),
                        _display_value(metric.get("required")),
                        _display_value(metric.get("actual")),
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_manifest(
    *,
    output_dir: Path,
    created_at: str,
    source_count: int,
    source_label: str,
    optagent_commit: str,
    benchmarks_commit: str,
    availability: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    artifact_names = [
        ROWS_JSONL,
        CURVES_JSONL,
        THROUGHPUT_JSONL,
        METRICS_JSON,
        STATISTICAL_TESTS_JSON,
        DASHBOARD_JSON,
        DASHBOARD_MD,
    ]
    artifacts = {
        name: {
            "path": name,
            "bytes": (output_dir / name).stat().st_size,
            "sha256": _sha256(output_dir / name),
        }
        for name in artifact_names
    }
    return {
        "manifest_schema_version": ARTIFACT_SCHEMA_VERSION,
        "created_at": created_at,
        "generator": {
            "name": GENERATOR_NAME,
            "version": GENERATOR_VERSION,
        },
        "commits": {
            "opt-agent": optagent_commit,
            "benchmarks": benchmarks_commit,
        },
        "source": {
            "count": source_count,
            "label": source_label,
            "canonical_format": "protobuf",
            "accepted_projection": "json_diagnostics",
        },
        "availability": dict(availability or {}),
        "artifacts": artifacts,
        "provenance": {
            ROWS_JSONL: [source_label, ROWS_JSONL],
            CURVES_JSONL: [source_label, ROWS_JSONL, CURVES_JSONL],
            THROUGHPUT_JSONL: [source_label, ROWS_JSONL, THROUGHPUT_JSONL],
            METRICS_JSON: [source_label, ROWS_JSONL, CURVES_JSONL, METRICS_JSON],
            STATISTICAL_TESTS_JSON: [source_label, ROWS_JSONL, STATISTICAL_TESTS_JSON],
            DASHBOARD_JSON: [
                source_label,
                ROWS_JSONL,
                CURVES_JSONL,
                THROUGHPUT_JSONL,
                METRICS_JSON,
                STATISTICAL_TESTS_JSON,
                DASHBOARD_JSON,
            ],
        },
    }


def availability_summary(payload: Any) -> dict[str, int]:
    summary: dict[str, int] = {}

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            availability = value.get("availability")
            if isinstance(availability, str):
                summary[availability] = summary.get(availability, 0) + 1
            objective_availability = value.get("objective_availability")
            if isinstance(objective_availability, str):
                summary[objective_availability] = summary.get(objective_availability, 0) + 1
            for child in value.values():
                visit(child)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for child in value:
                visit(child)

    visit(payload)
    return summary


def _dimension_section(name: str, payload: Any) -> dict[str, Any]:
    return {
        "name": name,
        "source_artifact": METRICS_JSON,
        "metrics": list(_flatten_metric_entries(payload, prefix=name, source_artifact=METRICS_JSON)),
    }


def _statistical_section(payload: Any) -> dict[str, Any]:
    return {
        "name": "statistical_validity",
        "source_artifact": STATISTICAL_TESTS_JSON,
        "metrics": list(
            _flatten_metric_entries(
                payload,
                prefix="statistical_validity",
                source_artifact=STATISTICAL_TESTS_JSON,
            )
        ),
    }


def _flatten_metric_entries(
    payload: Any,
    *,
    prefix: str,
    source_artifact: str,
) -> Iterable[dict[str, Any]]:
    if isinstance(payload, Mapping):
        if "availability" in payload:
            yield {
                "schema_version": ARTIFACT_SCHEMA_VERSION,
                "path": prefix,
                "availability": payload.get("availability"),
                "value": payload.get("value"),
                "unit": payload.get("unit"),
                "sample_count": payload.get("sample_count"),
                "required": payload.get("required"),
                "actual": payload.get("actual"),
                "reason": payload.get("reason"),
                "source": payload.get("source"),
                "source_artifact": source_artifact,
                "provenance": payload.get("provenance")
                or ["run-telemetry.pb", ROWS_JSONL, source_artifact],
            }
            return
        for key, value in payload.items():
            child_prefix = f"{prefix}.{key}"
            yield from _flatten_metric_entries(value, prefix=child_prefix, source_artifact=source_artifact)
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        for index, value in enumerate(payload):
            yield from _flatten_metric_entries(value, prefix=f"{prefix}[{index}]", source_artifact=source_artifact)


def _display_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, Mapping) or isinstance(value, list):
        return "`complex`"
    return str(value)


def _write_json(path: str | Path, payload: Any) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def _read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit(path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return "unknown"
    return result.stdout.strip() or "unknown"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish canonical telemetry metric artifacts.")
    parser.add_argument("telemetry_json", nargs="+", help="Canonical telemetry JSON projection files.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--reference", action="append", default=[], help="instance_id=objective")
    parser.add_argument("--target", action="append", default=[], help="instance_id=objective")
    args = parser.parse_args(argv)

    payloads = [_read_json(path) for path in args.telemetry_json]
    result = publish_telemetry_artifacts(
        payloads,
        args.output_dir,
        references=_parse_key_values(args.reference),
        targets=_parse_key_values(args.target),
    )
    print(json.dumps(result["manifest"], indent=2, ensure_ascii=True, sort_keys=True))
    return 0


def _parse_key_values(values: Sequence[str]) -> dict[str, float]:
    parsed: dict[str, float] = {}
    for value in values:
        key, raw = value.split("=", 1)
        parsed[key] = float(raw)
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
