# Repository Guidelines

## Project Structure

This repository is the `benchmarks` Python package for OptAgent benchmark cases,
telemetry metrics, and dashboard artifacts.

- `cases/`: benchmark case declarations and source-specific loaders.
- `presentation/`: suite execution, artifact dashboard rendering, and historical
  presentation helpers.
- `docs/`: current contracts and responsibility boundaries.
- `tests/`: telemetry, artifact, and case-governance regression tests.

## Supported Commands

Run commands from this directory with `PYTHONPATH=..`.

- `PYTHONPATH=.. python -m benchmarks.run --list-cases`
- `PYTHONPATH=.. python -m benchmarks.run --case tsplib_berlin52 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `PYTHONPATH=.. python -m benchmarks.presentation.suite --list-inventory --family sequence_blackbox_tsp --tier smoke --timestamp local-smoke`
- `PYTHONPATH=.. python -m benchmarks.telemetry_artifacts <telemetry-json> --output-dir <artifact-dir>`
- `PYTHONPATH=.. python -m benchmarks.presentation.dashboard <artifact-dir>`
- `python -m compileall cases presentation telemetry_metrics.py telemetry_artifacts.py`

## Coding Style

Use standard Python style with 4-space indentation and type annotations where
they clarify data contracts. Prefer dataclasses and explicit dictionaries that
match documented artifact contracts over ad-hoc tuples.

Benchmark ids are lowercase with source prefixes, such as `jsplib_ft06`,
`psplib_j90_1_1`, `qaplib_nug12`, and `tsplib_berlin52`.

## Testing

Run focused tests for the touched surface:

- case declarations: `tests/test_case_implementation_integrity.py`
- telemetry metrics: `tests/test_telemetry_metrics.py`
- artifact publication: `tests/test_telemetry_artifacts.py`

For case changes, also run `compileall`, `--list-cases`, and at least one small
`benchmarks.run` invocation for the affected family.

## Results And Artifacts

Canonical five-dimensional dashboard data is published through
`benchmarks.telemetry_artifacts`. Generated artifact directories are immutable
evidence and should include `manifest.json` plus checksummed metric files.

Historical `presentation/results/` and `presentation/aggregates/` files are
legacy static dashboard facts. Do not edit generated indexes or aggregates by
hand.
