# Repository Guidelines

## Repository Boundary

This is the independently maintained `optagent-benchmarks` repository. Do not
assume access to an OptAgent source checkout. Runtime validation uses an
explicit OptAgent wheel unless a task specifically concerns local integration.

Run commands from the repository root through the single public entrypoint:

```bash
./.venv/bin/python benchmark.py <command>
```

Do not require a particular checkout directory name, `PYTHONPATH`, editable
installation, or installation of the benchmark repository itself.

## Ownership

- `benchmark.py` and `benchmarks/cli.py` own the external command interface.
- `benchmarks/cases/` owns case metadata, data loading, references, model construction, decoding, and verification.
- `benchmarks/run.py` owns lightweight execution rows.
- `benchmarks/authority.py` and `benchmarks/authoritative_baseline.py` own capability evidence.
- `benchmarks/comparison_*` and `benchmarks/strategy_comparison*` own paired GA evidence.
- `benchmarks/telemetry_metrics.py` and `benchmarks/telemetry_artifacts.py` own canonical metrics and artifacts.
- `benchmarks/presentation/` owns rendering, navigation, and historical adapters only.

Runtime facts must come from canonical OptAgent telemetry. Do not derive new
statistics from flat diagnostics, private runner rows, solver logs, or dashboard
summaries.

## Validation

```bash
./.venv/bin/python -m pytest -q
./.venv/bin/ruff check benchmark.py benchmarks tests
./.venv/bin/python -m compileall benchmark.py benchmarks tests
./.venv/bin/python benchmark.py list-cases --tier smoke
```

For case changes, run at least one small `--no-download` case in the affected
family. For artifact or comparison changes, verify CLI help and immutable output
behavior.

## Documentation

`README.md` is the user entrypoint. Canonical policy lives only in
`docs/authority.md`, `docs/ga-comparison.md`, `docs/telemetry-artifacts.md`, and
short notes under `benchmarks/cases/`.

Do not duplicate full case inventories in Markdown. The registry and
`python benchmark.py list-cases` are authoritative. Do not link to private or
parent-repository documentation as a prerequisite.

## Artifacts

Authority, comparison, and telemetry output directories are immutable evidence.
Never overwrite or hand-edit generated manifests, row streams, indexes, or
aggregates. Historical files under `benchmarks/presentation/results/` are legacy
facts and must not become inputs to current metric computation.
