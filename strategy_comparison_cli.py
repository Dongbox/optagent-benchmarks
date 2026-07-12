from __future__ import annotations

import argparse
import json
import sys

from benchmarks.comparison_protocol import get_comparison_protocol
from benchmarks.strategy_baselines import promote_comparison_baseline
from benchmarks.strategy_comparison_runner import run_protocol_pair


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or compare OptAgent GA strategy comparisons.")
    commands = parser.add_subparsers(dest="command", required=True)
    compare = commands.add_parser("compare", help="Compare two immutable run artifacts.")
    compare.add_argument("--baseline", required=True)
    compare.add_argument("--challenger", required=True)
    compare.add_argument("--output-dir", required=True)
    run_pair = commands.add_parser("run-pair", help="Run baseline and challenger wheels through one protocol.")
    run_pair.add_argument("--protocol", required=True)
    run_pair.add_argument("--baseline-wheel", required=True)
    run_pair.add_argument("--challenger-wheel", required=True)
    run_pair.add_argument("--output-dir", required=True)
    run_pair.add_argument("--python-executable", default=None)
    run_pair.add_argument("--baseline-commit", default="unknown")
    run_pair.add_argument("--challenger-commit", default="unknown")
    run_pair.add_argument("--allow-download", action="store_true")
    promote = commands.add_parser("promote", help="Explicitly promote an improved comparison to a baseline registry.")
    promote.add_argument("--comparison-dir", required=True)
    promote.add_argument("--registry", required=True)
    promote.add_argument("--approved-by", required=True)
    args = parser.parse_args()

    if args.command == "compare":
        from benchmarks.strategy_comparison import compare_run_artifacts

        result = compare_run_artifacts(args.baseline, args.challenger, args.output_dir)
    elif args.command == "run-pair":
        result = run_protocol_pair(
            protocol=get_comparison_protocol(args.protocol),
            baseline_wheel=args.baseline_wheel,
            challenger_wheel=args.challenger_wheel,
            output_dir=args.output_dir,
            bootstrap_python=args.python_executable or sys.executable,
            allow_download=bool(args.allow_download),
            baseline_commit=args.baseline_commit,
            challenger_commit=args.challenger_commit,
        )
    else:
        result = promote_comparison_baseline(
            args.comparison_dir,
            args.registry,
            approved_by=args.approved_by,
        )
    print(json.dumps(result, indent=2, ensure_ascii=True, sort_keys=True))
    if args.command == "promote":
        return 0
    return 0 if result["verdict"] not in {"invalid", "incompatible", "regressed"} else 1
