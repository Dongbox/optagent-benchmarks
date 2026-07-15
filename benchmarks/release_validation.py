from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from benchmarks.cases.registry import benchmark_cases, default_model_styles_for_family
from benchmarks.run import case_object_by_id, default_strategy_names_for_family


RELEASE_VALIDATION_SEEDS = (11, 23, 47, 59, 71, 83, 97, 101, 113, 127)
REPEAT_SEEDS = (11, 59, 113)
LINUX_FULL_SEED = 11
REPRESENTATIVE_CASE_IDS = (
    "psplib_j90_1_1",
    "psplib_j90_1_8",
    "miplib2017_50v-10",
    "miplib2017_reblock115",
    "fjsplib_sfjs02",
    "fjsplib_mfjs07",
    "jsplib_ft06",
    "jsplib_abz5",
    "tsplib_burma14",
    "tsplib_a280",
    "qaplib_had12",
    "qaplib_had20",
    "custom_steel_sequence_toy",
    "custom_steel_sequence_bundled_head40",
)


def build_release_plan() -> dict[str, Any]:
    cases = benchmark_cases()
    by_id = {str(case["benchmark_id"]): case for case in cases}
    missing = sorted(set(REPRESENTATIVE_CASE_IDS) - set(by_id))
    if missing:
        raise ValueError(f"release validation cases are not registered: {', '.join(missing)}")
    representative = []
    for case_id in REPRESENTATIVE_CASE_IDS:
        case = by_id[case_id]
        family = str(case["family"])
        exact = family == "exact_linear_mip"
        representative.append(
            {
                "benchmark_id": case_id,
                "family": family,
                "tier": str(case["tier"]),
                "strategies": list(default_strategy_names_for_family(family)),
                "model_styles": list(default_model_styles_for_family(family)) or [None],
                "seeds": [0] if exact else list(RELEASE_VALIDATION_SEEDS),
                "repeat_seeds": [] if exact else list(REPEAT_SEEDS),
                "repeat_count": 1 if exact else 3,
            }
        )
    return {
        "schema_version": 1,
        "plan_id": "optagent-release-validation-py312-v1",
        "representative_cases": representative,
        "linux_full": {
            "seed": LINUX_FULL_SEED,
            "case_ids": sorted(by_id),
            "cases": [
                {
                    "benchmark_id": case_id,
                    "family": str(by_id[case_id]["family"]),
                    "tier": str(by_id[case_id]["tier"]),
                    "strategies": list(default_strategy_names_for_family(str(by_id[case_id]["family"]))),
                    "model_styles": list(default_model_styles_for_family(str(by_id[case_id]["family"]))) or [None],
                }
                for case_id in sorted(by_id)
            ],
        },
    }


def prepare_release_data() -> dict[str, Any]:
    plan = build_release_plan()
    for case_id in plan["linux_full"]["case_ids"]:
        case_object_by_id(case_id).build_model(allow_download=True)
    case_root = Path(__file__).resolve().parent / "cases"
    files = []
    for path in sorted(case_root.glob("**/raw/*")):
        if not path.is_file():
            continue
        files.append(
            {
                "path": str(path.relative_to(case_root)),
                "size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    if not files:
        raise RuntimeError("release data preparation produced no raw benchmark files")
    return {"schema_version": 1, "files": files}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the fixed OptAgent release-validation benchmark plan.")
    parser.add_argument("--output")
    parser.add_argument("--prepare-data", action="store_true")
    parser.add_argument("--data-manifest")
    args = parser.parse_args(argv)
    plan = build_release_plan()
    if args.prepare_data:
        manifest = prepare_release_data()
        plan["data_manifest"] = manifest
        if args.data_manifest:
            Path(args.data_manifest).write_text(
                json.dumps(manifest, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8"
            )
    payload = json.dumps(plan, indent=2, ensure_ascii=True, sort_keys=True) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as stream:
            stream.write(payload)
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
