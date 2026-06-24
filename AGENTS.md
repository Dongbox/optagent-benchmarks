# Repository Guidelines

## Project Structure & Module Organization

This repository is the `benchmarks` Python package for OptAgent benchmark cases and dashboard data. Core benchmark declarations live in `cases/`, grouped by source library and domain, for example `cases/tsplib/routing/tsp/` and `cases/qaplib/assignment/quadratic_assignment/`. Presentation and artifact tooling lives in `presentation/`, including suite runners, dashboard publishers, aggregate generation, and telemetry helpers. Long-lived dashboard facts are checked in under `presentation/results/`; generated summaries are under `presentation/aggregates/`. Design notes and data contracts live in `docs/`.

## Build, Test, and Development Commands

Run commands from this directory with `PYTHONPATH=..` when invoking `benchmarks.*` modules locally.

- `PYTHONPATH=.. python -m benchmarks.run --list-cases`: list registered benchmark cases.
- `PYTHONPATH=.. python -m benchmarks.run --case tsplib_berlin52 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`: quick local smoke run for one case.
- `PYTHONPATH=.. python -m benchmarks.presentation.suite --list-inventory --family sequence_blackbox_tsp --tier smoke --timestamp local-smoke`: validate suite inventory without running solvers.
- `PYTHONPATH=.. python -m benchmarks.presentation.generate_dashboard_data --check`: verify generated dashboard index and aggregates are current.
- `python -m compileall cases presentation`: catch Python syntax errors quickly.

CI uses Python 3.12 and builds or installs OptAgent before executing benchmark suites.

## Coding Style & Naming Conventions

Use standard Python style with 4-space indentation, type annotations where they clarify data contracts, and `from __future__ import annotations` in new modules. Keep benchmark ids lowercase with library prefixes, such as `jsplib_ft06`, `psplib_j90_1_1`, or `tsplib_berlin52`. Prefer dataclasses and explicit dictionaries matching the existing result contracts over ad hoc tuples.

## Testing Guidelines

There is no local test suite in this package; use focused smoke commands instead. For case changes, run `compileall`, `--list-cases`, and at least one tiny `benchmarks.run` invocation for the affected family. For dashboard result changes, always run `generate_dashboard_data --check` or regenerate with `python -m benchmarks.presentation.generate_dashboard_data`.

## Commit & Pull Request Guidelines

Recent commits use short imperative subjects such as `Document dashboard data source boundaries` and `Regenerate benchmark dashboard data`. Keep commits focused: separate code changes from large generated result updates when practical. Pull requests should describe changed benchmark families, commands run, whether downloads were enabled, and any updates to `presentation/results/` or `presentation/aggregates/`. Link related issues or OptAgent commits when benchmark output depends on upstream behavior.

## Results & Configuration Notes

Do not edit `presentation/results/index.json` or `presentation/aggregates/*.json` by hand; regenerate them. Add new immutable run summary JSON files instead of rewriting historical facts unless correcting a documented data error.
