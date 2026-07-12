from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from benchmarks.artifact_io import checksum_json, read_json, sha256_file, write_json
from benchmarks.comparison_artifacts import load_run_artifact


REGISTRY_SCHEMA_VERSION = 1


def promote_comparison_baseline(
    comparison_dir: str | Path,
    registry_path: str | Path,
    *,
    approved_by: str,
) -> dict[str, Any]:
    comparison_root = Path(comparison_dir)
    manifest = read_json(comparison_root / "comparison_manifest.json")
    artifacts = dict(manifest.get("artifacts") or {})
    required = {
        "paired_rows.jsonl",
        "dimension_metrics.json",
        "statistical_evidence.json",
        "delta_index.json",
        "feedback.md",
    }
    if set(artifacts) != required:
        raise ValueError("comparison manifest does not declare the required evidence set")
    for name, entry in artifacts.items():
        if sha256_file(comparison_root / name) != entry.get("sha256"):
            raise ValueError(f"comparison artifact checksum mismatch: {name}")
    index_value = read_json(comparison_root / "delta_index.json")
    if index_value.get("verdict") != "improved" or not bool(index_value.get("promotable")):
        raise ValueError("only an improved promotable comparison can update the baseline registry")
    challenger = dict(index_value.get("challenger") or {})
    provenance = dict(challenger.get("provenance") or {})
    protocol_id = str(index_value.get("protocol_id") or "")
    platform_name = str(provenance.get("platform") or "")
    if not protocol_id or not platform_name:
        raise ValueError("comparison is missing protocol or platform identity")

    path = Path(registry_path)
    registry = (
        read_json(path)
        if path.exists()
        else {"registry_schema_version": REGISTRY_SCHEMA_VERSION, "active": {}, "history": []}
    )
    if registry.get("registry_schema_version") != REGISTRY_SCHEMA_VERSION:
        raise ValueError("unsupported baseline registry schema")
    key = f"{protocol_id}|{platform_name}"
    active = dict(registry.get("active") or {})
    previous = active.get(key)
    comparison_checksum = sha256_file(comparison_root / "comparison_manifest.json")
    challenger_artifact = load_run_artifact(Path(str(challenger.get("path") or "")))
    challenger_manifest_path = challenger_artifact.root / "manifest.json"
    challenger_artifact_checksum = sha256_file(challenger_manifest_path)
    if challenger_artifact_checksum != challenger.get("manifest_checksum"):
        raise ValueError("challenger artifact changed after comparison")
    record_payload = {
        "protocol_id": protocol_id,
        "platform": platform_name,
        "index_profile_id": index_value.get("index_profile_id"),
        "protocol_checksum": index_value.get("protocol_checksum"),
        "index_profile_checksum": index_value.get("index_profile_checksum"),
        "challenger_provenance": provenance,
        "challenger_artifact_checksum": challenger_artifact_checksum,
        "comparison_manifest_checksum": comparison_checksum,
        "comparison_path": str(comparison_root.resolve()),
        "approved_by": approved_by,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "previous_baseline_id": previous.get("baseline_id") if isinstance(previous, dict) else None,
    }
    baseline_id = checksum_json(record_payload)
    record = {"baseline_id": baseline_id, **record_payload}
    history = list(registry.get("history") or [])
    if not any(item.get("baseline_id") == baseline_id for item in history if isinstance(item, dict)):
        history.append(record)
    active[key] = record
    updated = {
        "registry_schema_version": REGISTRY_SCHEMA_VERSION,
        "active": dict(sorted(active.items())),
        "history": history,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, updated)
    return {"active": record, "history": history, "registry_path": str(path)}
