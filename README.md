# OptAgent Modeling-Native Benchmarks

This directory owns performance benchmark inputs and harness code. It is separate from `examples/`: examples teach API usage, while benchmarks provide repeatable evidence for strategy and backend optimization.

The first catalog is generated from public benchmark metadata and external objective references:

```bash
./.venv/bin/python scripts/build_modeling_native_benchmark_catalog.py
```

Generated outputs:

- `benchmarks/catalog/modeling-native-catalog-v1.json`: source-of-truth catalog checked into the repo.
- `docs/evals/benchmark-suite/catalogs/modeling-native-catalog-v1.md`: readable catalog snapshot.

Local or CI runs should write immutable artifacts under `docs/evals/benchmark-suite/runs/<timestamp>/`. Curated comparisons belong under `docs/evals/benchmark-suite/reports/`.

## Run Status

The suite is runner-ready for:

- `interval_job_shop`: JSPLIB ScheduleOpt JSON, modeled as one `interval_var` per operation, machine `sequence_var` plus `no_overlap`, job `precedence`, and a makespan objective. The runner emits a `solve_cpsat` exact baseline row plus GA/ALNS/Tabu strategy rows.
- `sequence_blackbox_tsp`: TSPLIB `.tsp` / `.tsp.gz`, modeled as `sequence_var` tour plus deterministic `external_call` tour length.
- `sequence_quadratic_assignment`: QAPLIB `.dat`, modeled as `sequence_var` facility-to-location assignment plus deterministic `external_call` quadratic cost.

The runnable strategy families use `GaConfig`, `AlnsConfig`, and `TabuConfig`, and emit `config.json`, `results.jsonl`, `results.csv`, `summary.json`, and `report.md`. JSPLIB additionally emits a `cpsat` exact-baseline route. Other catalog families are selected and described, but their family runners are not implemented yet.

For local native development, run against the current native build tree so the benchmark does not accidentally load an older editable-install extension:

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.run --tier smoke
```

By default this runs the JSPLIB, TSPLIB, and QAPLIB smoke cases with GA, ALNS, and Tabu, plus CP-SAT exact baseline rows for JSPLIB. Outputs are written to:

```text
docs/evals/benchmark-suite/runs/<timestamp>/
```

Use tighter budgets for harness smoke checks:

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.run \
  --tier smoke \
  --max-iterations 5 \
  --time-limit-s 2 \
  --population-size 6
```

## Structure

| Path | Responsibility |
| --- | --- |
| `catalog/` | Versioned catalogs with selected cases, external references, and OptAgent modeling declarations. |
| `definitions/<family>/` | Family-level selected case manifests and modeling notes. |
| `loaders/` | Public-format loaders for JSPLIB, PSPLIB, TSPLIB, QAPLIB, and MPS data. |
| `models/` | OptAgent `ModelBuilder` construction per benchmark family. |
| `runners/` | Shared strategy and exact runners that consume catalog case ids. |
| `data-cache/` | Local ignored cache for downloaded public instances. |

## Source Policy

Catalog objective references must come from public benchmark sources, not local OptAgent runs. Local results may be compared against the catalog, but they must not become catalog ground truth.
