# OptAgent Benchmarks

`optagent-benchmarks` is the independently maintained benchmark repository for
OptAgent. Benchmark maintainers work from released or supplied OptAgent wheels;
access to the OptAgent source repository is not required.

This repository owns:

- benchmark cases, raw-data loaders, references, and independent verifiers;
- lightweight case and suite runners;
- authoritative capability evidence;
- paired GA baseline/challenger comparisons;
- telemetry-derived metrics and immutable dashboard artifacts.

It does not own OptAgent runtime semantics or solver implementation details.

## Documentation

- [Authority and capability](docs/authority.md)
- [GA strategy comparison](docs/ga-comparison.md)
- [Telemetry, metrics, and artifacts](docs/telemetry-artifacts.md)
- [Case sources and maintenance](cases/README.md)

These files are canonical. Documentation in an OptAgent source checkout must
link here instead of duplicating benchmark policy.

## Setup

Clone the repository into a directory named `benchmarks`. The package name is
`benchmarks`, so commands run from the repository directory with its parent on
`PYTHONPATH`.

```bash
git clone https://github.com/Dongbox/optagent-benchmarks.git benchmarks
cd benchmarks
python -m venv .venv
./.venv/bin/python -m pip install --upgrade pip pytest ruff
```

For local case and suite runs, install the wheel being measured:

```bash
./.venv/bin/python -m pip install /path/to/optagent.whl
```

Use a clean environment for release evidence. Do not install an editable
OptAgent source checkout into that environment.

All examples below run from the `benchmarks/` directory:

```bash
export PYTHONPATH=..
```

On Windows PowerShell use `$env:PYTHONPATH = ".."` and the corresponding
`.venv\Scripts\python.exe` path.

## Recommended Workflow

```text
single-case smoke
    -> suite smoke
    -> GA paired smoke (for GA changes)
    -> calibration
    -> frozen configuration
    -> release holdout / authoritative baseline
    -> explicit baseline promotion
```

### 1. Discover Cases

```bash
PYTHONPATH=.. ./.venv/bin/python -m benchmarks.run --list-cases
```

The registry is the source of truth for case IDs, tiers, families, model styles,
references, and lifecycle state. Source README files intentionally do not
duplicate the complete inventory.

### 2. Run One Case

```bash
PYTHONPATH=.. ./.venv/bin/python -m benchmarks.run \
  --case tsplib_berlin52 \
  --strategy ga \
  --model-style sequence_var_external_call \
  --no-download \
  --max-iterations 10 \
  --population-size 8 \
  --time-limit-s 0.5
```

Use this entrypoint for case development and diagnosis. Its output is not an
authoritative capability claim and must not be used to promote a strategy
baseline.

### 3. Run A Suite

```bash
PYTHONPATH=.. ./.venv/bin/python -m benchmarks.presentation.suite \
  --family sequence_blackbox_tsp \
  --tier smoke \
  --strategy ga \
  --timestamp local-smoke
```

Suite workspaces are execution evidence. Publish telemetry artifacts before
feeding results to the dashboard.

### 4. Compare A GA Change

Build or obtain baseline and challenger wheels, then run the frozen smoke
protocol:

```bash
PYTHONPATH=.. ./.venv/bin/python -m benchmarks.strategy_comparison run-pair \
  --protocol ga_release_smoke_v1 \
  --baseline-wheel /path/to/baseline.whl \
  --challenger-wheel /path/to/challenger.whl \
  --baseline-commit <baseline-sha> \
  --challenger-commit <challenger-sha> \
  --output-dir /tmp/ga-smoke
```

`run-pair` installs each wheel into a separate temporary environment. The
benchmark maintainer does not need either OptAgent source checkout.

Smoke detects invalid evidence and obvious regressions but cannot return an
`improved` promotion verdict. Continue with:

```bash
--protocol ga_calibration_v1
--protocol ga_release_holdout_v1
```

Use a new empty output directory for each run. Read:

```text
comparison/feedback.md
comparison/delta_index.json
comparison/dimension_metrics.json
comparison/statistical_evidence.json
```

See [GA strategy comparison](docs/ga-comparison.md) for the Delta Index,
validity gates, statistical rules, and promotion process.

### 5. Produce An Authoritative Baseline

Use an exact wheel and a clean empty output directory:

```bash
PYTHONPATH=.. ./.venv/bin/python -m benchmarks.authoritative_baseline \
  --output-dir /artifact-storage/authoritative-baseline \
  --wheel /path/to/optagent.whl \
  --python-executable ./.venv/bin/python \
  --allow-download \
  --require-authoritative
```

This command installs the wheel into an isolated child environment and records
wheel, benchmark, platform, backend, case, and evidence checksums. See
[Authority and capability](docs/authority.md).

## Telemetry And Dashboard Artifacts

Publish canonical runtime telemetry:

```bash
PYTHONPATH=.. ./.venv/bin/python -m benchmarks.telemetry_artifacts \
  /path/to/run-telemetry.json \
  --output-dir /tmp/telemetry-artifacts \
  --reference toy-001=10.0
```

Render a dashboard from the immutable artifact:

```bash
PYTHONPATH=.. ./.venv/bin/python -m benchmarks.presentation.dashboard \
  /tmp/telemetry-artifacts \
  --output-root /tmp/telemetry-dashboard
```

Dashboard code must not read authority artifacts, runner workspaces, raw logs,
or Git-managed historical result trees. See
[Telemetry, metrics, and artifacts](docs/telemetry-artifacts.md).

## Development

Run the complete repository suite:

```bash
PYTHONPATH=.. ./.venv/bin/python -m pytest -q
./.venv/bin/ruff check .
./.venv/bin/python -m compileall cases presentation *.py
```

For case changes, also run `--list-cases` and one small `--no-download` case in
the affected family.

Generated benchmark output and downloaded raw caches are not documentation.
Do not commit them unless the case contract explicitly governs them as source
evidence.

## Repository Layout

```text
cases/          case declarations, loaders, references, verifiers, raw caches
docs/           benchmark-owned policy and data contracts
presentation/   suite workspaces, dashboard rendering, historical adapters
tests/          governance, artifact, metric, and case regression tests
```
