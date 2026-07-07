# Strategy Telemetry Evaluation

OptAgent benchmark statistics are derived from canonical runtime telemetry, not
from solver logs, dashboard summaries, or ad-hoc diagnostics dictionaries.

Current pipeline:

```text
OptAgent runtime telemetry
        |
        v
benchmarks.telemetry_metrics
        |
        v
normalized rows / curves / derived metrics
        |
        v
benchmarks.telemetry_artifacts
        |
        v
immutable dashboard artifacts
        |
        v
benchmarks.presentation.dashboard
```

Runtime produces facts. Benchmarks derive metrics. Dashboards render published
artifacts.

## Inputs

Supported inputs are OptAgent `RunTelemetry` protobuf objects or JSON
projections generated from the protobuf contract. Required facts include run
identity, instance identity, budget, outcome, effort, progress events, search
state, framework extension fields, backend facts, environment, and schema
version.

Unsupported inputs are rejected:

- flat `solution.diagnostics` metrics;
- old `results.jsonl` rows;
- generated dashboard summaries;
- solver-private text logs.

Missing unsupported facts must remain `null` or `unsupported`; they must not be
encoded as zero.

## Derived Dimensions

### Effectiveness

Measures final solution quality:

- final objective;
- feasibility;
- absolute and relative gap to reference or best known solution;
- best-known-solution gap where a reference is available.

### Efficiency

Measures computational effort:

- wall-clock time;
- CPU time when reported;
- iteration count;
- evaluated candidate count;
- function/objective evaluation count;
- throughput;
- memory/RSS when reported.

### Robustness

Measures repeatability across matched runs:

- success rate;
- solved ratio;
- mean, median, variance, standard deviation;
- coefficient of variation;
- worst/best/quantile objective summaries.

### Anytime Performance

Measures quality as budget is consumed:

- incumbent curves;
- time-to-target and evaluations-to-target;
- empirical cumulative distribution data;
- primal integral where objective, reference, and time curve are available;
- trace truncation status.

Improvement, restart, and termination progress events are preserved before
ordinary sampled events.

### Statistical Validity

Measures whether observed differences are supported by sufficient matched data:

- Wilcoxon signed-rank test for paired strategy comparisons;
- Friedman test for multi-strategy instance blocks;
- Vargha-Delaney A12 as the primary effect size;
- Cliff's Delta as a secondary effect size;
- insufficient-data status with required and actual sample counts.

## Artifact Contract

`benchmarks.telemetry_artifacts` writes immutable artifact directories:

```text
manifest.json
rows.jsonl
curves.jsonl
throughput.jsonl
five_dimensional_metrics.json
statistical_tests.json
dashboard.json
```

`manifest.json` records schema version, generator, creation time, source count,
artifact checksums, and provenance. Dashboard code reads these artifacts only;
it does not recalculate metrics from runtime payloads.

## Governance Rules

- New runtime fields must be added to the canonical telemetry contract first.
- Framework-specific facts belong in governed extension namespaces and must have
  documented semantics.
- Benchmark code may add derived metrics without changing runtime ownership.
- Dashboard code must show insufficient or unsupported data explicitly instead
  of silently hiding it.
- Legacy scoring modules are not supported entrypoints and must not be
  reintroduced.

## Validation

Focused validation for telemetry and artifact changes:

```bash
PYTHONPATH=.. python -m pytest tests/test_telemetry_metrics.py tests/test_telemetry_artifacts.py
PYTHONPATH=.. python -m benchmarks.telemetry_artifacts <telemetry-json> --output-dir <artifact-dir>
PYTHONPATH=.. python -m benchmarks.presentation.dashboard <artifact-dir>
```
