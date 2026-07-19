from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from benchmarks.artifact_io import checksum_json


ProtocolKind = Literal["smoke", "calibration", "release_holdout"]

CALIBRATION_SEEDS = (11, 23, 47, 59, 71, 83, 97, 101, 113, 127)


@dataclass(frozen=True)
class ComparisonProfile:
    family: str
    model_style: str
    case_ids: tuple[str, ...]
    generalization_status: str = "full"


@dataclass(frozen=True)
class ComparisonProtocol:
    protocol_id: str
    kind: ProtocolKind
    index_profile_id: str
    profiles: tuple[ComparisonProfile, ...]
    seeds: tuple[int, ...]
    wall_time_s: float
    search_candidate_checkpoint: int
    max_iterations: int
    population_size: int
    trace_limit: int
    thread_count: int = 1
    strategy: str = "ga"
    solve_route: str = "native_search"
    execution_order: str = "deterministic_interleaved_pairs"
    performance_platform: str = "linux_x86_64"

    def protocol_snapshot(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def checksum(self) -> str:
        return checksum_json(self.protocol_snapshot())


@dataclass(frozen=True)
class MetricThreshold:
    mode: Literal["absolute", "relative", "absolute_or_relative"]
    value: float
    absolute_floor: float = 0.0


@dataclass(frozen=True)
class IndexProfile:
    profile_id: str
    dimension_weights: dict[str, float]
    component_weights: dict[str, dict[str, float]]
    thresholds: dict[str, MetricThreshold]
    target_gaps: tuple[float, ...]
    unresolved_gap_penalty: float
    gap_cap: float
    verdict_threshold: float
    dimension_regression_limit: float
    bootstrap_samples: int
    bootstrap_seed: int

    def protocol_snapshot(self) -> dict[str, Any]:
        snapshot = asdict(self)
        snapshot["thresholds"] = {name: asdict(value) for name, value in self.thresholds.items()}
        return snapshot

    @property
    def checksum(self) -> str:
        return checksum_json(self.protocol_snapshot())


_PROFILE_CATALOG = (
    (
        "sequence_transition_penalty",
        "sequence_var_external_transition_penalty",
        ("custom_steel_sequence_toy", "custom_steel_sequence_bundled_head40"),
        ("custom_steel_sequence_bundled",),
        "limited_generalization",
    ),
    (
        "sequence_blackbox_tsp",
        "sequence_var_external_call",
        ("tsplib_berlin52", "tsplib_eil51", "tsplib_st70"),
        ("tsplib_pr76", "tsplib_kroc100"),
        "full",
    ),
    (
        "sequence_blackbox_tsp",
        "sequence_var_sequence_transition_sum",
        ("tsplib_berlin52", "tsplib_eil51", "tsplib_st70"),
        ("tsplib_pr76", "tsplib_kroc100"),
        "full",
    ),
    (
        "sequence_quadratic_assignment",
        "sequence_var_external_call",
        ("qaplib_nug12", "qaplib_had12", "qaplib_scr12"),
        ("qaplib_chr12a", "qaplib_tai12b"),
        "full",
    ),
    (
        "interval_job_shop",
        "interval_var_sequence_no_overlap_precedence",
        ("jsplib_ft06", "jsplib_la01", "jsplib_orb03"),
        ("jsplib_abz5", "jsplib_ft10"),
        "full",
    ),
    (
        "flexible_interval_job_shop",
        "optional_interval_machine_choice_no_overlap_precedence",
        ("fjsplib_sfjs03", "fjsplib_sfjs02", "fjsplib_sfjs04"),
        ("fjsplib_sfjs05", "fjsplib_sfjs06"),
        "full",
    ),
    (
        "cumulative_resource_scheduling",
        "interval_var_cumulative_precedence",
        ("psplib_j90_13_2", "psplib_j90_16_7", "psplib_j90_17_10"),
        ("psplib_j90_19_5", "psplib_j90_29_1"),
        "full",
    ),
)


def _profiles(partition: Literal["smoke", "calibration", "holdout"]) -> tuple[ComparisonProfile, ...]:
    profiles = []
    for family, model_style, calibration, holdout, status in _PROFILE_CATALOG:
        if partition == "smoke":
            case_ids = (calibration[0],)
        elif partition == "calibration":
            case_ids = calibration
        else:
            case_ids = holdout
        profiles.append(ComparisonProfile(family, model_style, case_ids, status))
    return tuple(profiles)


_PROTOCOLS = {
    "ga_release_smoke_v1": ComparisonProtocol(
        protocol_id="ga_release_smoke_v1",
        kind="smoke",
        index_profile_id="ga_strategy_comparison_index_v1",
        profiles=_profiles("smoke"),
        seeds=(11, 23, 47),
        wall_time_s=2.0,
        search_candidate_checkpoint=200,
        max_iterations=100_000,
        population_size=16,
        trace_limit=4096,
    ),
    "ga_calibration_v1": ComparisonProtocol(
        protocol_id="ga_calibration_v1",
        kind="calibration",
        index_profile_id="ga_strategy_comparison_index_v1",
        profiles=_profiles("calibration"),
        seeds=CALIBRATION_SEEDS,
        wall_time_s=5.0,
        search_candidate_checkpoint=1000,
        max_iterations=100_000,
        population_size=32,
        trace_limit=4096,
    ),
    "ga_release_holdout_v1": ComparisonProtocol(
        protocol_id="ga_release_holdout_v1",
        kind="release_holdout",
        index_profile_id="ga_strategy_comparison_index_v1",
        profiles=_profiles("holdout"),
        seeds=CALIBRATION_SEEDS,
        wall_time_s=10.0,
        search_candidate_checkpoint=2000,
        max_iterations=100_000,
        population_size=32,
        trace_limit=4096,
    ),
}


_INDEX_PROFILES = {
    "ga_strategy_comparison_index_v1": IndexProfile(
        profile_id="ga_strategy_comparison_index_v1",
        dimension_weights={"quality": 0.4, "anytime": 0.3, "robustness": 0.2, "efficiency": 0.1},
        component_weights={
            "quality": {"median_final_gap": 0.7, "paired_quality_win_rate": 0.3},
            "anytime": {"normalized_primal_integral": 0.6, "target_hit_rate": 0.25, "time_to_target": 0.15},
            "robustness": {"p90_final_gap": 0.5, "gap_mad": 0.3, "case_direction_consistency": 0.2},
            "efficiency": {"search_candidate_throughput": 0.5, "fixed_search_candidate_elapsed": 0.5},
        },
        thresholds={
            "median_final_gap": MetricThreshold("absolute_or_relative", 0.1, 0.01),
            "paired_quality_win_rate": MetricThreshold("absolute", 0.1),
            "normalized_primal_integral": MetricThreshold("relative", 0.1),
            "target_hit_rate": MetricThreshold("absolute", 0.05),
            "time_to_target": MetricThreshold("relative", 0.1),
            "p90_final_gap": MetricThreshold("absolute_or_relative", 0.1, 0.01),
            "gap_mad": MetricThreshold("relative", 0.1),
            "case_direction_consistency": MetricThreshold("absolute", 0.1),
            "search_candidate_throughput": MetricThreshold("relative", 0.1),
            "fixed_search_candidate_elapsed": MetricThreshold("relative", 0.1),
        },
        target_gaps=(0.1, 0.05, 0.01),
        unresolved_gap_penalty=1.0,
        gap_cap=1.0,
        verdict_threshold=10.0,
        dimension_regression_limit=-15.0,
        bootstrap_samples=2000,
        bootstrap_seed=20260712,
    )
}


def get_comparison_protocol(protocol_id: str) -> ComparisonProtocol:
    try:
        return _PROTOCOLS[protocol_id]
    except KeyError as exc:
        raise KeyError(f"unknown comparison protocol: {protocol_id}") from exc


def get_index_profile(profile_id: str) -> IndexProfile:
    try:
        return _INDEX_PROFILES[profile_id]
    except KeyError as exc:
        raise KeyError(f"unknown index profile: {profile_id}") from exc


def index_profile_from_snapshot(snapshot: dict[str, Any]) -> IndexProfile:
    payload = dict(snapshot)
    thresholds = {name: MetricThreshold(**dict(value)) for name, value in dict(payload.pop("thresholds")).items()}
    payload["target_gaps"] = tuple(payload["target_gaps"])
    return IndexProfile(thresholds=thresholds, **payload)
