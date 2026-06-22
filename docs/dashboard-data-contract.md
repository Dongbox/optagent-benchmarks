# Dashboard Data Contract

This document defines the generated static JSON files consumed by `optagent-dashboard`.

The dashboard must not scan the Git tree. It reads generated files first, then loads a run summary or artifact only when a user opens a detail view.

## Generate Data

Run from a checkout that contains the `benchmarks/` Python package:

```bash
python -m benchmarks.runners.generate_dashboard_data
```

Validation-only mode:

```bash
python -m benchmarks.runners.generate_dashboard_data --check
```

The generator reads immutable run summaries under `results/` and rewrites:

```text
results/index.json
aggregates/leaderboard.json
aggregates/commit-history.json
aggregates/strategy-comparison.json
aggregates/runtime-quality.json
```

Generated files are deterministic for the same input run summaries. By default, `generated_at` is the latest `created_at` value among input runs, not wall-clock time.

## Path Rules

Dashboard-facing paths use `/results/...` so the dashboard can serve copied benchmark data from a static public root.

Examples:

```text
/results/sample/ga/2026/06/sample-ga-20260622-000000-3f8a1d2.json
/results/sample/ga/2026/06/sample-ga-20260622-000000-3f8a1d2/trace.json
```

If `optagent-dashboard` copies benchmark data to `public/data`, its loader may prefix these paths with `/data`.

## `results/index.json`

Entrypoint for run discovery.

Shape:

```json
{
  "schema_version": 1,
  "generated_at": "2026-06-22T00:01:00Z",
  "runs": [
    {
      "run_id": "sample-ga-20260622-000000-3f8a1d2",
      "benchmark_group": "sample",
      "benchmark_id": "sample_tiny_sequence",
      "family": "sequence_blackbox_tsp",
      "tier": "smoke",
      "strategy": "ga",
      "strategy_profile": "ga_sample_v1",
      "seed": 123,
      "optagent_commit": "3f8a1d2",
      "benchmark_commit": "7a91e4f",
      "created_at": "2026-06-22T00:00:00Z",
      "status": "success",
      "feasible": true,
      "summary_path": "/results/sample/ga/2026/06/sample-ga-20260622-000000-3f8a1d2.json"
    }
  ],
  "groups": {
    "sample": {
      "ga": [
        "/results/sample/ga/2026/06/sample-ga-20260622-000000-3f8a1d2.json"
      ]
    }
  }
}
```

Dashboard usage:

- populate benchmark group lists;
- locate run summaries without scanning directories;
- open Run Detail through `summary_path`.

## `aggregates/leaderboard.json`

Entrypoint for group-level ranking.

Shape:

```json
{
  "schema_version": 1,
  "generated_at": "2026-06-22T00:01:00Z",
  "groups": {
    "sample": {
      "benchmark_count": 1,
      "strategy_count": 2,
      "run_count": 2,
      "entries": [
        {
          "rank": 1,
          "benchmark_group": "sample",
          "strategy": "ga",
          "run_count": 1,
          "success_rate": 1.0,
          "feasible_rate": 1.0,
          "best_run_id": "sample-ga-20260622-000000-3f8a1d2",
          "best_summary_path": "/results/sample/ga/2026/06/sample-ga-20260622-000000-3f8a1d2.json",
          "best_objective": 125.2,
          "best_cost": 125.2,
          "best_gap_rel": 0.0433333333,
          "best_runtime_ms": 532,
          "latest_created_at": "2026-06-22T00:00:00Z",
          "optagent_commit": "3f8a1d2",
          "optagent_commit_url": "https://github.com/Dongbox/optagent/commit/3f8a1d2"
        }
      ]
    }
  }
}
```

Ranking rule:

1. higher feasible rate;
2. higher success rate;
3. lower `gap_rel`, or lower `objective`, or lower `best_cost`;
4. lower runtime;
5. strategy name.

## `aggregates/commit-history.json`

Entrypoint for trend by OptAgent commit.

Shape:

```json
{
  "schema_version": 1,
  "generated_at": "2026-06-22T00:01:00Z",
  "series": [
    {
      "key": "sample/sample_tiny_sequence/ga/seed-123",
      "benchmark_group": "sample",
      "benchmark_id": "sample_tiny_sequence",
      "strategy": "ga",
      "seed": 123,
      "metric": "best_cost",
      "points": [
        {
          "commit": "3f8a1d2",
          "commit_url": "https://github.com/Dongbox/optagent/commit/3f8a1d2",
          "created_at": "2026-06-22T00:00:00Z",
          "run_id": "sample-ga-20260622-000000-3f8a1d2",
          "summary_path": "/results/sample/ga/2026/06/sample-ga-20260622-000000-3f8a1d2.json",
          "status": "success",
          "feasible": true,
          "objective": 125.2,
          "best_cost": 125.2,
          "gap_rel": 0.0433333333,
          "runtime_ms": 532
        }
      ]
    }
  ]
}
```

Series are grouped by benchmark group, benchmark id, strategy, and seed.

## `aggregates/strategy-comparison.json`

Entrypoint for same-case strategy comparison.

Shape:

```json
{
  "schema_version": 1,
  "generated_at": "2026-06-22T00:01:00Z",
  "comparisons": [
    {
      "benchmark_group": "sample",
      "benchmark_id": "sample_tiny_sequence",
      "tier": "smoke",
      "strategies": [
        {
          "strategy": "ga",
          "run_count": 1,
          "success_rate": 1.0,
          "feasible_rate": 1.0,
          "best_run_id": "sample-ga-20260622-000000-3f8a1d2",
          "best_summary_path": "/results/sample/ga/2026/06/sample-ga-20260622-000000-3f8a1d2.json",
          "best_objective": 125.2,
          "best_cost": 125.2,
          "best_gap_rel": 0.0433333333,
          "avg_runtime_ms": 532,
          "latest_run_id": "sample-ga-20260622-000000-3f8a1d2",
          "latest_summary_path": "/results/sample/ga/2026/06/sample-ga-20260622-000000-3f8a1d2.json",
          "latest_status": "success",
          "latest_feasible": true,
          "latest_created_at": "2026-06-22T00:00:00Z"
        }
      ]
    }
  ]
}
```

Comparisons are grouped by benchmark group, benchmark id, and tier.

## `aggregates/runtime-quality.json`

Entrypoint for runtime-vs-quality scatter charts.

Shape:

```json
{
  "schema_version": 1,
  "generated_at": "2026-06-22T00:01:00Z",
  "points": [
    {
      "run_id": "sample-ga-20260622-000000-3f8a1d2",
      "summary_path": "/results/sample/ga/2026/06/sample-ga-20260622-000000-3f8a1d2.json",
      "benchmark_group": "sample",
      "benchmark_id": "sample_tiny_sequence",
      "family": "sequence_blackbox_tsp",
      "tier": "smoke",
      "strategy": "ga",
      "strategy_profile": "ga_sample_v1",
      "seed": 123,
      "created_at": "2026-06-22T00:00:00Z",
      "optagent_commit": "3f8a1d2",
      "optagent_commit_url": "https://github.com/Dongbox/optagent/commit/3f8a1d2",
      "status": "success",
      "feasible": true,
      "runtime_ms": 532,
      "objective": 125.2,
      "best_cost": 125.2,
      "gap_rel": 0.0433333333,
      "time_to_first_feasible_ms": 80,
      "time_to_best_ms": 410,
      "evaluations_per_s": 1234.5,
      "improvement_per_second": 42.1
    }
  ]
}
```

Use this file for scatter plots and anytime-solver overview tables. Detailed trace charts should still load the run summary and optional `trace.json` artifact on demand.
