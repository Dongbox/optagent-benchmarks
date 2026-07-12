# Repository Guidelines

## Repository Boundary

This is the independently maintained `optagent-benchmarks` repository. Do not
assume access to an OptAgent source checkout. Runtime validation must use an
explicit OptAgent wheel unless a task specifically concerns integration with a
local source tree.

Clone or check out this repository as `benchmarks/`. Run commands from this
directory with `PYTHONPATH=..` so the package is importable as `benchmarks`.

## Ownership

- `cases/` owns case metadata, data loading, references, model construction,
  solution decoding, and independent verification.
- `run.py` owns lightweight execution rows.
- `authority.py` and `authoritative_baseline.py` own capability evidence.
- `comparison_*` and `strategy_comparison*` own paired GA evidence.
- `telemetry_metrics.py` and `telemetry_artifacts.py` own canonical telemetry
  metrics and immutable dashboard artifacts.
- `presentation/` owns rendering, navigation, and historical adapters only.

Runtime facts must come from canonical OptAgent telemetry. Do not derive new
statistics from flat diagnostics, private runner rows, solver logs, or dashboard
summaries.

## Validation

Run focused tests while editing and the full suite before completion:

```bash
PYTHONPATH=.. ./.venv/bin/python -m pytest -q
./.venv/bin/ruff check .
./.venv/bin/python -m compileall cases presentation *.py
PYTHONPATH=.. ./.venv/bin/python -m benchmarks.run --list-cases
```

For case changes, run at least one small `--no-download` case in the affected
family. For artifact or comparison changes, verify CLI help and immutable output
behavior.

## Documentation

`README.md` is the user entrypoint. Canonical policy lives only in:

- `docs/authority.md`
- `docs/ga-comparison.md`
- `docs/telemetry-artifacts.md`
- `cases/README.md` and short source-specific notes

Do not duplicate full case inventories in Markdown; the registry and
`benchmarks.run --list-cases` are authoritative. Do not link to private or
parent-repository documentation as a prerequisite.

## Artifacts

Authority, comparison, and telemetry output directories are immutable evidence.
Never overwrite or hand-edit generated manifests, row streams, indexes, or
aggregates. Historical files under `presentation/results/` are legacy facts and
must not become inputs to current metric computation.
