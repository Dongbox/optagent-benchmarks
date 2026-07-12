from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


REGISTRY_SCHEMA_VERSION = 1


def promote_comparison_baseline(
    comparison_dir: str | Path,
    registry_path: str | Path,
    *,
    approved_by: str,
) -> dict[str, Any]:
    comparison_root = Path(comparison_dir)
    manifest = _read_json(comparison_root / "comparison_manifest.json")
    for name, entry in dict(manifest.get("artifacts") or {}).items():
        if _sha256(comparison_root / name) != entry.get("sha256"):
            raise ValueError(f"comparison artifact checksum mismatch: {name}")
    score = _read_json(comparison_root / "score.json")
    if score.get("verdict") != "improved" or not bool(score.get("promotable")):
        raise ValueError("only an improved promotable comparison can update the baseline registry")
    candidate = dict(score.get("candidate") or {})
    provenance = dict(candidate.get("provenance") or {})
    protocol_id = str(score.get("protocol_id") or "")
    platform_name = str(provenance.get("platform") or "")
    if not protocol_id or not platform_name:
        raise ValueError("comparison is missing protocol or platform identity")

    path = Path(registry_path)
    registry = (
        _read_json(path)
        if path.exists()
        else {"registry_schema_version": REGISTRY_SCHEMA_VERSION, "active": {}, "history": []}
    )
    if registry.get("registry_schema_version") != REGISTRY_SCHEMA_VERSION:
        raise ValueError("unsupported baseline registry schema")
    key = f"{protocol_id}|{platform_name}"
    active = dict(registry.get("active") or {})
    previous = active.get(key)
    comparison_checksum = _sha256(comparison_root / "comparison_manifest.json")
    candidate_manifest_path = Path(str(candidate.get("path") or "")) / "manifest.json"
    candidate_artifact_checksum = _sha256(candidate_manifest_path)
    record_payload = {
        "protocol_id": protocol_id,
        "platform": platform_name,
        "scoring_profile_id": score.get("scoring_profile_id"),
        "protocol_checksum": score.get("protocol_checksum"),
        "scoring_profile_checksum": score.get("scoring_profile_checksum"),
        "candidate_provenance": provenance,
        "candidate_artifact_checksum": candidate_artifact_checksum,
        "comparison_manifest_checksum": comparison_checksum,
        "comparison_path": str(comparison_root.resolve()),
        "approved_by": approved_by,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "previous_baseline_id": previous.get("baseline_id") if isinstance(previous, dict) else None,
    }
    baseline_id = _json_checksum(record_payload)
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
    path.write_text(json.dumps(updated, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    return {"active": record, "history": history, "registry_path": str(path)}


def _read_json(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json_checksum(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
