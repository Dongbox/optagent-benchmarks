# OptAgent Benchmarks

`optagent-benchmarks` is the independently maintained benchmark repository for
OptAgent. Benchmark maintainers work from released or supplied OptAgent wheels;
access to the OptAgent source repository is not required.

This repository owns benchmark cases and verifiers, suite execution, capability
evidence, paired GA comparisons, and telemetry-derived evaluation artifacts. It
does not own OptAgent runtime semantics or solver implementation details.

## Documentation

- [Authority and capability](docs/authority.md)
- [GA strategy comparison](docs/ga-comparison.md)
- [Telemetry, metrics, and artifacts](docs/telemetry-artifacts.md)
- [Case sources and maintenance](benchmarks/cases/README.md)

## Setup

The checkout directory may have any name. Run all commands from its root:

```bash
git clone https://github.com/Dongbox/optagent-benchmarks.git optagent-benchmarks
cd optagent-benchmarks
python -m venv .venv
./.venv/bin/python -m pip install --upgrade pip pytest ruff
./.venv/bin/python -m pip install /path/to/optagent.whl
```

Use a clean environment for release evidence. Do not install an editable
OptAgent source checkout there. For explicit local source development only, set
`OPTAGENT_SOURCE_ROOT=/path/to/optagent`.

## Command Guide

All commands run from the repository root:

```bash
./.venv/bin/python benchmark.py <command> [options]
```

| Command | Use it when |
| --- | --- |
| `list-cases` | Discover case IDs, families, tiers, and comparison coordinates. |
| `run` | Diagnose one case or strategy quickly without creating authoritative evidence. |
| `suite` | Execute a repeatable case matrix and write a benchmark run workspace. |
| `authority` | Verify release capability from one exact OptAgent wheel. |
| `compare-ga` | Run, compare, or explicitly promote paired GA strategy evidence. |
| `publish-telemetry` | Convert canonical runtime telemetry into immutable metric artifacts. |
| `dashboard` | Render a static view from published telemetry artifacts. |
| `compare-runs` | Review two suite workspaces and optionally record a curated decision. |
| `publish-results` | Publish suite rows into the legacy Git-managed dashboard dataset. |
| `generate-results-index` | Rebuild or verify the legacy dashboard index and aggregates. |

### `list-cases`

Use this before selecting a `--case`, family, tier, or model style. It prints
the filtered registry inventory as JSON and does not execute a solver.

```bash
./.venv/bin/python benchmark.py list-cases

./.venv/bin/python benchmark.py list-cases \
  --family sequence_blackbox_tsp \
  --tier smoke
```

### `run`

Use this for a fast local smoke test, case development, or failure diagnosis.
The JSON printed to standard output is diagnostic evidence only: it is not an
authoritative baseline and cannot promote a strategy.

```bash
./.venv/bin/python benchmark.py run \
  --case tsplib_berlin52 \
  --strategy ga \
  --model-style sequence_var_external_call \
  --seed 11 \
  --max-iterations 10 \
  --population-size 8 \
  --time-limit-s 0.5 \
  --no-download
```

Repeat `--strategy` or `--model-style` when comparing multiple routes for the
same case.

### `suite`

Use this for repeatable smoke, calibration, or matrix runs. It writes a run
workspace containing inventory, environment, result rows, and telemetry under
`--output-root`; the default is `docs/evals/benchmark-suite/runs/`.

```bash
./.venv/bin/python benchmark.py suite \
  --family sequence_blackbox_tsp \
  --tier smoke \
  --strategy ga \
  --output-root /tmp/benchmark-runs \
  --timestamp local-ga-smoke
```

For multi-seed calibration, repeat `--calibration-seed`. For concurrency
analysis, use `--parallel-matrix` or repeat `--thread-count`. To inspect the
selected matrix without solving, use `--list-inventory`.

### `authority`

Use this only for release-gate capability evidence. The command creates an
isolated environment, installs the exact wheel, executes the frozen authority
matrix, independently verifies solutions, and writes checksummed rows and a
manifest. Use a clean benchmark checkout and an empty output directory.

```bash
./.venv/bin/python benchmark.py authority \
  --output-dir /artifact-storage/authoritative-baseline \
  --wheel /path/to/optagent.whl \
  --optagent-commit <optagent-sha> \
  --python-executable ./.venv/bin/python \
  --memory-limit-mb 4096 \
  --allow-download \
  --require-authoritative
```

`--require-authoritative` returns a non-zero status when the generated evidence
does not satisfy the authority gates. See [Authority and capability](docs/authority.md).

### `compare-ga`

Use this for controlled baseline/challenger evaluation of GA changes. It has
three actions.

Run two wheels through the same frozen protocol in separate environments:

```bash
./.venv/bin/python benchmark.py compare-ga run-pair \
  --protocol ga_release_smoke_v1 \
  --baseline-wheel /path/to/baseline.whl \
  --challenger-wheel /path/to/challenger.whl \
  --baseline-commit <baseline-sha> \
  --challenger-commit <challenger-sha> \
  --output-dir /tmp/ga-smoke
```

Recompute a comparison from two existing immutable run artifacts:

```bash
./.venv/bin/python benchmark.py compare-ga compare \
  --baseline /artifacts/baseline \
  --challenger /artifacts/challenger \
  --output-dir /tmp/ga-recomparison
```

Promote an approved `improved` comparison into a baseline registry:

```bash
./.venv/bin/python benchmark.py compare-ga promote \
  --comparison-dir /artifacts/ga-holdout/comparison \
  --registry /artifact-storage/ga-baselines.json \
  --approved-by <reviewer-id>
```

Smoke detects invalid evidence and obvious regressions but cannot produce an
`improved` promotion verdict. Continue with `ga_calibration_v1` and then
`ga_release_holdout_v1`. See [GA strategy comparison](docs/ga-comparison.md).

### `publish-telemetry`

Use this after obtaining canonical telemetry JSON projections. It derives the
five-dimensional metrics, statistical evidence, anytime curves, throughput,
strategy feedback, checksums, and the immutable dashboard input artifact.

```bash
./.venv/bin/python benchmark.py publish-telemetry \
  /path/to/run-a-telemetry.json \
  /path/to/run-b-telemetry.json \
  --output-dir /tmp/telemetry-artifacts \
  --reference tsplib_berlin52=7542 \
  --target tsplib_berlin52=7600
```

Repeat `--reference` and `--target` for additional instance IDs. See
[Telemetry, metrics, and artifacts](docs/telemetry-artifacts.md).

### `dashboard`

Use this only after `publish-telemetry`. It reads the immutable artifact
directory, validates its checksums, and writes a static dashboard directory.
It does not recompute metrics from raw logs or suite rows.

```bash
./.venv/bin/python benchmark.py dashboard \
  /tmp/telemetry-artifacts \
  --output-root /tmp/telemetry-dashboard \
  --dashboard-id ga-calibration-20260712
```

### `compare-runs`

Use this to compare two artifact-producing `suite` workspaces. Without
`--report-id` it prints JSON or Markdown. With `--report-id` it also writes a
curated report and appends a decision to the benchmark ledger.

```bash
./.venv/bin/python benchmark.py compare-runs \
  /artifact-storage/runs/accepted-baseline \
  /artifact-storage/runs/candidate \
  --format markdown \
  --report-id ga-candidate-20260712 \
  --baseline-commit <baseline-sha> \
  --candidate-commit <candidate-sha> \
  --decision needs_follow_up \
  --follow-up "run release holdout"
```

This command compares suite-level rows; use `compare-ga` when the decision must
follow the frozen paired GA protocol and Delta Index rules.

### `publish-results`

This is a dashboard-maintainer and CI command for the legacy Git-managed result
dataset under `benchmarks/presentation/results/`. It converts one `suite` run
workspace into a published summary with explicit OptAgent and benchmark
provenance, then regenerates aggregates unless `--no-regenerate` is set.

```bash
./.venv/bin/python benchmark.py publish-results \
  /artifact-storage/runs/gha-smoke \
  --optagent-version 1.2.0rc1 \
  --optagent-commit <optagent-sha> \
  --optagent-commit-url https://example.invalid/optagent/commit/<optagent-sha> \
  --optagent-wheel-sha256 sha256:<wheel-sha256> \
  --benchmarks-commit <benchmarks-sha> \
  --benchmarks-commit-url https://github.com/Dongbox/optagent-benchmarks/commit/<benchmarks-sha>
```

Do not use this command as the input path for current telemetry metrics.

### `generate-results-index`

This is also a legacy dashboard-maintainer and CI command. It rebuilds
`results/index.json` and the aggregate JSON files from committed published run
summaries. Use `--check` in CI to fail when generated data is stale without
rewriting it.

```bash
./.venv/bin/python benchmark.py generate-results-index

./.venv/bin/python benchmark.py generate-results-index --check
```

Use `--results-root` and `--aggregates-root` only when validating an alternate
dataset outside the repository defaults.

Run `./.venv/bin/python benchmark.py --help` or append `--help` to any command
for the complete option list.

## Development

```bash
./.venv/bin/python -m pytest -q
./.venv/bin/ruff check benchmark.py benchmarks tests
./.venv/bin/python -m compileall benchmark.py benchmarks tests
./.venv/bin/python benchmark.py list-cases --tier smoke
```

For case changes, also run one small `--no-download` case in the affected
family. Generated output and downloaded raw caches are not documentation and
must not be committed unless a case contract governs them as source evidence.

## Repository Layout

```text
benchmark.py       single command-line entrypoint
benchmarks/        implementation, cases, verifiers, and presentation code
docs/              benchmark-owned policies and data contracts
tests/             governance, artifact, metric, and case regression tests
```
