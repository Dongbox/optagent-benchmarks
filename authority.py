from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


HEURISTIC_SEEDS = (11, 23, 47)


@dataclass(frozen=True)
class ReleaseGateEntry:
    benchmark_id: str
    family: str
    model_styles: tuple[str, ...]
    strategies: tuple[str, ...]
    seeds: tuple[int, ...] = HEURISTIC_SEEDS
    tier: str = "smoke"


RELEASE_GATE_PLAN = (
    ReleaseGateEntry(
        benchmark_id="custom_steel_sequence_toy",
        family="sequence_transition_penalty",
        model_styles=("sequence_var_external_transition_penalty",),
        strategies=("ga", "alns"),
    ),
    ReleaseGateEntry(
        benchmark_id="fjsplib_sfjs01",
        family="flexible_interval_job_shop",
        model_styles=("optional_interval_machine_choice_no_overlap_precedence",),
        strategies=("ga", "alns"),
    ),
    ReleaseGateEntry(
        benchmark_id="jsplib_ft06",
        family="interval_job_shop",
        model_styles=("interval_var_sequence_no_overlap_precedence",),
        strategies=("ga", "alns"),
    ),
    ReleaseGateEntry(
        benchmark_id="psplib_j90_1_1",
        family="cumulative_resource_scheduling",
        model_styles=("interval_var_cumulative_precedence",),
        strategies=("ga", "alns"),
        tier="calibration",
    ),
    ReleaseGateEntry(
        benchmark_id="tsplib_berlin52",
        family="sequence_blackbox_tsp",
        model_styles=("sequence_var_external_call", "sequence_var_sequence_transition_sum"),
        strategies=("ga", "alns"),
    ),
    ReleaseGateEntry(
        benchmark_id="qaplib_nug12",
        family="sequence_quadratic_assignment",
        model_styles=("sequence_var_external_call",),
        strategies=("ga", "alns"),
    ),
    ReleaseGateEntry(
        benchmark_id="miplib2017_50v-10",
        family="exact_linear_mip",
        model_styles=("mps_linear_mp",),
        strategies=("optx",),
        seeds=(0,),
    ),
)


def make_run_key(*, benchmark_id: str, model_style: str, strategy: str, seed: int, thread_count: int = 1) -> str:
    return f"{benchmark_id}|{model_style}|{strategy}|seed={seed}|threads={thread_count}"


def expected_run_keys(plan: Iterable[ReleaseGateEntry] = RELEASE_GATE_PLAN) -> set[str]:
    return {
        make_run_key(
            benchmark_id=entry.benchmark_id,
            model_style=model_style,
            strategy=strategy,
            seed=seed,
        )
        for entry in plan
        for model_style in entry.model_styles
        for strategy in entry.strategies
        for seed in entry.seeds
    }


@dataclass(frozen=True)
class AuthorityInputs:
    optagent_commit: str
    benchmarks_commit: str
    wheel_sha256: str
    optagent_dirty: bool
    benchmarks_dirty: bool


@dataclass(frozen=True)
class AuthorityAssessment:
    status: str
    reasons: tuple[str, ...]
    inputs: AuthorityInputs


def assess_authority(inputs: AuthorityInputs, rows: Iterable[dict[str, Any]]) -> AuthorityAssessment:
    materialized = list(rows)
    reasons: list[str] = []
    if len(inputs.optagent_commit) != 40:
        reasons.append("optagent commit is not a full SHA")
    if len(inputs.benchmarks_commit) != 40:
        reasons.append("benchmarks commit is not a full SHA")
    if not inputs.wheel_sha256.startswith("sha256:") or len(inputs.wheel_sha256) != 71:
        reasons.append("wheel SHA256 is missing or malformed")
    if inputs.optagent_dirty:
        reasons.append("optagent checkout is dirty")
    if inputs.benchmarks_dirty:
        reasons.append("benchmarks checkout is dirty")

    expected = expected_run_keys()
    actual = {str(row.get("run_key")) for row in materialized}
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        reasons.append(f"missing planned runs: {', '.join(missing)}")
    if unexpected:
        reasons.append(f"unexpected runs: {', '.join(unexpected)}")
    if len(actual) != len(materialized):
        reasons.append("duplicate run keys are present")

    unverified_candidates = [
        str(row.get("run_key"))
        for row in materialized
        if row.get("status") in {"feasible", "optimal"} and row.get("verification_status") not in {"passed", "failed"}
    ]
    if unverified_candidates:
        reasons.append(
            "independent verification was not completed for returned candidates: "
            + ", ".join(sorted(unverified_candidates))
        )

    return AuthorityAssessment(
        status="authoritative" if not reasons else "non_authoritative",
        reasons=tuple(reasons),
        inputs=inputs,
    )


def assess_capabilities(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    materialized = list(rows)
    profiles: dict[str, dict[str, Any]] = {}
    for entry in RELEASE_GATE_PLAN:
        for model_style in entry.model_styles:
            for strategy in entry.strategies:
                key = f"{entry.family}|{model_style}|{strategy}"
                matched = [
                    row
                    for row in materialized
                    if row.get("benchmark_id") == entry.benchmark_id
                    and row.get("model_style") == model_style
                    and row.get("strategy") == strategy
                ]
                passed = len(matched) == len(entry.seeds) and all(_row_passed(row) for row in matched)
                profiles[key] = {
                    "benchmark_id": entry.benchmark_id,
                    "family": entry.family,
                    "model_style": model_style,
                    "strategy": strategy,
                    "status": "supported" if passed else "failed",
                    "passed_run_count": sum(1 for row in matched if _row_passed(row)),
                    "expected_run_count": len(entry.seeds),
                }

    families: dict[str, dict[str, Any]] = {}
    for entry in RELEASE_GATE_PLAN:
        if entry.family in families:
            continue
        family_entries = [item for item in RELEASE_GATE_PLAN if item.family == entry.family]
        styles = sorted({style for item in family_entries for style in item.model_styles})
        supported_styles = [
            style
            for style in styles
            if any(
                profile["status"] == "supported"
                for profile in profiles.values()
                if profile["family"] == entry.family and profile["model_style"] == style
            )
        ]
        families[entry.family] = {
            "status": "supported" if supported_styles == styles else "experimental",
            "required_model_styles": styles,
            "supported_model_styles": supported_styles,
        }

    return {
        "release_status": "passed"
        if families and all(item["status"] == "supported" for item in families.values())
        else "failed",
        "families": dict(sorted(families.items())),
        "profiles": dict(sorted(profiles.items())),
    }


def _row_passed(row: dict[str, Any]) -> bool:
    return (
        row.get("status") in {"feasible", "optimal"}
        and bool(row.get("feasible"))
        and row.get("verification_status") == "passed"
        and bool(row.get("verification_passed"))
    )
