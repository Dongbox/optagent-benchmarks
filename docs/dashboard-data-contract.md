# Dashboard Artifact Contract

The supported dashboard input is an immutable artifact directory produced by
`benchmarks.telemetry_artifacts`.

Release evidence produced by `benchmarks.authoritative_baseline` is a separate
artifact type and is never a supported dashboard input.

Dashboard code must not scan runner workspaces, solve logs, raw telemetry
payloads, or Git-managed historical result trees. It reads published artifacts
and renders them as-is.

## Artifact Directory

Required files:

```text
manifest.json
rows.jsonl
curves.jsonl
throughput.jsonl
five_dimensional_metrics.json
statistical_tests.json
dashboard.json
```

`manifest.json` is the entrypoint. It records:

- artifact schema version;
- generator name and version;
- creation time;
- source telemetry count;
- source identity and provenance;
- per-file checksum and byte size.

Dashboard renderers should verify the manifest before using the remaining
files. Missing optional metric values must be displayed as `unsupported` or
`insufficient_data`, not coerced to zero.

## File Roles

- `rows.jsonl`: normalized per-run facts and derived row-level metrics.
- `curves.jsonl`: anytime curve samples, incumbent points, and trace truncation
  status.
- `throughput.jsonl`: effort and throughput summaries by run/strategy/instance.
- `five_dimensional_metrics.json`: grouped Effectiveness, Efficiency,
  Robustness, Anytime, and Statistical Validity summaries.
- `statistical_tests.json`: paired and grouped statistical comparison results.
- `dashboard.json`: presentation-ready summary assembled from the other
  artifacts.

## Ownership

- Runtime owns telemetry facts.
- Benchmarks own metric derivation and artifact publication.
- Dashboard owns rendering and navigation only.

Dashboard code must not compute gap, rank, primal integral, ECDF, statistical
tests, or effect sizes from raw runtime payloads.

## Local Smoke

Publish artifacts:

```bash
PYTHONPATH=.. python -m benchmarks.telemetry_artifacts \
  tests/fixtures/telemetry/phase0/native_search_minimal.json \
  --output-dir /tmp/optagent-telemetry-artifacts \
  --reference toy-001=10.0
```

Render dashboard files:

```bash
PYTHONPATH=.. python -m benchmarks.presentation.dashboard \
  /tmp/optagent-telemetry-artifacts \
  --output-root /tmp/optagent-telemetry-dashboard
```

## Historical Results

`presentation/results/` and `presentation/aggregates/` are retained only for
historical static facts. They are not the current five-dimensional telemetry
metrics contract.
