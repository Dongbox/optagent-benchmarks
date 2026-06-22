# Result JSON Contract

This document defines Phase 1 benchmark result files for `optagent-benchmarks`.

The current fact layer is Git-managed JSON. Each benchmark run writes a new immutable summary file and, when useful, a sibling artifact directory. Generated indexes and aggregates are Phase 2 concerns.

## Run Summary Path

Run summaries live at:

```text
results/<benchmark-group>/<strategy>/<yyyy>/<mm>/<run-id>.json
```

Example:

```text
results/sample/ga/2026/06/sample-ga-20260622-000000-3f8a1d2.json
```

## Run ID

`run_id` must be stable and file-system safe:

```text
<benchmark-group>-<strategy>-<yyyymmdd>-<hhmmss>-<short-optagent-commit>
```

Rules:

- use lowercase ASCII words separated by `-`;
- include the strategy name;
- include UTC date and time;
- include the short OptAgent commit;
- do not reuse a `run_id` for different content.

## Summary JSON

The summary JSON is the default file read by generated indexes and dashboard aggregates.

Required top-level fields:

- `schema_version`
- `run_id`
- `benchmark_group`
- `benchmark_id`
- `family`
- `tier`
- `strategy`
- `strategy_profile`
- `strategy_config`
- `seed`
- `optagent`
- `benchmarks`
- `environment`
- `metrics`
- `artifacts`
- `created_at`

Required identity fields:

- `optagent.version`
- `optagent.commit`
- `optagent.commit_url`
- `optagent.wheel_sha256`
- `benchmarks.commit`
- `benchmarks.commit_url`

Required metric fields:

- `status`
- `feasible`
- `runtime_ms`

Successful rows should also include:

- `objective`
- `best_cost`
- `reference_cost`
- `gap_rel`
- `time_to_first_feasible_ms`
- `time_to_best_ms`

Error rows must still be written and must include:

- `metrics.status = "error"`
- `metrics.feasible = false`
- `metrics.error_type`
- `metrics.error_message`

## Artifact Directory

Optional larger artifacts live next to the summary JSON:

```text
results/<benchmark-group>/<strategy>/<yyyy>/<mm>/<run-id>/
  metrics.json
  solution.json
  trace.json
```

Rules:

- `metrics.json` contains full metric details.
- `solution.json` is optional and may be absent for failed runs.
- `trace.json` is optional and may be absent when the run has no trace.
- summary JSON `artifacts` values are repository-relative paths.

## Schema

The current JSON Schema is:

```text
results/schema/run-v1.schema.json
```

The schema is intentionally conservative. It validates required identity and metric fields but still allows benchmark-family-specific extension fields.
