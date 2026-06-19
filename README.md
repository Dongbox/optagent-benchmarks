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

The suite is runner-ready for all catalog families:

- `interval_job_shop`: JSPLIB ScheduleOpt JSON, modeled as one `interval_var` per operation, machine `sequence_var` plus `no_overlap`, job `precedence`, and a makespan objective. The runner emits a `solve_cpsat` exact baseline row plus GA/ALNS strategy rows.
- `sequence_blackbox_tsp`: TSPLIB `.tsp` / `.tsp.gz`, modeled as `sequence_var` tour plus deterministic `external_call` tour length.
- `sequence_quadratic_assignment`: QAPLIB `.dat`, modeled as `sequence_var` facility-to-location assignment plus deterministic `external_call` quadratic cost.
- `cumulative_resource_scheduling`: PSPLIB `.rcp` / `.sm` resource-constrained project scheduling, modeled with `interval_var`, precedence, cumulative renewable resources, and a makespan objective. The runner emits a `solve_cpsat` exact baseline row plus GA/ALNS strategy rows.
- `exact_linear_mip`: MIPLIB `.mps` / `.mps.gz`, modeled as canonical linear MP with bool/int/float variables, linear constraints, and a linear objective. This family is exact-only and emits an OptX baseline row; GA/ALNS/Tabu are intentionally ignored because the catalog cases are pure linear MIP baselines rather than native search domains.

The benchmark suite uses family-aware strategy routes and emits `config.json`, `results.jsonl`, `results.csv`, `summary.json`, and `report.md`. Every row includes a stable `strategy_profile`, `budget_profile`, `model_style`, and effective budget fields so runs can be compared after strategy tuning. JSPLIB and PSPLIB use `GaConfig` and `AlnsConfig` plus `cpsat` exact-baseline rows; standalone Tabu and standalone LNS are not scheduling benchmark routes because both currently fall back without producing useful feasible scheduling rows. Requested scheduling `tabu` or `lns` names are replaced by `alns` and recorded in `strategy_substitutions`. TSPLIB and QAPLIB keep `GaConfig`, `AlnsConfig`, and `TabuConfig` sequence/permutation rows. MIPLIB emits `optx` exact-baseline rows only. Requested strategy names on MIPLIB runs are recorded in row metadata as ignored requests while `mip_heuristic_route_enabled=false`; a future MIP heuristic must use a dedicated MILP-native route and must not replace the OptX exact baseline.

Named Phase 5 profiles include:

- `ga_scheduling_feasibility_v1`
- `alns_scheduling_repair_v1`
- `ga_tsp_graph_v1` / `alns_tsp_graph_v1`
- `ga_qap_delta_v1` / `alns_qap_delta_v1`
- `cpsat_scheduling_exact_v1`
- `optx_mip_exact_v1`

Budgets are resolved by family and tier with a ceiling policy. CLI budget flags remain upper bounds; smoke runs stay short, calibration runs allow more optimization comparison, and full runs provide the performance baseline. Reports show both strategy rows and exact-baseline rows explicitly.

For local native development, run against the current native build tree so the benchmark does not accidentally load an older editable-install extension:

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.run --tier smoke
```

By default this runs the JSPLIB, TSPLIB, and QAPLIB smoke cases with family-aware strategy routes. JSPLIB emits GA/ALNS plus CP-SAT exact baseline rows; TSPLIB and QAPLIB emit GA/ALNS/Tabu rows. Outputs are written to:

```text
docs/evals/benchmark-suite/runs/<timestamp>/
```

Run the remaining exact/scheduling families explicitly:

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.run \
  --family cumulative_resource_scheduling \
  --tier calibration \
  --max-iterations 5 \
  --time-limit-s 2 \
  --population-size 6

PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.run \
  --family exact_linear_mip \
  --tier smoke \
  --time-limit-s 10
```

Use tighter budgets for harness smoke checks:

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.run \
  --tier smoke \
  --max-iterations 5 \
  --time-limit-s 2 \
  --population-size 6
```

Compare two immutable run directories:

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.compare \
  docs/evals/benchmark-suite/runs/<baseline> \
  docs/evals/benchmark-suite/runs/<candidate> \
  --format markdown
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
