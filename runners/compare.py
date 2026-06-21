from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from benchmarks.runners.bootstrap import prefer_local_development_paths
from benchmarks.runners.common import REPO_ROOT, append_jsonl, metadata_highlights, normalize_result_row, utc_timestamp
from benchmarks.runners.telemetry import BENCHMARK_SCHEMA_VERSION


RowKey = tuple[str, str, str, str, str, str]
DEFAULT_REPORTS_DIR = REPO_ROOT / "docs" / "evals" / "benchmark-suite" / "reports"
BASE_SCHEMA_REQUIRED_FIELDS = (
    "benchmark_schema_version",
    "benchmark_id",
    "family",
    "strategy",
    "strategy_profile",
    "model_style",
    "kind",
    "status",
    "feasible",
    "runtime_s",
)
THROUGHPUT_DELTA_FIELDS = (
    "moves_attempted_per_s",
    "evaluations_per_s",
    "delta_evaluations_per_s",
    "full_evaluations_per_s",
    "repairs_attempted_per_s",
    "repairs_succeeded_per_s",
)


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
        "quality_regressions": sum(1 for item in comparisons if _is_quality_regression(item)),
        "time_to_best_improvements": sum(
            1
            for item in comparisons
            if item.get("time_to_best_seconds_delta") is not None
            and item["time_to_best_seconds_delta"] < 0
        ),
        "time_to_best_regressions": sum(
            1
            for item in comparisons
            if item.get("time_to_best_seconds_delta") is not None
            and item["time_to_best_seconds_delta"] > 0
        ),
        "family_summary": _family_summary(comparisons),
        "candidate_reference_summary": _reference_summary(candidate_rows),
        "gates": _comparison_gates(
            baseline_rows=baseline_rows,
            candidate_rows=candidate_rows,
            comparisons=comparisons,
        ),
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
        f"- Gate status: `{comparison.get('gates', {}).get('overall_status', '')}`",
        "",
        "## Gate Summary",
        "",
        "| Gate | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for gate_name, gate in sorted(comparison.get("gates", {}).get("checks", {}).items()):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{gate_name}`",
                    f"`{gate.get('status')}`",
                    _gate_detail(gate),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## By Family",
            "",
            "| Family | Matched | Objective improvements | Feasible improvements | Quality regressions | Time-to-best improvements | Time-to-best regressions | Throughput regressions | Strategy rows | Exact rows |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for family, row in sorted(comparison.get("family_summary", {}).items()):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{family}`",
                    str(row["matched_rows"]),
                    str(row["objective_improvements"]),
                    str(row["feasible_improvements"]),
                    str(row["quality_regressions"]),
                    str(row["time_to_best_improvements"]),
                    str(row["time_to_best_regressions"]),
                    str(row["throughput_regressions"]),
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
            "| Case | Family | Strategy | Profile | Style | Kind | Threads | Status | Feasible | Objective Delta | Gap Delta | Seconds Delta | Time-to-best Delta | Improvement/s Delta | Eval/s Delta | Delta Eval/s Delta | Repairs/s Delta | Diagnostics |",
            "| --- | --- | --- | --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
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
                    f"`{row['thread_count']}`",
                    str(row["status"]),
                    _feasible_delta(row),
                    _fmt(row.get("objective_delta")),
                    _fmt(row.get("gap_rel_delta")),
                    _fmt(row.get("elapsed_seconds_delta")),
                    _fmt(row.get("time_to_best_seconds_delta")),
                    _fmt(row.get("improvement_per_second_delta")),
                    _fmt(row.get("evaluations_per_s_delta")),
                    _fmt(row.get("delta_evaluations_per_s_delta")),
                    _fmt(row.get("repairs_attempted_per_s_delta")),
                    ", ".join(row.get("candidate_highlights") or []),
                ]
            )
            + " |"
    )
    return "\n".join(lines) + "\n"


def write_curated_report(
    comparison: dict[str, Any],
    *,
    reports_dir: str | Path = DEFAULT_REPORTS_DIR,
    report_id: str | None = None,
    baseline_commit: str | None = None,
    candidate_commit: str | None = None,
    decision: str = "needs_follow_up",
    follow_up_actions: list[str] | None = None,
) -> dict[str, Any]:
    report_id = report_id or f"comparison-{utc_timestamp()}"
    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    report_path = reports_path / f"{report_id}.md"
    ledger_path = reports_path / "ledger.jsonl"
    entry = {
        "report_id": report_id,
        "created_at_utc": utc_timestamp(),
        "baseline_run_id": Path(str(comparison["baseline_dir"])).name,
        "candidate_run_id": Path(str(comparison["candidate_dir"])).name,
        "baseline_dir": comparison["baseline_dir"],
        "candidate_dir": comparison["candidate_dir"],
        "baseline_commit": baseline_commit,
        "candidate_commit": candidate_commit,
        "decision": decision,
        "follow_up_actions": follow_up_actions or [],
        "gate_status": comparison.get("gates", {}).get("overall_status"),
        "report_path": str(report_path),
    }
    report_path.write_text(_render_curated_report(comparison, entry), encoding="utf-8")
    append_jsonl(ledger_path, [entry])
    return {
        "report_path": str(report_path),
        "ledger_path": str(ledger_path),
        "ledger_entry": entry,
    }


def main() -> int:
    prefer_local_development_paths()
    parser = argparse.ArgumentParser(description="Compare two OptAgent benchmark run directories.")
    parser.add_argument("baseline_dir")
    parser.add_argument("candidate_dir")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--report-id", help="Write a curated report and ledger entry using this stable id.")
    parser.add_argument("--reports-dir", default=str(DEFAULT_REPORTS_DIR), help="Directory for curated comparison reports.")
    parser.add_argument("--baseline-commit", help="Commit identifier for the accepted baseline run.")
    parser.add_argument("--candidate-commit", help="Commit identifier for the candidate run.")
    parser.add_argument(
        "--decision",
        choices=("accepted", "rejected", "needs_follow_up"),
        default="needs_follow_up",
        help="Decision recorded in the curated benchmark ledger when --report-id is set.",
    )
    parser.add_argument("--follow-up", action="append", dest="follow_ups", default=[], help="Follow-up action recorded in the curated ledger. Repeat as needed.")
    args = parser.parse_args()

    comparison = compare_run_dirs(args.baseline_dir, args.candidate_dir)
    if args.report_id:
        comparison["curated_report"] = write_curated_report(
            comparison,
            reports_dir=args.reports_dir,
            report_id=args.report_id,
            baseline_commit=args.baseline_commit,
            candidate_commit=args.candidate_commit,
            decision=args.decision,
            follow_up_actions=list(args.follow_ups),
        )
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
        str(row.get("thread_count") or 1),
    )


def _compare_row(key: RowKey, baseline: dict[str, Any] | None, candidate: dict[str, Any] | None) -> dict[str, Any]:
    benchmark_id, strategy, strategy_profile, model_style, kind, thread_count = key
    if baseline is None:
        status = "missing_in_baseline"
    elif candidate is None:
        status = "missing_in_candidate"
    else:
        status = "matched"
    throughput_deltas = _throughput_deltas(candidate, baseline)
    return {
        "benchmark_id": benchmark_id,
        "family": str((candidate or baseline or {}).get("family") or ""),
        "strategy": strategy,
        "strategy_profile": strategy_profile,
        "model_style": model_style,
        "kind": kind,
        "thread_count": thread_count,
        "status": status,
        "baseline_feasible": baseline.get("feasible") if baseline else None,
        "candidate_feasible": candidate.get("feasible") if candidate else None,
        "baseline_objective": baseline.get("objective") if baseline else None,
        "candidate_objective": candidate.get("objective") if candidate else None,
        "objective_delta": _delta(candidate, baseline, "objective"),
        "gap_rel_delta": _delta(candidate, baseline, "gap_rel"),
        "elapsed_seconds_delta": _delta(candidate, baseline, "elapsed_seconds"),
        "time_to_first_feasible_seconds_delta": _delta(candidate, baseline, "time_to_first_feasible_seconds"),
        "time_to_best_seconds_delta": _delta(candidate, baseline, "time_to_best_seconds"),
        "improvement_per_second_delta": _delta(candidate, baseline, "improvement_per_second"),
        "throughput_deltas": throughput_deltas,
        **throughput_deltas,
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
                "quality_regressions": 0,
                "time_to_best_improvements": 0,
                "time_to_best_regressions": 0,
                "throughput_regressions": 0,
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
        if _is_quality_regression(row):
            bucket["quality_regressions"] += 1
        time_to_best_delta = row.get("time_to_best_seconds_delta")
        if time_to_best_delta is not None and time_to_best_delta < 0:
            bucket["time_to_best_improvements"] += 1
        elif time_to_best_delta is not None and time_to_best_delta > 0:
            bucket["time_to_best_regressions"] += 1
        if _has_throughput_regression(row):
            bucket["throughput_regressions"] += 1
        if row.get("kind") == "exact_baseline":
            bucket["exact_baseline_rows"] += 1
        else:
            bucket["strategy_rows"] += 1
    return summary


def _comparison_gates(
    *,
    baseline_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> dict[str, Any]:
    checks = {
        "schema_completeness": _schema_gate(baseline_rows, candidate_rows),
        "feasible_rate": _feasible_rate_gate(comparisons),
        "quality": _quality_gate(comparisons),
        "throughput": _throughput_gate(comparisons),
    }
    return {
        "overall_status": "pass" if all(item["status"] == "pass" for item in checks.values()) else "fail",
        "checks": checks,
    }


def _schema_gate(
    baseline_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline_issues = _schema_issues(baseline_rows)
    candidate_issues = _schema_issues(candidate_rows)
    return {
        "status": "pass" if not baseline_issues and not candidate_issues else "fail",
        "expected_schema_version": BENCHMARK_SCHEMA_VERSION,
        "baseline_issue_count": len(baseline_issues),
        "candidate_issue_count": len(candidate_issues),
        "baseline_issues": baseline_issues,
        "candidate_issues": candidate_issues,
    }


def _schema_issues(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in rows:
        missing = [field for field in BASE_SCHEMA_REQUIRED_FIELDS if row.get(field) is None]
        if row.get("feasible") is True and row.get("best_cost") is None:
            missing.append("best_cost")
        schema_version = row.get("benchmark_schema_version")
        if schema_version != BENCHMARK_SCHEMA_VERSION:
            missing.append("benchmark_schema_version=2")
        if missing:
            issues.append(
                {
                    "row_key": _row_key_dict(row),
                    "missing_or_invalid_fields": sorted(set(missing)),
                }
            )
    return issues


def _feasible_rate_gate(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    by_family: dict[str, dict[str, int]] = {}
    for row in comparisons:
        if row.get("status") != "matched":
            continue
        family = str(row.get("family") or "unknown")
        bucket = by_family.setdefault(
            family,
            {
                "matched_rows": 0,
                "baseline_feasible_rows": 0,
                "candidate_feasible_rows": 0,
            },
        )
        bucket["matched_rows"] += 1
        if row.get("baseline_feasible") is True:
            bucket["baseline_feasible_rows"] += 1
        if row.get("candidate_feasible") is True:
            bucket["candidate_feasible_rows"] += 1
    regressions = []
    for family, bucket in sorted(by_family.items()):
        matched = bucket["matched_rows"]
        baseline_rate = bucket["baseline_feasible_rows"] / matched if matched else 0.0
        candidate_rate = bucket["candidate_feasible_rows"] / matched if matched else 0.0
        bucket["baseline_feasible_rate"] = baseline_rate
        bucket["candidate_feasible_rate"] = candidate_rate
        if candidate_rate < baseline_rate:
            regressions.append({"family": family, **bucket})
    return {
        "status": "pass" if not regressions else "fail",
        "family_regressions": regressions,
    }


def _quality_gate(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    regressions = [row for row in comparisons if _is_quality_regression(row)]
    return {
        "status": "pass" if not regressions else "fail",
        "regression_count": len(regressions),
        "regressions": [_row_key_dict(row) for row in regressions],
    }


def _throughput_gate(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    regressions = [row for row in comparisons if _has_throughput_regression(row)]
    return {
        "status": "pass" if not regressions else "fail",
        "regression_count": len(regressions),
        "regressions": [_row_key_dict(row) for row in regressions],
    }


def _is_quality_regression(row: dict[str, Any]) -> bool:
    if row.get("status") != "matched":
        return False
    gap_delta = row.get("gap_rel_delta")
    if gap_delta is not None:
        return gap_delta > 0
    objective_delta = row.get("objective_delta")
    return objective_delta is not None and objective_delta > 0


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


def _throughput_deltas(candidate: dict[str, Any] | None, baseline: dict[str, Any] | None) -> dict[str, float | None]:
    return {f"{field}_delta": _delta(candidate, baseline, field) for field in THROUGHPUT_DELTA_FIELDS}


def _has_throughput_regression(row: dict[str, Any]) -> bool:
    for field in THROUGHPUT_DELTA_FIELDS:
        value = row.get(f"{field}_delta")
        if value is not None and value < 0:
            return True
    return False


def _row_key_dict(row: dict[str, Any]) -> dict[str, str]:
    return {
        "benchmark_id": str(row.get("benchmark_id") or ""),
        "family": str(row.get("family") or ""),
        "strategy": str(row.get("strategy") or ""),
        "strategy_profile": str(row.get("strategy_profile") or ""),
        "model_style": str(row.get("model_style") or ""),
        "kind": str(row.get("kind") or ""),
    }


def _render_curated_report(comparison: dict[str, Any], ledger_entry: dict[str, Any]) -> str:
    follow_ups = ledger_entry.get("follow_up_actions") or []
    lines = [
        "# Curated Benchmark Comparison",
        "",
        "## Ledger Metadata",
        "",
        f"- Report id: `{ledger_entry['report_id']}`",
        f"- Baseline run id: `{ledger_entry['baseline_run_id']}`",
        f"- Candidate run id: `{ledger_entry['candidate_run_id']}`",
        f"- Baseline commit: `{ledger_entry.get('baseline_commit') or ''}`",
        f"- Candidate commit: `{ledger_entry.get('candidate_commit') or ''}`",
        f"- Decision: `{ledger_entry['decision']}`",
        f"- Gate status: `{ledger_entry.get('gate_status') or ''}`",
        "",
        "## Follow-Up Actions",
        "",
    ]
    if follow_ups:
        lines.extend(f"- {item}" for item in follow_ups)
    else:
        lines.append("- None recorded.")
    lines.extend(["", render_markdown(comparison).rstrip(), ""])
    return "\n".join(lines)


def _gate_detail(gate: dict[str, Any]) -> str:
    if "baseline_issue_count" in gate:
        return (
            f"baseline issues={gate.get('baseline_issue_count', 0)}, "
            f"candidate issues={gate.get('candidate_issue_count', 0)}"
        )
    if "family_regressions" in gate:
        return f"family regressions={len(gate.get('family_regressions') or [])}"
    if "regression_count" in gate:
        return f"regressions={gate.get('regression_count', 0)}"
    return ""


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
