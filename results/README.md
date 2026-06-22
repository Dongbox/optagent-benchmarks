# Benchmark Results

This directory stores Git-managed benchmark result JSON.

Current Phase:

- Phase 1 result JSON contract is present.
- Tiny sample runs are present.
- Phase 2 generated `index.json` and aggregate files are present.

Layout:

```text
results/
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

After adding or changing run summary files, regenerate dashboard data:

```bash
python -m benchmarks.runners.generate_dashboard_data
```

Generated outputs:

```text
results/index.json
aggregates/leaderboard.json
aggregates/commit-history.json
aggregates/strategy-comparison.json
aggregates/runtime-quality.json
```

Use validation-only mode in review or CI:

```bash
python -m benchmarks.runners.generate_dashboard_data --check
```
