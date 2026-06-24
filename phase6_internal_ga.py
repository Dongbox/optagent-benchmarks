from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from benchmarks.bootstrap import prefer_local_development_paths
from benchmarks.presentation.common import DEFAULT_RUN_ROOT, ensure_run_dir, utc_timestamp, write_json


BASELINE_PROFILE = "baseline"
FJSP_FAMILY = "fjsp_external_decoder"
NON_FJSP_SEQUENCE_FAMILIES = {"sequence_blackbox_tsp"}
QAP_FAMILIES = {"sequence_quadratic_assignment"}
SCHEDULING_FAMILIES = {"interval_job_shop", "cumulative_resource_scheduling"}
GA_STRATEGIES = {"ga", "advanced_ga"}


def build_phase6_internal_ga_report(
    *,
    fjsp_summaries: dict[str, str | Path] | None = None,
    suite_run_dirs: dict[str, str | Path] | None = None,
    baseline_profile: str = BASELINE_PROFILE,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for profile, path in sorted((fjsp_summaries or {}).items()):
        rows.extend(_rows_from_fjsp_summary(profile=profile, path=Path(path)))
    for profile, path in sorted((suite_run_dirs or {}).items()):
        rows.extend(_rows_from_suite_run(profile=profile, run_dir=Path(path)))

    report = {
        "schema_version": 1,
        "generated_at_utc": utc_timestamp(),
        "generated_from": "phase6_internal_ga_benchmark",
        "baseline_profile": baseline_profile,
        "row_count": len(rows),
        "profiles": sorted({str(row["profile"]) for row in rows}),
        "families": sorted({str(row["family"]) for row in rows}),
        "wall_time_budgets_s": sorted(
            {float(row["wall_time_budget_s"]) for row in rows if row.get("wall_time_budget_s") is not None}
        ),
        "rows": rows,
        "groups": _build_groups(rows=rows, baseline_profile=baseline_profile),
        "gates": _build_phase6_gates(rows=rows, baseline_profile=baseline_profile),
    }
    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        write_json(output_path / "phase6_internal_ga_report.json", report)
        (output_path / "phase6_internal_ga_report.md").write_text(
            render_phase6_internal_ga_report(report),
            encoding="utf-8",
        )
        report["artifacts"] = {
            "json": str(output_path / "phase6_internal_ga_report.json"),
            "markdown": str(output_path / "phase6_internal_ga_report.md"),
        }
        write_json(output_path / "phase6_internal_ga_report.json", report)
    return report


def render_phase6_internal_ga_report(report: dict[str, Any]) -> str:
    lines = [
        "# Phase 6 Internal GA Benchmark Report",
        "",
        f"- Baseline profile: `{report.get('baseline_profile')}`",
        f"- Profiles: `{', '.join(report.get('profiles', []))}`",
        f"- Families: `{', '.join(report.get('families', []))}`",
        f"- Row count: {report.get('row_count', 0)}",
        f"- Gate status: `{report.get('gates', {}).get('overall_status', '')}`",
        "",
        "## Gates",
        "",
        "| Gate | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for name, gate in sorted(report.get("gates", {}).get("checks", {}).items()):
        detail = gate.get("detail") or gate.get("reason") or ""
        lines.append(f"| `{name}` | `{gate.get('status')}` | {detail} |")

    lines.extend(
        [
            "",
            "## Profile Comparisons",
            "",
            "| Family | Case | Style | Solver | Strategy | Budget s | Candidate | Objective delta | Time-to-best delta | Generated/s ratio | Unique/s ratio | Evaluated/s ratio | Duplicate ratio delta | Status |",
            "| --- | --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for group in report.get("groups", []):
        for comparison in group.get("comparisons", []):
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{group.get('family')}`",
                        f"`{group.get('case_id')}`",
                        f"`{group.get('model_style') or ''}`",
                        f"`{', '.join(group.get('solvers') or [])}`",
                        f"`{', '.join(group.get('strategies') or [])}`",
                        _fmt(group.get("wall_time_budget_s")),
                        f"`{comparison.get('candidate_profile')}`",
                        _fmt(comparison.get("objective_median_delta")),
                        _fmt(comparison.get("time_to_best_seconds_median_delta")),
                        _fmt(comparison.get("offspring_generated_per_s_ratio")),
                        _fmt(comparison.get("unique_offspring_per_s_ratio")),
                        _fmt(comparison.get("offspring_evaluated_per_s_ratio")),
                        _fmt(comparison.get("duplicate_ratio_delta")),
                        f"`{comparison.get('status')}`",
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Aggregates",
            "",
            "| Family | Case | Profile | Rows | Objective median | Best objective | Time-to-best median | Generated/s median | Unique/s median | Evaluated/s median | Duplicate ratio median | Callback count median |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for group in report.get("groups", []):
        for profile in group.get("profiles", []):
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{group.get('family')}`",
                        f"`{group.get('case_id')}`",
                        f"`{profile.get('profile')}`",
                        _fmt(profile.get("row_count")),
                        _fmt(profile.get("objective", {}).get("median")),
                        _fmt(profile.get("objective", {}).get("min")),
                        _fmt(profile.get("time_to_best_seconds", {}).get("median")),
                        _fmt(profile.get("offspring_generated_per_s", {}).get("median")),
                        _fmt(profile.get("unique_offspring_per_s", {}).get("median")),
                        _fmt(profile.get("offspring_evaluated_per_s", {}).get("median")),
                        _fmt(profile.get("duplicate_ratio", {}).get("median")),
                        _fmt(profile.get("external_callback_count", {}).get("median")),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def _rows_from_fjsp_summary(*, profile: str, path: Path) -> list[dict[str, Any]]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    config = summary.get("config") if isinstance(summary.get("config"), dict) else {}
    rows = []
    for result in summary.get("results", []):
        if not isinstance(result, dict):
            continue
        metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
        rows.append(
            _normalize_phase6_row(
                {
                    "profile": _profile_name(profile, result, config),
                    "source": str(path),
                    "source_kind": "fjsp_wallclock_summary",
                    "family": FJSP_FAMILY,
                    "case_id": summary.get("case") or "fjsp",
                    "model_style": "sequence_external_fjsp",
                    "seed": result.get("seed"),
                    "solver": result.get("solver"),
                    "strategy": result.get("strategy") or _strategy_from_solver(result.get("solver")),
                    "status": result.get("status"),
                    "objective": result.get("objective"),
                    "wall_seconds": result.get("wall_seconds"),
                    "time_to_best_seconds": result.get("time_to_best_seconds"),
                    "wall_time_budget_s": config.get("time_limit_s"),
                    "offspring_attempts": _first_present(
                        result,
                        metadata,
                        "offspring_attempts",
                        "ga_offspring_attempt_count",
                        "offspring_generated",
                    ),
                    "offspring_generated": result.get("offspring_generated"),
                    "unique_offspring": _first_present(result, metadata, "unique_offspring", "ga_unique_offspring_count"),
                    "offspring_evaluated": result.get("offspring_evaluated"),
                    "offspring_generated_per_s": result.get("offspring_generated_per_second"),
                    "offspring_evaluated_per_s": result.get("offspring_evaluated_per_second"),
                    "duplicate_count": _first_present(
                        result,
                        metadata,
                        "duplicate_offspring",
                        "ga_duplicate_offspring_count",
                        "duplicate_children",
                    ),
                    "duplicate_ratio": _first_present(result, metadata, "ga_duplicate_ratio"),
                    "duplicate_fallback_generations": _first_present(
                        result,
                        metadata,
                        "ga_duplicate_fallback_generation_count",
                    ),
                    "raw_duplicate_offspring": _first_present(
                        result,
                        metadata,
                        "raw_duplicate_offspring",
                        "ga_raw_duplicate_offspring_count",
                    ),
                    "post_improvement_duplicate_offspring": _first_present(
                        result,
                        metadata,
                        "post_improvement_duplicate_offspring",
                        "ga_post_improvement_duplicate_offspring_count",
                    ),
                    "post_repair_duplicate_offspring": _first_present(
                        result,
                        metadata,
                        "post_repair_duplicate_offspring",
                        "ga_post_repair_duplicate_offspring_count",
                    ),
                    "duplicate_fallback_evaluated": _first_present(
                        result,
                        metadata,
                        "duplicate_fallback_evaluated",
                        "ga_duplicate_fallback_evaluated_count",
                    ),
                    "generation_all_duplicate_count": _first_present(
                        result,
                        metadata,
                        "generation_all_duplicate_count",
                        "ga_generation_all_duplicate_count",
                    ),
                    "parent_hash_diversity_mean": _first_present(
                        result,
                        metadata,
                        "parent_hash_diversity_mean",
                        "ga_parent_hash_diversity_mean",
                    ),
                    "parent_hash_diversity_min": _first_present(
                        result,
                        metadata,
                        "parent_hash_diversity_min",
                        "ga_parent_hash_diversity_min",
                    ),
                    "external_callback_count": _first_present(
                        result,
                        metadata,
                        "external_rows_requested",
                        "ga_external_batch_rows",
                    ),
                    "external_callback_wall_time_ms": _first_present(
                        result,
                        metadata,
                        "external_callback_wall_time_ms",
                        "ga_external_callback_wall_time_ms",
                    ),
                    "external_evaluation_mode": _first_present(
                        result,
                        metadata,
                        "external_evaluation_mode",
                        "ga_external_evaluation_mode",
                    ),
                    "external_provider_capability": _first_present(
                        result,
                        metadata,
                        "external_provider_capability",
                    ),
                }
            )
        )
    return rows


def _rows_from_suite_run(*, profile: str, run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "rows.jsonl"
    if not path.exists():
        path = run_dir / "results.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("kind") != "strategy_run":
            continue
        strategy = str(row.get("strategy") or "")
        if strategy not in GA_STRATEGIES:
            strategy_role = "strategy_baseline"
        else:
            strategy_role = "ga_strategy"
        effective_budget = row.get("effective_budget") if isinstance(row.get("effective_budget"), dict) else {}
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        rows.append(
            _normalize_phase6_row(
                {
                    "profile": _profile_name(profile, row, {}),
                    "source": str(run_dir),
                    "source_kind": "benchmark_suite_run",
                    "family": row.get("family"),
                    "case_id": row.get("benchmark_id"),
                    "model_style": row.get("model_style"),
                    "seed": effective_budget.get("seed"),
                    "solver": row.get("solver_name") or "opt-agent",
                    "strategy": strategy,
                    "strategy_role": strategy_role,
                    "status": row.get("status"),
                    "feasible": row.get("feasible"),
                    "objective": row.get("objective"),
                    "wall_seconds": row.get("elapsed_seconds"),
                    "time_to_best_seconds": row.get("time_to_best_seconds"),
                    "wall_time_budget_s": row.get("effective_time_limit_s"),
                    "offspring_attempts": _first_present(row, metadata, "ga_offspring_attempt_count", "ga_offspring_generated"),
                    "offspring_generated": row.get("ga_offspring_generated"),
                    "unique_offspring": _first_present(row, metadata, "ga_unique_offspring_count"),
                    "offspring_evaluated": row.get("ga_offspring_evaluated"),
                    "offspring_generated_per_s": _rate(row.get("ga_offspring_generated"), row.get("elapsed_seconds")),
                    "offspring_evaluated_per_s": _rate(row.get("ga_offspring_evaluated"), row.get("elapsed_seconds")),
                    "duplicate_count": _first_present(row, metadata, "ga_duplicate_offspring_count", "ga_duplicate_child_count"),
                    "duplicate_ratio": _first_present(row, metadata, "ga_duplicate_ratio"),
                    "duplicate_fallback_generations": _first_present(row, metadata, "ga_duplicate_fallback_generation_count"),
                    "raw_duplicate_offspring": _first_present(row, metadata, "ga_raw_duplicate_offspring_count"),
                    "post_improvement_duplicate_offspring": _first_present(
                        row, metadata, "ga_post_improvement_duplicate_offspring_count"
                    ),
                    "post_repair_duplicate_offspring": _first_present(
                        row, metadata, "ga_post_repair_duplicate_offspring_count"
                    ),
                    "duplicate_fallback_evaluated": _first_present(
                        row, metadata, "ga_duplicate_fallback_evaluated_count"
                    ),
                    "generation_all_duplicate_count": _first_present(
                        row, metadata, "ga_generation_all_duplicate_count"
                    ),
                    "parent_hash_diversity_mean": _first_present(
                        row, metadata, "ga_parent_hash_diversity_mean"
                    ),
                    "parent_hash_diversity_min": _first_present(
                        row, metadata, "ga_parent_hash_diversity_min"
                    ),
                    "external_callback_count": _first_present(row, metadata, "external_rows_requested", "ga_external_batch_rows"),
                    "external_callback_wall_time_ms": _first_present(
                        row,
                        metadata,
                        "external_callback_wall_time_ms",
                        "ga_external_callback_wall_time_ms",
                    ),
                    "external_evaluation_mode": _first_present(
                        row,
                        metadata,
                        "external_evaluation_mode",
                        "ga_external_evaluation_mode",
                    ),
                }
            )
        )
    return rows


def _normalize_phase6_row(row: dict[str, Any]) -> dict[str, Any]:
    attempts = _float_or_none(row.get("offspring_attempts"))
    generated = _float_or_none(row.get("offspring_generated"))
    duplicate = _float_or_none(row.get("duplicate_count"))
    unique = _float_or_none(row.get("unique_offspring"))
    wall_seconds = _float_or_none(row.get("wall_seconds"))
    denominator = attempts if attempts is not None else generated
    if row.get("duplicate_ratio") is None and denominator and duplicate is not None:
        row["duplicate_ratio"] = duplicate / denominator
    if unique is None and denominator is not None and duplicate is not None:
        row["unique_offspring"] = max(0.0, denominator - duplicate)
    if row.get("unique_offspring_per_s") is None:
        row["unique_offspring_per_s"] = _rate(row.get("unique_offspring"), wall_seconds)
    if row.get("offspring_attempts_per_s") is None:
        row["offspring_attempts_per_s"] = _rate(row.get("offspring_attempts"), wall_seconds)
    if row.get("offspring_generated_per_s") is None:
        row["offspring_generated_per_s"] = _rate(row.get("offspring_generated"), wall_seconds)
    return {key: value for key, value in row.items() if value is not None}


def _build_groups(*, rows: list[dict[str, Any]], baseline_profile: str) -> list[dict[str, Any]]:
    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            row.get("family"),
            row.get("case_id"),
            row.get("model_style"),
            row.get("wall_time_budget_s"),
        )
        buckets.setdefault(key, []).append(row)

    groups = []
    for key, group_rows in sorted(buckets.items(), key=lambda item: tuple(str(part) for part in item[0])):
        profiles = [_profile_summary(profile, profile_rows) for profile, profile_rows in sorted(_by_profile(group_rows).items())]
        comparisons = _profile_comparisons(profiles=profiles, baseline_profile=baseline_profile)
        groups.append(
            {
                "family": key[0],
                "case_id": key[1],
                "model_style": key[2],
                "solver": ", ".join(sorted({str(row.get("solver")) for row in group_rows if row.get("solver")})),
                "strategy": ", ".join(sorted({str(row.get("strategy")) for row in group_rows if row.get("strategy")})),
                "solvers": sorted({str(row.get("solver")) for row in group_rows if row.get("solver")}),
                "strategies": sorted({str(row.get("strategy")) for row in group_rows if row.get("strategy")}),
                "wall_time_budget_s": key[3],
                "profiles": profiles,
                "comparisons": comparisons,
            }
        )
    return groups


def _profile_summary(profile: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "profile": profile,
        "row_count": len(rows),
        "ok_count": sum(1 for row in rows if row.get("status") == "ok" or row.get("feasible") is True),
        "objective": _distribution(_numeric_values(rows, "objective")),
        "wall_seconds": _distribution(_numeric_values(rows, "wall_seconds")),
        "time_to_best_seconds": _distribution(_numeric_values(rows, "time_to_best_seconds")),
        "offspring_generated_per_s": _distribution(_numeric_values(rows, "offspring_generated_per_s")),
        "offspring_attempts_per_s": _distribution(_numeric_values(rows, "offspring_attempts_per_s")),
        "unique_offspring_per_s": _distribution(_numeric_values(rows, "unique_offspring_per_s")),
        "offspring_evaluated_per_s": _distribution(_numeric_values(rows, "offspring_evaluated_per_s")),
        "duplicate_ratio": _distribution(_numeric_values(rows, "duplicate_ratio")),
        "external_callback_count": _distribution(_numeric_values(rows, "external_callback_count")),
        "external_callback_wall_time_ms": _distribution(_numeric_values(rows, "external_callback_wall_time_ms")),
        "external_modes": sorted({str(row.get("external_evaluation_mode")) for row in rows if row.get("external_evaluation_mode")}),
    }


def _profile_comparisons(*, profiles: list[dict[str, Any]], baseline_profile: str) -> list[dict[str, Any]]:
    by_name = {str(profile["profile"]): profile for profile in profiles}
    baseline = by_name.get(baseline_profile)
    if baseline is None:
        return []
    comparisons = []
    for candidate in profiles:
        if candidate["profile"] == baseline_profile:
            continue
        comparison = {
            "baseline_profile": baseline_profile,
            "candidate_profile": candidate["profile"],
            "objective_median_delta": _delta_median(candidate, baseline, "objective"),
            "time_to_best_seconds_median_delta": _delta_median(candidate, baseline, "time_to_best_seconds"),
            "offspring_generated_per_s_ratio": _ratio_median(candidate, baseline, "offspring_generated_per_s"),
            "unique_offspring_per_s_ratio": _ratio_median(candidate, baseline, "unique_offspring_per_s"),
            "offspring_evaluated_per_s_ratio": _ratio_median(candidate, baseline, "offspring_evaluated_per_s"),
            "duplicate_ratio_delta": _delta_median(candidate, baseline, "duplicate_ratio"),
            "external_callback_count_delta": _delta_median(candidate, baseline, "external_callback_count"),
            "external_callback_wall_time_ms_delta": _delta_median(candidate, baseline, "external_callback_wall_time_ms"),
        }
        comparison["status"] = _comparison_status(comparison)
        comparisons.append(comparison)
    return comparisons


def _comparison_status(comparison: dict[str, Any]) -> str:
    objective_delta = _float_or_none(comparison.get("objective_median_delta"))
    unique_ratio = _float_or_none(comparison.get("unique_offspring_per_s_ratio"))
    generated_ratio = _float_or_none(comparison.get("offspring_generated_per_s_ratio"))
    evaluated_ratio = _float_or_none(comparison.get("offspring_evaluated_per_s_ratio"))
    duplicate_delta = _float_or_none(comparison.get("duplicate_ratio_delta"))
    time_to_best_delta = _float_or_none(comparison.get("time_to_best_seconds_median_delta"))
    quality_regressed = objective_delta is not None and objective_delta > 0
    effective_improved = (
        (generated_ratio is not None and generated_ratio >= 1.10)
        or (unique_ratio is not None and unique_ratio >= 1.10)
        or (evaluated_ratio is not None and evaluated_ratio >= 1.10)
        or (duplicate_delta is not None and duplicate_delta <= -0.05)
        or (time_to_best_delta is not None and time_to_best_delta < 0)
    )
    if quality_regressed and not effective_improved:
        return "fail"
    if effective_improved or (objective_delta is not None and objective_delta < 0):
        return "pass"
    return "neutral"


def _build_phase6_gates(*, rows: list[dict[str, Any]], baseline_profile: str) -> dict[str, Any]:
    coverage = _coverage_gate(rows)
    baseline = _baseline_gate(rows, baseline_profile)
    effective = _effective_offspring_gate(rows, baseline_profile)
    quality = _quality_gate(rows, baseline_profile)
    external = _external_safety_gate(rows)
    feasibility = _feasibility_gate(rows)
    checks = {
        "coverage": coverage,
        "baseline": baseline,
        "effective_offspring": effective,
        "quality": quality,
        "feasibility": feasibility,
        "external_safety": external,
    }
    return {
        "overall_status": "pass" if all(check["status"] == "pass" for check in checks.values()) else "fail",
        "checks": checks,
    }


def _coverage_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    families = {str(row.get("family")) for row in rows}
    missing = []
    if FJSP_FAMILY not in families:
        missing.append("fjsp")
    if not (families & NON_FJSP_SEQUENCE_FAMILIES):
        missing.append("non_fjsp_sequence")
    if not (families & QAP_FAMILIES):
        missing.append("qap")
    if not (families & SCHEDULING_FAMILIES):
        missing.append("scheduling")
    return {
        "status": "pass" if not missing else "fail",
        "detail": f"families={sorted(families)}, missing={missing}",
        "missing": missing,
    }


def _baseline_gate(rows: list[dict[str, Any]], baseline_profile: str) -> dict[str, Any]:
    baseline_rows = [row for row in rows if row.get("profile") == baseline_profile]
    return {
        "status": "pass" if baseline_rows else "fail",
        "detail": f"baseline_profile={baseline_profile}, rows={len(baseline_rows)}",
    }


def _effective_offspring_gate(rows: list[dict[str, Any]], baseline_profile: str) -> dict[str, Any]:
    groups = _build_groups(rows=rows, baseline_profile=baseline_profile)
    comparisons = [comparison for group in groups for comparison in group.get("comparisons", [])]
    improved = [
        comparison
        for comparison in comparisons
        if comparison.get("status") == "pass"
        and (
            _float_or_none(comparison.get("unique_offspring_per_s_ratio")) is not None
            or _float_or_none(comparison.get("offspring_generated_per_s_ratio")) is not None
            or _float_or_none(comparison.get("offspring_evaluated_per_s_ratio")) is not None
            or _float_or_none(comparison.get("duplicate_ratio_delta")) is not None
            or _float_or_none(comparison.get("time_to_best_seconds_median_delta")) is not None
        )
    ]
    if improved:
        status = "pass"
        decision = "default_candidate_supported"
    elif comparisons:
        status = "pass"
        decision = "not_default_yet"
    else:
        status = "fail"
        decision = "insufficient_comparisons"
    return {
        "status": status,
        "detail": (
            f"comparisons={len(comparisons)}, effective_improvements={len(improved)}, "
            f"decision={decision}"
        ),
        "decision": decision,
    }


def _quality_gate(rows: list[dict[str, Any]], baseline_profile: str) -> dict[str, Any]:
    groups = _build_groups(rows=rows, baseline_profile=baseline_profile)
    failures = [
        comparison
        for group in groups
        for comparison in group.get("comparisons", [])
        if comparison.get("status") == "fail"
    ]
    return {
        "status": "pass" if not failures else "fail",
        "detail": f"quality_failures={len(failures)}",
        "failures": failures,
    }


def _feasibility_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required_families = NON_FJSP_SEQUENCE_FAMILIES | QAP_FAMILIES | SCHEDULING_FAMILIES
    required_rows = [
        row
        for row in rows
        if str(row.get("family")) in required_families
        and str(row.get("strategy")) in GA_STRATEGIES
    ]
    infeasible = [
        row
        for row in required_rows
        if row.get("feasible") is False or str(row.get("status") or "") in {"error", "infeasible"}
    ]
    return {
        "status": "pass" if required_rows and not infeasible else "fail",
        "detail": f"required_rows={len(required_rows)}, infeasible={len(infeasible)}",
        "infeasible": [
            {
                "family": row.get("family"),
                "case_id": row.get("case_id"),
                "strategy": row.get("strategy"),
                "profile": row.get("profile"),
                "status": row.get("status"),
                "feasible": row.get("feasible"),
            }
            for row in infeasible
        ],
    }


def _external_safety_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    unsafe = [
        row
        for row in rows
        if row.get("external_provider_capability") == "unknown"
        and str(row.get("external_evaluation_mode") or "") not in {"", "serial_external"}
    ]
    return {
        "status": "pass" if not unsafe else "fail",
        "detail": f"unsafe_unknown_external_rows={len(unsafe)}",
    }


def _by_profile(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        result.setdefault(str(row.get("profile") or ""), []).append(row)
    return result


def _profile_name(profile: str, row: dict[str, Any], config: dict[str, Any]) -> str:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    return str(
        row.get("phase6_profile")
        or metadata.get("phase6_profile")
        or row.get("variant")
        or config.get("phase6_profile")
        or profile
    )


def _strategy_from_solver(solver: Any) -> str:
    value = str(solver or "")
    if value == "op-solver":
        return "opsolver_reference"
    if value.startswith("opt-agent-advanced_ga"):
        return "advanced_ga"
    if value.startswith("opt-agent-ga") or value == "opt-agent":
        return "ga"
    return value or "unknown"


def _first_present(primary: dict[str, Any], secondary: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if primary.get(key) is not None:
            return primary.get(key)
        if secondary.get(key) is not None:
            return secondary.get(key)
    return None


def _numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    values = []
    for row in rows:
        value = _float_or_none(row.get(field))
        if value is not None:
            values.append(value)
    return values


def _distribution(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "median": None, "max": None, "mean": None}
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "min": ordered[0],
        "median": _median(ordered),
        "max": ordered[-1],
        "mean": sum(ordered) / len(ordered),
    }


def _median(ordered_values: list[float]) -> float:
    midpoint = len(ordered_values) // 2
    if len(ordered_values) % 2:
        return ordered_values[midpoint]
    return (ordered_values[midpoint - 1] + ordered_values[midpoint]) / 2.0


def _delta_median(candidate: dict[str, Any], baseline: dict[str, Any], field: str) -> float | None:
    candidate_value = _float_or_none(candidate.get(field, {}).get("median"))
    baseline_value = _float_or_none(baseline.get(field, {}).get("median"))
    if candidate_value is None or baseline_value is None:
        return None
    return candidate_value - baseline_value


def _ratio_median(candidate: dict[str, Any], baseline: dict[str, Any], field: str) -> float | None:
    candidate_value = _float_or_none(candidate.get(field, {}).get("median"))
    baseline_value = _float_or_none(baseline.get(field, {}).get("median"))
    if candidate_value is None or baseline_value is None or baseline_value == 0:
        return None
    return candidate_value / baseline_value


def _rate(value: Any, seconds: Any) -> float | None:
    numerator = _float_or_none(value)
    denominator = _float_or_none(seconds)
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


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
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _parse_labeled_path(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        path = Path(raw)
        return path.stem, path
    label, path = raw.split("=", 1)
    return label, Path(path)


def main(argv: list[str] | None = None) -> int:
    prefer_local_development_paths()
    parser = argparse.ArgumentParser(description="Build Phase 6 internal GA optimization benchmark reports.")
    parser.add_argument("--fjsp-summary", action="append", default=[], help="Labeled FJSP summary path: profile=path.")
    parser.add_argument("--suite-run-dir", action="append", default=[], help="Labeled benchmark suite run dir: profile=path.")
    parser.add_argument("--baseline-profile", default=BASELINE_PROFILE)
    parser.add_argument("--output-root", default=str(DEFAULT_RUN_ROOT))
    parser.add_argument("--timestamp")
    args = parser.parse_args(argv)

    output_dir = ensure_run_dir(args.output_root, timestamp=args.timestamp)
    report = build_phase6_internal_ga_report(
        fjsp_summaries=dict(_parse_labeled_path(value) for value in args.fjsp_summary),
        suite_run_dirs=dict(_parse_labeled_path(value) for value in args.suite_run_dir),
        baseline_profile=args.baseline_profile,
        output_dir=output_dir,
    )
    print(json.dumps(report, indent=2, ensure_ascii=True, sort_keys=True))
    return 0 if report.get("gates", {}).get("overall_status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
