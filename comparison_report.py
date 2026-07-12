from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from benchmarks.artifact_io import sha256_file, write_json, write_jsonl


COMPARISON_SCHEMA_VERSION = 1


def publish_comparison(
    output_dir: Path,
    result: dict[str, Any],
    pairs: Sequence[Mapping[str, Any]],
    dimensions: Mapping[str, Any],
    statistical: Mapping[str, Any],
) -> None:
    write_jsonl(output_dir / "paired_rows.jsonl", pairs)
    write_json(
        output_dir / "dimension_metrics.json",
        {"dimensions": dict(dimensions), "profiles": result.get("profiles", {})},
    )
    write_json(output_dir / "statistical_evidence.json", statistical)
    write_json(output_dir / "delta_index.json", result)
    (output_dir / "feedback.md").write_text(_render_feedback(result), encoding="utf-8")
    artifact_names = (
        "paired_rows.jsonl",
        "dimension_metrics.json",
        "statistical_evidence.json",
        "delta_index.json",
        "feedback.md",
    )
    manifest = {
        "comparison_schema_version": COMPARISON_SCHEMA_VERSION,
        "kind": "optagent_strategy_comparison",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verdict": result["verdict"],
        "protocol_id": result.get("protocol_id"),
        "artifacts": {
            name: {"sha256": sha256_file(output_dir / name), "bytes": (output_dir / name).stat().st_size}
            for name in artifact_names
        },
    }
    write_json(output_dir / "comparison_manifest.json", manifest)


def _render_feedback(result: Mapping[str, Any]) -> str:
    lines = [
        "# GA Strategy Comparison",
        "",
        f"- Verdict: `{result.get('verdict')}`",
        f"- Overall Delta Index: `{_display(result.get('overall_delta_index'))}`",
        f"- Promotable: `{str(bool(result.get('promotable'))).lower()}`",
        "",
        "## Dimensions",
        "",
        "| Dimension | Delta Index |",
        "| --- | ---: |",
    ]
    for name, value in dict(result.get("dimensions") or {}).items():
        lines.append(f"| {name} | {_display(value.get('index'))} |")
    lines.extend(["", "## Hard Gates", ""])
    for name, gate in dict(result.get("hard_gates") or {}).items():
        lines.append(f"- `{name}`: `{gate.get('status')}`")
    feedback = result.get("diagnostic_feedback")
    if isinstance(feedback, Mapping):
        lines.extend(["", "## Largest Quality Changes", ""])
        for row in feedback.get("largest_quality_improvements", [])[:3]:
            lines.append(f"- Improved `{row['coordinate']}` by `{_display(row['improvement'])}` gap units")
        for row in feedback.get("largest_quality_regressions", [])[:3]:
            if float(row.get("improvement") or 0.0) < 0:
                lines.append(f"- Regressed `{row['coordinate']}` by `{_display(-float(row['improvement']))}` gap units")
    reasons = result.get("compatibility_reasons")
    if reasons:
        lines.extend(["", "## Compatibility", ""])
        lines.extend(f"- {reason}" for reason in reasons)
    return "\n".join(lines).rstrip() + "\n"


def _display(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.3f}"
