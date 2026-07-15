from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from benchmarks.run import LocalRunBudget


OBSERVATION_TIMES_S = tuple(float(value) for value in range(1, 21))
FORMAL_CHECKPOINTS_S = (5.0, 10.0, 20.0)
FULL_CASE_IDS = (
    "jsplib_abz5",
    "jsplib_abz6",
    "jsplib_la16",
    "jsplib_la21",
    "jsplib_orb03",
    "jsplib_orb04",
    "qaplib_bur26a",
    "qaplib_bur26g",
    "qaplib_chr25a",
    "qaplib_els19",
    "qaplib_had20",
    "qaplib_kra30a",
    "qaplib_lipa20a",
    "qaplib_lipa20b",
    "qaplib_nug20",
    "qaplib_scr20",
    "qaplib_tai20b",
    "qaplib_tai30a",
    "qaplib_tai30b",
    "qaplib_tho30",
    "tsplib_a280",
    "tsplib_ch130",
    "tsplib_eil101",
    "tsplib_gil262",
    "tsplib_gr431",
    "tsplib_kroa150",
    "tsplib_lin318",
    "tsplib_pcb442",
    "tsplib_pr152",
    "tsplib_rat195",
    "tsplib_rd400",
    "tsplib_ts225",
)


@dataclass(frozen=True)
class EvaluationPreset:
    preset_id: str
    version: str
    final: bool
    seeds: tuple[int, ...]
    case_ids: tuple[str, ...]
    max_case_count: int
    time_limit_s: float = 20.0
    max_iterations: int | None = None
    observation_times_s: tuple[float, ...] = OBSERVATION_TIMES_S
    formal_checkpoints_s: tuple[float, ...] = FORMAL_CHECKPOINTS_S
    thread_count: int = 1
    worker_concurrency: int = 1
    trace_limit: int = 8

    def run_budget(self, seed: int) -> LocalRunBudget:
        if seed not in self.seeds:
            raise ValueError(f"seed {seed} does not belong to preset {self.preset_id}")
        return LocalRunBudget(
            seed=seed,
            max_iterations=self.max_iterations,
            time_limit_s=self.time_limit_s,
            population_size=16,
            trace_limit=self.trace_limit,
            thread_count=self.thread_count,
            observation_times_s=self.observation_times_s,
        )


FAST_DEVELOPMENT = EvaluationPreset(
    preset_id="ga_anytime_fast",
    version="1",
    final=False,
    seeds=(11, 59, 113),
    case_ids=FULL_CASE_IDS,
    max_case_count=6,
)

FULL_FINAL = EvaluationPreset(
    preset_id="ga_anytime_full",
    version="1",
    final=True,
    seeds=(11, 23, 47, 59, 71, 83, 97, 101, 113, 127),
    case_ids=FULL_CASE_IDS,
    max_case_count=32,
)


def get_evaluation_preset(name: str) -> EvaluationPreset:
    aliases = {
        "fast": FAST_DEVELOPMENT,
        FAST_DEVELOPMENT.preset_id: FAST_DEVELOPMENT,
        "full": FULL_FINAL,
        FULL_FINAL.preset_id: FULL_FINAL,
    }
    try:
        return aliases[name]
    except KeyError as exc:
        raise KeyError(f"unknown evaluation preset: {name}") from exc


def select_preset_cases(
    cases: Sequence[Mapping[str, Any]],
    *,
    preset: EvaluationPreset,
    target_family: str,
) -> tuple[str, ...]:
    available = {
        str(case.get("benchmark_id")): str(case.get("family"))
        for case in cases
        if case.get("benchmark_id") in preset.case_ids
    }
    ordered = [case_id for case_id in preset.case_ids if case_id in available]
    target_family = str(target_family)
    if target_family not in set(available.values()):
        raise ValueError(f"unknown target family for preset {preset.preset_id}: {target_family}")
    if preset.final:
        if len(ordered) != preset.max_case_count:
            raise ValueError(f"full preset requires {preset.max_case_count} fixed cases, found {len(ordered)}")
        return tuple(ordered)
    selected = [case_id for case_id in ordered if available[case_id] == target_family][:4]
    for family in sorted(set(available.values()) - {target_family}):
        candidates = [case_id for case_id in ordered if available[case_id] == family]
        if candidates:
            selected.append(candidates[0])
    return tuple(dict.fromkeys(selected))[: preset.max_case_count]
