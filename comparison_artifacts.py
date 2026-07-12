from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping

from benchmarks.artifact_io import checksum_json, read_json, read_jsonl, sha256_file, write_json, write_jsonl
from benchmarks.comparison_protocol import ComparisonProtocol, get_index_profile


ARTIFACT_SCHEMA_VERSION = 1
MANIFEST = "manifest.json"
PROTOCOL = "protocol.json"
ROWS = "rows.jsonl"
CURVES = "incumbent_curves.jsonl"
TELEMETRY = "telemetry.jsonl"
DIAGNOSTICS = "diagnostics.jsonl"

ArtifactRole = Literal["baseline", "challenger"]


@dataclass(frozen=True)
class RunArtifact:
    root: Path
    manifest: dict[str, Any]
    protocol: dict[str, Any]
    rows: list[dict[str, Any]]
    curves: list[dict[str, Any]]
    telemetry: list[dict[str, Any]]
    diagnostics: list[dict[str, Any]]


def publish_run_artifact(
    rows: Iterable[Mapping[str, Any]],
    output_dir: str | Path,
    *,
    protocol: ComparisonProtocol,
    role: ArtifactRole,
    provenance: Mapping[str, Any],
    experiment_mode: str = "implementation_comparison",
    experimental_variables: Iterable[str] = ("optagent_commit", "wheel_sha256"),
    created_at: str | None = None,
) -> dict[str, Any]:
    out = Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"run artifact output directory is not empty: {out}")

    materialized = [dict(row) for row in rows]
    _validate_matrix(materialized, protocol)
    normalized_rows: list[dict[str, Any]] = []
    curves: list[dict[str, Any]] = []
    telemetry_rows: list[dict[str, Any]] = []
    diagnostics_rows: list[dict[str, Any]] = []
    for row in materialized:
        coordinate = _coordinate(row)
        telemetry = row.get("telemetry")
        if not isinstance(telemetry, Mapping):
            raise ValueError(f"canonical telemetry is missing for {coordinate}")
        telemetry_payload = dict(telemetry)
        telemetry_complete = _validate_telemetry(telemetry_payload, coordinate)
        row_curves, curve_monotonic = _incumbent_curve(telemetry_payload, row, coordinate)
        normalized = dict(row)
        normalized["coordinate"] = coordinate
        normalized["curve_complete"] = telemetry_complete and curve_monotonic and bool(row_curves)
        normalized_rows.append(normalized)
        curves.extend(row_curves)
        telemetry_rows.append({"coordinate": coordinate, **telemetry_payload})
        diagnostics = row.get("diagnostics")
        diagnostics_rows.append(
            {"coordinate": coordinate, **(dict(diagnostics) if isinstance(diagnostics, Mapping) else {})}
        )

    out.mkdir(parents=True, exist_ok=True)
    index_policy = get_index_profile(protocol.index_profile_id)
    protocol_payload = {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "protocol": protocol.protocol_snapshot(),
        "protocol_checksum": protocol.checksum,
        "index_profile": index_policy.protocol_snapshot(),
        "index_profile_checksum": index_policy.checksum,
    }
    write_json(out / PROTOCOL, protocol_payload)
    write_jsonl(out / ROWS, normalized_rows)
    write_jsonl(out / CURVES, curves)
    write_jsonl(out / TELEMETRY, telemetry_rows)
    write_jsonl(out / DIAGNOSTICS, diagnostics_rows)
    artifact_names = (PROTOCOL, ROWS, CURVES, TELEMETRY, DIAGNOSTICS)
    manifest = {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "kind": "optagent_strategy_comparison",
        "status": "complete",
        "role": role,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "protocol_id": protocol.protocol_id,
        "protocol_checksum": protocol.checksum,
        "index_profile_id": protocol.index_profile_id,
        "index_profile_checksum": index_policy.checksum,
        "experiment_mode": experiment_mode,
        "experimental_variables": sorted(set(experimental_variables)),
        "provenance": dict(provenance),
        "row_count": len(normalized_rows),
        "curve_count": len(curves),
        "coordinates": sorted(row["coordinate"] for row in normalized_rows),
        "platforms": sorted({str(row.get("platform") or "") for row in normalized_rows}),
        "instance_checksums": _instance_checksums(telemetry_rows),
        "artifacts": {
            name: {"sha256": sha256_file(out / name), "bytes": (out / name).stat().st_size} for name in artifact_names
        },
    }
    write_json(out / MANIFEST, manifest)
    return {"output_dir": str(out), "manifest": manifest}


def load_run_artifact(path: str | Path) -> RunArtifact:
    root = Path(path)
    manifest = read_json(root / MANIFEST)
    if manifest.get("kind") != "optagent_strategy_comparison":
        raise ValueError("unsupported run artifact kind")
    artifacts = dict(manifest.get("artifacts") or {})
    required = {PROTOCOL, ROWS, CURVES, TELEMETRY, DIAGNOSTICS}
    if set(artifacts) != required:
        raise ValueError("run artifact manifest does not declare the required evidence set")
    for name, entry in artifacts.items():
        if sha256_file(root / name) != entry.get("sha256"):
            raise ValueError(f"artifact checksum mismatch: {name}")
    protocol = read_json(root / PROTOCOL)
    if protocol.get("protocol_checksum") != manifest.get("protocol_checksum"):
        raise ValueError("protocol checksum mismatch")
    if checksum_json(protocol.get("protocol")) != protocol.get("protocol_checksum"):
        raise ValueError("protocol snapshot checksum mismatch")
    if checksum_json(protocol.get("index_profile")) != protocol.get("index_profile_checksum"):
        raise ValueError("index profile snapshot checksum mismatch")
    if protocol.get("index_profile_checksum") != manifest.get("index_profile_checksum"):
        raise ValueError("index profile checksum mismatch")
    rows = read_jsonl(root / ROWS)
    curves = read_jsonl(root / CURVES)
    telemetry = read_jsonl(root / TELEMETRY)
    diagnostics = read_jsonl(root / DIAGNOSTICS)
    if len(rows) != int(manifest.get("row_count", -1)):
        raise ValueError("run row count mismatch")
    if len(curves) != int(manifest.get("curve_count", -1)):
        raise ValueError("run curve count mismatch")
    return RunArtifact(root, manifest, protocol, rows, curves, telemetry, diagnostics)


def _validate_matrix(rows: list[dict[str, Any]], protocol: ComparisonProtocol) -> None:
    expected = {
        _coordinate_values(profile.family, profile.model_style, case_id, seed)
        for profile in protocol.profiles
        for case_id in profile.case_ids
        for seed in protocol.seeds
    }
    actual = {_coordinate(row) for row in rows}
    if len(actual) != len(rows):
        raise ValueError("run artifact contains duplicate coordinates")
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ValueError(f"comparison matrix mismatch; missing={missing}, unexpected={unexpected}")
    for row in rows:
        if row.get("strategy") != protocol.strategy or row.get("solve_route") != protocol.solve_route:
            raise ValueError(f"comparison route mismatch for {_coordinate(row)}")
        budget = row.get("effective_budget")
        expected_budget = {
            "max_iterations": protocol.max_iterations,
            "time_limit_s": protocol.wall_time_s,
            "population_size": protocol.population_size,
            "trace_limit": protocol.trace_limit,
            "thread_count": protocol.thread_count,
        }
        if not isinstance(budget, Mapping) or any(budget.get(key) != value for key, value in expected_budget.items()):
            raise ValueError(f"protocol budget mismatch for {_coordinate(row)}")
        if row.get("thread_count") != protocol.thread_count:
            raise ValueError(f"thread count mismatch for {_coordinate(row)}")
        if protocol.kind != "smoke" and row.get("platform") != protocol.performance_platform:
            raise ValueError(f"performance platform mismatch for {_coordinate(row)}")


def _validate_telemetry(telemetry: dict[str, Any], coordinate: str) -> bool:
    for block in ("schema", "identity", "instance", "budget", "outcome", "effort", "progress"):
        expected_type = list if block == "progress" else Mapping
        if not isinstance(telemetry.get(block), expected_type):
            raise ValueError(f"canonical telemetry block {block} is missing for {coordinate}")
    schema = dict(telemetry["schema"])
    if int(schema.get("schema_version") or 0) != 1:
        raise ValueError(f"unsupported canonical telemetry schema for {coordinate}")
    overflow = telemetry.get("trace_overflow")
    if not isinstance(overflow, Mapping):
        return False
    required_overflow_fields = {
        "trace_truncated",
        "trace_event_limit",
        "emitted_event_count",
        "omitted_incumbent_events",
        "checkpoint_policy",
    }
    if not required_overflow_fields.issubset(overflow):
        return False
    try:
        omitted_incumbents = int(overflow.get("omitted_incumbent_events") or 0)
    except (TypeError, ValueError):
        return False
    return not bool(overflow.get("trace_truncated")) and omitted_incumbents == 0


def _incumbent_curve(
    telemetry: dict[str, Any], row: dict[str, Any], coordinate: str
) -> tuple[list[dict[str, Any]], bool]:
    reference = _number(row.get("reference_objective"))
    events = []
    monotonic = True
    previous_objective: float | None = None
    sense = str(dict(telemetry.get("outcome") or {}).get("objective_sense") or "minimize")
    for event in telemetry.get("progress", []):
        if not isinstance(event, Mapping) or not bool(event.get("feasible")):
            continue
        objective = _telemetry_number(event.get("objective_value"))
        elapsed = _number(event.get("elapsed_s"))
        if objective is None or elapsed is None:
            continue
        worsened = previous_objective is not None and (
            objective > previous_objective + 1e-12 if sense != "maximize" else objective < previous_objective - 1e-12
        )
        if bool(event.get("improved_best")) and worsened:
            monotonic = False
            continue
        improved = previous_objective is None or (
            objective < previous_objective - 1e-12 if sense != "maximize" else objective > previous_objective + 1e-12
        )
        if not improved:
            continue
        previous_objective = objective
        events.append(
            {
                "coordinate": coordinate,
                "elapsed_s": elapsed,
                "objective": objective,
                "gap_rel": _reference_gap(objective, reference, sense),
                "evaluated_candidates": _telemetry_integer(event.get("evaluated_candidates")),
            }
        )
    outcome = telemetry.get("outcome")
    effort = telemetry.get("effort")
    final_objective = _telemetry_number(outcome.get("objective_value")) if isinstance(outcome, Mapping) else None
    final_elapsed = _telemetry_number(effort.get("wall_time_s")) if isinstance(effort, Mapping) else None
    final_candidates = _telemetry_integer(effort.get("evaluated_candidates")) if isinstance(effort, Mapping) else None
    final_feasible = bool(outcome.get("feasible")) if isinstance(outcome, Mapping) else False
    final_improved = previous_objective is None or (
        final_objective is not None
        and (
            final_objective < previous_objective - 1e-12
            if sense != "maximize"
            else final_objective > previous_objective + 1e-12
        )
    )
    if final_feasible and final_objective is not None and final_elapsed is not None and final_improved:
        events.append(
            {
                "coordinate": coordinate,
                "elapsed_s": final_elapsed,
                "objective": final_objective,
                "gap_rel": _reference_gap(final_objective, reference, sense),
                "evaluated_candidates": final_candidates,
            }
        )
    return events, monotonic


def _coordinate(row: Mapping[str, Any]) -> str:
    return _coordinate_values(
        str(row.get("family") or ""),
        str(row.get("model_style") or ""),
        str(row.get("benchmark_id") or ""),
        int(row.get("seed") or 0),
    )


def _coordinate_values(family: str, model_style: str, case_id: str, seed: int) -> str:
    return f"{family}|{model_style}|{case_id}|seed={seed}"


def _instance_checksums(telemetry_rows: list[dict[str, Any]]) -> dict[str, str]:
    checksums = {}
    for telemetry in telemetry_rows:
        instance = telemetry.get("instance")
        if isinstance(instance, Mapping) and instance.get("id") and instance.get("checksum"):
            checksums[str(instance["id"])] = str(instance["checksum"])
    return dict(sorted(checksums.items()))


def _telemetry_number(value: Any) -> float | None:
    if isinstance(value, Mapping):
        return _number(value.get("number_value", value.get("integer_value")))
    return _number(value)


def _telemetry_integer(value: Any) -> int | None:
    number = _telemetry_number(value)
    return int(number) if number is not None else None


def _reference_gap(objective: float, reference: float | None, sense: str) -> float | None:
    if reference is None:
        return None
    denominator = max(abs(reference), 1e-12)
    raw = (reference - objective) if sense == "maximize" else (objective - reference)
    return max(0.0, raw / denominator)


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
