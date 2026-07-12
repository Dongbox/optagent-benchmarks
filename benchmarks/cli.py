from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
import sys


Command = tuple[str, Callable[[Sequence[str] | None], int]]


def _commands() -> dict[str, Command]:
    from benchmarks.authoritative_baseline import main as authority_main
    from benchmarks.presentation.compare import main as compare_runs_main
    from benchmarks.presentation.dashboard import main as dashboard_main
    from benchmarks.presentation.generate_dashboard_data import main as generate_results_index_main
    from benchmarks.presentation.publish_dashboard_results import main as publish_results_main
    from benchmarks.presentation.suite import main as suite_main
    from benchmarks.run import main as run_main
    from benchmarks.strategy_comparison_cli import main as compare_ga_main
    from benchmarks.telemetry_artifacts import main as publish_telemetry_main

    return {
        "list-cases": ("List registered benchmark cases.", lambda argv: run_main(["--list-cases", *(argv or ())])),
        "run": ("Run one benchmark case for local diagnosis.", run_main),
        "suite": ("Run an artifact-producing benchmark suite.", suite_main),
        "authority": ("Produce an authoritative release-gate baseline.", authority_main),
        "compare-ga": ("Run, compare, or promote paired GA evidence.", compare_ga_main),
        "publish-telemetry": ("Publish canonical telemetry metric artifacts.", publish_telemetry_main),
        "dashboard": ("Render a dashboard from immutable telemetry artifacts.", dashboard_main),
        "compare-runs": ("Compare two benchmark suite run directories.", compare_runs_main),
        "publish-results": ("Publish suite rows as dashboard result JSON.", publish_results_main),
        "generate-results-index": ("Regenerate dashboard indexes and aggregates.", generate_results_index_main),
    }


def _parser(commands: dict[str, Command]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python benchmark.py",
        description="Run and evaluate OptAgent benchmark evidence.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    commands = _commands()
    parser = _parser(commands)
    if not arguments:
        parser.print_help()
        return 0
    if arguments[0] in {"-h", "--help"}:
        parser.print_help()
        print("\ncommands:")
        for name, (description, _) in commands.items():
            print(f"  {name:<24} {description}")
        return 0

    command_name = arguments[0]
    if command_name not in commands:
        parser.error(f"unknown command: {command_name}")
    _, command = commands[command_name]
    return command(arguments[1:])


if __name__ == "__main__":
    raise SystemExit(main())
