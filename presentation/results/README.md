# Legacy Benchmark Results

This directory stores historical Git-managed benchmark result JSON under
`presentation/results/`.

The supported five-dimensional telemetry metrics publication path now uses
`benchmarks.telemetry_artifacts` to generate immutable artifact directories with
`manifest.json`, `rows.jsonl`, `curves.jsonl`, `throughput.jsonl`,
`five_dimensional_metrics.json`, `statistical_tests.json`, and `dashboard.json`.
Dashboard rendering should read those artifacts, not this legacy result summary
tree.

Current Phase:

- Phase 1 result JSON contract is present.
- Tiny sample runs are present.
- Phase 2 generated `index.json` and aggregate files are present.

Layout:

```text
presentation/results/
  index.json
  schema/
    run-v1.schema.json
  sample/
    ga/
      2026/
        06/
          sample-ga-20260622-000000-3f8a1d2.json
          sample-ga-20260622-000000-3f8a1d2/
            metrics.json
            solution.json
            trace.json
    alns/
      2026/
        06/
          sample-alns-20260622-000100-3f8a1d2.json
          sample-alns-20260622-000100-3f8a1d2/
            metrics.json
```

Do not append new facts to a shared `history.json`. Add a new run file instead.

Only when maintaining historical run summary files, regenerate legacy dashboard
data:

```bash
python -m benchmarks.presentation.generate_dashboard_data
```

Generated outputs:

```text
results/index.json
aggregates/leaderboard.json
aggregates/commit-history.json
aggregates/strategy-comparison.json
aggregates/runtime-quality.json
```

Use validation-only mode for legacy aggregate review:

```bash
python -m benchmarks.presentation.generate_dashboard_data --check
```
