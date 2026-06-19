from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_ROOT = REPO_ROOT / "docs" / "evals" / "benchmark-suite" / "runs"


def utc_timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")


def ensure_run_dir(output_root: str | Path = DEFAULT_RUN_ROOT, *, timestamp: str | None = None) -> Path:
    run_dir = Path(output_root) / (timestamp or utc_timestamp())
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def write_json(path: str | Path, payload: Any) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    with Path(path).open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def objective_gap(objective: float | int | None, reference: float | int | None) -> dict[str, float | None]:
    if objective is None or reference is None:
        return {"gap_abs": None, "gap_rel": None}
    gap_abs = float(objective) - float(reference)
    denominator = abs(float(reference))
    return {
        "gap_abs": gap_abs,
        "gap_rel": gap_abs / denominator if denominator else None,
    }


def summarize_solution_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "strategy",
        "strategy_source",
        "termination_reason",
        "iterations",
        "attempted_moves",
        "accepted_moves",
        "domain_best_sequence_penalty",
        "ga_generation_count",
        "ga_mutation_portfolio",
        "ga_offspring_generated",
        "ga_offspring_evaluated",
        "ga_tabu_improvement_count",
        "alns_iterations",
        "alns_candidates_evaluated",
        "alns_candidates_accepted",
        "alns_acceptance_model",
        "external_batch_count",
        "external_rows_requested",
        "external_cache_hits",
        "external_cache_misses",
        "external_duplicate_rows_coalesced",
        "budget",
        "seed",
    )
    return {key: metadata[key] for key in keys if key in metadata}
