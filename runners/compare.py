from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from benchmarks.runners.bootstrap import prefer_local_development_paths
from benchmarks.runners.common import metadata_highlights, normalize_result_row


RowKey = tuple[str, str, str, str, str]


def compare_run_dirs(baseline_dir: str | Path, candidate_dir: str | Path) -> dict[str, Any]:
    baseline_path = Path(baseline_dir)
    candidate_path = Path(candidate_dir)
    baseline_rows = _load_rows(baseline_path)
    candidate_rows = _load_rows(candidate_path)
    baseline_by_key = {_row_key(row): row for row in baseline_rows}
    candidate_by_key = {_row_key(row): row for row in candidate_rows}
    keys = sorted(set(baseline_by_key) | set(candidate_by_key))

    comparisons: list[dict[str, Any]] = []
    objective_improvements = 0
    feasible_improvements = 0
    regressions = 0
    for key in keys:
        baseline = baseline_by_key.get(key)
        candidate = candidate_by_key.get(key)
        entry = _compare_row(key, baseline, candidate)
        comparisons.append(entry)
        if entry.get("objective_delta") is not None and entry["objective_delta"] < 0:
            objective_improvements += 1
        if baseline is not None and candidate is not None:
            if baseline.get("feasible") is not True and candidate.get("feasible") is True:
                feasible_improvements += 1
            if baseline.get("feasible") is True and candidate.get("feasible") is not True:
                regressions += 1
            elif entry.get("objective_delta") is not None and entry["objective_delta"] > 0:
                regressions += 1

    return {
        "baseline_dir": str(baseline_path),
        "candidate_dir": str(candidate_path),
        "baseline_rows": len(baseline_rows),
        "candidate_rows": len(candidate_rows),
        "matched_rows": sum(1 for item in comparisons if item["status"] == "matched"),
        "missing_in_baseline": sum(1 for item in comparisons if item["status"] == "missing_in_baseline"),
        "missing_in_candidate": sum(1 for item in comparisons if item["status"] == "missing_in_candidate"),
        "objective_improvements": objective_improvements,
        "feasible_improvements": feasible_improvements,
        "regressions": regressions,
        "family_summary": _family_summary(comparisons),
        "candidate_reference_summary": _reference_summary(candidate_rows),
        "rows": comparisons,
    }


def render_markdown(comparison: dict[str, Any]) -> str:
    lines = [
        "# Benchmark Run Comparison",
        "",
        f"- Baseline: `{comparison['baseline_dir']}`",
        f"- Candidate: `{comparison['candidate_dir']}`",
        f"- Matched rows: {comparison['matched_rows']}",
        f"- Objective improvements: {comparison['objective_improvements']}",
        f"- Feasible improvements: {comparison['feasible_improvements']}",
        f"- Regressions: {comparison['regressions']}",
        "",
        "## By Family",
        "",
        "| Family | Matched | Objective improvements | Feasible improvements | Regressions | Strategy rows | Exact rows |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for family, row in sorted(comparison.get("family_summary", {}).items()):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{family}`",
                    str(row["matched_rows"]),
                    str(row["objective_improvements"]),
                    str(row["feasible_improvements"]),
                    str(row["regressions"]),
                    str(row["strategy_rows"]),
                    str(row["exact_baseline_rows"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Candidate Vs Reference",
            "",
            "| Family | Rows with reference | Feasible rows | Best gap | Mean gap | Strategy rows | Exact rows |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for family, row in sorted(comparison.get("candidate_reference_summary", {}).items()):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{family}`",
                    str(row["rows_with_reference"]),
                    str(row["feasible_rows"]),
                    _fmt(row.get("best_gap_rel")),
                    _fmt(row.get("mean_gap_rel")),
                    str(row["strategy_rows"]),
                    str(row["exact_baseline_rows"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| Case | Family | Strategy | Profile | Style | Kind | Status | Feasible | Objective Delta | Gap Delta | Seconds Delta | Diagnostics |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in comparison["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['benchmark_id']}`",
                    f"`{row['family']}`",
                    f"`{row['strategy']}`",
                    f"`{row['strategy_profile']}`",
                    f"`{row['model_style']}`",
                    f"`{row['kind']}`",
                    str(row["status"]),
                    _feasible_delta(row),
                    _fmt(row.get("objective_delta")),
                    _fmt(row.get("gap_rel_delta")),
                    _fmt(row.get("elapsed_seconds_delta")),
                    ", ".join(row.get("candidate_highlights") or []),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    prefer_local_development_paths()
    parser = argparse.ArgumentParser(description="Compare two OptAgent benchmark run directories.")
    parser.add_argument("baseline_dir")
    parser.add_argument("candidate_dir")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    comparison = compare_run_dirs(args.baseline_dir, args.candidate_dir)
    if args.format == "markdown":
        print(render_markdown(comparison), end="")
    else:
        print(json.dumps(comparison, indent=2, ensure_ascii=True, sort_keys=True))
    return 0


def _load_rows(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "results.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"benchmark results not found: {path}")
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(normalize_result_row(json.loads(line)))
    return rows


def _row_key(row: dict[str, Any]) -> RowKey:
    return (
        str(row.get("benchmark_id") or ""),
        str(row.get("strategy") or ""),
        str(row.get("strategy_profile") or ""),
        str(row.get("model_style") or ""),
        str(row.get("kind") or ""),
    )


def _compare_row(key: RowKey, baseline: dict[str, Any] | None, candidate: dict[str, Any] | None) -> dict[str, Any]:
    benchmark_id, strategy, strategy_profile, model_style, kind = key
    if baseline is None:
        status = "missing_in_baseline"
    elif candidate is None:
        status = "missing_in_candidate"
    else:
        status = "matched"
    return {
        "benchmark_id": benchmark_id,
        "family": str((candidate or baseline or {}).get("family") or ""),
        "strategy": strategy,
        "strategy_profile": strategy_profile,
        "model_style": model_style,
        "kind": kind,
        "status": status,
        "baseline_feasible": baseline.get("feasible") if baseline else None,
        "candidate_feasible": candidate.get("feasible") if candidate else None,
        "baseline_objective": baseline.get("objective") if baseline else None,
        "candidate_objective": candidate.get("objective") if candidate else None,
        "objective_delta": _delta(candidate, baseline, "objective"),
        "gap_rel_delta": _delta(candidate, baseline, "gap_rel"),
        "elapsed_seconds_delta": _delta(candidate, baseline, "elapsed_seconds"),
        "baseline_highlights": _row_highlights(baseline),
        "candidate_highlights": _row_highlights(candidate),
    }


def _family_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for row in rows:
        family = str(row.get("family") or "unknown")
        bucket = summary.setdefault(
            family,
            {
                "matched_rows": 0,
                "objective_improvements": 0,
                "feasible_improvements": 0,
                "regressions": 0,
                "strategy_rows": 0,
                "exact_baseline_rows": 0,
            },
        )
        if row.get("status") == "matched":
            bucket["matched_rows"] += 1
        if row.get("objective_delta") is not None and row["objective_delta"] < 0:
            bucket["objective_improvements"] += 1
        if row.get("baseline_feasible") is not True and row.get("candidate_feasible") is True:
            bucket["feasible_improvements"] += 1
        if row.get("baseline_feasible") is True and row.get("candidate_feasible") is not True:
            bucket["regressions"] += 1
        elif row.get("objective_delta") is not None and row["objective_delta"] > 0:
            bucket["regressions"] += 1
        if row.get("kind") == "exact_baseline":
            bucket["exact_baseline_rows"] += 1
        else:
            bucket["strategy_rows"] += 1
    return summary


def _reference_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for row in rows:
        family = str(row.get("family") or "unknown")
        bucket = summary.setdefault(
            family,
            {
                "rows_with_reference": 0,
                "feasible_rows": 0,
                "gap_rel_sum": 0.0,
                "best_gap_rel": None,
                "mean_gap_rel": None,
                "strategy_rows": 0,
                "exact_baseline_rows": 0,
            },
        )
        if row.get("kind") == "exact_baseline":
            bucket["exact_baseline_rows"] += 1
        else:
            bucket["strategy_rows"] += 1
        if row.get("feasible") is True:
            bucket["feasible_rows"] += 1
        gap_rel = row.get("gap_rel")
        if gap_rel is None:
            continue
        try:
            gap_value = float(gap_rel)
        except (TypeError, ValueError):
            continue
        bucket["rows_with_reference"] += 1
        bucket["gap_rel_sum"] += gap_value
        if bucket["best_gap_rel"] is None or gap_value < bucket["best_gap_rel"]:
            bucket["best_gap_rel"] = gap_value
    for bucket in summary.values():
        if bucket["rows_with_reference"]:
            bucket["mean_gap_rel"] = bucket["gap_rel_sum"] / bucket["rows_with_reference"]
        del bucket["gap_rel_sum"]
    return summary


def _row_highlights(row: dict[str, Any] | None) -> list[str]:
    if row is None:
        return []
    metadata = row.get("metadata")
    return metadata_highlights(metadata) if isinstance(metadata, dict) else []


def _delta(candidate: dict[str, Any] | None, baseline: dict[str, Any] | None, key: str) -> float | None:
    if candidate is None or baseline is None:
        return None
    left = candidate.get(key)
    right = baseline.get(key)
    if left is None or right is None:
        return None
    try:
        return float(left) - float(right)
    except (TypeError, ValueError):
        return None


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return str(value)


def _feasible_delta(row: dict[str, Any]) -> str:
    baseline = row.get("baseline_feasible")
    candidate = row.get("candidate_feasible")
    if baseline is None and candidate is None:
        return ""
    return f"{baseline}->{candidate}"


if __name__ == "__main__":
    raise SystemExit(main())
