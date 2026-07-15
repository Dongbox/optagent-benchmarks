from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Sequence

from benchmarks.artifact_io import checksum_json
from benchmarks.evaluation_presets import get_evaluation_preset, select_preset_cases
from benchmarks.run import all_cases, case_object_by_id, run_benchmark_case
from benchmarks.telemetry_artifacts import publish_telemetry_artifacts
from benchmarks.telemetry_metrics import load_run_telemetry


def run_evaluation(
    *,
    preset_name: str,
    target_family: str,
    strategy: str,
    output_dir: str | Path,
    allow_download: bool = True,
    created_at: str | None = None,
    optagent_commit: str | None = None,
    benchmarks_commit: str | None = None,
) -> dict[str, Any]:
    preset = get_evaluation_preset(preset_name)
    inventory = all_cases()
    case_ids = select_preset_cases(
        inventory,
        preset=preset,
        target_family=target_family,
    )
    declarations = {row["benchmark_id"]: row for row in inventory}
    payloads: list[dict[str, Any]] = []
    contexts: list[dict[str, Any]] = []
    for seed in preset.seeds:
        budget = preset.run_budget(seed)
        for case_id in case_ids:
            case = case_object_by_id(case_id)
            rows = run_benchmark_case(
                case,
                strategies=(strategy,),
                allow_download=allow_download,
                budget=budget,
            )
            if len(rows) != 1:
                raise ValueError(f"evaluation expected one row for {case_id}, found {len(rows)}")
            row = rows[0]
            telemetry = row.get("telemetry")
            if not isinstance(telemetry, dict) or not telemetry:
                raise ValueError(f"evaluation row is missing canonical telemetry: {case_id}")
            load_run_telemetry(telemetry)
            declaration = declarations[case_id]
            payloads.append(telemetry)
            contexts.append(
                {
                    "benchmark_id": case_id,
                    "family": row["family"],
                    "reference_objective": row.get("reference_objective"),
                    "case_checksum": checksum_json(
                        {
                            "benchmark_id": case_id,
                            "family": row["family"],
                            "reference": declaration.get("reference"),
                            "size": declaration.get("size"),
                        }
                    ),
                    "observations": row.get("observations") or [],
                    "solution_snapshots": row.get("solution_snapshots") or {},
                    "observation_verification_passed": row.get("observation_verification_passed"),
                    "observation_verification_errors": row.get("observation_verification_errors") or [],
                    "preset_id": preset.preset_id,
                    "preset_version": preset.version,
                    "review_mode": "single_family_focus",
                    "target_families": [target_family],
                    "formal_checkpoints_s": list(preset.formal_checkpoints_s),
                    "observation_times_s": list(preset.observation_times_s),
                    "expected_seed_count": len(preset.seeds),
                }
            )
    result = publish_telemetry_artifacts(
        payloads,
        output_dir,
        benchmark_contexts=contexts,
        source_label=f"evaluation:{preset.preset_id}:{preset.version}",
        created_at=created_at or datetime.now(timezone.utc).isoformat(),
        optagent_commit=optagent_commit,
        benchmarks_commit=benchmarks_commit,
    )
    result["evaluation"] = {
        "preset_id": preset.preset_id,
        "preset_version": preset.version,
        "final": preset.final,
        "review_mode": "single_family_focus",
        "target_families": [target_family],
        "case_ids": list(case_ids),
        "seeds": list(preset.seeds),
    }
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a fixed OptAgent strategy evaluation preset.")
    parser.add_argument("--preset", choices=("fast", "full"), required=True)
    parser.add_argument("--target-family", required=True)
    parser.add_argument("--strategy", default="ga")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--no-download", action="store_true")
    parser.add_argument("--created-at")
    parser.add_argument("--optagent-commit")
    parser.add_argument("--benchmarks-commit")
    args = parser.parse_args(argv)
    result = run_evaluation(
        preset_name=args.preset,
        target_family=args.target_family,
        strategy=args.strategy,
        output_dir=args.output_dir,
        allow_download=not args.no_download,
        created_at=args.created_at,
        optagent_commit=args.optagent_commit,
        benchmarks_commit=args.benchmarks_commit,
    )
    print(json.dumps(result["evaluation"], indent=2, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
