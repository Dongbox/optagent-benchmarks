from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import benchmarks.telemetry_artifacts as telemetry_artifacts
from benchmarks.bootstrap import prefer_local_development_paths
from benchmarks.presentation.common import REPO_ROOT, normalize_result_row, utc_timestamp, write_json
from benchmarks.presentation.compare import compare_run_dirs


DEFAULT_DASHBOARD_ROOT = REPO_ROOT / "docs" / "evals" / "benchmark-suite" / "dashboards"
THROUGHPUT_FIELDS = (
    "moves_attempted_per_s",
    "evaluations_per_s",
    "delta_evaluations_per_s",
    "full_evaluations_per_s",
    "repairs_attempted_per_s",
    "repairs_succeeded_per_s",
)


def generate_dashboard(
    artifact_dir: str | Path,
    *,
    output_root: str | Path = DEFAULT_DASHBOARD_ROOT,
    dashboard_id: str | None = None,
) -> dict[str, Any]:
    """Generate dashboard files from published telemetry artifacts only."""

    artifact_path = Path(artifact_dir)
    published = telemetry_artifacts.load_published_artifacts(artifact_path)
    output_dir = Path(output_root) / (dashboard_id or f"dashboard-{utc_timestamp()}")
    output_dir.mkdir(parents=True, exist_ok=False)

    dashboard = dict(published["dashboard"])
    dashboard.update(
        {
            "dashboard_id": output_dir.name,
            "artifact_dir": str(artifact_path),
            "manifest": published["manifest"],
            "artifacts": {
                "manifest_json": str(output_dir / "manifest.json"),
                "dashboard_json": str(output_dir / "dashboard.json"),
                "dashboard_md": str(output_dir / "dashboard.md"),
            },
        }
    )
    write_json(output_dir / "manifest.json", published["manifest"])
    write_json(output_dir / "dashboard.json", dashboard)
    (output_dir / "dashboard.md").write_text(
        telemetry_artifacts.render_dashboard_markdown(dashboard),
        encoding="utf-8",
    )
    return {
        **dashboard,
        "output_dir": str(output_dir),
    }


def generate_legacy_results_dashboard(
    candidate_dir: str | Path,
    *,
    baseline_dir: str | Path | None = None,
    output_root: str | Path = DEFAULT_DASHBOARD_ROOT,
    dashboard_id: str | None = None,
) -> dict[str, Any]:
    """Legacy dashboard generator for old ``results.jsonl`` run directories."""

    candidate_path = Path(candidate_dir)
    baseline_path = Path(baseline_dir) if baseline_dir is not None else None
    output_dir = Path(output_root) / (dashboard_id or f"dashboard-{utc_timestamp()}")
    output_dir.mkdir(parents=True, exist_ok=False)

    candidate_rows = _load_rows(candidate_path)
    baseline_rows = _load_rows(baseline_path) if baseline_path is not None else []
    comparison = compare_run_dirs(baseline_path, candidate_path) if baseline_path is not None else None
    summary = {
        "dashboard_schema_version": 1,
        "dashboard_id": output_dir.name,
        "baseline_dir": str(baseline_path) if baseline_path is not None else None,
        "candidate_dir": str(candidate_path),
        "candidate": _run_summary(candidate_rows),
        "baseline": _run_summary(baseline_rows) if baseline_path is not None else None,
        "comparison": _comparison_summary(comparison) if comparison is not None else None,
        "artifacts": {
            "dashboard_json": str(output_dir / "dashboard.json"),
            "anytime_curves_json": str(output_dir / "anytime-curves.json"),
            "dashboard_md": str(output_dir / "dashboard.md"),
        },
    }
    anytime_curves = {
        "dashboard_schema_version": 1,
        "dashboard_id": output_dir.name,
        "baseline": _anytime_curve_entries(baseline_rows),
        "candidate": _anytime_curve_entries(candidate_rows),
    }

    write_json(output_dir / "dashboard.json", summary)
    write_json(output_dir / "anytime-curves.json", anytime_curves)
    (output_dir / "dashboard.md").write_text(
        render_dashboard_markdown(summary, anytime_curves),
        encoding="utf-8",
    )
    return {
        **summary,
        "output_dir": str(output_dir),
    }


def render_dashboard_markdown(
    dashboard: dict[str, Any],
    anytime_curves: dict[str, Any],
) -> str:
    candidate = dashboard["candidate"]
    lines = [
        "# OptAgent Benchmark Dashboard",
        "",
        f"- Dashboard id: `{dashboard['dashboard_id']}`",
        f"- Candidate: `{dashboard['candidate_dir']}`",
        f"- Baseline: `{dashboard.get('baseline_dir') or ''}`",
        "",
        "## Candidate By Family",
        "",
        "| Family | Rows | Feasible % | Mean gap % | Best gap % | Avg improvement/s | Eval/s | Moves/s | Repairs/s |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for family, row in sorted(candidate.get("family_summary", {}).items()):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{family}`",
                    _fmt(row.get("row_count")),
                    _fmt_pct(row.get("feasible_rate")),
                    _fmt_pct(row.get("mean_gap_rel")),
                    _fmt_pct(row.get("best_gap_rel")),
                    _fmt(row.get("avg_improvement_per_second")),
                    _fmt(row.get("avg_evaluations_per_s")),
                    _fmt(row.get("avg_moves_attempted_per_s")),
                    _fmt(row.get("avg_repairs_attempted_per_s")),
                ]
            )
            + " |"
        )
    comparison = dashboard.get("comparison")
    if comparison is not None:
        lines.extend(
            [
                "",
                "## Commit Comparison",
                "",
                f"- Gate status: `{comparison.get('gate_status') or ''}`",
                f"- Matched rows: {comparison.get('matched_rows')}",
                f"- Objective improvements: {comparison.get('objective_improvements')}",
                f"- Quality regressions: {comparison.get('quality_regressions')}",
                "",
                "| Family | Matched | Feasible improvements | Quality regressions | Throughput regressions |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for family, row in sorted(comparison.get("family_summary", {}).items()):
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{family}`",
                        _fmt(row.get("matched_rows")),
                        _fmt(row.get("feasible_improvements")),
                        _fmt(row.get("quality_regressions")),
                        _fmt(row.get("throughput_regressions")),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Anytime Curves",
            "",
            "| Run | Family | Case | Strategy | Profile | Style | Kind | Threads | Points |",
            "| --- | --- | --- | --- | --- | --- | --- | ---: | ---: |",
        ]
    )
    for run_name in ("baseline", "candidate"):
        for row in anytime_curves.get(run_name, []):
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{run_name}`",
                        f"`{row.get('family')}`",
                        f"`{row.get('benchmark_id')}`",
                        f"`{row.get('strategy')}`",
                        f"`{row.get('strategy_profile')}`",
                        f"`{row.get('model_style')}`",
                        f"`{row.get('kind')}`",
                        _fmt(row.get("thread_count")),
                        _fmt(len(row.get("points") or [])),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    prefer_local_development_paths()
    parser = argparse.ArgumentParser(description="Generate static OptAgent telemetry artifact dashboard.")
    parser.add_argument("artifact_dir")
    parser.add_argument("--output-root", default=str(DEFAULT_DASHBOARD_ROOT))
    parser.add_argument("--dashboard-id")
    args = parser.parse_args()

    dashboard = generate_dashboard(
        args.artifact_dir,
        output_root=args.output_root,
        dashboard_id=args.dashboard_id,
    )
    print(json.dumps(dashboard, indent=2, ensure_ascii=True, sort_keys=True))
    return 0


def _load_rows(run_dir: Path | None) -> list[dict[str, Any]]:
    if run_dir is None:
        return []
    path = run_dir / "results.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"benchmark results not found: {path}")
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(normalize_result_row(json.loads(line)))
    return rows


def _run_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "row_count": len(rows),
        "strategy_rows": sum(1 for row in rows if row.get("kind") == "strategy_run"),
        "exact_baseline_rows": sum(1 for row in rows if row.get("kind") == "exact_baseline"),
        "family_summary": _family_summary(rows),
    }


def _family_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for row in rows:
        family = str(row.get("family") or "unknown")
        bucket = summary.setdefault(
            family,
            {
                "row_count": 0,
                "feasible_rows": 0,
                "gap_values": [],
                "improvement_per_second_values": [],
                "moves_attempted_per_s_values": [],
                "evaluations_per_s_values": [],
                "repairs_attempted_per_s_values": [],
            },
        )
        bucket["row_count"] += 1
        if row.get("feasible") is True:
            bucket["feasible_rows"] += 1
        _append_float(bucket["gap_values"], row.get("gap_rel"))
        _append_float(bucket["improvement_per_second_values"], row.get("improvement_per_second"))
        _append_float(bucket["moves_attempted_per_s_values"], row.get("moves_attempted_per_s"))
        _append_float(bucket["evaluations_per_s_values"], row.get("evaluations_per_s"))
        _append_float(bucket["repairs_attempted_per_s_values"], row.get("repairs_attempted_per_s"))
    result: dict[str, dict[str, Any]] = {}
    for family, bucket in summary.items():
        row_count = int(bucket["row_count"])
        gap_values = bucket["gap_values"]
        result[family] = {
            "row_count": row_count,
            "feasible_rows": bucket["feasible_rows"],
            "feasible_rate": bucket["feasible_rows"] / row_count if row_count else 0.0,
            "mean_gap_rel": _mean(gap_values),
            "best_gap_rel": min(gap_values) if gap_values else None,
            "avg_improvement_per_second": _mean(bucket["improvement_per_second_values"]),
            "avg_moves_attempted_per_s": _mean(bucket["moves_attempted_per_s_values"]),
            "avg_evaluations_per_s": _mean(bucket["evaluations_per_s_values"]),
            "avg_repairs_attempted_per_s": _mean(bucket["repairs_attempted_per_s_values"]),
        }
    return result


def _comparison_summary(comparison: dict[str, Any]) -> dict[str, Any]:
    return {
        "gate_status": comparison.get("gates", {}).get("overall_status"),
        "matched_rows": comparison.get("matched_rows"),
        "objective_improvements": comparison.get("objective_improvements"),
        "quality_regressions": comparison.get("quality_regressions"),
        "time_to_best_improvements": comparison.get("time_to_best_improvements"),
        "time_to_best_regressions": comparison.get("time_to_best_regressions"),
        "family_summary": comparison.get("family_summary", {}),
    }


def _anytime_curve_entries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries = []
    for row in rows:
        anytime = row.get("anytime")
        if not isinstance(anytime, list) or not anytime:
            continue
        entries.append(
            {
                "benchmark_id": row.get("benchmark_id"),
                "family": row.get("family"),
                "tier": row.get("tier"),
                "strategy": row.get("strategy"),
                "strategy_profile": row.get("strategy_profile"),
                "model_style": row.get("model_style"),
                "kind": row.get("kind"),
                "thread_count": row.get("thread_count", 1),
                "points": [
                    {
                        "time_s": point.get("time_s"),
                        "best_cost": point.get("best_cost"),
                        "gap_rel": point.get("gap_rel"),
                    }
                    for point in anytime
                    if isinstance(point, dict)
                ],
            }
        )
    return entries


def _append_float(values: list[float], value: Any) -> None:
    parsed = _float_or_none(value)
    if parsed is not None:
        values.append(parsed)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_pct(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value) * 100:.3f}%"


if __name__ == "__main__":
    raise SystemExit(main())
