# Result JSON Contract

This document defines Phase 1 benchmark result files for `optagent-benchmarks`.

The current fact layer is Git-managed JSON. Each benchmark run writes a new immutable summary file and, when useful, a sibling artifact directory. Generated indexes and aggregates are Phase 2 concerns.

Dashboard-facing generated data is defined in:

```text
docs/dashboard-data-contract.md
```

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

## Evidence Tiers

Not every benchmark output is a dashboard fact.

Dashboard-persisted evidence is limited to immutable run summaries under `presentation/results/`, optional sibling artifacts, generated `presentation/results/index.json`, and generated `presentation/aggregates/*.json`. These files are the long-term static data contract for `optagent-dashboard`.

Suite-run evidence lives in a run directory such as:

```text
docs/evals/benchmark-suite/runs/<timestamp>/
```

The runner may write `config.json`, `inventory.json`, `run_metadata.json`, `rows.jsonl`, `results.jsonl`, `results.csv`, `anytime.jsonl`, `curves.jsonl`, `throughput.jsonl`, `summary.json`, and `report.md`. These files are audit evidence for one execution. Dashboard publication must convert selected rows into run summaries instead of making the dashboard read those runner-private files directly.

Local ad-hoc evaluations are useful for strategy tuning and diagnostics, but they should not be promoted to dashboard history unless the run records reproducible catalog inputs, OptAgent commit, benchmark commit, wheel hash, seed, budget, and environment. Promoted local runs must pass the same schema and generated-data checks as CI runs.

Error rows are valid evidence. A run that fails inside OptAgent or the benchmark route must still be persisted with `metrics.status = "error"`, `metrics.feasible = false`, `metrics.error_type`, and `metrics.error_message` so the dashboard can show recording success separately from solver success.

## Comparable Environment

Dashboard-worthy quality comparisons should normally be produced by GitHub Actions or another explicitly documented standard runner.

Recommended minimum environment fields:

- runner name, such as `github-actions` or `local-smoke`;
- OS / platform;
- Python version;
- OptAgent wheel hash;
- OptAgent native extension availability when applicable;
- benchmark data cache/download mode;
- CPU information when available;
- thread count and other budget fields when they affect runtime.

Local smoke runs can prove that `optagent-benchmarks` produces dashboard-recordable JSON. They do not, by themselves, establish a comparable quality trend unless the environment is standardized and recorded.

## Schema

The current JSON Schema is:

```text
results/schema/run-v1.schema.json
```

The schema is intentionally conservative. It validates required identity and metric fields but still allows benchmark-family-specific extension fields.

## Generated Indexes

After adding run summary files, regenerate static dashboard data:

```bash
python -m benchmarks.presentation.generate_dashboard_data
```

The generator rewrites:

```text
results/index.json
aggregates/leaderboard.json
aggregates/commit-history.json
aggregates/strategy-comparison.json
aggregates/runtime-quality.json
```

These files are derived from run summaries and can be regenerated deterministically.
