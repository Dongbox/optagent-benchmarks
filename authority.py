from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Literal


HEURISTIC_SEEDS = (11, 23, 47)
AuthorityStatus = Literal["authoritative", "non_authoritative"]
CapabilityStatus = Literal["supported", "experimental", "failed"]
LifecycleStatus = Literal["declared", "runnable", "verified", "release_gate", "experimental", "retired"]


@dataclass(frozen=True)
class ReleaseGateEntry:
    benchmark_id: str
    family: str
    model_styles: tuple[str, ...]
    solve_route: str
    strategies: tuple[str, ...]
    seeds: tuple[int, ...] = HEURISTIC_SEEDS
    tier: str = "smoke"


RELEASE_GATE_PLAN = (
    ReleaseGateEntry(
        benchmark_id="custom_steel_sequence_toy",
        family="sequence_transition_penalty",
        model_styles=("sequence_var_external_transition_penalty",),
        solve_route="native_search",
        strategies=("ga", "alns"),
    ),
    ReleaseGateEntry(
        benchmark_id="fjsplib_sfjs01",
        family="flexible_interval_job_shop",
        model_styles=("optional_interval_machine_choice_no_overlap_precedence",),
        solve_route="native_search",
        strategies=("ga", "alns"),
    ),
    ReleaseGateEntry(
        benchmark_id="jsplib_ft06",
        family="interval_job_shop",
        model_styles=("interval_var_sequence_no_overlap_precedence",),
        solve_route="native_search",
        strategies=("ga", "alns"),
    ),
    ReleaseGateEntry(
        benchmark_id="psplib_j90_1_1",
        family="cumulative_resource_scheduling",
        model_styles=("interval_var_cumulative_precedence",),
        solve_route="native_search",
        strategies=("ga", "alns"),
        tier="calibration",
    ),
    ReleaseGateEntry(
        benchmark_id="tsplib_berlin52",
        family="sequence_blackbox_tsp",
        model_styles=("sequence_var_external_call", "sequence_var_sequence_transition_sum"),
        solve_route="native_search",
        strategies=("ga", "alns"),
    ),
    ReleaseGateEntry(
        benchmark_id="qaplib_nug12",
        family="sequence_quadratic_assignment",
        model_styles=("sequence_var_external_call",),
        solve_route="native_search",
        strategies=("ga", "alns"),
    ),
    ReleaseGateEntry(
        benchmark_id="miplib2017_50v-10",
        family="exact_linear_mip",
        model_styles=("mps_linear_mp",),
        solve_route="embedded_highs",
        strategies=("optx",),
        seeds=(0,),
    ),
)


@dataclass(frozen=True)
class RunCoordinate:
    benchmark_id: str
    family: str
    tier: str
    model_style: str
    solve_route: str
    strategy: str
    seed: int
    thread_count: int = 1

    @property
    def run_key(self) -> str:
        return make_run_key(
            benchmark_id=self.benchmark_id,
            model_style=self.model_style,
            solve_route=self.solve_route,
            strategy=self.strategy,
            seed=self.seed,
            thread_count=self.thread_count,
        )


def iter_run_coordinates(plan: Iterable[ReleaseGateEntry] = RELEASE_GATE_PLAN) -> tuple[RunCoordinate, ...]:
    return tuple(
        RunCoordinate(
            benchmark_id=entry.benchmark_id,
            family=entry.family,
            tier=entry.tier,
            model_style=model_style,
            solve_route=entry.solve_route,
            strategy=strategy,
            seed=seed,
        )
        for entry in plan
        for seed in entry.seeds
        for model_style in entry.model_styles
        for strategy in entry.strategies
    )


def make_run_key(
    *,
    benchmark_id: str,
    model_style: str,
    solve_route: str,
    strategy: str,
    seed: int,
    thread_count: int = 1,
) -> str:
    return f"{benchmark_id}|{model_style}|route={solve_route}|{strategy}|seed={seed}|threads={thread_count}"


def expected_run_keys(plan: Iterable[ReleaseGateEntry] = RELEASE_GATE_PLAN) -> set[str]:
    return {coordinate.run_key for coordinate in iter_run_coordinates(plan)}


@dataclass(frozen=True)
class AuthorityInputs:
    optagent_commit: str
    benchmarks_commit: str
    wheel_sha256: str
    optagent_dirty: bool
    benchmarks_dirty: bool


@dataclass(frozen=True)
class AuthorityAssessment:
    status: AuthorityStatus
    reasons: tuple[str, ...]
    inputs: AuthorityInputs


def assess_authority(
    inputs: AuthorityInputs,
    rows: Iterable[dict[str, Any]],
    *,
    evidence_checksums: dict[str, str] | None = None,
) -> AuthorityAssessment:
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

    checksums = dict(evidence_checksums or {})
    required_case_ids = {entry.benchmark_id for entry in RELEASE_GATE_PLAN}
    missing_evidence: list[str] = []
    for benchmark_id in sorted(required_case_ids):
        reference_key = f"{benchmark_id}:reference"
        if reference_key not in checksums:
            missing_evidence.append(reference_key)
        if not any(key.startswith(f"{benchmark_id}:instance:") for key in checksums):
            missing_evidence.append(f"{benchmark_id}:instance")
    if missing_evidence:
        reasons.append(f"missing evidence checksums: {', '.join(missing_evidence)}")
    malformed_checksums = sorted(
        key for key, value in checksums.items() if not value.startswith("sha256:") or len(value) != 71
    )
    if malformed_checksums:
        reasons.append(f"malformed evidence checksums: {', '.join(malformed_checksums)}")

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

    coordinates_by_key = {coordinate.run_key: coordinate for coordinate in iter_run_coordinates()}
    malformed_coordinates: list[str] = []
    missing_backend_identity: list[str] = []
    missing_platform: list[str] = []
    fallback_runs: list[str] = []
    for row in materialized:
        run_key = str(row.get("run_key"))
        coordinate = coordinates_by_key.get(run_key)
        if coordinate is not None and any(
            row.get(field) != expected_value
            for field, expected_value in (
                ("benchmark_id", coordinate.benchmark_id),
                ("family", coordinate.family),
                ("model_style", coordinate.model_style),
                ("solve_route", coordinate.solve_route),
                ("strategy", coordinate.strategy),
                ("seed", coordinate.seed),
                ("thread_count", coordinate.thread_count),
            )
        ):
            malformed_coordinates.append(run_key)
        if not row.get("backend_name") or not row.get("backend_version"):
            missing_backend_identity.append(run_key)
        if not row.get("platform"):
            missing_platform.append(run_key)
        if _explicit_strategy_fallback_count(row) > 0:
            fallback_runs.append(run_key)
    if malformed_coordinates:
        reasons.append(f"row coordinates do not match run keys: {', '.join(sorted(malformed_coordinates))}")
    if missing_backend_identity:
        reasons.append("backend identity is missing from rows: " + ", ".join(sorted(missing_backend_identity)))
    if missing_platform:
        reasons.append("platform coordinate is missing from rows: " + ", ".join(sorted(missing_platform)))
    if fallback_runs:
        reasons.append("explicit strategy fallback occurred in rows: " + ", ".join(sorted(fallback_runs)))

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
    platforms = sorted({str(row.get("platform")) for row in materialized if row.get("platform")})
    for entry in RELEASE_GATE_PLAN:
        for model_style in entry.model_styles:
            for strategy in entry.strategies:
                for platform_name in platforms:
                    key = f"{entry.family}|{model_style}|{entry.solve_route}|{strategy}|{platform_name}"
                    matched = [
                        row
                        for row in materialized
                        if row.get("benchmark_id") == entry.benchmark_id
                        and row.get("model_style") == model_style
                        and row.get("solve_route") == entry.solve_route
                        and row.get("strategy") == strategy
                        and row.get("platform") == platform_name
                    ]
                    passed = len(matched) == len(entry.seeds) and all(_row_passed(row) for row in matched)
                    profiles[key] = {
                        "benchmark_id": entry.benchmark_id,
                        "family": entry.family,
                        "model_style": model_style,
                        "solve_route": entry.solve_route,
                        "strategy": strategy,
                        "platform": platform_name,
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


CASE_LIFECYCLE_OVERRIDES: dict[str, LifecycleStatus] = {}


def case_lifecycle(benchmark_id: str) -> LifecycleStatus:
    if benchmark_id in CASE_LIFECYCLE_OVERRIDES:
        return CASE_LIFECYCLE_OVERRIDES[benchmark_id]
    if benchmark_id in {entry.benchmark_id for entry in RELEASE_GATE_PLAN}:
        return "release_gate"

    from benchmarks.cases.base import BenchmarkCase
    from benchmarks.cases.registry import benchmark_case_objects

    case = next((item for item in benchmark_case_objects() if item.benchmark_id == benchmark_id), None)
    if case is None:
        raise KeyError(f"benchmark case not found: {benchmark_id}")
    has_verifier = type(case).verify_solution is not BenchmarkCase.verify_solution
    if has_verifier and case.reference:
        return "verified"
    return "runnable"


def case_lifecycle_inventory() -> dict[str, LifecycleStatus]:
    from benchmarks.cases.registry import benchmark_case_objects

    return {case.benchmark_id: case_lifecycle(case.benchmark_id) for case in benchmark_case_objects()}


def _explicit_strategy_fallback_count(row: dict[str, Any]) -> float:
    diagnostics = row.get("diagnostics")
    sources = (row, diagnostics if isinstance(diagnostics, dict) else {})
    return sum(
        float(source.get(key) or 0.0) for source in sources for key in ("fallback_attempts", "fallback_successes")
    )


def _row_passed(row: dict[str, Any]) -> bool:
    return (
        row.get("status") in {"feasible", "optimal"}
        and bool(row.get("feasible"))
        and row.get("verification_status") == "passed"
        and bool(row.get("verification_passed"))
    )
