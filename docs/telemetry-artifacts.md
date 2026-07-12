# Telemetry, Metrics, And Artifacts

## Data Flow

Benchmark statistics start from canonical OptAgent runtime telemetry:

```text
OptAgent wheel
    -> canonical RunTelemetry
    -> benchmarks.telemetry_metrics
    -> normalized rows, curves, and metrics
    -> benchmarks.telemetry_artifacts
    -> immutable artifact directory
    -> benchmarks.presentation.dashboard
```

Runtime owns facts. Benchmarks own metric derivation and artifact publication.
Dashboard code owns rendering only.

Unsupported inputs are rejected:

- flat solution diagnostics;
- runner-private row streams;
- solver text logs;
- dashboard summaries;
- Git-managed historical result trees.

Missing facts remain `unsupported`, `insufficient_data`, or `null`; they are
never silently converted to zero.

## Five Dimensions

### Effectiveness

Final feasibility, objective, absolute/relative reference gap, and normalized
quality summaries.

### Efficiency

Wall time, CPU time when available, iteration and evaluated-candidate counts,
function evaluations, throughput, and memory when reported.

### Robustness

Success rate, solved ratio, distribution summaries, variance, coefficient of
variation, quantiles, and worst-case normalized gap.

### Anytime Performance

Incumbent curves, time/evaluations to target, ECDF data, primal integral,
normalized primal integral, missed-target penalties, and trace completeness.

### Statistical Validity

Matched Wilcoxon tests, multi-strategy Friedman tests, Vargha-Delaney A12,
Cliff's Delta, multiplicity correction, and explicit insufficient-data status.

Strategy optimization feedback interprets these benchmark-owned metrics into
conservative focus areas. It does not select a user strategy or change runtime
configuration.

## Case, Runner, And Presentation Boundary

Cases expose domain-owned solution facts through:

```python
case.solution_metrics(solution, **build_kwargs) -> dict[str, Any]
```

Allowed outputs include objective recomputation, reference objective, decoded
solution, model style, and small domain diagnostics needed for audit.

Cases do not own solver-common status/runtime fields, derived gap fields, or
dashboard display truncation. `run.py` assembles lightweight rows.
`telemetry_metrics.py` derives canonical statistics. `presentation/` renders
published data and must not recalculate gaps, ranks, integrals, effect sizes, or
statistical tests.

## Artifact Contract

`benchmarks.telemetry_artifacts` writes an immutable directory:

```text
manifest.json
rows.jsonl
curves.jsonl
throughput.jsonl
five_dimensional_metrics.json
statistical_tests.json
strategy_optimization_feedback.json
dashboard.json
```

`manifest.json` is the entrypoint and records schema version, generator,
creation time, source count, provenance, checksums, and byte sizes. Consumers
verify it before reading other files.

File roles:

- `rows.jsonl`: normalized per-run facts and row-level metrics;
- `curves.jsonl`: incumbent and checkpoint curves with completeness state;
- `throughput.jsonl`: effort and throughput summaries;
- `five_dimensional_metrics.json`: grouped metric dimensions;
- `statistical_tests.json`: paired and grouped statistical evidence;
- `strategy_optimization_feedback.json`: signals and conservative focus areas;
- `dashboard.json`: presentation-ready materialized summary.

Authority artifacts and GA comparison artifacts are different evidence types.
They are never accepted as dashboard telemetry input.

## Publish And Render

```bash
./.venv/bin/python benchmark.py publish-telemetry \
  /path/to/run-telemetry.json \
  --output-dir /tmp/telemetry-artifacts \
  --reference toy-001=10.0
```

```bash
./.venv/bin/python benchmark.py dashboard \
  /tmp/telemetry-artifacts \
  --output-root /tmp/telemetry-dashboard
```

Output directories are immutable. Publish a new directory for every run.

## Historical Results

`benchmarks/presentation/results/` and `benchmarks/presentation/aggregates/` contain legacy static
facts used by older dashboard flows. Do not edit generated indexes by hand and
do not use historical files as current metric inputs.
