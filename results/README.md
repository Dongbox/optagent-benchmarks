# Benchmark Results

This directory stores Git-managed benchmark result JSON.

Current Phase:

- Phase 1 result JSON contract is present.
- Tiny sample runs are present.
- Generated `index.json` and aggregate files are planned for Phase 2.

Layout:

```text
results/
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
