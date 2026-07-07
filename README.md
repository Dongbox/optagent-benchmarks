# OptAgent Benchmarks

This package contains OptAgent benchmark case declarations, lightweight local
case execution, telemetry metric derivation, and dashboard artifact rendering.

Run commands from the parent checkout with `PYTHONPATH=..`, or from an installed
environment where `benchmarks` is importable.

## Supported Entrypoints

- `benchmarks.run`: lightweight single-case runner.
- `benchmarks.presentation.suite`: suite runner and run workspace producer.
- `benchmarks.telemetry_metrics`: canonical telemetry-to-metrics library.
- `benchmarks.telemetry_artifacts`: immutable artifact publisher for dashboard
  consumption.
- `benchmarks.presentation.dashboard`: dashboard markdown/JSON renderer from
  published telemetry artifacts.

Legacy flat scoring scripts and ad-hoc diagnostics readers are intentionally
removed. New statistics must start from OptAgent canonical runtime telemetry.

## Case Runner

List cases:

```bash
PYTHONPATH=.. python -m benchmarks.run --list-cases
```

Run a local smoke case:

```bash
PYTHONPATH=.. python -m benchmarks.run \
  --case tsplib_berlin52 \
  --strategy ga \
  --no-download \
  --max-iterations 1 \
  --population-size 4 \
  --time-limit-s 0.1
```

Useful options:

- `--case <benchmark_id>`: select one or more cases.
- `--family <family>`: select cases by family.
- `--tier <smoke|calibration|full>`: select by benchmark tier.
- `--strategy <name>`: select one or more strategies.
- `--model-style <style>`: select supported modeling variants.
- `--no-download`: fail if required raw data is missing locally.
- `--max-iterations`, `--time-limit-s`, `--population-size`, `--trace-limit`:
  set local run budgets.

Programmatic use:

```python
from benchmarks.run import LocalRunBudget, run_case

rows = run_case(
    "tsplib_berlin52",
    strategies=("ga",),
    allow_download=False,
    budget=LocalRunBudget(max_iterations=1, population_size=4, time_limit_s=0.1),
)
```

## Suite Runs

Use `presentation.suite` when a run directory, inventory, row streams, reports,
or CI-style execution metadata are needed:

```bash
PYTHONPATH=.. python -m benchmarks.presentation.suite \
  --family sequence_blackbox_tsp \
  --tier smoke \
  --strategy ga \
  --timestamp local-smoke
```

Suite run directories are execution evidence. Dashboard-facing metrics should be
published through telemetry artifacts, not by making dashboard code read runner
private files directly.

## Five-Dimensional Metrics

`benchmarks.telemetry_metrics` accepts OptAgent canonical runtime telemetry
protobuf objects or JSON projections generated from protobuf. It rejects legacy
flat diagnostics, runner-private rows, and dashboard summaries.

Derived dimensions:

- Effectiveness
- Efficiency
- Robustness
- Anytime Performance
- Statistical Validity

Programmatic use:

```python
from benchmarks.telemetry_metrics import (
    build_metric_dataset,
    derive_five_dimensional_metrics,
)

dataset = build_metric_dataset(run_telemetry_payloads)
metrics = derive_five_dimensional_metrics(dataset, references=best_known_objectives)
```

Publish immutable dashboard artifacts:

```python
from benchmarks.telemetry_artifacts import publish_telemetry_artifacts

publish_telemetry_artifacts(
    run_telemetry_payloads,
    "docs/evals/benchmark-suite/artifacts/local-smoke",
    references=best_known_objectives,
)
```

Artifact directories contain:

```text
manifest.json
rows.jsonl
curves.jsonl
throughput.jsonl
five_dimensional_metrics.json
statistical_tests.json
dashboard.json
```

Render a dashboard from an artifact directory:

```bash
PYTHONPATH=.. python -m benchmarks.presentation.dashboard \
  docs/evals/benchmark-suite/artifacts/local-smoke \
  --output-root /tmp/optagent-dashboard
```

## Layout

- `cases/`: benchmark declarations, source-specific data loaders, and case
  model builders.
- `presentation/`: suite execution, dashboard rendering, and historical result
  helpers.
- `docs/`: current contracts and responsibility boundaries.
- `tests/`: governance and telemetry regression tests.

Case source details live in each source directory, for example
`cases/tsplib/README.md`, `cases/jsplib/README.md`, and
`cases/custom/README.md`.
